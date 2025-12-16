"""Multi-Model Manager for JarvisCore

Manages multiple loaded models simultaneously with:
- Async model loading
- Hot-swapping between models
- Memory management (VRAM limits)
- LRU eviction policy
"""

import asyncio
from typing import Dict, Optional, List
from pathlib import Path
import time
import psutil
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModelMetrics:
    """Metrics for a loaded model"""
    name: str
    vram_mb: int
    load_time_seconds: float
    last_used: datetime
    inference_count: int = 0
    total_tokens: int = 0


class MultiModelManager:
    """Manage multiple loaded LLM models simultaneously"""
    
    def __init__(self, max_models: int = 2, max_vram_gb: int = 16):
        """
        Initialize multi-model manager
        
        Args:
            max_models: Maximum number of models to keep loaded
            max_vram_gb: Maximum VRAM usage in GB
        """
        self.models: Dict[str, any] = {}  # {model_name: llama_runtime}
        self.metrics: Dict[str, ModelMetrics] = {}
        self.active_model: Optional[str] = None
        self.lock = asyncio.Lock()
        
        # Configuration
        self.max_models = max_models
        self.max_vram_gb = max_vram_gb
        
        print(f"[INFO] MultiModelManager initialized (max: {max_models} models, {max_vram_gb}GB VRAM)")
    
    async def load_model_async(
        self,
        model_path: str,
        model_name: str,
        n_ctx: int = 8192,
        n_gpu_layers: int = -1,
        n_threads: int = 8,
        verbose: bool = False
    ) -> bool:
        """Load model asynchronously
        
        Args:
            model_path: Path to GGUF model file
            model_name: Unique identifier for model
            n_ctx: Context window size
            n_gpu_layers: GPU layers (-1 for all)
            n_threads: CPU threads
            verbose: Enable verbose logging
            
        Returns:
            True if loaded successfully
        """
        async with self.lock:
            # Check if already loaded
            if model_name in self.models:
                print(f"[INFO] Model {model_name} already loaded, switching to it")
                self.active_model = model_name
                self.metrics[model_name].last_used = datetime.now()
                return True
            
            # Check if we need to unload models
            if len(self.models) >= self.max_models:
                print(f"[INFO] Max models ({self.max_models}) reached, evicting LRU model")
                await self._evict_lru_model()
            
            # Check VRAM availability
            estimated_vram = self._estimate_model_vram(model_path, n_ctx)
            current_vram = self._get_current_vram_usage()
            
            if current_vram + estimated_vram > self.max_vram_gb * 1024:
                print(f"[WARNING] VRAM limit would be exceeded ({current_vram + estimated_vram}MB > {self.max_vram_gb * 1024}MB)")
                # Try to free up space
                await self._evict_lru_model()
            
            # Load model
            print(f"[INFO] Loading model {model_name} from {model_path}...")
            start_time = time.time()
            
            try:
                # Import here to avoid circular dependency
                from core.llama_inference import LlamaInference
                
                runtime = LlamaInference()
                success = runtime.load_model(
                    model_path=model_path,
                    model_name=model_name,
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu_layers,
                    n_threads=n_threads,
                    verbose=verbose
                )
                
                if not success:
                    print(f"[ERROR] Failed to load model {model_name}")
                    return False
                
                load_time = time.time() - start_time
                
                # Store runtime and metrics
                self.models[model_name] = runtime
                self.metrics[model_name] = ModelMetrics(
                    name=model_name,
                    vram_mb=estimated_vram,
                    load_time_seconds=load_time,
                    last_used=datetime.now()
                )
                
                # Set as active
                self.active_model = model_name
                
                print(f"[SUCCESS] Model {model_name} loaded in {load_time:.2f}s (est. {estimated_vram}MB VRAM)")
                return True
                
            except Exception as e:
                print(f"[ERROR] Failed to load model {model_name}: {e}")
                return False
    
    async def switch_model(self, model_name: str) -> bool:
        """Switch to an already-loaded model
        
        Args:
            model_name: Name of model to switch to
            
        Returns:
            True if switched successfully
        """
        if model_name not in self.models:
            print(f"[ERROR] Model {model_name} not loaded")
            return False
        
        self.active_model = model_name
        self.metrics[model_name].last_used = datetime.now()
        print(f"[INFO] Switched to model {model_name}")
        return True
    
    async def unload_model(self, model_name: str) -> bool:
        """Unload a specific model
        
        Args:
            model_name: Name of model to unload
            
        Returns:
            True if unloaded successfully
        """
        async with self.lock:
            if model_name not in self.models:
                print(f"[WARNING] Model {model_name} not loaded")
                return False
            
            try:
                runtime = self.models[model_name]
                runtime.unload_model()
                
                del self.models[model_name]
                del self.metrics[model_name]
                
                if self.active_model == model_name:
                    self.active_model = None
                    # Switch to another model if available
                    if self.models:
                        self.active_model = next(iter(self.models.keys()))
                
                print(f"[INFO] Model {model_name} unloaded")
                return True
                
            except Exception as e:
                print(f"[ERROR] Failed to unload model {model_name}: {e}")
                return False
    
    async def _evict_lru_model(self):
        """Evict least recently used model"""
        if not self.models:
            return
        
        # Find LRU model
        lru_model = min(
            self.metrics.items(),
            key=lambda x: x[1].last_used
        )[0]
        
        print(f"[INFO] Evicting LRU model: {lru_model}")
        await self.unload_model(lru_model)
    
    def _estimate_model_vram(self, model_path: str, n_ctx: int) -> int:
        """Estimate VRAM usage for a model
        
        Args:
            model_path: Path to model file
            n_ctx: Context window size
            
        Returns:
            Estimated VRAM in MB
        """
        path = Path(model_path)
        if not path.exists():
            return 0
        
        # Get model size in MB
        model_size_mb = path.stat().st_size / (1024 * 1024)
        
        # Add context overhead (rough estimate: ~4 bytes per token)
        context_overhead_mb = (n_ctx * 4) / (1024 * 1024)
        
        # Total estimate with 20% buffer
        total_mb = int((model_size_mb + context_overhead_mb) * 1.2)
        
        return total_mb
    
    def _get_current_vram_usage(self) -> int:
        """Get current VRAM usage from loaded models
        
        Returns:
            VRAM usage in MB
        """
        return sum(m.vram_mb for m in self.metrics.values())
    
    def get_active_runtime(self):
        """Get active model runtime
        
        Returns:
            LlamaInference instance or None
        """
        if self.active_model and self.active_model in self.models:
            return self.models[self.active_model]
        return None
    
    def get_all_loaded_models(self) -> List[Dict[str, any]]:
        """Get info about all loaded models
        
        Returns:
            List of model info dicts
        """
        result = []
        for name, metrics in self.metrics.items():
            result.append({
                "name": name,
                "active": name == self.active_model,
                "vram_mb": metrics.vram_mb,
                "load_time_seconds": metrics.load_time_seconds,
                "last_used": metrics.last_used.isoformat(),
                "inference_count": metrics.inference_count,
                "total_tokens": metrics.total_tokens
            })
        return result
    
    def get_stats(self) -> Dict[str, any]:
        """Get manager statistics
        
        Returns:
            Statistics dict
        """
        return {
            "loaded_models": len(self.models),
            "active_model": self.active_model,
            "total_vram_mb": self._get_current_vram_usage(),
            "max_vram_mb": self.max_vram_gb * 1024,
            "max_models": self.max_models,
            "system_ram_percent": psutil.virtual_memory().percent,
            "models": self.get_all_loaded_models()
        }
    
    async def preload_models(self, model_configs: List[Dict[str, any]]) -> Dict[str, bool]:
        """Preload multiple models
        
        Args:
            model_configs: List of model configs with keys:
                - model_path
                - model_name
                - n_ctx (optional)
                - n_gpu_layers (optional)
                
        Returns:
            Dict of {model_name: success}
        """
        results = {}
        
        for config in model_configs:
            model_name = config['model_name']
            model_path = config['model_path']
            
            success = await self.load_model_async(
                model_path=model_path,
                model_name=model_name,
                n_ctx=config.get('n_ctx', 8192),
                n_gpu_layers=config.get('n_gpu_layers', -1),
                n_threads=config.get('n_threads', 8)
            )
            
            results[model_name] = success
        
        return results
    
    def update_inference_metrics(self, model_name: str, tokens: int):
        """Update inference metrics for a model
        
        Args:
            model_name: Model name
            tokens: Number of tokens generated
        """
        if model_name in self.metrics:
            self.metrics[model_name].inference_count += 1
            self.metrics[model_name].total_tokens += tokens
            self.metrics[model_name].last_used = datetime.now()
    
    async def generate(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, any]:
        """Generate text using active or specified model
        
        Args:
            prompt: Input prompt
            model_name: Optional model to use (defaults to active)
            **kwargs: Generation parameters
            
        Returns:
            Generation result dict
        """
        target_model = model_name or self.active_model
        
        if not target_model or target_model not in self.models:
            return {
                "success": False,
                "error": "No model loaded or specified"
            }
        
        # Switch to target model if needed
        if target_model != self.active_model:
            await self.switch_model(target_model)
        
        # Generate
        runtime = self.models[target_model]
        result = runtime.generate(prompt, **kwargs)
        
        # Update metrics
        if result.get('success'):
            tokens = result.get('tokens_generated', 0)
            self.update_inference_metrics(target_model, tokens)
        
        return result


# Global instance
multi_model_manager = MultiModelManager(max_models=2, max_vram_gb=16)
