"""
llama.cpp Inference Engine für J.A.R.V.I.S.
Vollständige lokale LLM-Inferenz mit GGUF-Modellen
"""

import os
import threading
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None


class LlamaInference:
    """llama.cpp Inference Engine für lokale GGUF-Modelle"""
    
    def __init__(self):
        self.model: Optional[Llama] = None
        self.model_path: Optional[Path] = None
        self.model_name: Optional[str] = None
        self.is_loaded: bool = False
        self.device: str = "cpu"
        self.n_gpu_layers: int = -1  # -1 = all layers on GPU
        self.n_ctx: int = 4096  # Context window
        self.max_layers: Optional[int] = None
        self.lock = threading.RLock()
        
        # Generation defaults
        self.default_temperature = 0.7
        self.default_top_p = 0.9
        self.default_top_k = 40
        self.default_max_tokens = 512
        self.default_repeat_penalty = 1.1
        
        # Check GPU availability
        if os.getenv("LLAMA_USE_GPU", "1") == "1":
            try:
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
                    self.n_gpu_layers = -1
            except ImportError:
                pass
    
    def load_model(
        self,
        model_path: str | Path,
        model_name: str = "unknown",
        n_ctx: int = 4096,
        n_gpu_layers: Optional[int] = None,
        verbose: bool = False
    ) -> bool:
        """Lade GGUF-Modell mit llama.cpp
        
        Args:
            model_path: Pfad zur .gguf Datei
            model_name: Name des Modells (für Logging)
            n_ctx: Context-Window-Größe
            n_gpu_layers: Anzahl GPU-Layers (-1 = alle)
            verbose: Verbose-Modus
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not LLAMA_CPP_AVAILABLE:
            print("[ERROR] llama-cpp-python nicht installiert!")
            return False
        
        with self.lock:
            # Unload existing model
            if self.is_loaded:
                self.unload_model()
            
            model_path = Path(model_path)
            if not model_path.exists():
                print(f"[ERROR] Model file not found: {model_path}")
                return False
            
            try:
                print(f"[INFO] Loading model: {model_name}")
                print(f"[INFO] Path: {model_path}")
                print(f"[INFO] Context: {n_ctx} tokens")
                print(f"[INFO] Device: {self.device}")
                
                load_start = time.time()
                
                # GPU Layers
                gpu_layers = n_gpu_layers if n_gpu_layers is not None else self.n_gpu_layers
                
                self.model = Llama(
                    model_path=str(model_path),
                    n_ctx=n_ctx,
                    n_gpu_layers=gpu_layers,
                    n_threads=os.cpu_count() or 4,
                    verbose=verbose,
                    use_mmap=True,
                    use_mlock=False,
                )
                
                load_time = time.time() - load_start
                
                self.model_path = model_path
                self.model_name = model_name
                self.n_ctx = n_ctx
                self.max_layers = getattr(self.model, "n_layers", None)
                self.is_loaded = True
                
                print(f"[SUCCESS] Model loaded in {load_time:.2f}s")
                print(f"[INFO] Context window: {n_ctx} tokens")
                print(f"[INFO] GPU layers: {gpu_layers}")
                if self.max_layers is not None:
                    print(f"[INFO] Model layers: {self.max_layers}")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] Failed to load model: {e}")
                self.model = None
                self.is_loaded = False
                self.max_layers = None
                return False
    
    def unload_model(self) -> bool:
        """Entlade aktuelles Modell und gebe Speicher frei"""
        with self.lock:
            if not self.is_loaded:
                return True
            
            try:
                print(f"[INFO] Unloading model: {self.model_name}")
                
                # llama.cpp Model freigeben
                if self.model is not None:
                    del self.model
                    self.model = None
                
                self.model_path = None
                self.model_name = None
                self.is_loaded = False
                self.max_layers = None
                
                # Force garbage collection
                import gc
                gc.collect()
                
                print("[SUCCESS] Model unloaded")
                return True
                
            except Exception as e:
                print(f"[ERROR] Failed to unload model: {e}")
                return False

    def get_max_layers(self) -> Optional[int]:
        """Get maximum layer count from loaded model metadata."""
        if not self.is_loaded or self.model is None:
            return None
        return getattr(self.model, "n_layers", None)
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generiere Text mit geladenem Modell
        
        Args:
            prompt: Input-Prompt
            max_tokens: Maximale Token-Anzahl
            temperature: Sampling-Temperature (0.0-2.0)
            top_p: Nucleus-Sampling (0.0-1.0)
            top_k: Top-K Sampling
            repeat_penalty: Wiederholungs-Penalty
            stop: Stop-Sequenzen
            stream: Streaming-Modus (noch nicht implementiert)
            
        Returns:
            Dict mit 'text', 'tokens_generated', 'time_taken'
        """
        if not self.is_loaded or self.model is None:
            return {
                'success': False,
                'error': 'Kein Modell geladen',
                'text': ''
            }
        
        with self.lock:
            try:
                gen_start = time.time()
                
                # Parameter mit Defaults
                params = {
                    'prompt': prompt,
                    'max_tokens': max_tokens or self.default_max_tokens,
                    'temperature': temperature if temperature is not None else self.default_temperature,
                    'top_p': top_p if top_p is not None else self.default_top_p,
                    'top_k': top_k or self.default_top_k,
                    'repeat_penalty': repeat_penalty or self.default_repeat_penalty,
                    'stop': stop or [],
                    'echo': False,
                }
                
                # Generate
                output = self.model(**params)
                
                gen_time = time.time() - gen_start
                
                # Extract text
                text = output['choices'][0]['text']
                tokens_generated = output['usage']['completion_tokens']
                
                return {
                    'success': True,
                    'text': text,
                    'tokens_generated': tokens_generated,
                    'time_taken': gen_time,
                    'tokens_per_second': tokens_generated / gen_time if gen_time > 0 else 0,
                    'model': self.model_name,
                    'device': self.device
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'text': ''
                }
    
    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Chat-Modus mit History
        
        Args:
            message: User-Nachricht
            history: Chat-Historie [{'role': 'user'|'assistant', 'content': '...'}]
            system_prompt: System-Prompt
            max_tokens: Max Tokens
            temperature: Sampling-Temperature
            
        Returns:
            Dict mit 'text', 'tokens_generated', 'time_taken'
        """
        if not self.is_loaded or self.model is None:
            return {
                'success': False,
                'error': 'Kein Modell geladen',
                'text': ''
            }
        
        # Build prompt with history
        prompt_parts = []
        
        # System prompt
        if system_prompt:
            prompt_parts.append(f"<|system|>\n{system_prompt}</s>")
        
        # History
        if history:
            for msg in history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                if role == 'user':
                    prompt_parts.append(f"<|user|>\n{content}</s>")
                elif role == 'assistant':
                    prompt_parts.append(f"<|assistant|>\n{content}</s>")
        
        # Current message
        prompt_parts.append(f"<|user|>\n{message}</s>")
        prompt_parts.append("<|assistant|>\n")
        
        full_prompt = "\n".join(prompt_parts)
        
        # Generate
        return self.generate(
            prompt=full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["</s>", "<|user|>", "<|system|>"]
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Status des Inference-Systems"""
        return {
            'loaded': self.is_loaded,
            'model_name': self.model_name,
            'model_path': str(self.model_path) if self.model_path else None,
            'device': self.device,
            'context_window': self.n_ctx,
            'gpu_layers': self.n_gpu_layers,
            'available': LLAMA_CPP_AVAILABLE
        }


# Global instance
llama_runtime = LlamaInference()
