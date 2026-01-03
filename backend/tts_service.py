"""
TTS Service for JarvisCore

Provides text-to-speech functionality with:
- XTTS v2 neural TTS (primary)
- pyttsx3 fallback
- Multi-language support (DE/EN)
- Voice sample management
- Settings integration
"""
import logging
import re
import os
import tempfile
import wave
from pathlib import Path
from typing import Optional, Dict, Tuple
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from TTS.api import TTS
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False
    TTS = None
    print("[WARNING] TTS library not available. Install with: pip install TTS")

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
    torch = None

logger = logging.getLogger(__name__)


def _sanitize_for_log(value: str, max_len: int = 120) -> str:
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", value).strip()
    if len(cleaned) > max_len:
        return f"{cleaned[:max_len]}…"
    return cleaned


class TTSService:
    """
    Text-to-Speech Service with multi-language support.
    
    Features:
    - XTTS v2 neural TTS with voice cloning
    - Automatic language detection
    - Voice sample management (DE/EN)
    - GPU acceleration
    - pyttsx3 fallback
    - Settings integration
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize TTS Service.
        
        Args:
            config: Configuration dict with TTS settings
        """
        self.config = config or self._default_config()
        
        # Voice samples
        self.voice_samples = {
            'de': project_root / 'models' / 'tts' / 'voices' / 'Jarvis_DE.wav',
            'en': project_root / 'models' / 'tts' / 'voices' / 'Jarvis_EN.wav'
        }
        
        # Engine state
        self.tts_engine = None
        self.pyttsx3_engine = None
        self.using_fallback = False
        self.current_language = self.config.get('default_language', 'de')
        
        # Latent cache (for XTTS performance)
        self.latent_cache = {}
        
        # Initialize
        self._initialize()
    
    def _default_config(self) -> Dict:
        """Default TTS configuration."""
        return {
            'enabled': True,
            'backend': 'xtts',  # 'xtts' or 'pyttsx3'
            'default_language': 'de',
            'auto_language_detection': True,
            'use_gpu': True,
            'fallback_to_pyttsx3': True,
            'model_name': 'tts_models/multilingual/multi-dataset/xtts_v2',
            'temperature': 0.75,
            'speed': 1.0,
            'cache_latents': True
        }
    
    def _initialize(self) -> None:
        """Initialize TTS engine based on configuration."""
        if not self.config.get('enabled', True):
            logger.info("TTS disabled in config")
            return
        
        backend = self.config.get('backend', 'xtts')
        
        if backend == 'xtts' and XTTS_AVAILABLE:
            self._init_xtts()
        elif self.config.get('fallback_to_pyttsx3', True) and PYTTSX3_AVAILABLE:
            self._init_pyttsx3()
        else:
            logger.error("No TTS backend available")
    
    def _init_xtts(self) -> None:
        """Initialize XTTS v2 engine."""
        try:
            logger.info("Initializing XTTS v2...")
            model_name = self.config.get('model_name', 'tts_models/multilingual/multi-dataset/xtts_v2')
            
            self.tts_engine = TTS(model_name=model_name)
            
            # GPU acceleration
            if self.config.get('use_gpu', True) and TORCH_AVAILABLE and torch.cuda.is_available():
                self.tts_engine = self.tts_engine.to("cuda")
                logger.info("✅ XTTS using GPU acceleration")
            else:
                logger.info("⚠️ XTTS using CPU (slower)")
            
            logger.info("✅ XTTS v2 initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ XTTS initialization failed: {e}")
            
            # Fallback to pyttsx3
            if self.config.get('fallback_to_pyttsx3', True):
                self._init_pyttsx3()
            else:
                raise
    
    def _init_pyttsx3(self) -> None:
        """Initialize pyttsx3 fallback engine."""
        if not PYTTSX3_AVAILABLE:
            logger.error("pyttsx3 not available")
            return
        
        try:
            logger.warning("⚠️ Falling back to pyttsx3 (lower quality)")
            self.pyttsx3_engine = pyttsx3.init()
            self._configure_pyttsx3()
            self.using_fallback = True
            logger.info("✅ pyttsx3 fallback initialized")
            
        except Exception as e:
            logger.error(f"❌ pyttsx3 initialization failed: {e}")
            raise RuntimeError("No TTS engine available") from e
    
    def _configure_pyttsx3(self) -> None:
        """Configure pyttsx3 settings."""
        if not self.pyttsx3_engine:
            return
        
        try:
            # Get available voices
            voices = self.pyttsx3_engine.getProperty('voices')
            
            # Try to find language-appropriate voice
            target_lang = self.current_language
            selected_voice = None
            
            for voice in voices:
                # Check for German voice
                if target_lang == 'de' and ('german' in voice.name.lower() or 'de' in str(voice.languages).lower()):
                    selected_voice = voice
                    break
                # Check for English voice
                elif target_lang == 'en' and ('english' in voice.name.lower() or 'en' in str(voice.languages).lower()):
                    selected_voice = voice
                    break
            
            if selected_voice:
                self.pyttsx3_engine.setProperty('voice', selected_voice.id)
                logger.info(f"Selected voice: {selected_voice.name}")
            
            # Set speed and volume
            speed = int(175 * self.config.get('speed', 1.0))
            self.pyttsx3_engine.setProperty('rate', speed)
            self.pyttsx3_engine.setProperty('volume', 0.9)
            
        except Exception as e:
            logger.warning(f"Failed to configure pyttsx3: {e}")
    
    def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            language: Language code ('de' or 'en'). Auto-detected if None.
            output_path: Where to save audio. Temp file if None.
        
        Returns:
            Path to generated audio file or None on error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return None
        
        text = text.strip()
        
        # Auto-detect language if not provided
        if language is None and self.config.get('auto_language_detection', True):
            language = self._detect_language(text)
        elif language is None:
            language = self.current_language
        
        # Validate language
        if language not in ['de', 'en']:
            logger.warning(f"Unsupported language '{language}', using '{self.current_language}'")
            language = self.current_language
        
        # Update current language
        self.current_language = language
        
        # Generate audio
        if self.using_fallback:
            return self._synthesize_pyttsx3(text, output_path)
        else:
            return self._synthesize_xtts(text, language, output_path)
    
    def _synthesize_xtts(
        self,
        text: str,
        language: str,
        output_path: Optional[Path]
    ) -> Optional[Path]:
        """Synthesize using XTTS v2."""
        if not self.tts_engine:
            logger.error("XTTS engine not initialized")
            return None
        
        # Get voice sample for language
        speaker_wav = self.voice_samples.get(language)
        if not speaker_wav or not speaker_wav.exists():
            logger.error(f"Voice sample not found for language '{language}': {speaker_wav}")
            return None
        
        # Create temp file if no output path
        if output_path is None:
            fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="jarvis_tts_")
            os.close(fd)
            output_path = Path(temp_path)
        
        try:
            logger.info("🎙️ Synthesizing (%s): '%s...'", language.upper(), _sanitize_for_log(text, 50))
            
            # Synthesize with voice cloning
            self.tts_engine.tts_to_file(
                text=text,
                file_path=str(output_path),
                speaker_wav=str(speaker_wav),
                language=language,
                temperature=self.config.get('temperature', 0.75)
            )
            
            logger.info(f"✅ Audio synthesized: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ XTTS synthesis failed: {e}")
            if output_path and output_path.exists():
                output_path.unlink()
            return None
    
    def _synthesize_pyttsx3(
        self,
        text: str,
        output_path: Optional[Path]
    ) -> Optional[Path]:
        """Synthesize using pyttsx3 fallback."""
        if not self.pyttsx3_engine:
            logger.error("pyttsx3 engine not initialized")
            return None
        
        try:
            if output_path:
                # Save to file
                logger.info(f"🔊 Synthesizing (pyttsx3): {output_path}")
                self.pyttsx3_engine.save_to_file(text, str(output_path))
                self.pyttsx3_engine.runAndWait()
                return output_path
            else:
                # Direct playback
                logger.info("🔊 Speaking (pyttsx3): '%s...'", _sanitize_for_log(text, 50))
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
                return None
                
        except Exception as e:
            logger.error(f"❌ pyttsx3 synthesis failed: {e}")
            return None
    
    def _detect_language(self, text: str) -> str:
        """
        Auto-detect text language.
        
        Simple heuristic based on common words.
        For production, use langdetect library.
        """
        # German indicators
        german_words = {
            'der', 'die', 'das', 'und', 'ist', 'ein', 'eine', 'nicht', 
            'ich', 'sie', 'mit', 'auf', 'werden', 'können', 'haben'
        }
        
        # English indicators
        english_words = {
            'the', 'and', 'is', 'are', 'a', 'an', 'not', 'i', 'you', 
            'with', 'on', 'can', 'have', 'will', 'that'
        }
        
        words = set(text.lower().split())
        
        german_score = len(words & german_words)
        english_score = len(words & english_words)
        
        if german_score > english_score:
            return 'de'
        elif english_score > german_score:
            return 'en'
        else:
            # Default to current language
            return self.current_language
    
    def get_status(self) -> Dict:
        """Get TTS service status."""
        return {
            'enabled': self.config.get('enabled', True),
            'available': self.is_available(),
            'engine': 'pyttsx3' if self.using_fallback else 'xtts',
            'backend': self.config.get('backend', 'xtts'),
            'current_language': self.current_language,
            'supported_languages': ['de', 'en'],
            'gpu_enabled': (
                self.config.get('use_gpu', True) and 
                not self.using_fallback and 
                TORCH_AVAILABLE and 
                torch.cuda.is_available()
            ),
            'voice_samples': {
                lang: str(path) if path.exists() else 'missing'
                for lang, path in self.voice_samples.items()
            }
        }
    
    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self.tts_engine is not None or self.pyttsx3_engine is not None
    
    def update_config(self, new_config: Dict) -> bool:
        """
        Update TTS configuration.
        
        Args:
            new_config: New configuration dict
        
        Returns:
            True if update successful
        """
        try:
            self.config.update(new_config)
            
            # Reinitialize if backend changed
            if 'backend' in new_config or 'use_gpu' in new_config:
                self._initialize()
            
            # Update pyttsx3 if using fallback
            if self.using_fallback and self.pyttsx3_engine:
                self._configure_pyttsx3()
            
            logger.info("TTS config updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update TTS config: {e}")
            return False


# Global TTS service instance
_tts_service: Optional[TTSService] = None


def get_tts_service(config: Optional[Dict] = None) -> TTSService:
    """Get or create global TTS service instance."""
    global _tts_service
    
    if _tts_service is None:
        _tts_service = TTSService(config)
    elif config:
        _tts_service.update_config(config)
    
    return _tts_service


__all__ = ['TTSService', 'get_tts_service']
