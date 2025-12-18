"""Model Downloader with Progress Bar for HuggingFace Models"""
import os
import requests
from pathlib import Path
from typing import Optional, Dict
from tqdm import tqdm
import hashlib

# Model Download URLs (HuggingFace)
MODEL_URLS = {
    "mistral": {
        "url": "https://huggingface.co/second-state/Mistral-Nemo-Instruct-2407-GGUF/resolve/main/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "filename": "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "size_gb": 7.5,
        "requires_token": False
    },
    "qwen": {
        "url": "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "filename": "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "size_gb": 4.8,
        "requires_token": False  # bartowski quantizations are public
    },
    "deepseek": {
        "url": "https://huggingface.co/Triangle104/DeepSeek-R1-Distill-Llama-8B-Q4_K_M-GGUF/resolve/main/deepseek-r1-distill-llama-8b-q4_k_m.gguf",
        "filename": "deepseek-r1-distill-llama-8b-q4_k_m.gguf",
        "size_gb": 6.9,
        "requires_token": False
    },
    "llama32-3b": {
        "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size_gb": 2.0,
        "requires_token": False  # bartowski quantizations are public
    },
    "phi3-mini": {
        "url": "https://huggingface.co/bartowski/Phi-3.1-mini-128k-instruct-GGUF/resolve/main/Phi-3.1-mini-128k-instruct-Q4_K_M.gguf",
        "filename": "Phi-3.1-mini-128k-instruct-Q4_K_M.gguf",
        "size_gb": 2.4,
        "requires_token": False  # bartowski quantizations are public
    },
    "gemma2-9b": {
        "url": "https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-Q4_K_M.gguf",
        "filename": "gemma-2-9b-it-Q4_K_M.gguf",
        "size_gb": 5.4,
        "requires_token": False  # bartowski quantizations are public
    },
    "llama33-70b": {
        "url": "https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF/resolve/main/Llama-3.3-70B-Instruct-Q4_K_M.gguf",
        "filename": "Llama-3.3-70B-Instruct-Q4_K_M.gguf",
        "size_gb": 40.0,
        "requires_token": False  # bartowski quantizations are public
    }
}

class ModelDownloader:
    """Downloads models from HuggingFace with progress tracking"""
    
    def __init__(self, models_dir: str = "models/llm"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Download state
        self.current_download: Optional[str] = None
        self.download_progress: float = 0.0
        self.is_downloading: bool = False
    
    def get_model_path(self, model_id: str) -> Optional[Path]:
        """Get path for a model file"""
        if model_id not in MODEL_URLS:
            return None
        return self.models_dir / MODEL_URLS[model_id]["filename"]
    
    def is_model_downloaded(self, model_id: str) -> bool:
        """Check if model is already downloaded"""
        model_path = self.get_model_path(model_id)
        if not model_path:
            return False
        return model_path.exists() and model_path.stat().st_size > 1024  # > 1KB
    
    def requires_token(self, model_id: str) -> bool:
        """Check if model requires HuggingFace token"""
        if model_id not in MODEL_URLS:
            return False
        return MODEL_URLS[model_id].get("requires_token", False)
    
    def get_download_status(self) -> Dict:
        """Get current download status"""
        return {
            "is_downloading": self.is_downloading,
            "current_model": self.current_download,
            "progress": self.download_progress
        }
    
    def download_model(self, model_id: str, hf_token: Optional[str] = None, progress_callback=None) -> Dict:
        """
        Download a model from HuggingFace
        
        Args:
            model_id: Model identifier (e.g. 'mistral', 'qwen')
            hf_token: Optional HuggingFace token for gated models
            progress_callback: Optional callback(progress_percent: float, status: str)
        
        Returns:
            Dict with success, message, and file_path
        """
        if model_id not in MODEL_URLS:
            return {
                "success": False,
                "message": f"Unknown model: {model_id}",
                "file_path": None
            }
        
        model_info = MODEL_URLS[model_id]
        url = model_info["url"]
        filename = model_info["filename"]
        output_path = self.models_dir / filename
        requires_token = model_info.get("requires_token", False)
        
        # Check if token is needed but not provided
        if requires_token and not hf_token:
            # Try to get from environment
            hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
            
            if not hf_token:
                return {
                    "success": False,
                    "message": "This model requires a HuggingFace token. Please provide one.",
                    "file_path": None,
                    "requires_token": True
                }
        
        # Check if already downloaded
        if self.is_model_downloaded(model_id):
            return {
                "success": True,
                "message": f"Model {model_id} already downloaded",
                "file_path": str(output_path)
            }
        
        try:
            self.is_downloading = True
            self.current_download = model_id
            self.download_progress = 0.0
            
            if progress_callback:
                progress_callback(0.0, "Starting download...")
            
            # Prepare headers with token if provided
            headers = {}
            if hf_token:
                headers["Authorization"] = f"Bearer {hf_token}"
            
            # Stream download with progress
            print(f"[INFO] Downloading {model_id} from {url}")
            response = requests.get(url, stream=True, headers=headers)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192  # 8KB chunks
            
            # Download with progress bar
            with open(output_path, 'wb') as f:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=f"Downloading {filename}"
                ) as pbar:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=block_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pbar.update(len(chunk))
                            
                            # Update progress
                            if total_size > 0:
                                self.download_progress = (downloaded / total_size) * 100
                                
                                if progress_callback:
                                    progress_callback(
                                        self.download_progress,
                                        f"Downloading... {self.download_progress:.1f}%"
                                    )
            
            self.is_downloading = False
            self.current_download = None
            self.download_progress = 100.0
            
            if progress_callback:
                progress_callback(100.0, "Download complete!")
            
            print(f"[INFO] Download complete: {output_path}")
            print(f"[INFO] File size: {output_path.stat().st_size / (1024**3):.2f} GB")
            
            return {
                "success": True,
                "message": f"Model {model_id} downloaded successfully",
                "file_path": str(output_path)
            }
            
        except requests.exceptions.HTTPError as e:
            self.is_downloading = False
            self.current_download = None
            
            # Check if 401/403 (authentication error)
            if e.response.status_code in [401, 403]:
                error_msg = "Authentication required. Please provide a valid HuggingFace token."
                print(f"[ERROR] {error_msg}")
                
                if output_path.exists():
                    output_path.unlink()
                
                if progress_callback:
                    progress_callback(0.0, error_msg)
                
                return {
                    "success": False,
                    "message": error_msg,
                    "file_path": None,
                    "requires_token": True
                }
            
            error_msg = f"Download error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            
            if output_path.exists():
                output_path.unlink()
            
            if progress_callback:
                progress_callback(0.0, f"Error: {str(e)}")
            
            return {
                "success": False,
                "message": error_msg,
                "file_path": None
            }
        
        except requests.exceptions.RequestException as e:
            self.is_downloading = False
            self.current_download = None
            error_msg = f"Download error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            
            # Clean up partial download
            if output_path.exists():
                output_path.unlink()
            
            if progress_callback:
                progress_callback(0.0, f"Error: {str(e)}")
            
            return {
                "success": False,
                "message": error_msg,
                "file_path": None
            }
        
        except Exception as e:
            self.is_downloading = False
            self.current_download = None
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            
            if progress_callback:
                progress_callback(0.0, f"Error: {str(e)}")
            
            return {
                "success": False,
                "message": error_msg,
                "file_path": None
            }

# Global downloader instance
model_downloader = ModelDownloader()

if __name__ == "__main__":
    # Test download
    print("Model Downloader Test")
    print("Available models:", list(MODEL_URLS.keys()))
    
    # Test with smallest model
    result = model_downloader.download_model("llama32-3b")
    print(f"\nResult: {result}")
