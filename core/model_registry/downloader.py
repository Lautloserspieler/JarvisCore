"""
Model Downloader - Ollama-level Download mit Resume und SHA256
"""

import os
import hashlib
import time
import requests
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

from utils.logger import Logger
from .manifest import ManifestHandler, ModelManifest, BlobInfo
from .modelpath import ModelPath, ModelPathParser


@dataclass
class DownloadProgress:
    """Download-Progress Information"""
    model_key: str
    status: str  # 'starting', 'downloading', 'verifying', 'completed', 'failed'
    downloaded: int = 0
    total: int = 0
    speed: float = 0.0  # bytes/sec
    eta: Optional[float] = None  # seconds
    message: Optional[str] = None
    
    @property
    def percent(self) -> Optional[float]:
        """Fortschritt in Prozent"""
        if self.total > 0:
            return (self.downloaded / self.total) * 100
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dict"""
        return {
            'model': self.model_key,
            'status': self.status,
            'downloaded': self.downloaded,
            'total': self.total,
            'percent': self.percent,
            'speed': self.speed,
            'eta': self.eta,
            'message': self.message
        }


class ModelDownloader:
    """Laedt Modelle mit Resume-Support und SHA256-Verifizierung herunter"""
    
    def __init__(
        self,
        models_dir: Path,
        manifest_handler: ManifestHandler,
        chunk_size: int = 4 * 1024 * 1024,  # 4MB chunks
        timeout: int = 30
    ):
        self.logger = Logger()
        self.models_dir = models_dir
        self.manifest_handler = manifest_handler
        self.chunk_size = chunk_size
        self.timeout = timeout
        
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._temp_dir = self.models_dir / ".downloads"
        self._temp_dir.mkdir(exist_ok=True)
    
    def download(
        self,
        model_path: str,
        filename: str,
        expected_sha256: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        hf_token: Optional[str] = None
    ) -> Path:
        """
        Laedt ein Modell herunter (mit Resume-Support).
        
        Args:
            model_path: Model-Pfad (z.B. "hf.co/bartowski/mistral")
            filename: Dateiname (z.B. "model.Q4_K_M.gguf")
            expected_sha256: Erwarteter SHA256-Hash (optional)
            progress_callback: Callback fuer Progress-Updates
            hf_token: Hugging Face Token (optional)
            
        Returns:
            Path zur heruntergeladenen Datei
        """
        # Model-Path parsen
        parsed_path = ModelPathParser.parse(model_path)
        parsed_path.filename = filename
        model_key = f"{parsed_path.namespace}_{parsed_path.repository}"
        
        # Download-URL erstellen
        url = parsed_path.resolve_url(filename)
        
        # Ziel-Pfad
        target_path = self.models_dir / filename
        temp_path = self._temp_dir / f"{filename}.download"
        
        # Pruefen ob Datei bereits existiert und valide ist
        if target_path.exists():
            if expected_sha256:
                if self._verify_file(target_path, expected_sha256):
                    self.logger.info(f"Modell bereits vorhanden und valide: {target_path}")
                    if progress_callback:
                        progress = DownloadProgress(
                            model_key=model_key,
                            status='completed',
                            downloaded=target_path.stat().st_size,
                            total=target_path.stat().st_size,
                            message='Bereits vorhanden'
                        )
                        progress_callback(progress)
                    return target_path
            else:
                self.logger.info(f"Modell bereits vorhanden: {target_path}")
                return target_path
        
        # Download starten
        self.logger.info(f"Starte Download: {url}")
        
        try:
            downloaded_path = self._download_with_resume(
                url=url,
                temp_path=temp_path,
                model_key=model_key,
                progress_callback=progress_callback,
                hf_token=hf_token
            )
            
            # SHA256-Verifizierung
            if expected_sha256:
                self._emit_progress(
                    DownloadProgress(
                        model_key=model_key,
                        status='verifying',
                        message='Verifiziere SHA256...'
                    ),
                    progress_callback
                )
                
                if not self._verify_file(downloaded_path, expected_sha256):
                    downloaded_path.unlink()
                    raise ValueError(f"SHA256-Verifizierung fehlgeschlagen fuer {filename}")
                
                self.logger.info(f"SHA256-Verifizierung erfolgreich: {filename}")
            
            # Verschiebe zu finalem Ziel
            os.replace(downloaded_path, target_path)
            
            # Manifest erstellen
            manifest = self.manifest_handler.create_manifest_from_file(
                model_key=model_key,
                file_path=target_path,
                name=parsed_path.repository,
                tag=parsed_path.tag
            )
            self.manifest_handler.save_manifest(model_key, manifest)
            
            # Erfolgs-Meldung
            self._emit_progress(
                DownloadProgress(
                    model_key=model_key,
                    status='completed',
                    downloaded=target_path.stat().st_size,
                    total=target_path.stat().st_size,
                    message='Download abgeschlossen'
                ),
                progress_callback
            )
            
            self.logger.info(f"Download abgeschlossen: {target_path}")
            return target_path
            
        except Exception as e:
            self.logger.error(f"Download fehlgeschlagen: {e}")
            self._emit_progress(
                DownloadProgress(
                    model_key=model_key,
                    status='failed',
                    message=str(e)
                ),
                progress_callback
            )
            raise
    
    def _download_with_resume(
        self,
        url: str,
        temp_path: Path,
        model_key: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]],
        hf_token: Optional[str]
    ) -> Path:
        """Download mit Resume-Support"""
        # Bereits heruntergeladene Bytes
        downloaded = 0
        if temp_path.exists():
            downloaded = temp_path.stat().st_size
            self.logger.info(f"Resume Download ab {downloaded} bytes")
        
        # Headers
        headers = {}
        if downloaded > 0:
            headers['Range'] = f'bytes={downloaded}-'
        if hf_token:
            headers['Authorization'] = f'Bearer {hf_token}'
        
        # Request
        response = requests.get(url, headers=headers, stream=True, timeout=self.timeout)
        response.raise_for_status()
        
        # Content-Length (kann bei Resume partial sein)
        content_length = response.headers.get('Content-Length')
        if content_length:
            total = downloaded + int(content_length)
        else:
            total = 0
        
        # Download
        mode = 'ab' if downloaded > 0 else 'wb'
        start_time = time.time()
        last_update = start_time
        
        with open(temp_path, mode) as f:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if not chunk:
                    continue
                
                f.write(chunk)
                downloaded += len(chunk)
                
                # Progress-Update (max alle 0.5s)
                now = time.time()
                if now - last_update >= 0.5 or downloaded == total:
                    elapsed = max(now - start_time, 0.001)
                    speed = downloaded / elapsed
                    eta = None
                    if total > 0 and downloaded < total and speed > 0:
                        eta = (total - downloaded) / speed
                    
                    self._emit_progress(
                        DownloadProgress(
                            model_key=model_key,
                            status='downloading',
                            downloaded=downloaded,
                            total=total,
                            speed=speed,
                            eta=eta
                        ),
                        progress_callback
                    )
                    last_update = now
        
        return temp_path
    
    def _verify_file(self, file_path: Path, expected_sha256: str) -> bool:
        """Verifiziert eine Datei mit SHA256"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        actual_sha256 = sha256.hexdigest()
        return actual_sha256.lower() == expected_sha256.lower()
    
    def _emit_progress(
        self,
        progress: DownloadProgress,
        callback: Optional[Callable[[DownloadProgress], None]]
    ) -> None:
        """Sendet Progress-Update"""
        if callback:
            try:
                callback(progress)
            except Exception as e:
                self.logger.warning(f"Progress-Callback fehlgeschlagen: {e}")
    
    def cleanup_temp_files(self) -> None:
        """Loescht temporaere Download-Dateien"""
        if self._temp_dir.exists():
            for temp_file in self._temp_dir.glob('*.download'):
                try:
                    temp_file.unlink()
                    self.logger.debug(f"Temporaere Datei geloescht: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"Konnte temp file nicht loeschen: {e}")
