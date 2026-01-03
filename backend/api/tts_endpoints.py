"""
TTS API Endpoints for JarvisCore
Handles voice synthesis requests and settings management
"""

import logging
import re
from pathlib import Path

from fastapi import APIRouter, Body
from fastapi.responses import FileResponse

try:
    from backend.core.tts_service import Language, get_tts_service
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    get_tts_service = None
    Language = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tts", tags=["tts"])

# TTS Settings storage
tts_settings = {
    "enabled": True,
    "language": "de",
    "autoplay": False,
    "volume": 1.0,
    "speed": 1.0,
    "use_voice_samples": True,
}


def clean_text_for_tts(text: str) -> str:
    """
    Clean text for TTS by removing LLM tokens and control characters

    Args:
        text: Raw text from LLM

    Returns:
        Cleaned text suitable for TTS
    """
    # Trim overly long input before regex processing
    text = text[:5000]

    # Remove LLM special tokens
    text = re.sub(r'<\|[^|]*\|>', '', text)  # <|endoftext|>, <|im_start|>, etc.
    text = re.sub(r'</?s>', '', text)  # <s>, </s>
    text = re.sub(r'\[INST\]|\[/INST\]', '', text)  # Llama instruction tokens
    text = re.sub(r'<<SYS>>|<</SYS>>', '', text)  # System tokens

    # Remove markdown code blocks (they sound terrible)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)

    # Remove URLs (they sound terrible when spoken)
    text = re.sub(r'https?://\S+', 'Link', text)

    # Clean up excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


@router.post("/synthesize")
async def synthesize_speech(data: dict = Body(...)):
    """
    Synthesize text to speech

    Request body:
    {
        "text": "Hello world",
        "language": "de",  # Optional, defaults to settings
        "autoplay": false
    }
    """
    if not TTS_AVAILABLE or get_tts_service is None:
        return {"success": False, "message": "TTS service not available"}

    tts_service = get_tts_service()
    if not tts_service or not tts_service.is_available():
        return {"success": False, "message": "TTS engine not initialized"}

    text = data.get("text", "").strip()
    if not text:
        return {"success": False, "message": "Empty text provided"}

    # Clean text for TTS
    text = clean_text_for_tts(text)

    if not text:
        return {"success": False, "message": "Text became empty after cleaning"}

    # Get language from request or settings
    lang_str = data.get("language", tts_settings["language"])
    try:
        language = Language[lang_str.upper()]
    except (KeyError, AttributeError):
        language = Language.DE

    try:
        # Synthesize asynchronously
        audio_path = await tts_service.synthesize(text, language)

        if not audio_path or not audio_path.exists():
            logger.error("Audio synthesis failed for text length: %d", len(text))
            return {"success": False, "message": "Audio synthesis failed"}

        logger.info(f"Audio synthesized: {audio_path}")

        # Return audio file
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename=\"jarvis_{lang_str}.wav\""}
        )

    except Exception:
        logger.exception("Synthesis endpoint error")
        return {"success": False, "message": "Internal server error"}


@router.get("/status")
async def get_tts_status():
    """
    Get TTS service status
    """
    if not TTS_AVAILABLE or get_tts_service is None:
        return {
            "available": False,
            "message": "TTS module not available"
        }

    tts_service = get_tts_service()
    if not tts_service:
        return {
            "available": False,
            "message": "TTS service not initialized"
        }

    return tts_service.get_status()


@router.get("/voices")
async def get_available_voices():
    """
    List available voice samples
    """
    voices = [
        {
            "language": "de",
            "name": "Jarvis Deutsch",
            "description": "German JARVIS voice (v2.2 optimized)",
            "path": "models/tts/voices/Jarvis_DE.wav",
            "available": Path("models/tts/voices/Jarvis_DE.wav").exists()
        },
        {
            "language": "en",
            "name": "Jarvis English",
            "description": "English JARVIS voice (v2.2 optimized)",
            "path": "models/tts/voices/Jarvis_EN.wav",
            "available": Path("models/tts/voices/Jarvis_EN.wav").exists()
        }
    ]
    return {"voices": voices}


@router.get("/settings")
async def get_tts_settings():
    """
    Get TTS user settings
    """
    return tts_settings


@router.post("/settings")
async def save_tts_settings(data: dict = Body(...)):
    """
    Save TTS user settings

    Request body:
    {
        "enabled": true,
        "language": "de",
        "autoplay": false,
        "volume": 1.0,
        "speed": 1.0,
        "use_voice_samples": true
    }
    """
    global tts_settings

    # Update settings
    valid_keys = ["enabled", "language", "autoplay", "volume", "speed", "use_voice_samples"]
    for key in valid_keys:
        if key in data:
            tts_settings[key] = data[key]

    logger.info(f"TTS settings updated: {tts_settings}")

    return {
        "success": True,
        "message": "Settings saved",
        "settings": tts_settings
    }


@router.post("/test")
async def test_tts(data: dict = Body(...)):
    """
    Test TTS with a sample text

    Request body:
    {
        "language": "de"  # Optional
    }
    """
    if not TTS_AVAILABLE or get_tts_service is None:
        return {"success": False, "message": "TTS not available"}

    lang_str = data.get("language", "de")

    test_texts = {
        "de": "Dies ist ein Test der Sprachausgabe. Die Jarvis Stimme funktioniert gut.",
        "en": "This is a test of the voice synthesis. The Jarvis voice works great."
    }

    test_text = test_texts.get(lang_str, test_texts["de"])

    try:
        language = Language[lang_str.upper()]
    except (KeyError, AttributeError, NameError):
        language = Language.DE

    try:
        tts_service = get_tts_service()
        audio_path = await tts_service.synthesize(test_text, language)

        if audio_path and audio_path.exists():
            return FileResponse(
                audio_path,
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=\"test.wav\""}
            )
        else:
            return {"success": False, "message": "Test synthesis failed"}

    except Exception:
        logger.exception("Test TTS error")
        return {"success": False, "message": "Internal server error"}
