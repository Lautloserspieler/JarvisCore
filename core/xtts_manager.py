import os
import threading
import functools
import warnings
import importlib
import inspect
import torch
from pathlib import Path

# Torch compatibility patch: ensure weight_norm is exposed in parametrizations namespace
try:
    param_mod = importlib.import_module("torch.nn.utils.parametrizations")
    utils_mod = importlib.import_module("torch.nn.utils")
    if not hasattr(param_mod, "weight_norm") and hasattr(utils_mod, "weight_norm"):
        setattr(param_mod, "weight_norm", utils_mod.weight_norm)
    pytree_mod = importlib.import_module("torch.utils._pytree")
    base_register = getattr(pytree_mod, "_register_pytree_node", None)
    if not hasattr(pytree_mod, "register_pytree_node") or base_register is not None:
        if base_register is None:
            base_register = getattr(utils_mod, "register_pytree_node", None)
        if base_register is None:
            def _noop_register(*_args, **_kwargs):
                warnings.warn("register_pytree_node fallback used; XTTS compatibility mode active.")
            compat_register = _noop_register
        else:
            def compat_register(typ, flatten_fn, unflatten_fn, **kwargs):
                allowed_keys = {"to_dumpable_context", "from_dumpable_context"}
                filtered = {k: v for k, v in kwargs.items() if k in allowed_keys}
                return base_register(typ, flatten_fn, unflatten_fn, **filtered)
        setattr(pytree_mod, "register_pytree_node", compat_register)

except Exception:
    pass

try:
    from TTS.api import TTS as CoquiTTS  # type: ignore
    from TTS.tts.configs.xtts_config import XttsConfig  # type: ignore
except Exception:
    CoquiTTS = None  # type: ignore
    XttsConfig = None  # type: ignore

def _torch_add_safe_globals(items):
    add_fn = getattr(torch.serialization, "add_safe_globals", None)
    if callable(add_fn):
        try:
            add_fn(items)
        except Exception:
            pass

class XTTSManager:
    """
    Manager for XTTS v2 text-to-speech functionality.
    Handles TTS synthesis and audio playback.
    """
    
    def __init__(self, config=None, settings=None):
        """
        Initialize the XTTS manager.
        
        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
            settings (Settings, optional): Settings object. Defaults to None.
        """
        self.logger = None  # Will be set by main application
        self.config = config or {}
        self.settings = settings
        self.voice_dir = Path(self.config.get('voice_dir', 'models/tts/voices'))
        self.output_dir = Path(self.config.get('output_dir', 'output'))
        self.voice_file = self.voice_dir / self.config.get('voice_file', 'Jarvis.wav')
        self.language = self.config.get('language', 'de')
        
        # GPU-Nutzung basierend auf Einstellungen steuern
        if self.settings and 'speech' in self.settings.settings and 'tts_use_gpu' in self.settings.settings['speech']:
            self.use_gpu = self.settings.settings['speech']['tts_use_gpu'] and torch.cuda.is_available()
        else:
            self.use_gpu = self.config.get('use_gpu', False) and torch.cuda.is_available()
            
        self.commercial = self.config.get('commercial', False)
        self.tts = None
        
        # Create necessary directories
        self.voice_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize the XTTS model."""
        if CoquiTTS is None or XttsConfig is None:
            if self.logger:
                self.logger.error("Coqui TTS library not available. Install coqui-tts to enable XTTS.")
            self.tts = None
            return

        try:
            # Suppress UserWarnings
            warnings.filterwarnings("ignore", category=UserWarning)

            # Coqui TOS / License
            os.environ["COQUI_TOS_AGREED"] = "1"
            os.environ["COQUI_COMMERCIAL_LICENSE"] = "1" if self.commercial else "0"

            # PyTorch 2.6+ Safe-Globals for XTTS
            _torch_add_safe_globals([XttsConfig])

            # Add safe globals for XTTS classes
            xtts_mod = importlib.import_module("TTS.tts.models.xtts")
            safe_classes = [obj for _, obj in xtts_mod.__dict__.items() if inspect.isclass(obj)]
            _torch_add_safe_globals(safe_classes)

            # Initialize TTS
            self.tts = CoquiTTS(
                model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                gpu=self.use_gpu,
            )

            if self.logger:
                self.logger.info(f"XTTS v2 initialized (GPU: {'enabled' if self.use_gpu else 'disabled'})")

        except Exception as e:
            if "Weights only load failed" in str(e) and CoquiTTS is not None:
                # Fallback for weights loading issue
                torch.load = functools.partial(torch.load, weights_only=False)
                self.tts = CoquiTTS(
                    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                    gpu=self.use_gpu,
                )
                if self.logger:
                    self.logger.warning("XTTS weights-only load failed; retried with full weight loading.")
            else:
                self.tts = None
                if self.logger:
                    self.logger.error(f"Failed to initialize XTTS: {str(e)}")
    
    def synthesize(self, text, output_file=None, async_play=True):
        """
        Convert text to speech and optionally play it.
        
        Args:
            text (str): Text to convert to speech
            output_file (str, optional): Output file path. Defaults to None.
            async_play (bool, optional): Whether to play asynchronously. Defaults to True.
            
        Returns:
            str: Path to the generated audio file
        """
        if not text or not self.tts:
            return None
            
        if not output_file:
            output_file = self.output_dir / "jarvis_output.wav"
        else:
            output_file = Path(output_file)
            
        try:
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate speech
            self.tts.tts_to_file(
                text=text,
                speaker_wav=str(self.voice_file),
                language=self.language,
                file_path=str(output_file)
            )
            
            # Play the audio
            self._play_audio(output_file, async_play)
            
            return str(output_file)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in speech synthesis: {str(e)}")
            return None
    
    def _play_audio(self, audio_path, async_play=True):
        """
        Play audio file using platform-specific methods.
        
        Args:
            audio_path (str): Path to the audio file
            async_play (bool): Whether to play asynchronously
        """
        try:
            if os.name == 'nt':  # Windows
                import winsound

                def _play_sync():
                    try:
                        # Stop any pending playback handles before starting a new one
                        winsound.PlaySound(None, 0)
                    except RuntimeError:
                        # Ignore if there was nothing to stop
                        pass
                    flags = winsound.SND_FILENAME | winsound.SND_NODEFAULT
                    if async_play:
                        flags |= winsound.SND_ASYNC
                    winsound.PlaySound(str(audio_path), flags)
                    if not async_play:
                        # Ensure handle is released after synchronous playback
                        winsound.PlaySound(None, 0)

                if async_play:
                    threading.Thread(target=_play_sync, daemon=True).start()
                else:
                    _play_sync()
            else:  # Linux/macOS
                import subprocess
                cmd = ['aplay', str(audio_path)] if os.uname().sysname == 'Linux' else ['afplay', str(audio_path)]
                if async_play:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run(cmd, check=True)
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error playing audio: {str(e)}")
    
    def set_voice(self, voice_file):
        """
        Set the voice file to use for synthesis.
        
        Args:
            voice_file (str): Path to the voice file
        """
        voice_file = Path(voice_file)
        if voice_file.exists():
            self.voice_file = voice_file
            if self.logger:
                self.logger.info(f"Voice set to: {voice_file}")
            return True
        return False
    
    def set_language(self, language):
        """
        Set the language for TTS synthesis.
        
        Args:
            language (str): Language code (e.g., 'de', 'en')
        """
        self.language = language
        if self.logger:
            self.logger.info(f"Language set to: {language}")
    
    def speak(self, text, async_play=True):
        """
        Speak the given text (compatibility method for existing code).
        
        Args:
            text (str): Text to speak
            async_play (bool): Whether to play asynchronously
            
        Returns:
            str: Path to the generated audio file
        """
        return self.synthesize(text, async_play=async_play)

# For testing
if __name__ == "__main__":
    tts = XTTSManager()
    tts.synthesize("Hallo, ich bin Jarvis. Wie kann ich Ihnen helfen?")
    import time
    time.sleep(5)  # Keep the program running to hear the audio
