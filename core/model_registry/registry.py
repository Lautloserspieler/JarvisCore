"""
Model Registry - Zentrale Verwaltung fuer Model-Downloads
"""

from pathlib import Path
from typing import Dict, Optional, Callable, List, Any

from utils.logger import Logger
from .modelpath import ModelPath, ModelPathParser
from .manifest import ManifestHandler, ModelManifest
from .downloader import ModelDownloader, DownloadProgress


class ModelRegistry:
    """
    Zentrale Registry fuer Model-Management.
    Kombiniert ModelPath-Parsing, Downloads und Manifest-Handling.
    """
    
    # Bekannte Modelle mit SHA256-Checksums (wird nach und nach erweitert)
    KNOWN_MODELS: Dict[str, Dict[str, Any]] = {
        "mistral-nemo-instruct-2407-q4": {
            "path": "hf.co/second-state/Mistral-Nemo-Instruct-2407-GGUF",
            "filename": "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
            "sha256": None,  # TODO: Add checksum
            "size_gb": 7.48,
            "description": "Mistral Nemo Instruct Q4_K_M"
        },
        "deepseek-r1-distill-llama-8b-q4": {
            "path": "hf.co/Triangle104/DeepSeek-R1-Distill-Llama-8B-Q4_K_M-GGUF",
            "filename": "deepseek-r1-distill-llama-8b-q4_k_m.gguf",
            "sha256": None,
            "size_gb": 6.9,
            "description": "DeepSeek R1 Distill Llama 8B Q4_K_M"
        },
        "qwen2.5-7b-instruct-q4": {
            "path": "hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF",
            "filename": "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
            "sha256": None,
            "size_gb": 5.2,
            "description": "Qwen 2.5 7B Instruct Q4_K_M"
        },
        "llama-2-7b-chat-q4": {
            "path": "hf.co/TheBloke/Llama-2-7B-Chat-GGUF",
            "filename": "llama-2-7b-chat.Q4_K_M.gguf",
            "sha256": None,
            "size_gb": 4.0,
            "description": "Llama 2 7B Chat Q4_K_M"
        },
    }
    
    def __init__(
        self,
        models_dir: Path,
        manifests_dir: Optional[Path] = None,
        chunk_size: int = 4 * 1024 * 1024
    ):
        self.logger = Logger()
        self.models_dir = Path(models_dir)
        self.manifests_dir = manifests_dir or (self.models_dir / ".manifests")
        
        # Sub-Komponenten initialisieren
        self.manifest_handler = ManifestHandler(self.manifests_dir)
        self.downloader = ModelDownloader(
            models_dir=self.models_dir,
            manifest_handler=self.manifest_handler,
            chunk_size=chunk_size
        )
    
    def download_model(
        self,
        model_identifier: str,
        filename: Optional[str] = None,
        expected_sha256: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        hf_token: Optional[str] = None
    ) -> Path:
        """
        Laedt ein Modell herunter.
        
        Args:
            model_identifier: Kann sein:
                - Bekannter Key ("mistral-nemo-instruct-2407-q4")
                - Model-Pfad ("hf.co/bartowski/model")
                - Namespace/Repo ("bartowski/model")
            filename: Dateiname (optional, wenn bekanntes Modell)
            expected_sha256: SHA256-Checksum (optional)
            progress_callback: Callback fuer Progress-Updates
            hf_token: Hugging Face Token
            
        Returns:
            Path zur heruntergeladenen Datei
        """
        # Pruefe ob es ein bekanntes Modell ist
        if model_identifier in self.KNOWN_MODELS:
            known = self.KNOWN_MODELS[model_identifier]
            model_path = known['path']
            filename = filename or known['filename']
            expected_sha256 = expected_sha256 or known.get('sha256')
        else:
            model_path = model_identifier
            if not filename:
                raise ValueError(
                    f"Filename muss angegeben werden fuer unbekanntes Modell: {model_identifier}"
                )
        
        # Download durchfuehren
        return self.downloader.download(
            model_path=model_path,
            filename=filename,
            expected_sha256=expected_sha256,
            progress_callback=progress_callback,
            hf_token=hf_token
        )
    
    def parse_model_path(self, path: str) -> ModelPath:
        """Parst einen Model-Pfad"""
        return ModelPathParser.parse(path)
    
    def get_manifest(self, model_key: str) -> Optional[ModelManifest]:
        """Laedt ein Manifest"""
        return self.manifest_handler.load_manifest(model_key)
    
    def model_exists(self, filename: str) -> bool:
        """Prueft ob ein Modell lokal existiert"""
        return (self.models_dir / filename).exists()
    
    def list_local_models(self) -> List[str]:
        """Listet alle lokalen GGUF-Modelle"""
        return [f.name for f in self.models_dir.glob('*.gguf')]
    
    def list_known_models(self) -> Dict[str, Dict[str, Any]]:
        """Gibt die Liste bekannter Modelle zurueck"""
        return self.KNOWN_MODELS.copy()
    
    def cleanup_temp_files(self) -> None:
        """Raumt temporaere Download-Dateien auf"""
        self.downloader.cleanup_temp_files()
    
    def verify_model(
        self,
        filename: str,
        expected_sha256: str
    ) -> bool:
        """
        Verifiziert ein lokales Modell.
        
        Args:
            filename: Dateiname des Modells
            expected_sha256: Erwarteter SHA256-Hash
            
        Returns:
            True wenn valide, False sonst
        """
        file_path = self.models_dir / filename
        if not file_path.exists():
            return False
        
        return self.downloader._verify_file(file_path, expected_sha256)
    
    def get_model_info(self, model_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Gibt Informationen ueber ein Modell zurueck.
        
        Args:
            model_identifier: Bekannter Key oder Model-Pfad
            
        Returns:
            Dict mit Model-Informationen oder None
        """
        # Bekanntes Modell?
        if model_identifier in self.KNOWN_MODELS:
            info = self.KNOWN_MODELS[model_identifier].copy()
            filename = info['filename']
            info['local'] = self.model_exists(filename)
            info['model_key'] = model_identifier
            return info
        
        # Versuche zu parsen
        try:
            parsed = self.parse_model_path(model_identifier)
            return {
                'path': parsed.full_path(),
                'registry': parsed.registry,
                'namespace': parsed.namespace,
                'repository': parsed.repository,
                'tag': parsed.tag,
                'local': False,
                'model_key': f"{parsed.namespace}_{parsed.repository}"
            }
        except ValueError:
            return None
