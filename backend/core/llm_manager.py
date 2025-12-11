import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
from datetime import datetime

class LLMManager:
    """Manager for local LLM models from Hugging Face"""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.loaded_model = None
        self.model_config_path = self.models_dir / "models_config.json"
        self.download_progress = {}
        self.load_config()
    
    def load_config(self):
        """Load models configuration"""
        if self.model_config_path.exists():
            with open(self.model_config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default configuration with real HuggingFace models
            self.config = {
                'available_models': [
                    {
                        'id': 'llama-3.2-1b',
                        'name': 'Llama 3.2 1B Instruct',
                        'provider': 'Meta',
                        'size': '1B parameters (~2.5GB)',
                        'hf_model': 'meta-llama/Llama-3.2-1B-Instruct',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'instruction-following']
                    },
                    {
                        'id': 'phi-3-mini',
                        'name': 'Phi-3 Mini 4K',
                        'provider': 'Microsoft',
                        'size': '3.8B parameters (~7.6GB)',
                        'hf_model': 'microsoft/Phi-3-mini-4k-instruct',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'code', 'reasoning']
                    },
                    {
                        'id': 'gemma-2-2b',
                        'name': 'Gemma 2 2B',
                        'provider': 'Google',
                        'size': '2B parameters (~5GB)',
                        'hf_model': 'google/gemma-2-2b-it',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'instruction-following']
                    },
                    {
                        'id': 'qwen-2.5-3b',
                        'name': 'Qwen 2.5 3B Instruct',
                        'provider': 'Alibaba',
                        'size': '3B parameters (~6GB)',
                        'hf_model': 'Qwen/Qwen2.5-3B-Instruct',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'multilingual', 'code']
                    },
                    {
                        'id': 'tinyllama-1.1b',
                        'name': 'TinyLlama 1.1B Chat',
                        'provider': 'TinyLlama',
                        'size': '1.1B parameters (~2.2GB)',
                        'hf_model': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat']
                    },
                    {
                        'id': 'stablelm-2-1.6b',
                        'name': 'StableLM 2 1.6B',
                        'provider': 'Stability AI',
                        'size': '1.6B parameters (~3.2GB)',
                        'hf_model': 'stabilityai/stablelm-2-1_6b-chat',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'instruction-following']
                    }
                ],
                'active_model': None
            }
            self.save_config()
    
    def save_config(self):
        """Save models configuration"""
        with open(self.model_config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """Get all available models"""
        # Check if models are actually downloaded
        for model in self.config['available_models']:
            model_path = self.models_dir / model['id']
            model['isDownloaded'] = model_path.exists() and any(model_path.iterdir())
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
        if model_path.exists() and any(model_path.iterdir()):
            log_warning(f"Model {model['name']} already downloaded", category='model')
            model['isDownloaded'] = True
            self.save_config()
            return {'success': True, 'message': f"{model['name']} bereits heruntergeladen"}
        
        # Mark as downloading
        self.download_progress[model_id] = {'progress': 0, 'status': 'downloading'}
        
        try:
            # Try to import huggingface_hub
            try:
                from huggingface_hub import snapshot_download
                log_info("Using huggingface_hub for download", category='model')
            except ImportError:
                log_error("huggingface_hub not installed. Installing...", category='model')
                import subprocess
                subprocess.check_call(["pip", "install", "huggingface_hub"])
                from huggingface_hub import snapshot_download
                log_info("huggingface_hub installed successfully", category='model')
            
            # Create model directory
            model_path.mkdir(exist_ok=True)
            
            log_info(f"Downloading to {model_path}", category='model')
            
            # Download the model
            def progress_callback(current, total):
                if total > 0:
                    progress = int((current / total) * 100)
                    self.download_progress[model_id]['progress'] = progress
                    if progress % 10 == 0:  # Log every 10%
                        log_info(f"Download progress: {progress}%", category='model')
            
            # Download model from HuggingFace
            snapshot_download(
                repo_id=model['hf_model'],
                local_dir=str(model_path),
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            # Mark as downloaded
            model['isDownloaded'] = True
            self.save_config()
            
            log_info(f"Successfully downloaded {model['name']}", category='model')
            
            if model_id in self.download_progress:
                del self.download_progress[model_id]
            
            return {'success': True, 'message': f"{model['name']} erfolgreich heruntergeladen"}
            
        except Exception as e:
            log_error(f"Failed to download {model['name']}: {str(e)}", category='model', exc_info=True)
            if model_id in self.download_progress:
                del self.download_progress[model_id]
            return {'success': False, 'message': f'Download fehlgeschlagen: {str(e)}'}
    
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
        if not (model_path.exists() and any(model_path.iterdir())):
            log_warning(f"Cannot load {model['name']} - not downloaded", category='model')
            return False
        
        # Unload current model
        for m in self.config['available_models']:
            m['isActive'] = False
        
        # Load new model
        model['isActive'] = True
        self.config['active_model'] = model_id
        self.save_config()
        
        log_info(f"Loaded model: {model['name']}", category='model')
        return True
    
    def unload_model(self) -> bool:
        """Unload current model"""
        from core.logger import log_info
        
        for model in self.config['available_models']:
            model['isActive'] = False
        self.config['active_model'] = None
        self.save_config()
        
        log_info("Model unloaded", category='model')
        return True

# Global instance
llm_manager = LLMManager()
