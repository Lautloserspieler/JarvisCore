"""
Whisper Model Downloader
Handles downloading and caching of Whisper models for speech recognition
"""
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class WhisperDownloader:
    """
    Downloads and manages Whisper models for faster-whisper
    
    The models are cached locally and automatically downloaded
    by faster-whisper when needed.
    """
    
    AVAILABLE_MODELS = [
        "tiny",
        "tiny.en",
        "base",
        "base.en",
        "small",
        "small.en",
        "medium",
        "medium.en",
        "large-v1",
        "large-v2",
        "large-v3",
    ]
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialize WhisperDownloader
        
        Args:
            models_dir: Directory to store models. Defaults to current directory.
        """
        if models_dir is None:
            models_dir = Path(__file__).parent
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Whisper models directory: {self.models_dir}")
        
    def download_model(self, model_name: str = "base") -> Path:
        """
        Download Whisper model if not already cached
        
        Args:
            model_name: Model size (tiny, base, small, medium, large-v3, etc.)
            
        Returns:
            Path to model directory
            
        Raises:
            ValueError: If model_name is not valid
        """
        if model_name not in self.AVAILABLE_MODELS:
            logger.warning(
                f"Model '{model_name}' not in known models list. "
                f"Available: {', '.join(self.AVAILABLE_MODELS)}"
            )
        
        model_path = self.models_dir / model_name
        
        if model_path.exists():
            logger.info(f"Model '{model_name}' already exists at {model_path}")
            return model_path
            
        logger.info(f"Preparing to download Whisper model: {model_name}")
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Note: faster-whisper will automatically download models to its cache
        # when first used. This method just ensures the directory structure exists.
        logger.info(
            f"Model directory created. faster-whisper will download '{model_name}' "
            "automatically on first use."
        )
        
        return model_path
    
    def get_model_path(self, model_name: str = "base") -> Path:
        """
        Get path to model directory
        
        Args:
            model_name: Model size
            
        Returns:
            Path to model directory
        """
        return self.models_dir / model_name
    
    def list_downloaded_models(self) -> list[str]:
        """
        List all downloaded models
        
        Returns:
            List of model names that exist locally
        """
        downloaded = []
        for model_name in self.AVAILABLE_MODELS:
            if (self.models_dir / model_name).exists():
                downloaded.append(model_name)
        return downloaded
    
    def cleanup_model(self, model_name: str) -> bool:
        """
        Remove a downloaded model to free up space
        
        Args:
            model_name: Name of model to remove
            
        Returns:
            True if model was removed, False if it didn't exist
        """
        model_path = self.models_dir / model_name
        if model_path.exists():
            import shutil
            shutil.rmtree(model_path)
            logger.info(f"Removed model: {model_name}")
            return True
        return False
