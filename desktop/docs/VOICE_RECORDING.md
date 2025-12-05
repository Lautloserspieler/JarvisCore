# Voice Recording Integration

## Überblick

Die Desktop-UI unterstützt **native Audio-Aufnahme** mit automatischer Transkription durch JarvisCore STT.

## Architektur

```
Vue.js Component (VoiceRecordingButton)
    │ Click: Start/Stop
    ↓
useVoiceRecording Composable
    │ StartRecording() / StopRecording()
    ↓
Wails Bridge
    │
    ↓
Go Backend (internal/audio/recorder.go)
    │ PortAudio: Native Audio Capture
    │ PCM → WAV Conversion
    ↓ HTTP POST /api/stt
JarvisCore Python Backend
    │ VOSK / Whisper / Faster-Whisper
    ↓
Transcription Text
    ↓ WebSocket Broadcast
Vue.js Component
    │ Auto-Send zu Chat
```

---

## Installation

### 1. PortAudio installieren

**Windows:**

```powershell
# Mit vcpkg (empfohlen)
vcpkg install portaudio:x64-windows

# ODER mit MSYS2
pacman -S mingw-w64-x86_64-portaudio
```

**Linux:**

```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev

# Fedora/RHEL
sudo dnf install portaudio-devel

# Arch
sudo pacman -S portaudio
```

**macOS:**

```bash
brew install portaudio
```

### 2. Go Dependencies

```bash
cd desktop/backend
go mod download
go get github.com/gordonklaus/portaudio
```

### 3. Test Audio-System

```bash
cd desktop
wails dev

# In der App: Mikrofon-Button klicken
# Falls Fehler: Mikrofon-Berechtigung prüfen
```

---

## Nutzung

### Frontend (Vue.js)

**VoiceRecordingButton Component:**

```vue
<template>
  <VoiceRecordingButton @transcription="handleTranscription" />
</template>

<script>
import VoiceRecordingButton from './VoiceRecordingButton.vue'

export default {
  components: { VoiceRecordingButton },
  setup() {
    const handleTranscription = (text) => {
      console.log('Transkription:', text)
      // Auto-send zu Chat
    }
    
    return { handleTranscription }
  }
}
</script>
```

**useVoiceRecording Composable:**

```javascript
import { useVoiceRecording } from '../composables/useVoiceRecording'

const {
  isRecording,
  isProcessing,
  recordingDuration,
  formattedDuration,
  error,
  startRecording,
  stopRecording,
  cancelRecording
} = useVoiceRecording()

// Start Recording
await startRecording()

// Stop Recording (returns transcription)
const text = await stopRecording()

// Cancel Recording
await cancelRecording()
```

### Backend (Go)

**App Methods:**

```go
// Start Recording
err := app.StartRecording()

// Stop Recording (returns transcription)
transcription, err := app.StopRecording()

// Check if recording
isRecording := app.IsRecording()

// Get duration
duration := app.GetRecordingDuration() // seconds
```

---

## Audio-Spezifikationen

### Recording Format

| Parameter | Wert | Grund |
|-----------|------|-------|
| **Sample Rate** | 16000 Hz | Whisper/VOSK Standard |
| **Channels** | 1 (Mono) | STT benötigt nur Mono |
| **Bit Depth** | 16-bit | Standard PCM |
| **Encoding** | PCM | Unkomprimiert |
| **Container** | WAV | Standard Audio-Format |

### WAV Header

```
RIFF Header (12 bytes)
fmt Chunk (24 bytes)
  - Audio Format: 1 (PCM)
  - Channels: 1
  - Sample Rate: 16000
  - Byte Rate: 32000
  - Block Align: 2
  - Bits per Sample: 16
data Chunk (8 bytes + audio data)
```

---

## JarvisCore STT Endpoint

### API Endpoint

```
POST /api/stt
Content-Type: multipart/form-data

Body:
  audio: [WAV file]
```

### Response

```json
{
  "text": "Transkribierter Text",
  "confidence": 0.95,
  "language": "de"
}
```

### Fehler-Codes

| Code | Bedeutung |
|------|----------|
| 200 | Erfolg |
| 400 | Ungültiges Audio-Format |
| 413 | Audio zu groß (>10MB) |
| 500 | STT-Fehler |

---

## Features

### ✅ Implementiert

- 🎤 **Native Audio-Aufnahme** via PortAudio
- ⏺ **Start/Stop Button** mit visueller Animation
- ⏱️ **Live Duration Counter** (0.1s Genauigkeit)
- 📊 **Recording Indicator** (Pulse-Animation)
- 🔄 **Auto-Transcription** zu JarvisCore STT
- 💬 **Auto-Send** zu Chat nach Transkription
- ⚠️ **Error Handling** mit User-Feedback
- 🔊 **WAV Conversion** (PCM → WAV)
- 🔌 **WebSocket Events** (recording_started, recording_stopped, transcription_received)

### 🚧 Geplant

- 🔊 Volume Meter (Live-Visualisierung)
- 🏛️ Audio-Playback (Aufnahme anhören)
- 💾 Local Storage (Aufnahmen speichern)
- ⚙️ Settings (Mikrofon auswählen)
- 🌍 Language Detection

---

## User Flow

1. **Click Mikrofon-Button**
   - Button wird rot + Pulse-Animation
   - "Aufnahme läuft" Indicator
   - Duration Counter startet

2. **Sprechen**
   - Audio wird in Echtzeit aufgenommen
   - Buffer füllt sich (PCM-Daten)

3. **Click Stopp (oder erneut Mikrofon)**
   - Button zeigt "Verarbeitung" (Sanduhr)
   - Audio → WAV konvertiert
   - POST zu JarvisCore /api/stt
   
4. **Transkription erhalten**
   - Text wird automatisch in Chat-Eingabe eingesetzt
   - Message wird automatisch gesendet
   - Assistant antwortet

---

## Performance

### Audio Buffer

```go
framesPerBuffer := 1024  // ~64ms bei 16kHz
channelBuffer := 256     // Messages
```

- **Latenz:** ~100ms (64ms Buffer + 36ms Processing)
- **Memory:** ~2KB/s bei 16kHz Mono 16-bit
- **Max Duration:** Unbegrenzt (nur durch RAM limitiert)

### Network

- **Upload Size:** ~1MB pro Minute Audio (WAV)
- **Request Time:** ~500ms - 2s (abhängig von STT-Modell)

---

## Troubleshooting

### "PortAudio Init fehlgeschlagen"

**Ursache:** PortAudio nicht installiert

**Lösung:**

```bash
# Windows
vcpkg install portaudio:x64-windows

# Linux
sudo apt-get install portaudio19-dev

# macOS
brew install portaudio

# Go Dependencies neu laden
cd desktop/backend
go mod download
```

### "Mikrofon nicht gefunden"

**Ursache:** Kein Mikrofon angeschlossen oder Berechtigung fehlt

**Lösung:**

1. Mikrofon anschließen und als Standard setzen
2. System-Einstellungen: Mikrofon-Berechtigung geben
3. App neu starten

### "STT Request fehlgeschlagen"

**Ursache:** JarvisCore Backend nicht erreichbar

**Lösung:**

```bash
# JarvisCore starten
cd JarvisCore
python main.py

# Check ob STT aktiviert
# In data/settings.json:
{
  "stt": {
    "enabled": true,
    "engine": "vosk"  // oder "whisper"
  }
}
```

### "Audio zu leise"

**Lösung:**

1. System-Lautstärke Mikrofon erhöhen
2. Näher ans Mikrofon sprechen
3. Externes Mikrofon nutzen

### "Transkription ungenau"

**Lösung:**

1. **Besseres Modell:** Whisper statt VOSK
2. **Deutlich sprechen:** Klare Aussprache
3. **Umgebung:** Ruhige Umgebung ohne Echo
4. **Mikrofon:** Bessere Hardware

---

## Testing

### Unit Tests (Go)

```bash
cd desktop/backend
go test ./internal/audio -v
```

### Integration Test

```bash
# 1. JarvisCore starten
cd JarvisCore
python main.py

# 2. Desktop UI starten
cd desktop
wails dev

# 3. Mikrofon-Button testen
# - Klick: Recording startet
# - Sprechen: "Hallo J.A.R.V.I.S."
# - Klick: Recording stoppt
# - Erwartung: Text erscheint in Chat
```

---

## Best Practices

1. **Kurze Aufnahmen** - Max 10-15 Sekunden für beste Ergebnisse
2. **Deutlich sprechen** - Klare Aussprache verbessert Genauigkeit
3. **Ruhige Umgebung** - Hintergrundgeräusche vermeiden
4. **Gutes Mikrofon** - Externe Mikrofone sind besser als Laptop-Mikros
5. **Close-to-Mic** - 15-30cm Abstand ideal

---

## Weitere Infos

- **PortAudio Docs:** http://portaudio.com/docs/
- **Go PortAudio:** https://github.com/gordonklaus/portaudio
- **WAV Format:** https://en.wikipedia.org/wiki/WAV
- **Whisper:** https://github.com/openai/whisper
- **VOSK:** https://alphacephei.com/vosk/
