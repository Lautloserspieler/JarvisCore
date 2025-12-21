""" 
TTS Service Module for JarvisCore
Handles text-to-speech synthesis with XTTS v2 and language support
"""

import logging
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from enum import Enum

try:
    from TTS.api import TTS
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False
    TTS = None

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages for TTS"""
    DE = "de"
    EN = "en"


class TTSService:
    """Text-to-Speech Service for JarvisCore"""

    def __init__(self, use_gpu: bool = True):
        """
        Initialize TTS Service
        
        Args:
            use_gpu: Use GPU acceleration if available
        """
        self.use_gpu = use_gpu and TORCH_AVAILABLE and torch.cuda.is_available() if TORCH_AVAILABLE else False
        self.tts_engine: Optional[TTS] = None
        self.pyttsx3_engine = None
        self.using_fallback = False
        self.device = "cuda" if self.use_gpu else "cpu"
        
        # Voice sample paths
        self.voice_samples = {
            Language.DE: Path("models/tts/voices/Jarvis_DE.wav"),
            Language.EN: Path("models/tts/voices/Jarvis_EN.wav"),
        }
        
        # Initialize
        self._initialize_engine()
    
    def _initialize_engine(self) -> None:
        """Initialize TTS engine"""
        if not XTTS_AVAILABLE:
            logger.warning("XTTS not available, will use pyttsx3 fallback")
            self._init_fallback()
            return
        
        try:
            logger.info("Initializing XTTS v2 engine...")
            # Note: verbose parameter removed in newer TTS versions
            self.tts_engine = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
            
            if self.use_gpu:
                self.tts_engine = self.tts_engine.to("cuda")
                logger.info(f"✅ XTTS initialized on {self.device} (GPU)")
            else:
                logger.info(f"✅ XTTS initialized on {self.device} (CPU)")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize XTTS: {e}")
            self._init_fallback()
    
    def _init_fallback(self) -> None:
        """Initialize pyttsx3 fallback"""
        if not PYTTSX3_AVAILABLE:
            logger.error("❌ pyttsx3 also unavailable - TTS will not work")
            return
        
        try:
            logger.warning("Initializing pyttsx3 fallback...")
            self.pyttsx3_engine = pyttsx3.init()
            self.using_fallback = True
            logger.info("✅ pyttsx3 fallback initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize pyttsx3: {e}")
    
    async def synthesize(
        self,
        text: str,
        language: Language = Language.DE,
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Synthesize text to speech
        
        Args:
            text: Text to synthesize
            language: Language (DE or EN)
            output_path: Output file path (temp if None)
            
        Returns:
            Path to audio file or None
        """
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return None
        
        text = text.strip()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._synthesize_sync,
            text,
            language,
            output_path
        )
    
    def _synthesize_sync(self, text: str, language: Language, output_path: Optional[Path]) -> Optional[Path]:
        """Synchronous synthesis (runs in thread pool)"""
        try:
            if self.using_fallback or not self.tts_engine:
                return self._synthesize_pyttsx3(text, output_path)
            else:
                return self._synthesize_xtts(text, language, output_path)
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return None
    
    def _synthesize_xtts(self, text: str, language: Language, output_path: Optional[Path]) -> Optional[Path]:
        """Synthesize using XTTS"""
        if not self.tts_engine:
            return None
        
        try:
            # Get voice sample path
            speaker_wav = self.voice_samples.get(language)
            if not speaker_wav or not speaker_wav.exists():
                logger.error(f"Voice sample not found: {speaker_wav}")
                return None
            
            # Generate temp file if needed
            if output_path is None:
                fd, output_path_str = tempfile.mkstemp(suffix=".wav", prefix="jarvis_tts_")
                os.close(fd)
                output_path = Path(output_path_str)
            
            logger.debug(f"Synthesizing with XTTS ({language.value}): '{text[:50]}...'")
            
            # Synthesize
            self.tts_engine.tts_to_file(
                text=text,
                speaker_wav=str(speaker_wav),
                language=language.value,
                file_path=str(output_path)
            )
            
            logger.info(f"✅ Audio synthesized: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"XTTS synthesis failed: {e}")
            if output_path and output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            return None
    
    def _synthesize_pyttsx3(self, text: str, output_path: Optional[Path]) -> Optional[Path]:
        """Synthesize using pyttsx3 fallback"""
        if not self.pyttsx3_engine:
            return None
        
        try:
            if output_path is None:
                fd, output_path_str = tempfile.mkstemp(suffix=".wav", prefix="jarvis_tts_")
                os.close(fd)
                output_path = Path(output_path_str)
            
            logger.debug(f"Synthesizing with pyttsx3: '{text[:50]}...'")
            self.pyttsx3_engine.save_to_file(text, str(output_path))
            self.pyttsx3_engine.runAndWait()
            
            logger.info(f"✅ Audio synthesized (pyttsx3): {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"pyttsx3 synthesis failed: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if TTS is available"""
        return self.tts_engine is not None or self.pyttsx3_engine is not None
    
    def get_status(self) -> Dict:
        """Get TTS service status"""
        return {
            "available": self.is_available(),
            "engine": "pyttsx3" if self.using_fallback else "xtts",
            "device": self.device,
            "gpu_enabled": self.use_gpu and not self.using_fallback,
            "languages": [lang.value for lang in Language]
        }


# Global instance
tts_service: Optional[TTSService] = None

def init_tts_service() -> TTSService:
    """Initialize and return TTS service"""
    global tts_service
    if tts_service is None:
        tts_service = TTSService(use_gpu=True)
    return tts_service

def get_tts_service() -> Optional[TTSService]:
    """Get TTS service instance"""
    return tts_service
