"""
Manifest Handler - Verwaltet Model-Metadaten und Manifeste
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field


@dataclass
class BlobInfo:
    """Information ueber einen Model-Blob (Layer)"""
    digest: str  # SHA256 Hash
    size: int
    media_type: str = "application/octet-stream"
    filename: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlobInfo':
        return cls(**data)


@dataclass
class ModelManifest:
    """Model-Manifest (aehnlich wie Ollama)"""
    schema_version: int = 2
    name: str = ""
    tag: str = "latest"
    digest: str = ""  # SHA256 des gesamten Manifests
    size: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    layers: List[BlobInfo] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    
    def add_layer(self, digest: str, size: int, filename: Optional[str] = None) -> None:
        """Fuegt einen Layer zum Manifest hinzu"""
        blob = BlobInfo(digest=digest, size=size, filename=filename)
        self.layers.append(blob)
        self.size += size
    
    def calculate_digest(self) -> str:
        """Berechnet den SHA256-Hash des Manifests"""
        # Manifest ohne digest serialisieren
        data = self.to_dict()
        data.pop('digest', None)
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dict"""
        return {
            'schemaVersion': self.schema_version,
            'name': self.name,
            'tag': self.tag,
            'digest': self.digest,
            'size': self.size,
            'createdAt': self.created_at,
            'layers': [layer.to_dict() for layer in self.layers],
            'config': self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelManifest':
        """Erstellt Manifest aus Dict"""
        layers_data = data.pop('layers', [])
        layers = [BlobInfo.from_dict(layer) for layer in layers_data]
        
        # Key-Mapping (camelCase -> snake_case)
        mapped_data = {
            'schema_version': data.get('schemaVersion', 2),
            'name': data.get('name', ''),
            'tag': data.get('tag', 'latest'),
            'digest': data.get('digest', ''),
            'size': data.get('size', 0),
            'created_at': data.get('createdAt', datetime.utcnow().isoformat()),
            'config': data.get('config', {}),
            'layers': layers
        }
        
        return cls(**mapped_data)


class ManifestHandler:
    """Verwaltet Model-Manifeste"""
    
    def __init__(self, manifests_dir: Path):
        self.manifests_dir = manifests_dir
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_manifest_path(self, model_key: str) -> Path:
        """Gibt den Pfad zur Manifest-Datei zurueck"""
        return self.manifests_dir / f"{model_key}.json"
    
    def save_manifest(self, model_key: str, manifest: ModelManifest) -> None:
        """Speichert ein Manifest"""
        # Digest berechnen vor dem Speichern
        manifest.digest = manifest.calculate_digest()
        
        path = self._get_manifest_path(model_key)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)
    
    def load_manifest(self, model_key: str) -> Optional[ModelManifest]:
        """Laedt ein Manifest"""
        path = self._get_manifest_path(model_key)
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ModelManifest.from_dict(data)
        except Exception:
            return None
    
    def manifest_exists(self, model_key: str) -> bool:
        """Prueft ob ein Manifest existiert"""
        return self._get_manifest_path(model_key).exists()
    
    def delete_manifest(self, model_key: str) -> bool:
        """Loescht ein Manifest"""
        path = self._get_manifest_path(model_key)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def list_manifests(self) -> List[str]:
        """Listet alle verfuegbaren Manifeste"""
        return [p.stem for p in self.manifests_dir.glob('*.json')]
    
    def create_manifest_from_file(
        self, 
        model_key: str, 
        file_path: Path,
        name: Optional[str] = None,
        tag: str = "latest"
    ) -> ModelManifest:
        """
        Erstellt ein Manifest aus einer existierenden Datei.
        Berechnet SHA256 und erstellt Layer-Info.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")
        
        # SHA256 berechnen
        sha256 = hashlib.sha256()
        size = 0
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
                size += len(chunk)
        
        digest = sha256.hexdigest()
        
        # Manifest erstellen
        manifest = ModelManifest(
            name=name or model_key,
            tag=tag
        )
        manifest.add_layer(
            digest=digest,
            size=size,
            filename=file_path.name
        )
        
        return manifest
