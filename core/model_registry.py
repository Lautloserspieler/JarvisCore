"""
Model Registry für J.A.R.V.I.S.
Ollama-inspirierte Multi-Registry-Unterstützung für LLM-Downloads
Unterstützt: Hugging Face, Ollama Registry, Custom URLs
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class ModelPath:
    """Parsed model path information (Ollama-Style)"""
    protocol: str = "https"
    registry: str = "huggingface.co"
    namespace: str = "bartowski"
    repository: str = ""
    tag: str = "main"
    filename: Optional[str] = None
    
    def base_url(self) -> str:
        """Konstruiert die Base-URL für den Download"""
        return f"{self.protocol}://{self.registry}"
    
    def full_url(self, filename: Optional[str] = None) -> str:
        """Konstruiert die vollständige Download-URL"""
        fname = filename or self.filename or "model.gguf"
        
        # Hugging Face Format
        if "huggingface.co" in self.registry or "hf.co" in self.registry:
            return f"{self.base_url()}/{self.namespace}/{self.repository}/resolve/{self.tag}/{fname}"
        
        # Ollama Registry Format
        if "ollama.ai" in self.registry:
            return f"{self.base_url()}/api/pull/{self.namespace}/{self.repository}:{self.tag}"
        
        # Generic/Custom Registry
        return f"{self.base_url()}/{self.namespace}/{self.repository}/{fname}"
    
    def __str__(self) -> str:
        """String representation: registry/namespace/repo:tag"""
        base = f"{self.registry}/{self.namespace}/{self.repository}"
        if self.tag and self.tag != "main":
            base += f":{self.tag}"
        return base


class ModelRegistry:
    """
    Multi-Registry Model Path Parser (Ollama-Style)
    
    Unterstützte Formate:
    - "mistral" → huggingface.co/bartowski/mistral:main
    - "hf.co/user/repo" → huggingface.co/user/repo:main
    - "ollama.ai/library/llama2" → ollama.ai/library/llama2:latest
    - "custom.com/ns/model:tag" → custom.com/ns/model:tag
    """
    
    DEFAULT_REGISTRY = "huggingface.co"
    DEFAULT_NAMESPACE = "bartowski"
    DEFAULT_TAG = "main"
    
    # Bekannte Registry-Aliase
    REGISTRY_ALIASES = {
        "hf.co": "huggingface.co",
        "hf": "huggingface.co",
        "huggingface": "huggingface.co",
        "ollama": "registry.ollama.ai",
    }
    
    # Vordefinierte Modell-Mappings (für Shortcuts)
    KNOWN_MODELS = {
        "mistral": {
            "namespace": "second-state",
            "repository": "Mistral-Nemo-Instruct-2407-GGUF",
            "filename": "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
            "tag": "main"
        },
        "deepseek": {
            "namespace": "Triangle104",
            "repository": "DeepSeek-R1-Distill-Llama-8B-Q4_K_M-GGUF",
            "filename": "deepseek-r1-distill-llama-8b-q4_k_m.gguf",
            "tag": "main"
        },
        "qwen": {
            "namespace": "bartowski",
            "repository": "Qwen2.5-7B-Instruct-GGUF",
            "filename": "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
            "tag": "main"
        },
        "llama": {
            "namespace": "TheBloke",
            "repository": "Llama-2-7B-Chat-GGUF",
            "filename": "llama-2-7b-chat.Q4_K_M.gguf",
            "tag": "main"
        }
    }
    
    @classmethod
    def parse(cls, model_name: str) -> ModelPath:
        """
        Parse model name into structured ModelPath
        
        Examples:
            parse("mistral") → ModelPath(registry=hf.co, namespace=second-state, ...)
            parse("hf.co/user/repo") → ModelPath(registry=hf.co, namespace=user, repo=repo)
            parse("custom.ai/org/model:v1.0") → ModelPath(registry=custom.ai, ...)
        """
        model_name = model_name.strip()
        
        # Check if it's a known shortcut
        if model_name in cls.KNOWN_MODELS:
            known = cls.KNOWN_MODELS[model_name]
            return ModelPath(
                registry=cls.DEFAULT_REGISTRY,
                namespace=known["namespace"],
                repository=known["repository"],
                tag=known.get("tag", cls.DEFAULT_TAG),
                filename=known.get("filename")
            )
        
        # Parse full path: [protocol://][registry/]namespace/repo[:tag][/filename]
        protocol = "https"
        if "://" in model_name:
            protocol, model_name = model_name.split("://", 1)
        
        # Split by slashes
        parts = model_name.split("/")
        
        # Simple format: "namespace/repo" or "repo"
        if len(parts) == 1:
            # Just repo name → use defaults
            return ModelPath(
                protocol=protocol,
                registry=cls.DEFAULT_REGISTRY,
                namespace=cls.DEFAULT_NAMESPACE,
                repository=parts[0],
                tag=cls.DEFAULT_TAG
            )
        
        if len(parts) == 2:
            # Format: "namespace/repo[:tag]" → default registry
            namespace, repo_tag = parts
            repo, tag = cls._split_tag(repo_tag)
            
            # Check if first part is a registry alias
            if namespace in cls.REGISTRY_ALIASES or "." in namespace:
                registry = cls.REGISTRY_ALIASES.get(namespace, namespace)
                return ModelPath(
                    protocol=protocol,
                    registry=registry,
                    namespace=cls.DEFAULT_NAMESPACE,
                    repository=repo,
                    tag=tag
                )
            
            return ModelPath(
                protocol=protocol,
                registry=cls.DEFAULT_REGISTRY,
                namespace=namespace,
                repository=repo,
                tag=tag
            )
        
        # Format: "registry/namespace/repo[:tag][/filename]"
        registry = parts[0]
        registry = cls.REGISTRY_ALIASES.get(registry, registry)
        namespace = parts[1]
        repo_part = parts[2]
        
        # Check for filename (4th part)
        filename = parts[3] if len(parts) > 3 else None
        
        repo, tag = cls._split_tag(repo_part)
        
        return ModelPath(
            protocol=protocol,
            registry=registry,
            namespace=namespace,
            repository=repo,
            tag=tag,
            filename=filename
        )
    
    @staticmethod
    def _split_tag(repo_tag: str) -> tuple[str, str]:
        """Split repo:tag into (repo, tag)"""
        if ":" in repo_tag:
            repo, tag = repo_tag.rsplit(":", 1)
            return repo, tag
        return repo_tag, ModelRegistry.DEFAULT_TAG
    
    @classmethod
    def resolve_download_url(
        cls,
        model_path: ModelPath,
        filename: Optional[str] = None,
        quantization: Optional[str] = None
    ) -> str:
        """
        Resolve final download URL with optional quantization variant
        
        Args:
            model_path: Parsed ModelPath
            filename: Optional specific filename
            quantization: Optional quantization (Q4_K_M, Q5_K_M, Q8_0, etc.)
        
        Returns:
            Full download URL
        """
        # Use provided filename or model_path filename
        fname = filename or model_path.filename
        
        # Apply quantization variant if specified
        if quantization and fname:
            base_name = fname.rsplit(".", 1)[0]  # Remove .gguf
            # Remove existing quantization
            for quant in ["Q4_K_M", "Q4_K_S", "Q5_K_M", "Q6_K", "Q8_0"]:
                base_name = base_name.replace(f"-{quant}", "").replace(f".{quant}", "")
            fname = f"{base_name}-{quantization}.gguf"
        
        return model_path.full_url(fname)
    
    @classmethod
    def get_variants(cls, model_name: str) -> List[str]:
        """
        Get all quantization variants for a model
        
        Returns list of URLs for different quantizations:
        - Q4_K_M (default, balanced)
        - Q4_K_S (smaller, faster)
        - Q5_K_M (higher quality)
        - Q6_K (even higher quality)
        - Q8_0 (highest quality)
        """
        model_path = cls.parse(model_name)
        quantizations = ["Q4_K_M", "Q4_K_S", "Q5_K_M", "Q6_K", "Q8_0"]
        
        return [
            cls.resolve_download_url(model_path, quantization=q)
            for q in quantizations
        ]
    
    @classmethod
    def add_known_model(
        cls,
        shortcut: str,
        namespace: str,
        repository: str,
        filename: str,
        tag: str = "main"
    ) -> None:
        """
        Add a new model shortcut to known models
        
        Example:
            ModelRegistry.add_known_model(
                "my-model",
                "myuser",
                "my-awesome-model-GGUF",
                "model-q4_k_m.gguf"
            )
            # Now you can use: parse("my-model")
        """
        cls.KNOWN_MODELS[shortcut] = {
            "namespace": namespace,
            "repository": repository,
            "filename": filename,
            "tag": tag
        }
    
    @classmethod
    def list_known_models(cls) -> Dict[str, Dict[str, str]]:
        """Return all known model shortcuts"""
        return dict(cls.KNOWN_MODELS)


# Convenience functions
def parse_model_path(model_name: str) -> ModelPath:
    """Parse model name into ModelPath (convenience function)"""
    return ModelRegistry.parse(model_name)


def get_download_url(model_name: str, quantization: Optional[str] = None) -> str:
    """Get download URL for model (convenience function)"""
    model_path = ModelRegistry.parse(model_name)
    return ModelRegistry.resolve_download_url(model_path, quantization=quantization)
