#!/usr/bin/env python3
"""
Beispiel-Endpoint für STT (Speech-to-Text) in JarvisCore

Dieser Endpoint empfängt Audio-Dateien und gibt Transkription zurück.

Usage:
    In core/api/routes.py einbinden:
    
    @routes.post('/api/stt')
    async def stt_endpoint(request):
        return await handle_stt_request(request)
"""

import io
import wave
import json
from pathlib import Path
from aiohttp import web


async def handle_stt_request(request):
    """
    Verarbeitet STT-Request von Desktop UI
    
    Request:
        POST /api/stt
        Content-Type: multipart/form-data
        Body: audio=[WAV file]
    
    Response:
        {
            "text": "Transkribierter Text",
            "confidence": 0.95,
            "language": "de"
        }
    """
    try:
        # Multipart-Daten lesen
        reader = await request.multipart()
        
        audio_data = None
        filename = None
        
        async for field in reader:
            if field.name == 'audio':
                filename = field.filename
                audio_data = await field.read()
                break
        
        if not audio_data:
            return web.json_response(
                {'error': 'Keine Audio-Daten empfangen'},
                status=400
            )
        
        # Audio-Validierung
        if len(audio_data) > 10 * 1024 * 1024:  # Max 10MB
            return web.json_response(
                {'error': 'Audio-Datei zu groß (max 10MB)'},
                status=413
            )
        
        # WAV-Validierung
        try:
            audio_io = io.BytesIO(audio_data)
            with wave.open(audio_io, 'rb') as wav:
                # Check Format
                channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                framerate = wav.getframerate()
                
                print(f"🎤 Audio empfangen: {channels}ch, {framerate}Hz, {sample_width*8}bit")
        except Exception as e:
            return web.json_response(
                {'error': f'Ungültiges Audio-Format: {str(e)}'},
                status=400
            )
        
        # STT-Engine aufrufen (VOSK / Whisper / Faster-Whisper)
        transcription = await transcribe_audio(audio_data)
        
        return web.json_response({
            'text': transcription['text'],
            'confidence': transcription.get('confidence', 0.0),
            'language': transcription.get('language', 'de')
        })
        
    except Exception as e:
        print(f"❌ STT Error: {e}")
        return web.json_response(
            {'error': f'Transkription fehlgeschlagen: {str(e)}'},
            status=500
        )


async def transcribe_audio(audio_data: bytes) -> dict:
    """
    Transkribiert Audio mit VOSK/Whisper
    
    Returns:
        {
            "text": "Transkription",
            "confidence": 0.95,
            "language": "de"
        }
    """
    # OPTION 1: VOSK
    if USE_VOSK:
        return await transcribe_with_vosk(audio_data)
    
    # OPTION 2: Whisper
    elif USE_WHISPER:
        return await transcribe_with_whisper(audio_data)
    
    # OPTION 3: Faster-Whisper
    elif USE_FASTER_WHISPER:
        return await transcribe_with_faster_whisper(audio_data)
    
    # Fallback
    return {
        'text': '[STT nicht konfiguriert]',
        'confidence': 0.0,
        'language': 'de'
    }


# ===== VOSK =====

USE_VOSK = False

try:
    from vosk import Model, KaldiRecognizer
    import wave
    import io
    
    # Modell laden (einmal beim Start)
    VOSK_MODEL_PATH = "models/vosk-model-de-0.21"
    VOSK_MODEL = Model(VOSK_MODEL_PATH)
    USE_VOSK = True
    print("✅ VOSK STT aktiviert")
except:
    pass


async def transcribe_with_vosk(audio_data: bytes) -> dict:
    """
    Transkription mit VOSK
    """
    audio_io = io.BytesIO(audio_data)
    
    with wave.open(audio_io, 'rb') as wf:
        recognizer = KaldiRecognizer(VOSK_MODEL, wf.getframerate())
        recognizer.SetWords(True)
        
        result_text = ""
        
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                result_text += result.get('text', '') + ' '
        
        # Finales Ergebnis
        final_result = json.loads(recognizer.FinalResult())
        result_text += final_result.get('text', '')
    
    return {
        'text': result_text.strip(),
        'confidence': 0.9,  # VOSK gibt keine Confidence
        'language': 'de'
    }


# ===== Whisper =====

USE_WHISPER = False

try:
    import whisper
    import tempfile
    
    # Modell laden (einmal beim Start)
    WHISPER_MODEL = whisper.load_model("base")  # tiny, base, small, medium, large
    USE_WHISPER = True
    print("✅ Whisper STT aktiviert")
except:
    pass


async def transcribe_with_whisper(audio_data: bytes) -> dict:
    """
    Transkription mit Whisper
    """
    # Temp-Datei erstellen
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name
    
    try:
        # Transkribieren
        result = WHISPER_MODEL.transcribe(
            tmp_path,
            language='de',
            fp16=False  # CPU-Kompatibilität
        )
        
        return {
            'text': result['text'].strip(),
            'confidence': 0.95,
            'language': result.get('language', 'de')
        }
    finally:
        # Temp-Datei löschen
        Path(tmp_path).unlink(missing_ok=True)


# ===== Faster-Whisper =====

USE_FASTER_WHISPER = False

try:
    from faster_whisper import WhisperModel
    
    # Modell laden
    FASTER_WHISPER_MODEL = WhisperModel(
        "base",  # tiny, base, small, medium, large
        device="cpu",  # oder "cuda"
        compute_type="int8"  # int8, int16, float16, float32
    )
    USE_FASTER_WHISPER = True
    print("✅ Faster-Whisper STT aktiviert")
except:
    pass


async def transcribe_with_faster_whisper(audio_data: bytes) -> dict:
    """
    Transkription mit Faster-Whisper
    """
    # Temp-Datei erstellen
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name
    
    try:
        segments, info = FASTER_WHISPER_MODEL.transcribe(
            tmp_path,
            language='de',
            beam_size=5
        )
        
        # Segmente zusammenfügen
        text = ' '.join([segment.text for segment in segments])
        
        return {
            'text': text.strip(),
            'confidence': 0.95,
            'language': info.language
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ===== Integration in JarvisCore =====

"""
In core/api/routes.py:

from docs.examples.stt_endpoint import handle_stt_request

@routes.post('/api/stt')
async def stt_endpoint(request):
    return await handle_stt_request(request)
"""
