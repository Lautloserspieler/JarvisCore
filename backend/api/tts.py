"""
TTS API Endpoints for JarvisCore

Provides REST API for text-to-speech functionality:
- Speech synthesis with language selection
- Configuration management
- Status monitoring
- Language support
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse
from typing import Optional, Dict
from pathlib import Path
import logging

try:
    from backend.tts_service import get_tts_service
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    get_tts_service = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.post("/synthesize")
async def synthesize_speech(data: dict = Body(...)):
    """
    Synthesize speech from text.
    
    Request body:
    {
        "text": "Text to synthesize",
        "language": "de" | "en" (optional, auto-detected if omitted),
        "return_file": true | false (optional, default true)
    }
    
    Returns:
        Audio file (WAV) or error message
    """
    if not TTS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="TTS service not available. Install with: pip install TTS"
        )
    
    text = data.get("text", "").strip()
    language = data.get("language")  # None = auto-detect
    return_file = data.get("return_file", True)
    
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Get TTS service
    try:
        tts = get_tts_service()
        
        if not tts.is_available():
            raise HTTPException(
                status_code=503,
                detail="TTS engine not initialized"
            )
        
        # Synthesize
        audio_path = tts.synthesize(text=text, language=language)
        
        if not audio_path or not audio_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Failed to generate audio"
            )
        
        # Return file response
        if return_file:
            return FileResponse(
                path=audio_path,
                media_type="audio/wav",
                filename=f"jarvis_tts_{language or 'auto'}.wav",
                headers={
                    "X-Language": language or tts.current_language,
                    "X-Engine": "xtts" if not tts.using_fallback else "pyttsx3"
                }
            )
        else:
            return {
                "success": True,
                "audio_path": str(audio_path),
                "language": language or tts.current_language,
                "engine": "xtts" if not tts.using_fallback else "pyttsx3"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_tts_status():
    """
    Get TTS service status.
    
    Returns:
    {
        "enabled": bool,
        "available": bool,
        "engine": "xtts" | "pyttsx3",
        "current_language": "de" | "en",
        "supported_languages": ["de", "en"],
        "gpu_enabled": bool,
        "voice_samples": {...}
    }
    """
    if not TTS_AVAILABLE:
        return {
            "enabled": False,
            "available": False,
            "error": "TTS library not installed"
        }
    
    try:
        tts = get_tts_service()
        return tts.get_status()
    except Exception as e:
        logger.error(f"Failed to get TTS status: {e}")
        return {
            "enabled": False,
            "available": False,
            "error": str(e)
        }


@router.post("/config")
async def update_tts_config(config: dict = Body(...)):
    """
    Update TTS configuration.
    
    Request body:
    {
        "enabled": bool,
        "backend": "xtts" | "pyttsx3",
        "default_language": "de" | "en",
        "auto_language_detection": bool,
        "use_gpu": bool,
        "temperature": float (0.0-1.0),
        "speed": float (0.5-2.0)
    }
    
    Returns:
        Success status and updated configuration
    """
    if not TTS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="TTS service not available"
        )
    
    try:
        tts = get_tts_service()
        success = tts.update_config(config)
        
        if success:
            return {
                "success": True,
                "message": "TTS configuration updated",
                "config": tts.config
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update configuration"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update TTS config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages.
    
    Returns:
    {
        "languages": [
            {
                "code": "de",
                "name": "Deutsch",
                "voice_available": bool
            },
            ...
        ]
    }
    """
    languages = [
        {
            "code": "de",
            "name": "Deutsch",
            "native_name": "Deutsch",
            "voice_sample": "Jarvis_DE.wav"
        },
        {
            "code": "en",
            "name": "English",
            "native_name": "English",
            "voice_sample": "Jarvis_EN.wav"
        }
    ]
    
    # Check if voice samples exist
    if TTS_AVAILABLE:
        try:
            tts = get_tts_service()
            status = tts.get_status()
            voice_samples = status.get('voice_samples', {})
            
            for lang in languages:
                code = lang['code']
                lang['voice_available'] = voice_samples.get(code) != 'missing'
        except Exception as e:
            logger.warning(f"Could not check voice samples: {e}")
    
    return {
        "languages": languages,
        "default": "de"
    }


@router.get("/voices")
async def get_available_voices():
    """
    Get list of available voice samples.
    
    Returns:
        List of voice samples with metadata
    """
    if not TTS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="TTS service not available"
        )
    
    try:
        tts = get_tts_service()
        status = tts.get_status()
        
        voices = []
        for lang, path_str in status.get('voice_samples', {}).items():
            voice_path = Path(path_str) if path_str != 'missing' else None
            
            voices.append({
                "language": lang,
                "name": f"JARVIS {lang.upper()}",
                "path": path_str,
                "available": voice_path and voice_path.exists() if voice_path else False,
                "version": "v2.2"
            })
        
        return {
            "voices": voices,
            "engine": status.get('engine', 'unknown')
        }
    
    except Exception as e:
        logger.error(f"Failed to get voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']
