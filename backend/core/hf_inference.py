"""
HuggingFace Inference Runtime Manager
Lädt lokale HF-Modelle und führt Text-Generation aus
"""

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
)
from typing import Optional, Dict, Any
from pathlib import Path
import gc


class HFInferenceRuntime:
    """Runtime für HuggingFace Model Inference"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_id = None
        self.device = self._get_device()
        self.generation_config = {
            'max_new_tokens': 512,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 50,
            'do_sample': True,
            'repetition_penalty': 1.1
        }
    
    def _get_device(self) -> str:
        """Detect best available device"""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():  # Apple Silicon
            return "mps"
        else:
            return "cpu"
    
    def load_model(self, model_path: Path, model_id: str) -> bool:
        """
        Lädt HuggingFace Model von lokaler Directory
        
        Args:
            model_path: Pfad zum Model (z.B. ./models/tinyllama-1.1b)
            model_id: Model-ID für Logging
        
        Returns:
            True wenn erfolgreich geladen
        """
        from core.logger import log_info, log_error, log_warning
        
        try:
            # Unload vorheriges Model
            if self.model is not None:
                self.unload_model()
            
            log_info(f"Loading model from {model_path}", category='inference')
            log_info(f"Using device: {self.device}", category='inference')
            
            # Tokenizer laden
            log_info("Loading tokenizer...", category='inference')
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                local_files_only=True,
                trust_remote_code=False
            )
            
            # Pad token setzen falls nicht vorhanden
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Model laden mit optimalen Einstellungen
            log_info("Loading model weights...", category='inference')
            
            load_kwargs = {
                'local_files_only': True,
                'trust_remote_code': False,
                'low_cpu_mem_usage': True
            }
            
            # Device-spezifische Optimierungen
            if self.device == "cuda":
                load_kwargs['device_map'] = "auto"
                load_kwargs['torch_dtype'] = torch.float16
                log_info("Using GPU with float16 precision", category='inference')
            elif self.device == "mps":
                load_kwargs['torch_dtype'] = torch.float16
                log_info("Using Apple Silicon GPU", category='inference')
            else:
                load_kwargs['torch_dtype'] = torch.float32
                log_warning("Using CPU - inference will be slow!", category='inference')
            
            self.model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                **load_kwargs
            )
            
            # Model auf Device verschieben (falls nicht auto)
            if self.device != "cuda":
                self.model = self.model.to(self.device)
            
            # Eval mode
            self.model.eval()
            
            self.model_id = model_id
            
            log_info(f"✓ Model {model_id} loaded successfully", category='inference')
            log_info(f"  Device: {self.device}", category='inference')
            log_info(f"  Parameters: ~{self.model.num_parameters() / 1e9:.2f}B", category='inference')
            
            return True
            
        except Exception as e:
            log_error(f"Failed to load model: {e}", category='inference', exc_info=True)
            self.model = None
            self.tokenizer = None
            self.model_id = None
            return False
    
    def unload_model(self):
        """Entlädt aktuelles Model aus Memory"""
        from core.logger import log_info
        
        if self.model is not None:
            log_info(f"Unloading model {self.model_id}", category='inference')
            
            # Model löschen
            del self.model
            del self.tokenizer
            
            self.model = None
            self.tokenizer = None
            self.model_id = None
            
            # Memory freigeben
            gc.collect()
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
                log_info("GPU cache cleared", category='inference')
            
            log_info("Model unloaded", category='inference')
    
    def is_loaded(self) -> bool:
        """Prüft ob ein Model geladen ist"""
        return self.model is not None and self.tokenizer is not None
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generiert Text basierend auf Prompt
        
        Args:
            prompt: Input-Text
            max_new_tokens: Maximale Anzahl neuer Tokens
            temperature: Sampling Temperature
            system_prompt: System-Anweisung (optional)
        
        Returns:
            Dict mit 'text', 'tokens_generated', 'model'
        """
        from core.logger import log_debug, log_error
        
        if not self.is_loaded():
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        try:
            # Build prompt (mit System-Prompt falls vorhanden)
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            log_debug(f"Generating text for prompt (length: {len(full_prompt)} chars)", category='inference')
            
            # Tokenize
            inputs = self.tokenizer(
                full_prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048
            ).to(self.device)
            
            # Generation config
            gen_config = self.generation_config.copy()
            if max_new_tokens:
                gen_config['max_new_tokens'] = max_new_tokens
            if temperature:
                gen_config['temperature'] = temperature
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    **gen_config,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode (nur neue Tokens)
            input_length = inputs['input_ids'].shape[1]
            generated_tokens = outputs[0][input_length:]
            generated_text = self.tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True
            )
            
            log_debug(f"Generated {len(generated_tokens)} tokens", category='inference')
            
            return {
                'text': generated_text.strip(),
                'tokens_generated': len(generated_tokens),
                'model': self.model_id,
                'device': self.device
            }
            
        except Exception as e:
            log_error(f"Generation failed: {e}", category='inference', exc_info=True)
            raise
    
    def chat(
        self,
        message: str,
        history: Optional[list] = None,
        system_prompt: str = "Du bist JARVIS, ein hilfreicher KI-Assistent."
    ) -> Dict[str, Any]:
        """
        Chat-Funktion mit Kontext-Historie
        
        Args:
            message: User-Nachricht
            history: Liste von {'role': 'user'/'assistant', 'content': '...'}
            system_prompt: System-Anweisung
        
        Returns:
            Dict mit 'text', 'tokens_generated', 'model'
        """
        # Build chat prompt
        chat_prompt = f"{system_prompt}\n\n"
        
        if history:
            for msg in history[-5:]:  # Nur letzte 5 Messages für Kontext
                role = "User" if msg['role'] == 'user' else "Assistant"
                chat_prompt += f"{role}: {msg['content']}\n"
        
        chat_prompt += f"User: {message}\nAssistant:"
        
        return self.generate(chat_prompt, system_prompt=None)
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        """Info über geladenes Model"""
        if not self.is_loaded():
            return None
        
        return {
            'model_id': self.model_id,
            'device': self.device,
            'parameters': self.model.num_parameters(),
            'config': self.generation_config
        }


# Global singleton
hf_runtime = HFInferenceRuntime()
