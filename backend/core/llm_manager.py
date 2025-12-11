import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

class LLMManager:
    """Manager for local LLM models from Hugging Face"""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.loaded_model = None
        self.model_config_path = self.models_dir / "models_config.json"
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
    
    def download_model(self, model_id: str) -> bool:
        """Download model from Hugging Face (placeholder)"""
        # TODO: Implement actual download logic using huggingface_hub
        for model in self.config['available_models']:
            if model['id'] == model_id:
                model['isDownloaded'] = True
                self.save_config()
                return True
        return False
    
    def load_model(self, model_id: str) -> bool:
        """Load a model into memory"""
        # TODO: Implement actual model loading
        for model in self.config['available_models']:
            model['isActive'] = False
            if model['id'] == model_id:
                model['isActive'] = True
                self.config['active_model'] = model_id
        self.save_config()
        return True
    
    def unload_model(self) -> bool:
        """Unload current model"""
        for model in self.config['available_models']:
            model['isActive'] = False
        self.config['active_model'] = None
        self.save_config()
        return True

# Global instance
llm_manager = LLMManager()
