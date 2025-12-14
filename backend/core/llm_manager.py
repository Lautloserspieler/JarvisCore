import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
from datetime import datetime
import threading

# Import HF Runtime
from core.hf_inference import hf_runtime

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
    
    async def _send_progress_update(self, model_id: str, progress: int, message: str):
        """Send progress update via WebSocket"""
        try:
            from core.event_system import get_ws_manager
            ws_manager = get_ws_manager()
            await ws_manager.broadcast({
                'type': 'model_download_progress',
                'modelId': model_id,
                'progress': progress,
                'message': message
            })
        except Exception as e:
            from core.logger import log_debug
            log_debug(f"Could not send WS update: {e}", category='model')
    
    async def download_model(self, model_id: str) -> Dict[str, Any]:
        """Download model from Hugging Face using huggingface_hub"""
        from core.logger import log_info, log_error, log_warning
        
        model = None
        for m in self.config['available_models']:
            if m['id'] == model_id:
                model = m
                break
        
        if not model:
            return {'success': False, 'message': 'Modell nicht gefunden'}
        
        log_info(f"Starting download of {model['name']} from HuggingFace", category='model')
        log_info(f"Model: {model['hf_model']}", category='model')
        
        # Check if already downloaded
        model_path = self.models_dir / model_id
        is_complete, status_msg = self._is_model_complete(model_path)
        
        if is_complete:
            log_warning(f"Model {model['name']} already downloaded", category='model')
            model['isDownloaded'] = True
            self.save_config()
            return {'success': True, 'message': f"{model['name']} bereits heruntergeladen"}
        
        # Mark as downloading
        self.download_progress[model_id] = {
            'progress': 0, 
            'status': 'initializing',
            'message': 'Initialisiere Download...'
        }
        
        try:
            # Try to import huggingface_hub
            try:
                from huggingface_hub import snapshot_download
                log_info("Using huggingface_hub for download", category='model')
            except ImportError:
                log_info("huggingface_hub not installed. Installing...", category='model')
                self.download_progress[model_id]['message'] = 'Installiere huggingface_hub...'
                await self._send_progress_update(model_id, 5, 'Installiere Dependencies...')
                
                import subprocess
                subprocess.check_call(["pip", "install", "huggingface_hub"])
                from huggingface_hub import snapshot_download
                log_info("huggingface_hub installed successfully", category='model')
            
            # Create model directory
            model_path.mkdir(exist_ok=True)
            
            self.download_progress[model_id] = {
                'progress': 10,
                'status': 'downloading',
                'message': f'Lade {model["name"]} herunter...'
            }
            await self._send_progress_update(model_id, 10, 'Starte Download...')
            
            log_info(f"Downloading to {model_path}", category='model')
            log_info(f"This may take several minutes depending on model size ({model['size']})", category='model')
            
            # Download the model
            log_info("Starting file download from HuggingFace Hub...", category='model')
            result_path = snapshot_download(
                repo_id=model['hf_model'],
                local_dir=str(model_path),
                local_dir_use_symlinks=False,
                resume_download=True,
                allow_patterns=["*.json", "*.safetensors", "*.model", "*.bin", "*.txt", "tokenizer*", "config.json", "vocab*", "merges.txt"],
                ignore_patterns=["*.msgpack", "*.h5", "*.ot", "pytorch_model.bin.index.json"],
                max_workers=4,  # Parallel downloads
                token=False  # Explicitly no auth
            )
            
            # Verify download completed successfully
            is_complete, status_msg = self._is_model_complete(model_path)
            
            if not is_complete:
                raise Exception(f"Download incomplete: {status_msg}")
            
            # Mark as completed
            self.download_progress[model_id] = {
                'progress': 100,
                'status': 'completed',
                'message': 'Download abgeschlossen!'
            }
            await self._send_progress_update(model_id, 100, 'Download abgeschlossen!')
            
            # Mark as downloaded
            model['isDownloaded'] = True
            self.save_config()
            
            log_info(f"Successfully downloaded {model['name']}", category='model')
            log_info(f"Model saved to: {model_path}", category='model')
            
            # Clean up progress after 3 seconds
            await asyncio.sleep(3)
            if model_id in self.download_progress:
                del self.download_progress[model_id]
            
            return {'success': True, 'message': f"{model['name']} erfolgreich heruntergeladen"}
            
        except Exception as e:
            error_msg = str(e)
            
            # Better error messages
            if "401" in error_msg or "GatedRepoError" in error_msg:
                error_msg = "Dieses Modell erfordert HuggingFace Login. Bitte wähle ein anderes Modell."
            elif "404" in error_msg:
                error_msg = "Modell nicht gefunden auf HuggingFace."
            elif "timeout" in error_msg.lower():
                error_msg = "Download-Timeout. Bitte prüfe deine Internetverbindung."
            
            log_error(f"Failed to download {model['name']}: {error_msg}", category='model', exc_info=True)
            
            self.download_progress[model_id] = {
                'progress': 0,
                'status': 'failed',
                'message': f'Fehler: {error_msg}'
            }
            await self._send_progress_update(model_id, 0, f'Fehler: {error_msg}')
            
            await asyncio.sleep(5)
            if model_id in self.download_progress:
                del self.download_progress[model_id]
            
            return {'success': False, 'message': f'Download fehlgeschlagen: {error_msg}'}
    
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
        
        # NEU: HF Runtime laden
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
        
        # NEU: Runtime unload
        hf_runtime.unload_model()
        
        for model in self.config['available_models']:
            model['isActive'] = False
        self.config['active_model'] = None
        self.save_config()
        
        log_info("Model unloaded", category='model')
        return True

# Global instance
llm_manager = LLMManager()
