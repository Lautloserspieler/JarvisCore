"""
Advanced Model Downloader für J.A.R.V.I.S.
Ollama-Level Features: Resume-Support, SHA256-Verifizierung, Parallel-Downloads
"""

import os
import time
import hashlib
import threading
import contextlib
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

from utils.logger import Logger


class DownloadCancelled(Exception):
    """Raised when a download is cancelled."""



@dataclass
class DownloadProgress:
    """Download progress information"""
    model_key: str
    status: str = "pending"  # pending, downloading, verifying, completed, failed
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_bytes_per_sec: float = 0.0
    eta_seconds: Optional[float] = None
    error: Optional[str] = None
    sha256: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    
    @property
    def percent(self) -> float:
        """Download progress percentage"""
        if self.total_bytes <= 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100.0
    
    @property
    def elapsed_seconds(self) -> float:
        """Elapsed time since start"""
        return time.time() - self.start_time
    
    @property
    def speed_mbps(self) -> float:
        """Download speed in MB/s"""
        return self.speed_bytes_per_sec / (1024 * 1024)
    
    @property
    def eta_formatted(self) -> str:
        """Formatted ETA (e.g., '5m 30s')"""
        if self.eta_seconds is None or self.eta_seconds <= 0:
            return "calculating..."
        
        minutes, seconds = divmod(int(self.eta_seconds), 60)
        if minutes > 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}h {minutes}m"
        return f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "model": self.model_key,
            "status": self.status,
            "downloaded": self.downloaded_bytes,
            "total": self.total_bytes,
            "percent": round(self.percent, 2),
            "speed": round(self.speed_bytes_per_sec, 2),
            "speed_mbps": round(self.speed_mbps, 2),
            "eta": self.eta_formatted,
            "elapsed": round(self.elapsed_seconds, 2),
            "error": self.error,
            "sha256": self.sha256
        }


class ModelDownloader:
    """
    Advanced Model Downloader mit Ollama-Level Features:
    - Resume-Support (HTTP Range Requests)
    - SHA256-Verifizierung
    - Progress-Callbacks
    - Parallel-Downloads
    - Automatic Retry
    """
    
    def __init__(self, download_dir: Path, logger: Optional[Logger] = None):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or Logger()
        
        # Active downloads tracking
        self.active_downloads: Dict[str, DownloadProgress] = {}
        self.download_locks: Dict[str, threading.Lock] = {}
        self.cancel_flags: Dict[str, threading.Event] = {}
        
        # Configuration
        self.chunk_size = 4 * 1024 * 1024  # 4 MB chunks
        self.progress_update_interval = 0.5  # 500ms
        self.max_retries = 3
        self.retry_delay = 2.0  # seconds
        self.timeout = 30  # seconds
        
        # HuggingFace token support
        self.hf_token: Optional[str] = os.environ.get("HUGGINGFACE_TOKEN")
    
    def set_hf_token(self, token: str) -> None:
        """Set HuggingFace API token for private repos"""
        self.hf_token = token
        self.logger.info("❌ HuggingFace Token gesetzt")
    
    def download(
        self,
        model_key: str,
        url: str,
        filename: str,
        expected_sha256: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        force: bool = False
    ) -> Path:
        """
        Download model with resume support and verification
        
        Args:
            model_key: Unique model identifier
            url: Download URL
            filename: Target filename
            expected_sha256: Optional SHA256 hash for verification
            progress_callback: Optional callback for progress updates
            force: Force re-download even if file exists
        
        Returns:
            Path to downloaded file
        
        Raises:
            RuntimeError: If download fails
        """
        if requests is None:
            raise RuntimeError("requests library not installed. Install with: pip install requests")
        
        target_path = self.download_dir / filename
        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        
        # Check if already downloaded and verified
        if target_path.exists() and not force:
            if expected_sha256:
                self.logger.info(f"Verifiziere existierende Datei: {filename}")
                if self._verify_file(target_path, expected_sha256):
                    self.logger.info(f"✅ Datei bereits vorhanden und verifiziert: {filename}")
                    return target_path
                self.logger.warning(f"⚠️ SHA256-Mismatch, lade neu herunter: {filename}")
            else:
                self.logger.info(f"✅ Datei bereits vorhanden: {filename}")
                return target_path
        
        # Initialize progress tracking
        progress = DownloadProgress(model_key=model_key, status="downloading")
        self.active_downloads[model_key] = progress
        self.cancel_flags[model_key] = threading.Event()
        
        # Get or create lock for this model
        if model_key not in self.download_locks:
            self.download_locks[model_key] = threading.Lock()
        
        with self.download_locks[model_key]:
            try:
                self._download_with_resume(
                    url=url,
                    target_path=temp_path,
                    progress=progress,
                    progress_callback=progress_callback,
                    cancel_event=self.cancel_flags[model_key]
                )
                
                # Verify if hash provided
                if expected_sha256:
                    progress.status = "verifying"
                    self._emit_progress(progress, progress_callback)
                    
                    self.logger.info(f"Verifiziere SHA256: {filename}")
                    if not self._verify_file(temp_path, expected_sha256):
                        raise RuntimeError(f"SHA256-Verifizierung fehlgeschlagen für {filename}")
                    
                    progress.sha256 = expected_sha256
                    self.logger.info(f"✅ SHA256 verifiziert: {filename}")
                
                # Move to final location
                temp_path.replace(target_path)
                
                progress.status = "completed"
                progress.downloaded_bytes = progress.total_bytes
                self._emit_progress(progress, progress_callback, force=True)
                
                self.logger.info(f"✅ Download abgeschlossen: {filename} ({self._format_bytes(progress.total_bytes)})")
                return target_path
                
            except DownloadCancelled as exc:
                progress.status = "cancelled"
                progress.error = str(exc)
                self._emit_progress(progress, progress_callback, force=True)
                with contextlib.suppress(Exception):
                    if temp_path.exists():
                        temp_path.unlink()
                raise RuntimeError(f"Download abgebrochen für {model_key}") from exc
            except Exception as exc:
                progress.status = "failed"
                progress.error = str(exc)
                self._emit_progress(progress, progress_callback, force=True)
                
                # Cleanup temp file
                with contextlib.suppress(Exception):
                    if temp_path.exists():
                        temp_path.unlink()
                
                raise RuntimeError(f"Download fehlgeschlagen für {model_key}: {exc}") from exc
            
            finally:
                # Cleanup
                self.active_downloads.pop(model_key, None)
                self.cancel_flags.pop(model_key, None)
    
    def _download_with_resume(
        self,
        url: str,
        target_path: Path,
        progress: DownloadProgress,
        progress_callback: Optional[Callable[[DownloadProgress], None]],
        cancel_event: threading.Event
    ) -> None:
        """Download with resume support (HTTP Range)"""
        # Check existing partial download
        existing_size = 0
        if target_path.exists():
            existing_size = target_path.stat().st_size
            progress.downloaded_bytes = existing_size
            self.logger.info(f"Setze Download fort ab Byte {existing_size}")
        
        # Prepare headers
        headers = {}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"
        
        if existing_size > 0:
            headers["Range"] = f"bytes={existing_size}-"
        
        # Start download with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    stream=True,
                    timeout=self.timeout
                )
                
                # Check if server supports resume
                if existing_size > 0 and response.status_code not in (200, 206):
                    self.logger.warning("Server unterstützt kein Resume, starte von vorn")
                    existing_size = 0
                    progress.downloaded_bytes = 0
                    headers.pop("Range", None)
                    response = requests.get(url, headers=headers, stream=True, timeout=self.timeout)
                
                response.raise_for_status()
                
                # Get total size
                content_length = response.headers.get("Content-Length")
                if content_length:
                    if response.status_code == 206:  # Partial content
                        progress.total_bytes = existing_size + int(content_length)
                    else:
                        progress.total_bytes = int(content_length)
                
                # Download chunks
                mode = "ab" if existing_size > 0 and response.status_code == 206 else "wb"
                last_update = time.time()
                start_time = time.time()
                
                with open(target_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if cancel_event.is_set():
                            progress.status = "cancelled"
                            self._emit_progress(progress, progress_callback, force=True)
                            raise DownloadCancelled("Download wurde abgebrochen")
                        if not chunk:
                            continue
                        
                        f.write(chunk)
                        progress.downloaded_bytes += len(chunk)
                        
                        # Update progress
                        now = time.time()
                        if now - last_update >= self.progress_update_interval:
                            elapsed = max(now - start_time, 0.001)
                            progress.speed_bytes_per_sec = (progress.downloaded_bytes - existing_size) / elapsed
                            
                            if progress.total_bytes > 0 and progress.speed_bytes_per_sec > 0:
                                remaining = progress.total_bytes - progress.downloaded_bytes
                                progress.eta_seconds = remaining / progress.speed_bytes_per_sec
                            
                            self._emit_progress(progress, progress_callback)
                            last_update = now
                
                # Success, break retry loop
                break
                
            except Exception as exc:
                self.logger.warning(f"Download-Versuch {attempt + 1}/{self.max_retries} fehlgeschlagen: {exc}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
    
    def _verify_file(self, file_path: Path, expected_sha256: str) -> bool:
        """Verify file SHA256 hash"""
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(self.chunk_size), b""):
                    sha256_hash.update(chunk)
            
            actual_hash = sha256_hash.hexdigest().lower()
            expected_hash = expected_sha256.lower()
            
            return actual_hash == expected_hash
            
        except Exception as exc:
            self.logger.error(f"SHA256-Verifizierung fehlgeschlagen: {exc}")
            return False
    
    def _emit_progress(
        self,
        progress: DownloadProgress,
        callback: Optional[Callable[[DownloadProgress], None]],
        force: bool = False
    ) -> None:
        """Emit progress update to callback"""
        if callback:
            try:
                callback(progress)
            except Exception as exc:
                self.logger.warning(f"Progress-Callback Fehler: {exc}")
    
    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def get_active_downloads(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all active downloads"""
        return {
            key: progress.to_dict()
            for key, progress in self.active_downloads.items()
        }
    
    def cancel_download(self, model_key: str) -> bool:
        """Cancel an active download"""
        if model_key in self.active_downloads:
            self.active_downloads[model_key].status = "cancelled"
            cancel_event = self.cancel_flags.get(model_key)
            if cancel_event:
                cancel_event.set()
            return True
        return False
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(self.chunk_size), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest().lower()
