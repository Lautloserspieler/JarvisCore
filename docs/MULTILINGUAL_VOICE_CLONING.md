# Multilingual Voice Cloning für XTTS v2

**Version:** 1.0  
**Datum:** 2025-12-20  
**Status:** ✅ Productive

## Übersicht

Das erweiterte TTS-System unterstützt nun **mehrsprachiges Voice Cloning mit intelligenter Caching-Mechanik**:

- 🇩🇪 **Deutsch** - Automatisch erkannt und gecacht
- 🇬🇧 **Englisch** - Automatisch erkannt und gecacht  
- ⚡ **Performance** - Voice Clone Computation nur 1x pro Sprache (~2s), dann <10ms Latenz
- 🔄 **Auto-Detection** - Sprache wird automatisch aus Text erkannt
- 💾 **Persistent Caching** - Latents werden auf Disk gespeichert

## Konfiguration

### Minimale Konfiguration (Single-Language Legacy)

```yaml
speech:
  tts_backend: 'xtts'        # Oder pyttsx3 für Fallback
  tts_rate: 180              # Sprechgeschwindigkeit
  tts_volume: 0.8            # Lautstärke
  tts_use_gpu: true          # GPU-Beschleunigung
  voice_sample: 'models/tts/voices/Jarvis.wav'  # Wird für beide Sprachen verwendet
```

**Verhalten:** Wenn nur `voice_sample` gesetzt ist, wird die gleiche Stimme für Deutsch und Englisch verwendet.

### Empfohlene Konfiguration (Multilingual)

```yaml
speech:
  tts_backend: 'xtts'
  tts_rate: 180
  tts_volume: 0.8
  tts_use_gpu: true
  
  # Sprachspezifische Voice Samples
  voice_sample_de: 'models/tts/voices/Jarvis_DE.wav'    # Deutsch (z.B. männlich)
  voice_sample_en: 'models/tts/voices/Jarvis_EN.wav'    # Englisch (z.B. amerikanisch)
  
  # Optional: Fallback wenn sprachspezifisches Sample nicht existiert
  voice_sample: 'models/tts/voices/Jarvis.wav'
  
  # Optional: Sprecher für Multi-Speaker-Modelle
  tts_xtts_speaker: 'speaker_0'
  
  # Optional: Preset für Voice Effects
  voice_preset: 'jarvis_marvel'  # Aktiviert Marvel-JARVIS-Effekte

models:
  tts:
    xtts:
      default_speaker: 'speaker_0'  # Fallback Speaker
```

## Voice Samples vorbereiten

### Audio-Anforderungen

```
Format:       WAV oder MP3
Sample-Rate:  22050 Hz oder höher (empfohlen: 24000 Hz)
Kanäle:       Mono oder Stereo
Dauer:        5-15 Sekunden (optimal: 10 Sekunden)
Qualität:     Laut und deutlich, minimale Hintergrundgeräusche
Inhalt:       Neutrale Sprachproben (z.B. "This is a voice sample for text-to-speech synthesis")
```

### Sample-Erstellung

**Deutsch (Jarvis_DE.wav):**
```
"Hallo, das ist eine Sprachabtastung für die Textsynthese. 
Jarvis ist ein intelligenter persönlicher Assistent.
Ich kann mehrere Sprachen sprechen."
```

**Englisch (Jarvis_EN.wav):**
```
"Hello, this is a voice sample for text-to-speech synthesis.
I am Jarvis, an intelligent personal assistant.
I can speak multiple languages."
```

### Verzeichnisstruktur

```
JarvisCore/
├── models/
│   └── tts/
│       └── voices/
│           ├── Jarvis.wav          # Legacy/Fallback
│           ├── Jarvis_DE.wav       # 🇩🇪 Deutsch
│           └── Jarvis_EN.wav       # 🇬🇧 Englisch
└── data/
    └── tts/
        ├── voice_latents_de.pt     # Auto-generiert (Deutsch)
        └── voice_latents_en.pt     # Auto-generiert (Englisch)
```

## Funktionsweise

### 1. Voice Clone Computation (Erste Verwendung pro Sprache)

```
Benutzer: "Hallo, wie geht es dir?"
         ↓
    [Language Detection] → German (de)
         ↓
    [Check Latents Cache] → voice_latents_de.pt existiert nicht
         ↓
    [Load Voice Sample] → Jarvis_DE.wav
         ↓
    [Compute Latents] → ~2 Sekunden ⏱️
         ↓
    [Cache to Disk] → voice_latents_de.pt
         ↓
    [Synthesize] → Audio output
         ↓
    [Play] → 🔊
```

**Dauer:** ~2-3 Sekunden (einmalig pro Sprache)

### 2. Voice Clone Usage (Nachfolgende Aufrufe)

```
Benutzer: "Wie ist das Wetter?"
         ↓
    [Language Detection] → German (de)
         ↓
    [Check Latents Cache] → voice_latents_de.pt existiert ✓
         ↓
    [Load Cached Latents] → <10ms ⚡
         ↓
    [Synthesize] → Audio output
         ↓
    [Play] → 🔊
```

**Dauer:** ~0.5-1 Sekunde (nur Synthese, kein Voice Cloning nötig)

### 3. Sprachenwechsel

```
Benutzer: "Hallo!"
         ↓
    [Synthese mit German Latents]
         ↓

Benutzer: "Hello there!"
         ↓
    [Language Detection] → English (en)
         ↓
    [Latents ändern] → voice_latents_en.pt
         ↓
    [Synthese mit English Latents]
```

**Wichtig:** Der XTTS-Modell selbst wird **nicht neu geladen**. Nur die Latents (Stimmprofil) wechseln.

## API-Verwendung

### Einfache Verwendung (Auto-Language Detection)

```python
from core.text_to_speech import TextToSpeech

tts = TextToSpeech(settings)

# Sprache wird automatisch erkannt
tts.speak("Hallo, wie geht es dir?")   # → German
tts.speak("Hello, how are you?")       # → English
```

### Explizite Sprachanforderung

```python
# Erzwinge Deutsch
tts.speak("Hello!", language='de')

# Erzwinge Englisch
tts.speak("Hallo!", language='en')

# Mit Style-Modifier
tts.speak("Guten Morgen!", language='de', style='freundlich')
```

### Mit Styles kombiniert

```python
# Deutsch + Stil
tts.speak("Das ist fantastisch!", language='de', style='humorvoll')

# Englisch + Stil
tts.speak("That is amazing!", language='en', style='professionell')
```

## Cache-Verwaltung

### Auto-Generated Caches

```
data/tts/
├── voice_latents_de.pt    # Deutsch Voice Latents + Metadata
├── voice_latents_en.pt    # Englisch Voice Latents + Metadata
└── ...
```

### Cache-Inhalt

```python
# Jede .pt Datei enthält:
{
    "gpt_cond_latent": <torch.Tensor>,           # GPT-Konditionierung
    "speaker_embedding": <torch.Tensor>,         # Speaker-Embedding
    "sample_path": "/absolute/path/to/sample.wav",  # Referenz
    "sample_mtime": 1702958567.123,              # Änderungsdatum
    "created": 1702958569.456,                   # Erstellungsdatum
    "language": "de"                             # Sprache
}
```

### Cache invalidieren (Manuell)

```bash
# Cache löschen (wird beim nächsten Start neu generiert)
rm data/tts/voice_latents_de.pt
rm data/tts/voice_latents_en.pt

# Oder über Python
import shutil
shutil.rmtree('data/tts')
```

### Cache auto-invalidieren bei Voice Sample Änderung

Wenn `Jarvis_DE.wav` modifiziert wird:
1. `sample_mtime` wird bei Laden geprüft
2. Falls unterschiedlich → Cache wird verworfen
3. Neue Latents werden berechnet

## Performance-Charakteristiken

### Erste Initialisierung

```
Zustand: XTTS-Modell wird geladen + beide Voice Clones werden berechnet

Zeitlinie:
- XTTS-Modell laden: ~5-10s
- German Voice Clone: ~2s
- English Voice Clone: ~2s (parallel möglich)
- Gesamt: ~10-15s

Speicher:
- XTTS Modell: ~3-4 GB (GPU) / ~6-8 GB (CPU)
- Voice Latents: ~100 KB je Sprache
```

### Laufzeit Pro Anfrage

| Szenario | Zeit | Notes |
|----------|------|-------|
| **First German call** | ~2-3s | Voice Clone + Synthesis |
| **German (cached)** | ~0.5-1s | Nur Synthesis |
| **English (cached)** | ~0.5-1s | Nur Synthesis |
| **Language switch** | <10ms | Nur Latents-Wechsel |
| **50 char text (DE)** | ~0.5s | Synthesis time |
| **250 char text (EN)** | ~1.5s | Synthesis time |

### Speicher-Footprint

```
After Init + Both Languages Cached:

Component               Size        Location
─────────────────────────────────────────────────
XTTS Modell             3-4 GB      GPU/RAM
German Latents          ~50 KB      disk (voice_latents_de.pt)
English Latents         ~50 KB      disk (voice_latents_en.pt)
Audio Output Cache      ~5-20 MB    output/tts_cache/ (24 files)
```

## Troubleshooting

### Problem: "Voice sample not found"

**Symptom:** `WARNING: XTTS hat kein Voice-Sample gefunden`

**Lösung:**
```yaml
# Überprüfe die Config
speech:
  voice_sample_de: '/absolute/path/to/Jarvis_DE.wav'  # Absolute Pfade bevorzugt
  voice_sample_en: 'models/tts/voices/Jarvis_EN.wav'
  voice_sample: 'models/tts/voices/Jarvis.wav'        # Fallback
```

### Problem: "Language detection fails"

**Symptom:** Text wird in falscher Sprache synthesiert

**Lösung:**
```python
# Explizite Sprache angeben
tts.speak("Mein Name ist Jarvis", language='de')  # Erzwinge Deutsch
```

### Problem: Cache wird nicht verwendet

**Symptom:** Jede Anfrage dauert ~2s (Voice Clone statt cached)

**Lösung 1:** Cache-Ordner überprüfen
```bash
ls -la data/tts/
# Sollte zeigen:
# voice_latents_de.pt
# voice_latents_en.pt
```

**Lösung 2:** Logs überprüfen
```
grep "aus Cache geladen" logs/jarvis.log
# Sollte zeigen: "XTTS Voice-Latents für de aus Cache geladen."
```

### Problem: Voice klingt unterschiedlich je Sprache

**Erwartet:** Das ist normal! Unterschiedliche Voice Samples erzeugen unterschiedliche Klangfarben.

**Tipp:** Verwende identische Voice Samples für beide Sprachen wenn konsistente Stimme gewünscht ist.

## Migration von Single-Language Setup

### Schritt 1: Alte Config sichern
```bash
cp config.yaml config.yaml.backup
```

### Schritt 2: Neue Voice Samples vorbereiten
```
models/tts/voices/
├── Jarvis.wav          # ← Alte Config (bleibt erhalten!)
├── Jarvis_DE.wav       # ← Neu: Deutsch
└── Jarvis_EN.wav       # ← Neu: Englisch
```

### Schritt 3: Config erweitern
```yaml
# ALT (funktioniert noch):
speech:
  tts_backend: 'xtts'
  voice_sample: 'models/tts/voices/Jarvis.wav'

# NEU (empfohlen):
speech:
  tts_backend: 'xtts'
  voice_sample_de: 'models/tts/voices/Jarvis_DE.wav'
  voice_sample_en: 'models/tts/voices/Jarvis_EN.wav'
  voice_sample: 'models/tts/voices/Jarvis.wav'  # Fallback
```

### Schritt 4: Cache regenerieren
```bash
# Alt-Cache löschen (optional)
rm -f data/tts/xtts_voice_latents.pt  # Legacy

# Neu-Cache wird beim Start auto-generiert
python main.py
```

**Ergebnis:** Beim ersten Start werden automatisch `voice_latents_de.pt` und `voice_latents_en.pt` generiert.

## Best Practices

### 1. Voice Samples auf Qualität überprüfen

```bash
# Mit ffprobe (wenn installiert)
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=noprint_wrappers=1:nokey=1:noprivate=1 Jarvis_DE.wav

# Erwartet: codec=pcm_s16le oder ähnlich, sample_rate=22050+, channels=1 oder 2
```

### 2. Separate Stimmen für jede Sprache

```yaml
# Gut: Unterschiedliche Sprecher/Akzente
voice_sample_de: 'models/tts/voices/Jarvis_DE_male.wav'  # Deutsch, männlich
voice_sample_en: 'models/tts/voices/Jarvis_EN_female.wav'  # Englisch, weiblich

# Auch gut: Gleiche Person, aber in jeder Sprache
voice_sample_de: 'models/tts/voices/same_person_de.wav'
voice_sample_en: 'models/tts/voices/same_person_en.wav'

# Nicht empfohlen: Gleiches Sample für beide
voice_sample: 'models/tts/voices/one_sample.wav'  # Akzent bei nicht-Muttersprache
```

### 3. Logs überwachen

```bash
# Cache-Generierung überprüfen
grep -E "Computing voice latents|aus Cache geladen" logs/jarvis.log

# Performance überprüfen
grep -E "XTTS queued|Sprachausgabe gestoppt" logs/jarvis.log
```

### 4. Voice Latents regelmäßig überprüfen

```python
# In einem Monitoring-Script
import os
from pathlib import Path

for lang in ['de', 'en']:
    cache = Path('data/tts') / f'voice_latents_{lang}.pt'
    if cache.exists():
        size = cache.stat().st_size
        print(f"{lang}: {size} bytes, exists: ✓")
    else:
        print(f"{lang}: missing (will be regenerated on first use)")
```

## Zu den technischen Details

### Warum Latents Caching?

Die Voice Cloning Berechnung ist der teuerste Schritt:
```
1. Audio laden (schnell)
2. Mel-Spectrogram erstellen (schnell)
3. GPT-Model durchlaufen (~1.5s) ← GPU/CPU-intensive Berechnung
4. Sprecher-Embedding extrahieren (~0.5s) ← GPU/CPU-intensive Berechnung
5. Tensor serialisieren (schnell)
```

Durch Caching sparen wir Schritte 3-4 (~2s) für alle nachfolgenden Anfragen.

### Warum separate Caches pro Sprache?

- **Modell-Konsistenz:** Ein XTTS-Modell pro Sprache könnte verschieden sein
- **Voice-Varianz:** Unterschiedliche Voice Samples erzeugen unterschiedliche Embeddings
- **Klang-Optimierung:** Jede Sprache kann eigene Stimm-Charakteristiken haben
- **Wartbarkeit:** Einfacher zu debuggen und zu verstehen

### Warum Auto-Language Detection?

- **UX:** Benutzer müssen Sprache nicht manuell angeben
- **Konsistenz:** Richtige Phoneme und Prosodie pro Sprache
- **Fallback:** Python-Heuristik falls Erkennung unsicher

## Siehe auch

- [XTTS v2 Dokumentation](https://github.com/coqui-ai/TTS)
- [Konfiguration](./CONFIG.md)
- [Audio-Setup](./AUDIO_SETUP.md)
