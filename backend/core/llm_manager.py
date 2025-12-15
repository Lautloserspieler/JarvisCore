import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
from datetime import datetime
import threading
import time

# Import HF Runtime
from core.hf_inference import hf_runtime

class DownloadTask:
    """Background download task with real-time progress tracking"""
    
    def __init__(self, model_id: str, model: Dict, model_path: Path, llm_manager):
        self.model_id = model_id
        self.model = model
        self.model_path = model_path
        self.llm_manager = llm_manager
        self.cancelled = False
        self.error = None
        self.start_time = time.time()
        
    async def run(self):
        """Run download in background with progress tracking"""
        from core.logger import log_info, log_error, log_warning
        
        try:
            # Initialize
            await self._update_progress(5, 'initializing', 'Initialisiere Download...')
            
            # Import or install huggingface_hub
            try:
                from huggingface_hub import snapshot_download, HfApi
                log_info("Using huggingface_hub for download", category='model')
            except ImportError:
                log_info("huggingface_hub not installed. Installing...", category='model')
                await self._update_progress(10, 'installing_deps', 'Installiere Dependencies...')
                
                import subprocess
                result = subprocess.run(
                    ["pip", "install", "huggingface_hub"],
                    capture_output=True,
                    timeout=300  # 5 min timeout
                )
                
                if result.returncode != 0:
                    raise Exception(f"Failed to install huggingface_hub: {result.stderr.decode()}")
                
                from huggingface_hub import snapshot_download, HfApi
                log_info("huggingface_hub installed successfully", category='model')
            
            # Get HF token from environment if available
            hf_token = os.getenv('HF_TOKEN', None)
            if hf_token:
                log_info("Using HuggingFace token from environment", category='model')
            else:
                log_info("No HF token found - using public access", category='model')
            
            # Create model directory
            self.model_path.mkdir(exist_ok=True)
            
            # Get repository info for size estimation
            await self._update_progress(15, 'fetching_metadata', 'Lade Modell-Metadaten...')
            
            try:
                api = HfApi()
                repo_info = api.repo_info(
                    repo_id=self.model['hf_model'],
                    repo_type='model',
                    token=hf_token
                )
                
                # Calculate total size
                total_size = 0
                file_count = 0
                for sibling in repo_info.siblings:
                    if self._should_download_file(sibling.rfilename):
                        total_size += sibling.size if sibling.size else 0
                        file_count += 1
                
                total_size_gb = total_size / (1024**3)
                log_info(f"Model size: {total_size_gb:.2f} GB ({file_count} files)", category='model')
                
                # Store for progress calculation
                self.total_size = total_size
                self.file_count = file_count
                
            except Exception as e:
                log_warning(f"Could not fetch repo metadata: {e}", category='model')
                self.total_size = 0
                self.file_count = 0
            
            await self._update_progress(20, 'downloading', f'Lade {self.file_count} Dateien herunter...')
            
            log_info(f"Downloading to {self.model_path}", category='model')
            log_info(f"This may take several minutes depending on model size ({self.model['size']})", category='model')
            
            # Start progress monitoring in background
            monitor_task = asyncio.create_task(self._monitor_download_progress())
            
            # Download in thread pool to not block event loop
            loop = asyncio.get_event_loop()
            
            try:
                result_path = await loop.run_in_executor(
                    None,
                    self._download_snapshot,
                    hf_token
                )
            finally:
                # Stop monitoring
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Verify download
            await self._update_progress(95, 'verifying', 'Verifiziere Download...')
            
            is_complete, status_msg = self.llm_manager._is_model_complete(self.model_path)
            
            if not is_complete:
                raise Exception(f"Download incomplete: {status_msg}")
            
            # Calculate final size
            files = [f for f in self.model_path.iterdir() if f.is_file() and not f.name.startswith('.')]
            final_size = sum(f.stat().st_size for f in files) / (1024**3)
            
            # Success!
            await self._update_progress(100, 'completed', f'Download abgeschlossen! ({final_size:.2f} GB)')
            
            # Mark as downloaded
            self.model['isDownloaded'] = True
            self.llm_manager.save_config()
            
            elapsed = time.time() - self.start_time
            log_info(f"Successfully downloaded {self.model['name']} in {elapsed:.1f}s", category='model')
            log_info(f"Model saved to: {self.model_path}", category='model')
            
            # Clean up progress after 5 seconds
            await asyncio.sleep(5)
            if self.model_id in self.llm_manager.download_progress:
                del self.llm_manager.download_progress[self.model_id]
            
        except asyncio.CancelledError:
            log_info(f"Download cancelled: {self.model['name']}", category='model')
            await self._update_progress(0, 'cancelled', 'Download abgebrochen')
            raise
            
        except Exception as e:
            error_msg = str(e)
            
            # Better error messages
            if "401" in error_msg or "GatedRepoError" in error_msg:
                error_msg = "Dieses Modell erfordert HuggingFace Login. Setze HF_TOKEN Umgebungsvariable."
            elif "404" in error_msg:
                error_msg = "Modell nicht gefunden auf HuggingFace."
            elif "timeout" in error_msg.lower():
                error_msg = "Download-Timeout. Bitte prüfe deine Internetverbindung."
            elif "403" in error_msg:
                error_msg = "Zugriff verweigert. Eventuell Rate-Limit erreicht oder Token ungültig."
            
            log_error(f"Failed to download {self.model['name']}: {error_msg}", category='model', exc_info=True)
            
            await self._update_progress(0, 'failed', f'Fehler: {error_msg}')
            self.error = error_msg
            
            # Clean up after 10 seconds
            await asyncio.sleep(10)
            if self.model_id in self.llm_manager.download_progress:
                del self.llm_manager.download_progress[self.model_id]
    
    def _should_download_file(self, filename: str) -> bool:
        """Check if file should be downloaded"""
        # Allow patterns
        allowed_extensions = [".json", ".safetensors", ".model", ".bin", ".txt"]
        allowed_prefixes = ["tokenizer", "vocab", "merges", "config"]
        
        # Check extensions
        if any(filename.endswith(ext) for ext in allowed_extensions):
            # Skip index files for multi-shard models (we want single files)
            if "index.json" in filename and "pytorch_model" in filename:
                return False
            return True
        
        # Check prefixes
        if any(filename.startswith(prefix) for prefix in allowed_prefixes):
            return True
        
        return False
    
    def _download_snapshot(self, hf_token):
        """Download snapshot (runs in thread pool)"""
        from huggingface_hub import snapshot_download
        
        return snapshot_download(
            repo_id=self.model['hf_model'],
            local_dir=str(self.model_path),
            local_dir_use_symlinks=False,
            resume_download=True,
            allow_patterns=["*.json", "*.safetensors", "*.model", "*.bin", "*.txt", "tokenizer*", "config.json", "vocab*", "merges.txt"],
            ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*pytorch_model.bin.index.json"],
            max_workers=4,
            token=hf_token if hf_token else False,
            etag_timeout=30,
            resume_download_timeout=30
        )
    
    async def _monitor_download_progress(self):
        """Monitor download progress by checking file sizes"""
        try:
            while True:
                await asyncio.sleep(2)  # Check every 2 seconds
                
                if not self.model_path.exists():
                    continue
                
                # Calculate current size
                files = [f for f in self.model_path.iterdir() if f.is_file() and not f.name.startswith('.')]
                current_size = sum(f.stat().st_size for f in files)
                current_files = len(files)
                
                if self.total_size > 0:
                    # Calculate progress based on size
                    progress = int(20 + (current_size / self.total_size) * 75)  # 20-95%
                    progress = min(95, max(20, progress))
                    
                    # Calculate ETA
                    elapsed = time.time() - self.start_time
                    if current_size > 0 and elapsed > 0:
                        speed_bps = current_size / elapsed
                        remaining_bytes = self.total_size - current_size
                        eta_seconds = remaining_bytes / speed_bps if speed_bps > 0 else 0
                        
                        # Format ETA
                        if eta_seconds > 60:
                            eta_str = f"~{int(eta_seconds / 60)}m"
                        else:
                            eta_str = f"~{int(eta_seconds)}s"
                        
                        # Format speed
                        speed_mbps = speed_bps / (1024**2)
                        
                        current_gb = current_size / (1024**3)
                        total_gb = self.total_size / (1024**3)
                        
                        message = f'Lade herunter: {current_gb:.2f}/{total_gb:.2f} GB ({speed_mbps:.1f} MB/s, ETA: {eta_str})'
                    else:
                        current_gb = current_size / (1024**3)
                        message = f'Lade herunter: {current_gb:.2f} GB ({current_files} Dateien)...'
                else:
                    # No size info, use file count
                    if self.file_count > 0:
                        progress = int(20 + (current_files / self.file_count) * 75)
                        progress = min(95, max(20, progress))
                    else:
                        progress = min(95, 20 + (current_files * 5))  # Rough estimate
                    
                    current_gb = current_size / (1024**3)
                    message = f'Lade herunter: {current_gb:.2f} GB ({current_files} Dateien)...'
                
                await self._update_progress(progress, 'downloading', message)
                
        except asyncio.CancelledError:
            pass
    
    async def _update_progress(self, progress: int, status: str, message: str):
        """Update progress and send via WebSocket"""
        self.llm_manager.download_progress[self.model_id] = {
            'progress': progress,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send via WebSocket
        try:
            from core.event_system import event_bus, Event, EventType
            await event_bus.publish(Event(
                EventType.MODEL_DOWNLOAD_PROGRESS,
                {
                    'modelId': self.model_id,
                    'progress': progress,
                    'status': status,
                    'message': message
                },
                source='llm_manager'
            ))
        except Exception:
            pass  # WebSocket not critical


class LLMManager:
    """Manager for local LLM models from Hugging Face"""
    
    # Version number for config - increment when model list changes
    CONFIG_VERSION = 3
    
    # Required files for a model to be considered "downloaded"
    REQUIRED_FILES = ['config.json']  # All models must have this
    MODEL_FILE_PATTERNS = ['.safetensors', '.bin', '.model']  # At least one of these
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.loaded_model = None
        self.model_config_path = self.models_dir / "models_config.json"
        self.download_progress = {}
        self.download_tasks = {}  # Track background tasks
        self.load_config()
        self.scan_downloaded_models()  # Scan on startup
    
    def get_default_config(self):
        """Get default configuration with 100% UNGATED HuggingFace models"""
        return {
            'config_version': self.CONFIG_VERSION,
            'available_models': [
                {
                    'id': 'tinyllama-1.1b',
                    'name': 'TinyLlama 1.1B Chat',
                    'provider': 'TinyLlama',
                    'size': '1.1B parameters (~2.2GB)',
                    'hf_model': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
                    'isActive': False,
                    'isDownloaded': False,
                    'capabilities': ['text-generation', 'chat', 'fast']
                },
                {
                    'id': 'stablelm-2-1.6b',
                    'name': 'StableLM 2 1.6B Chat',
                    'provider': 'Stability AI',
                    'size': '1.6B parameters (~3.2GB)',
                    'hf_model': 'stabilityai/stablelm-2-1_6b-chat',
                    'isActive': False,
                    'isDownloaded': False,
                    'capabilities': ['text-generation', 'chat', 'instruction-following']
                },
                {
                    'id': 'redpajama-3b',
                    'name': 'RedPajama 3B Instruct',
                    'provider': 'Together',
                    'size': '3B parameters (~6GB)',
                    'hf_model': 'togethercomputer/RedPajama-INCITE-Instruct-3B-v1',
                    'isActive': False,
                    'isDownloaded': False,
                    'capabilities': ['text-generation', 'chat', 'instruction-following']
                },
                {
                    'id': 'pythia-1.4b',
                    'name': 'Pythia 1.4B',
                    'provider': 'EleutherAI',
                    'size': '1.4B parameters (~2.8GB)',
                    'hf_model': 'EleutherAI/pythia-1.4b',
                    'isActive': False,
                    'isDownloaded': False,
                    'capabilities': ['text-generation', 'versatile']
                },
                {
                    'id': 'gpt2-xl',
                    'name': 'GPT-2 XL',
                    'provider': 'OpenAI',
                    'size': '1.5B parameters (~6GB)',
                    'hf_model': 'gpt2-xl',
                    'isActive': False,
                    'isDownloaded': False,
                    'capabilities': ['text-generation', 'classic', 'proven']
                },
                {
                    'id': 'openhermes-2.5',
                    'name': 'OpenHermes 2.5 Mistral 7B',
                    'provider': 'Teknium',
                    'size': '7B parameters (~14GB)',
                    'hf_model': 'teknium/OpenHermes-2.5-Mistral-7B',
                    'isActive': False,
                    'isDownloaded': False,
                    'capabilities': ['text-generation', 'chat', 'reasoning', 'code']
                }
            ],
            'active_model': None
        }
    
    def _is_model_complete(self, model_path: Path) -> tuple[bool, str]:
        """Check if model directory contains all required files"""
        if not model_path.exists():
            return False, "Directory does not exist"
        
        files = [f for f in model_path.iterdir() if f.is_file() and not f.name.startswith('.')]
        
        if len(files) == 0:
            return False, "No files found"
        
        # Check for config.json
        config_exists = any(f.name == 'config.json' for f in files)
        if not config_exists:
            return False, "Missing config.json (incomplete download)"
        
        # Check for at least one model weight file
        has_weights = any(
            any(f.name.endswith(pattern) for pattern in self.MODEL_FILE_PATTERNS)
            for f in files
        )
        
        if not has_weights:
            return False, "Missing model weights (incomplete download)"
        
        return True, f"Complete ({len(files)} files)"
    
    def load_config(self):
        """Load models configuration with version checking"""
        from core.logger import log_info, log_warning
        
        if self.model_config_path.exists():
            with open(self.model_config_path, 'r') as f:
                loaded_config = json.load(f)
            
            # Check config version
            config_version = loaded_config.get('config_version', 1)
            
            if config_version < self.CONFIG_VERSION:
                log_warning(f"Config version outdated ({config_version} < {self.CONFIG_VERSION}). Resetting to defaults...", category='model')
                self.config = self.get_default_config()
                self.save_config()
                log_info("Model configuration reset to latest version", category='model')
            else:
                self.config = loaded_config
        else:
            log_info("No config found, creating default configuration", category='model')
            self.config = self.get_default_config()
            self.save_config()
    
    def scan_downloaded_models(self):
        """Scan models directory and update download status"""
        from core.logger import log_info, log_debug, log_warning
        
        log_info("Scanning models directory for downloaded models...", category='model')
        
        downloaded_count = 0
        
        # First, get list of valid model IDs
        valid_model_ids = {model['id'] for model in self.config['available_models']}
        
        # Scan models directory for unknown folders
        if self.models_dir.exists():
            for item in self.models_dir.iterdir():
                if item.is_dir() and item.name not in valid_model_ids and item.name != 'models_config.json':
                    log_warning(f"Unknown model directory found: '{item.name}' - You can delete this folder", category='model')
        
        # Check configured models
        for model in self.config['available_models']:
            model_path = self.models_dir / model['id']
            
            # Check if model is complete
            is_complete, status_msg = self._is_model_complete(model_path)
            
            if is_complete:
                model['isDownloaded'] = True
                downloaded_count += 1
                
                # Calculate size
                files = [f for f in model_path.iterdir() if f.is_file() and not f.name.startswith('.')]
                total_size = sum(f.stat().st_size for f in files)
                size_gb = total_size / (1024**3)
                
                log_info(f"✓ Found: {model['name']} ({size_gb:.2f} GB, {len(files)} files)", category='model')
            else:
                model['isDownloaded'] = False
                if model_path.exists():
                    log_warning(f"✗ Incomplete: {model['name']} - {status_msg}", category='model')
                else:
                    log_debug(f"✗ Not found: {model['name']}", category='model')
        
        # Validate active model still exists
        active_id = self.config.get('active_model')
        if active_id:
            active_model = next((m for m in self.config['available_models'] if m['id'] == active_id), None)
            if active_model:
                if not active_model['isDownloaded']:
                    log_warning(f"Active model '{active_model['name']}' no longer found, clearing...", category='model')
                    self.config['active_model'] = None
                    for m in self.config['available_models']:
                        m['isActive'] = False
            else:
                log_warning(f"Active model ID '{active_id}' not in model list, clearing...", category='model')
                self.config['active_model'] = None
        
        self.save_config()
        
        if downloaded_count > 0:
            log_info(f"✓ Model scan complete: {downloaded_count}/{len(self.config['available_models'])} models downloaded", category='model')
        else:
            log_info(f"Model scan complete: No models downloaded yet", category='model')
    
    def save_config(self):
        """Save models configuration"""
        with open(self.model_config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """Get all available models with current download status"""
        # Re-check download status on every get (in case files were manually added/removed)
        for model in self.config['available_models']:
            model_path = self.models_dir / model['id']
            is_complete, _ = self._is_model_complete(model_path)
            model['isDownloaded'] = is_complete
            
            # Add progress if downloading
            if model['id'] in self.download_progress:
                model['downloadProgress'] = self.download_progress[model['id']]
        
        return self.config['available_models']
    
    def get_active_model(self) -> Optional[Dict[str, Any]]:
        """Get currently active model"""
        active_id = self.config.get('active_model')
        if active_id:
            for model in self.config['available_models']:
                if model['id'] == active_id:
                    return model
        return None
    
    async def download_model(self, model_id: str) -> Dict[str, Any]:
        """Download model from Hugging Face using background task"""
        from core.logger import log_info, log_warning
        
        model = None
        for m in self.config['available_models']:
            if m['id'] == model_id:
                model = m
                break
        
        if not model:
            return {'success': False, 'message': 'Modell nicht gefunden'}
        
        # Check if already downloading
        if model_id in self.download_tasks:
            log_warning(f"Download already in progress: {model['name']}", category='model')
            return {'success': False, 'message': 'Download bereits aktiv'}
        
        # Check if already downloaded
        model_path = self.models_dir / model_id
        is_complete, status_msg = self._is_model_complete(model_path)
        
        if is_complete:
            log_warning(f"Model {model['name']} already downloaded", category='model')
            model['isDownloaded'] = True
            self.save_config()
            return {'success': True, 'message': f"{model['name']} bereits heruntergeladen"}
        
        log_info(f"Starting background download of {model['name']} from HuggingFace", category='model')
        log_info(f"Model: {model['hf_model']}", category='model')
        
        # Create and start background task
        task = DownloadTask(model_id, model, model_path, self)
        self.download_tasks[model_id] = asyncio.create_task(task.run())
        
        return {'success': True, 'message': f"Download von {model['name']} gestartet"}
    
    def get_download_progress(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get download progress for a model"""
        return self.download_progress.get(model_id)
    
    def load_model(self, model_id: str) -> bool:
        """Load a model into memory"""
        from core.logger import log_info, log_error, log_warning
        
        model = None
        for m in self.config['available_models']:
            if m['id'] == model_id:
                model = m
                break
        
        if not model:
            log_error(f"Model {model_id} not found", category='model')
            return False
        
        # Check if downloaded
        model_path = self.models_dir / model_id
        is_complete, status_msg = self._is_model_complete(model_path)
        
        if not is_complete:
            log_warning(f"Cannot load {model['name']} - {status_msg}", category='model')
            return False
        
        # Unload current model
        for m in self.config['available_models']:
            m['isActive'] = False
        
        # Load new model
        model['isActive'] = True
        self.config['active_model'] = model_id
        self.save_config()
        
        log_info(f"Loaded model: {model['name']}", category='model')
        log_info(f"Model path: {model_path}", category='model')
        
        # Load into HF Runtime
        log_info("Loading model into inference runtime...", category='model')
        success = hf_runtime.load_model(model_path, model_id)
        
        if not success:
            log_error("Failed to load model into runtime", category='model')
            model['isActive'] = False
            self.config['active_model'] = None
            self.save_config()
            return False
        
        log_info(f"✓ Model {model['name']} ready for inference", category='model')
        return True
    
    def unload_model(self) -> bool:
        """Unload current model"""
        from core.logger import log_info
        
        # Unload from runtime
        hf_runtime.unload_model()
        
        for model in self.config['available_models']:
            model['isActive'] = False
        self.config['active_model'] = None
        self.save_config()
        
        log_info("Model unloaded", category='model')
        return True

# Global instance
llm_manager = LLMManager()
