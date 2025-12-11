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
            # Default configuration
            self.config = {
                'available_models': [
                    {
                        'id': 'llama-3.2-1b',
                        'name': 'Llama 3.2 1B',
                        'provider': 'Meta',
                        'size': '1B parameters',
                        'hf_model': 'meta-llama/Llama-3.2-1B',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'instruction-following']
                    },
                    {
                        'id': 'llama-3.2-3b',
                        'name': 'Llama 3.2 3B',
                        'provider': 'Meta',
                        'size': '3B parameters',
                        'hf_model': 'meta-llama/Llama-3.2-3B',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'instruction-following', 'reasoning']
                    },
                    {
                        'id': 'phi-3-mini',
                        'name': 'Phi-3 Mini',
                        'provider': 'Microsoft',
                        'size': '3.8B parameters',
                        'hf_model': 'microsoft/Phi-3-mini-4k-instruct',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'code', 'reasoning']
                    },
                    {
                        'id': 'mistral-7b',
                        'name': 'Mistral 7B',
                        'provider': 'Mistral AI',
                        'size': '7B parameters',
                        'hf_model': 'mistralai/Mistral-7B-Instruct-v0.3',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'instruction-following', 'multilingual']
                    },
                    {
                        'id': 'gemma-2-2b',
                        'name': 'Gemma 2 2B',
                        'provider': 'Google',
                        'size': '2B parameters',
                        'hf_model': 'google/gemma-2-2b-it',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'instruction-following']
                    },
                    {
                        'id': 'qwen-2.5-3b',
                        'name': 'Qwen 2.5 3B',
                        'provider': 'Alibaba',
                        'size': '3B parameters',
                        'hf_model': 'Qwen/Qwen2.5-3B-Instruct',
                        'isActive': False,
                        'isDownloaded': False,
                        'capabilities': ['text-generation', 'chat', 'multilingual', 'code']
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
        """Download model from Hugging Face"""
        from core.logger import logger
        
        model = None
        for m in self.config['available_models']:
            if m['id'] == model_id:
                model = m
                break
        
        if not model:
            return {'success': False, 'message': 'Modell nicht gefunden'}
        
        logger.info(f"Starting download of {model['name']}", extra={'category': 'model'})
        
        # Mark as downloading
        self.download_progress[model_id] = {'progress': 0, 'status': 'downloading'}
        
        try:
            # Simulate download (replace with actual huggingface_hub download)
            for i in range(0, 101, 10):
                await asyncio.sleep(0.5)
                self.download_progress[model_id]['progress'] = i
                logger.debug(f"Download progress: {i}%", extra={'category': 'model'})
            
            # Mark as downloaded
            model['isDownloaded'] = True
            self.save_config()
            
            logger.info(f"Successfully downloaded {model['name']}", extra={'category': 'model'})
            
            del self.download_progress[model_id]
            
            return {'success': True, 'message': f"{model['name']} erfolgreich heruntergeladen"}
            
        except Exception as e:
            logger.error(f"Failed to download {model['name']}: {str(e)}", extra={'category': 'model'})
            if model_id in self.download_progress:
                del self.download_progress[model_id]
            return {'success': False, 'message': f'Download fehlgeschlagen: {str(e)}'}
    
    def get_download_progress(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get download progress for a model"""
        return self.download_progress.get(model_id)
    
    def load_model(self, model_id: str) -> bool:
        """Load a model into memory"""
        from core.logger import logger
        
        model = None
        for m in self.config['available_models']:
            if m['id'] == model_id:
                model = m
                break
        
        if not model:
            logger.error(f"Model {model_id} not found", extra={'category': 'model'})
            return False
        
        if not model.get('isDownloaded'):
            logger.warning(f"Cannot load {model['name']} - not downloaded", extra={'category': 'model'})
            return False
        
        # Unload current model
        for m in self.config['available_models']:
            m['isActive'] = False
        
        # Load new model
        model['isActive'] = True
        self.config['active_model'] = model_id
        self.save_config()
        
        logger.info(f"Loaded model: {model['name']}", extra={'category': 'model'})
        return True
    
    def unload_model(self) -> bool:
        """Unload current model"""
        from core.logger import logger
        
        for model in self.config['available_models']:
            model['isActive'] = False
        self.config['active_model'] = None
        self.save_config()
        
        logger.info("Model unloaded", extra={'category': 'model'})
        return True

# Global instance
llm_manager = LLMManager()
