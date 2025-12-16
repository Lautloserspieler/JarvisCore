"""
LLM Manager Integration - Erweitert den bestehenden LLM Manager
mit Ollama-level Download-Funktionalitaet
"""

from pathlib import Path
from typing import Optional, Callable, Dict, Any

from utils.logger import Logger
from core.model_registry import ModelRegistry, DownloadProgress


class LLMManagerMixin:
    """
    Mixin fuer LLM Manager - fuegt Ollama-level Download hinzu.
    Wird in den bestehenden LLM Manager integriert.
    """
    
    def _init_model_registry(self) -> None:
        """Initialisiert die Model Registry"""
        if not hasattr(self, 'models_dir'):
            self.models_dir = Path("models/llm")
        
        if not hasattr(self, 'logger'):
            self.logger = Logger()
        
        # Registry initialisieren
        self.model_registry = ModelRegistry(
            models_dir=self.models_dir,
            manifests_dir=self.models_dir / ".manifests"
        )
        
        self.logger.info("Model Registry initialisiert (Ollama-level)")
    
    def download_model_advanced(
        self,
        model_identifier: str,
        filename: Optional[str] = None,
        expected_sha256: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        """
        Laedt ein Modell mit Ollama-level Features herunter.
        
        Args:
            model_identifier: Model-Key oder Pfad (z.B. "hf.co/bartowski/model")
            filename: Dateiname (optional fuer bekannte Modelle)
            expected_sha256: SHA256-Checksum (optional)
            progress_callback: Callback fuer Progress-Updates
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not hasattr(self, 'model_registry'):
            self._init_model_registry()
        
        # HuggingFace Token aus Settings holen
        hf_token = None
        if hasattr(self, 'settings') and self.settings:
            try:
                llm_config = self.settings.get('llm', {})
                if isinstance(llm_config, dict):
                    hf_token = llm_config.get('huggingface_token')
            except Exception:
                pass
        
        # Wrapper fuer Progress-Callback (DownloadProgress → Dict)
        def wrapped_callback(progress: DownloadProgress) -> None:
            if progress_callback:
                progress_callback(progress.to_dict())
        
        try:
            downloaded_path = self.model_registry.download_model(
                model_identifier=model_identifier,
                filename=filename,
                expected_sha256=expected_sha256,
                progress_callback=wrapped_callback,
                hf_token=hf_token
            )
            
            self.logger.info(f"Modell erfolgreich heruntergeladen: {downloaded_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Download fehlgeschlagen: {e}")
            return False
    
    def parse_model_path(self, path: str) -> Dict[str, Any]:
        """
        Parst einen Model-Pfad.
        
        Args:
            path: Model-Pfad (z.B. "hf.co/bartowski/model:v1")
            
        Returns:
            Dict mit geparsten Komponenten
        """
        if not hasattr(self, 'model_registry'):
            self._init_model_registry()
        
        parsed = self.model_registry.parse_model_path(path)
        return {
            'protocol': parsed.protocol,
            'registry': parsed.registry,
            'namespace': parsed.namespace,
            'repository': parsed.repository,
            'tag': parsed.tag,
            'full_path': parsed.full_path(),
            'base_url': parsed.base_url(),
            'is_huggingface': parsed.is_huggingface()
        }
    
    def list_known_models(self) -> Dict[str, Dict[str, Any]]:
        """Listet alle bekannten Modelle"""
        if not hasattr(self, 'model_registry'):
            self._init_model_registry()
        
        return self.model_registry.list_known_models()
    
    def get_model_registry_info(self, model_identifier: str) -> Optional[Dict[str, Any]]:
        """Gibt Registry-Informationen ueber ein Modell zurueck"""
        if not hasattr(self, 'model_registry'):
            self._init_model_registry()
        
        return self.model_registry.get_model_info(model_identifier)
    
    def cleanup_download_temp_files(self) -> None:
        """Raumt temporaere Download-Dateien auf"""
        if not hasattr(self, 'model_registry'):
            self._init_model_registry()
        
        self.model_registry.cleanup_temp_files()
        self.logger.info("Temporaere Download-Dateien geloescht")
