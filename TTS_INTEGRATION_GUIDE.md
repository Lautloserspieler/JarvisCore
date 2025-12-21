# 🎙️ TTS Integration Guide - JarvisCore v1.2.0

## ✅ Implementiert! Text-to-Speech ist jetzt vollständig vorbereitet

Diese Anleitung zeigt dir, wie du die Deutsch-Englische Sprachausgabe aktivierst und verwendest.

---

## 🚀 Quick Start

### 1. TTS Library installieren

```bash
# Python 3.11 ist erforderlich (TTS unterstützt nicht Python 3.12+)
python --version  # Sollte 3.11.x sein

# Installiere alle Dependencies
pip install -r requirements.txt

# Oder nur TTS (wenn nicht in requirements.txt enthalten):
pip install tts>=0.21.3
```

### 2. Backend starten

```bash
cd backend
python main.py
```

Du solltest folgende Meldung sehen:
```
[INFO] TTS service initialized...
✅ XTTS initialized on cuda (GPU)
✅ Available languages: de, en
```

### 3. Frontend starten (neues Terminal)

```bash
cd frontend
npm install  # Nur beim ersten Mal
npm run dev
```

### 4. TTS Settings öffnen

- Öffne http://localhost:5000
- Gehe zu **Settings/Einstellungen** Tab
- Scroll zu "Voice Settings (Text-to-Speech)"
- Wähle Sprache: Deutsch oder English
- Klicke "Test Voice" um die Stimme zu testen

---

## 🎯 Features

### Sprachauswahl
- **Deutsch (🇩🇪)**: Jarvis_DE.wav (v2.2 optimiert)
- **English (🇬🇧)**: Jarvis_EN.wav (v2.2 optimiert)

Die Sprache wird automatisch erkannt basierend auf deiner Einstellung in den Settings.

### Einstellungen

Du kannst in der UI folgende Parameter einstellen:

| Setting | Bereich | Standard | Beschreibung |
|---------|---------|----------|---------------|
| **Enable Voice** | On/Off | On | Aktiviert/Deaktiviert TTS |
| **Language** | DE/EN | DE | Welche Sprache verwenden? |
| **Auto-play** | On/Off | Off | Automatisch sprechen nach Antwort |
| **Volume** | 0-100% | 100% | Lautstärke der Sprachausgabe |
| **Speed** | 0.5x-2x | 1.0x | Sprechgeschwindigkeit |

### API Endpoints

```bash
# Text zu Sprache synthetisieren
POST /api/tts/synthesize
Content-Type: application/json

{
  "text": "Hallo Welt",
  "language": "de",
  "autoplay": false
}

# Response: Audio WAV-Datei

---

# TTS Service Status
GET /api/tts/status

Response:
{
  "available": true,
  "engine": "xtts",
  "device": "cuda",
  "gpu_enabled": true,
  "languages": ["de", "en"]
}

---

# Verfügbare Voice Samples
GET /api/tts/voices

Response:
{
  "voices": [
    {
      "language": "de",
      "name": "Jarvis Deutsch",
      "description": "German JARVIS voice (v2.2 optimized)",
      "available": true
    },
    {
      "language": "en",
      "name": "Jarvis English",
      "description": "English JARVIS voice (v2.2 optimized)",
      "available": true
    }
  ]
}

---

# TTS Einstellungen abrufen
GET /api/tts/settings

Response:
{
  "enabled": true,
  "language": "de",
  "autoplay": false,
  "volume": 1.0,
  "speed": 1.0,
  "use_voice_samples": true
}

---

# TTS Einstellungen speichern
POST /api/tts/settings
Content-Type: application/json

{
  "enabled": true,
  "language": "de",
  "autoplay": true,
  "volume": 0.8,
  "speed": 1.2,
  "use_voice_samples": true
}

---

# TTS testen
POST /api/tts/test
Content-Type: application/json

{
  "language": "de"
}

Response: Audio WAV-Datei mit Test-Text
```

---

## 💻 Integration in den Chat

Um TTS automatisch mit Chat-Antworten zu nutzen:

### Backend (backend/main.py)

```python
# Import TTS service
from backend.api.tts_endpoints import get_tts_settings
from backend.core.tts_service import get_tts_service, Language

# Im WebSocket handler, nach Antwort generiert:
async def websocket_endpoint(websocket: WebSocket):
    # ... existing code ...
    
    # Get AI response
    response_text, is_plugin, tokens, tokens_per_sec = await generate_ai_response(user_message, session_id)
    
    # Check if TTS is enabled
    tts_settings = get_tts_settings()
    if tts_settings['enabled'] and not is_plugin:
        tts_service = get_tts_service()
        if tts_service:
            # Determine language
            lang = tts_settings['language'].upper()
            language = Language[lang] if lang in ['DE', 'EN'] else Language.DE
            
            # Synthesize speech
            audio_path = await tts_service.synthesize(response_text, language)
            
            if audio_path:
                # Send audio URL to frontend
                await websocket.send_text(json.dumps({
                    'type': 'chat_response_audio',
                    'audio_url': f"/audio/{audio_path.name}",
                    'messageId': response_id
                }))
```

### Frontend (Chat komponente)

Die `TTSSettings.vue` Komponente ist bereits vorbereitet. Integriere sie in dein Settings Tab:

```vue
<!-- frontend/src/views/Settings.vue -->
<template>
  <div class="settings-page">
    <!-- ... existing settings ... -->
    
    <!-- TTS Settings -->
    <TTSSettings />
  </div>
</template>

<script setup>
import TTSSettings from '@/components/TTSSettings.vue'
</script>
```

Audio im Chat abspielen:

```vue
<!-- Wenn Voice Option aktiviert: -->
<div v-if="message.audio_url" class="audio-player">
  <audio controls :src="message.audio_url"></audio>
</div>
```

---

## 🔧 Troubleshooting

### Problem: "TTS module not available"

```bash
# Stelle sicher, dass TTS installiert ist:
pip install tts>=0.21.3

# Prüfe Python Version:
python --version
# Sollte 3.11.x sein (nicht 3.12+)
```

### Problem: "Voice sample not found"

```bash
# Prüfe, dass Voice Samples vorhanden sind:
ls -la models/tts/voices/
# Sollte zeigen:
# - Jarvis_DE.wav
# - Jarvis_EN.wav
```

### Problem: GPU wird nicht genutzt

```bash
# Prüfe GPU Status:
python -c "import torch; print(torch.cuda.is_available())"
# Sollte 'True' sein

# Falls False, NVIDIA CUDA installieren:
# https://developer.nvidia.com/cuda-downloads
```

### Problem: Langsame Synthese

```python
# In TTSSettings.vue oder backend/core/tts_service.py:
# - num_gpt_tokens reduzieren (schneller, aber weniger Qualität)
# - speed Parameter erhöhen (1.5x statt 1.0x)
# - temperature anpassen (0.7 für konsistent, 0.85 für vielfältig)
```

### Problem: Fehler bei Installation

```bash
# Manchmal gibt es Konflikte mit NumPy/Torch
pip install --upgrade pip setuptools wheel
pip install numpy>=1.24.3,<2.0  # Muss vor torch installiert sein
pip install torch>=2.1.0
pip install tts>=0.21.3
```

---

## ⚡ Performance Tips

### Für schnelle Synthese:
```yaml
# config.yaml
tts:
  num_gpt_tokens: 25    # Schneller (default 30)
  temperature: 0.7      # Konsistent
  device: "cuda"        # GPU
  use_cache: true       # Voice Latents cachen
```

### Für beste Qualität:
```yaml
tts:
  num_gpt_tokens: 40    # Länger, bessere Qualität
  temperature: 0.80     # Mehr Variation
  device: "cuda"        # GPU für speed
  use_cache: true       # Always cache
```

### CPU-only Modus:
```python
# In tts_service.py:
tts_service = TTSService(use_gpu=False)
# Fallback zu pyttsx3 wird automatisch verwendet wenn XTTS zu langsam
```

---

## 🚀 Nächste Schritte

### v1.2.0 (Aktuell)
- ✅ TTS Service implementiert
- ✅ Multi-Language Support (DE/EN)
- ✅ Settings UI
- ✅ Voice Testing
- 🔄 Chat Integration (In Arbeit)
- 🔄 Auto-play Response (In Arbeit)

### v1.3.0 (Geplant)
- [ ] Whisper Voice Input
- [ ] Custom Voice Cloning
- [ ] Accent Control (Regional accents)
- [ ] Emotion Control (Happy, Serious, etc.)
- [ ] Multi-format Output (MP3, OGG, etc.)

---

## 📚 Weitere Dokumentation

- [XTTS v2 Paper](https://arxiv.org/abs/2406.04904)
- [Coqui TTS Docs](https://tts.readthedocs.io/)
- [Voice Samples Guide](./models/tts/voices/README.md)
- [Main README](./README.md)

---

## ✅ Fertig!

Die TTS-Integration ist jetzt ready to use! 🎙️

Klicke einfach auf "Test Voice" in den Settings um die Deutsch/English Stimmen zu hören!

**Status:** Production-ready v1.2.0 ✅

*Last Updated: 21. Dezember 2025*
