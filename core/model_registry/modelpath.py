"""
Model Path Parser - Ollama-kompatibel
Parst Model-Pfade wie: mistral, hf.co/bartowski/model:tag, registry.com/namespace/repo
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ModelPath:
    """Repraesentiert einen geparsten Model-Pfad"""
    protocol: str = "https"
    registry: str = "huggingface.co"
    namespace: str = "bartowski"
    repository: str = ""
    tag: str = "latest"
    filename: Optional[str] = None
    
    def base_url(self) -> str:
        """Erstellt die Base-URL fuer die Registry"""
        return f"{self.protocol}://{self.registry}"
    
    def full_path(self) -> str:
        """Gibt den vollstaendigen Pfad zurueck"""
        return f"{self.registry}/{self.namespace}/{self.repository}:{self.tag}"
    
    def is_huggingface(self) -> bool:
        """Prueft ob es eine Hugging Face Registry ist"""
        return "huggingface.co" in self.registry or "hf.co" in self.registry
    
    def resolve_url(self, filename: Optional[str] = None) -> str:
        """Erstellt die Download-URL"""
        file = filename or self.filename or "model.gguf"
        
        if self.is_huggingface():
            # HuggingFace Format: /resolve/main/ oder /resolve/{tag}/
            branch = "main" if self.tag == "latest" else self.tag
            return f"{self.base_url()}/{self.namespace}/{self.repository}/resolve/{branch}/{file}"
        
        # Custom Registry Format
        return f"{self.base_url()}/{self.namespace}/{self.repository}/{self.tag}/{file}"


class ModelPathParser:
    """Parser fuer Model-Pfade (Ollama-kompatibel)"""
    
    # Regex Pattern fuer Model-Pfade
    FULL_PATH_PATTERN = re.compile(
        r'^(?P<registry>[\w\.-]+(?::[\d]+)?)/(?P<namespace>[\w\.-]+)/(?P<repo>[\w\.-]+)(?::(?P<tag>[\w\.-]+))?$'
    )
    SHORT_PATH_PATTERN = re.compile(
        r'^(?P<namespace>[\w\.-]+)/(?P<repo>[\w\.-]+)(?::(?P<tag>[\w\.-]+))?$'
    )
    SIMPLE_NAME_PATTERN = re.compile(r'^[\w\.-]+$')
    
    # Default-Werte
    DEFAULT_PROTOCOL = "https"
    DEFAULT_REGISTRY = "huggingface.co"
    DEFAULT_NAMESPACE = "bartowski"
    DEFAULT_TAG = "latest"
    
    # Registry-Aliases
    REGISTRY_ALIASES = {
        "hf": "huggingface.co",
        "hf.co": "huggingface.co",
        "ollama": "registry.ollama.ai",
        "ollama.ai": "registry.ollama.ai",
    }
    
    @classmethod
    def parse(cls, path: str) -> ModelPath:
        """
        Parst einen Model-Pfad in seine Komponenten.
        
        Unterstuetzte Formate:
        - mistral → huggingface.co/bartowski/mistral:latest
        - bartowski/mistral → huggingface.co/bartowski/mistral:latest
        - hf.co/bartowski/mistral:v1 → huggingface.co/bartowski/mistral:v1
        - registry.com/namespace/repo:tag → registry.com/namespace/repo:tag
        
        Args:
            path: Model-Pfad String
            
        Returns:
            ModelPath Objekt
        """
        if not path or not path.strip():
            raise ValueError("Model-Pfad darf nicht leer sein")
        
        path = path.strip()
        
        # 1. Vollstaendiger Pfad: registry/namespace/repo:tag
        match = cls.FULL_PATH_PATTERN.match(path)
        if match:
            registry = cls._normalize_registry(match.group('registry'))
            return ModelPath(
                protocol=cls.DEFAULT_PROTOCOL,
                registry=registry,
                namespace=match.group('namespace'),
                repository=match.group('repo'),
                tag=match.group('tag') or cls.DEFAULT_TAG
            )
        
        # 2. Kurzer Pfad: namespace/repo:tag
        match = cls.SHORT_PATH_PATTERN.match(path)
        if match:
            return ModelPath(
                protocol=cls.DEFAULT_PROTOCOL,
                registry=cls.DEFAULT_REGISTRY,
                namespace=match.group('namespace'),
                repository=match.group('repo'),
                tag=match.group('tag') or cls.DEFAULT_TAG
            )
        
        # 3. Einfacher Name: mistral
        if cls.SIMPLE_NAME_PATTERN.match(path):
            return ModelPath(
                protocol=cls.DEFAULT_PROTOCOL,
                registry=cls.DEFAULT_REGISTRY,
                namespace=cls.DEFAULT_NAMESPACE,
                repository=path,
                tag=cls.DEFAULT_TAG
            )
        
        raise ValueError(f"Ungueltiges Model-Pfad Format: {path}")
    
    @classmethod
    def _normalize_registry(cls, registry: str) -> str:
        """Normalisiert Registry-Namen (resolved Aliases)"""
        registry_lower = registry.lower()
        return cls.REGISTRY_ALIASES.get(registry_lower, registry)
    
    @classmethod
    def is_valid_path(cls, path: str) -> bool:
        """Prueft ob ein Pfad gueltig ist"""
        try:
            cls.parse(path)
            return True
        except ValueError:
            return False
