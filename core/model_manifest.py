"""
Model Manifest Management für J.A.R.V.I.S.
Speichert Metadaten, SHA256-Hashes und Versions-Informationen
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from datetime import datetime

from utils.logger import Logger


@dataclass
class ModelLayer:
    """Model layer/file information (Ollama-Style)"""
    filename: str
    sha256: str
    size_bytes: int
    download_url: Optional[str] = None
    downloaded_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelLayer':
        return cls(**data)


@dataclass
class ModelManifest:
    """
    Model manifest with metadata (Ollama-Style)
    
    Speichert:
    - Model-Metadaten (Name, Version, Parameter)
    - Layer-Informationen (Dateien + SHA256)
    - Download-Status
    - Load-Konfiguration
    """
    model_key: str
    registry: str
    namespace: str
    repository: str
    tag: str
    
    # Model metadata
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[str] = None  # e.g., "7B", "13B"
    context_length: int = 4096
    quantization: Optional[str] = None  # e.g., "Q4_K_M"
    
    # Layers (files)
    layers: List[ModelLayer] = field(default_factory=list)
    
    # Status
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    downloaded: bool = False
    verified: bool = False
    
    # Load configuration
    gpu_layers: int = -1  # -1 = auto/all
    threads: Optional[int] = None  # None = auto
    
    # Usage statistics
    load_count: int = 0
    last_loaded: Optional[float] = None
    
    def add_layer(self, filename: str, sha256: str, size_bytes: int, download_url: Optional[str] = None) -> None:
        """Add a layer/file to the manifest"""
        layer = ModelLayer(
            filename=filename,
            sha256=sha256,
            size_bytes=size_bytes,
            download_url=download_url
        )
        self.layers.append(layer)
        self.modified_at = time.time()
    
    def mark_downloaded(self) -> None:
        """Mark model as fully downloaded"""
        self.downloaded = True
        self.modified_at = time.time()
        for layer in self.layers:
            if layer.downloaded_at is None:
                layer.downloaded_at = time.time()
    
    def mark_verified(self) -> None:
        """Mark model as verified"""
        self.verified = True
        self.modified_at = time.time()
    
    def mark_loaded(self) -> None:
        """Update load statistics"""
        self.load_count += 1
        self.last_loaded = time.time()
        self.modified_at = time.time()
    
    @property
    def total_size_bytes(self) -> int:
        """Total size of all layers"""
        return sum(layer.size_bytes for layer in self.layers)
    
    @property
    def total_size_gb(self) -> float:
        """Total size in GB"""
        return self.total_size_bytes / (1024 ** 3)
    
    @property
    def primary_layer(self) -> Optional[ModelLayer]:
        """Get primary/first layer"""
        return self.layers[0] if self.layers else None
    
    @property
    def model_path_str(self) -> str:
        """Full model path string (registry/namespace/repo:tag)"""
        path = f"{self.registry}/{self.namespace}/{self.repository}"
        if self.tag and self.tag != "main":
            path += f":{self.tag}"
        return path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["layers"] = [layer.to_dict() for layer in self.layers]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelManifest':
        """Create from dictionary"""
        layers_data = data.pop("layers", [])
        manifest = cls(**data)
        manifest.layers = [ModelLayer.from_dict(layer) for layer in layers_data]
        return manifest


class ManifestManager:
    """
    Manages model manifests (Ollama-Style)
    
    Funktionen:
    - Speichern/Laden von Manifests
    - Versions-Tracking
    - Status-Updates
    - Cleanup alter Manifests
    """
    
    MANIFEST_VERSION = "1.0"
    
    def __init__(self, manifest_dir: Path, logger: Optional[Logger] = None):
        self.manifest_dir = Path(manifest_dir)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or Logger()
        
        # Cache
        self._cache: Dict[str, ModelManifest] = {}
        self._load_all_manifests()
    
    def _load_all_manifests(self) -> None:
        """Load all existing manifests into cache"""
        for manifest_file in self.manifest_dir.glob("*.json"):
            try:
                model_key = manifest_file.stem
                manifest = self._load_manifest_file(manifest_file)
                self._cache[model_key] = manifest
            except Exception as exc:
                self.logger.warning(f"Konnte Manifest nicht laden: {manifest_file}: {exc}")
    
    def _load_manifest_file(self, manifest_file: Path) -> ModelManifest:
        """Load manifest from file"""
        with open(manifest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check version
        if data.get("version") != self.MANIFEST_VERSION:
            self.logger.warning(f"Manifest-Version mismatch: {manifest_file}")
        
        manifest_data = data.get("manifest", {})
        return ModelManifest.from_dict(manifest_data)
    
    def _save_manifest_file(self, model_key: str, manifest: ModelManifest) -> None:
        """Save manifest to file"""
        manifest_file = self.manifest_dir / f"{model_key}.json"
        
        data = {
            "version": self.MANIFEST_VERSION,
            "created": datetime.now().isoformat(),
            "manifest": manifest.to_dict()
        }
        
        # Atomic write (write to temp, then rename)
        temp_file = manifest_file.with_suffix(".json.tmp")
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        temp_file.replace(manifest_file)
    
    def get_manifest(self, model_key: str) -> Optional[ModelManifest]:
        """Get manifest for model"""
        return self._cache.get(model_key)
    
    def create_manifest(
        self,
        model_key: str,
        registry: str,
        namespace: str,
        repository: str,
        tag: str = "main",
        **kwargs
    ) -> ModelManifest:
        """Create new manifest"""
        manifest = ModelManifest(
            model_key=model_key,
            registry=registry,
            namespace=namespace,
            repository=repository,
            tag=tag,
            **kwargs
        )
        
        self._cache[model_key] = manifest
        self._save_manifest_file(model_key, manifest)
        
        return manifest
    
    def update_manifest(self, model_key: str, manifest: ModelManifest) -> None:
        """Update existing manifest"""
        manifest.modified_at = time.time()
        self._cache[model_key] = manifest
        self._save_manifest_file(model_key, manifest)
    
    def delete_manifest(self, model_key: str) -> bool:
        """Delete manifest"""
        manifest_file = self.manifest_dir / f"{model_key}.json"
        
        if manifest_file.exists():
            manifest_file.unlink()
            self._cache.pop(model_key, None)
            return True
        
        return False
    
    def list_manifests(self) -> Dict[str, ModelManifest]:
        """List all manifests"""
        return dict(self._cache)
    
    def get_downloaded_models(self) -> List[str]:
        """Get list of downloaded model keys"""
        return [
            key for key, manifest in self._cache.items()
            if manifest.downloaded
        ]
    
    def get_verified_models(self) -> List[str]:
        """Get list of verified model keys"""
        return [
            key for key, manifest in self._cache.items()
            if manifest.verified
        ]
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about all models"""
        total_models = len(self._cache)
        downloaded_models = len(self.get_downloaded_models())
        verified_models = len(self.get_verified_models())
        
        total_size = sum(
            manifest.total_size_bytes
            for manifest in self._cache.values()
            if manifest.downloaded
        )
        
        most_used = None
        max_loads = 0
        for key, manifest in self._cache.items():
            if manifest.load_count > max_loads:
                max_loads = manifest.load_count
                most_used = key
        
        return {
            "total_models": total_models,
            "downloaded": downloaded_models,
            "verified": verified_models,
            "total_size_gb": round(total_size / (1024 ** 3), 2),
            "most_used_model": most_used,
            "most_used_count": max_loads
        }
    
    def cleanup_old_manifests(self, max_age_days: int = 90) -> int:
        """Cleanup manifests older than max_age_days"""
        now = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        cleaned = 0
        to_remove = []
        
        for key, manifest in self._cache.items():
            # Don't clean if downloaded or recently used
            if manifest.downloaded:
                continue
            
            age = now - manifest.modified_at
            if age > max_age_seconds:
                to_remove.append(key)
        
        for key in to_remove:
            if self.delete_manifest(key):
                cleaned += 1
        
        if cleaned > 0:
            self.logger.info(f"Bereinigt: {cleaned} alte Manifests")
        
        return cleaned
