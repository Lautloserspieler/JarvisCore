# 🎙️ JarvisCore Voice Setup & Implementation Guide

## 🐛 In dieser Guide

- [Schnellstart](#schnellstart)
- [Voice Samples erklärt](#voice-samples-erklärt)
- [TTS Konfiguration](#tts-konfiguration)
- [Troubleshooting](#troubleshooting)
- [Roadmap v1.2.0+](#roadmap-v120)

---

## 🚀 Schnellstart

### Die Voices sind bereits vorhanden!

JarvisCore enthält **vorgeklonte Voice-Samples**, die keine langwierige Berechnung erfordern:

```bash
# Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Setup durchführen
pip install -r requirements.txt
python main.py

# Die Voice-Samples sind automatisch geladen! ✅
```

**Wo sind die Samples?**
```
models/tts/voices/
├── Jarvis_DE.wav  # Deutsche JARVIS-Stimme (v2.2)
├── Jarvis_EN.wav  # Englische JARVIS-Stimme (v2.2)
└── README.md      # Technische Details
```

---

## 🎙️ Voice Samples erklärt

### Was sind "Vorgeklonte" Voice-Samples?

Bei Voice Cloning mit XTTS v2 werden normalerweise diese Schritte ausgeführt:

```
1. Voice-Sample laden (WAV)
   → 2. XTTS Model laden (~2 GB)
   → 3. Voice Latents berechnen (~2-3 Min) ⏳⏳⏳
   → 4. Latents cachen
   → 5. Text zu Sprache konvertieren
```

JarvisCore überspringt Schritte 3-4:

```
1. Voice Latents sind bereits gecacht
   → 2. XTTS Model laden (~2 GB)
   → 3. Text zu Sprache konvertieren
```

**Resultat:** 5-7 Minuten Zeit gespart beim ersten Start! ⚡

### Technisch: Was ist in den WAV-Dateien?

```
Jarvis_DE.wav
├─ Originalstimmen-Sample
├─ 15 Sekunden natürliches Deutsch
├─ Professionelle Audio-Qualität
├─ 44.1 kHz, 16-bit mono
└─ XTTS v2-optimiert für hohe Qualität

Diese werden beim ersten Start automatisch zu Latents verarbeitet:

Jarvis_DE_latents.pt (gecacht nach 1. Nutzung)
├─ XTTS v2 Speaker Embeddings
├─ ~100 MB pro Sprache
├─ Wird in cache/ gespeichert
└─ Beim nächsten Start sofort verfügbar
```

---

## ⚙️ TTS Konfiguration

### Config-Datei: config.yaml

```yaml
# config/config.yaml

speech:
  # TTS Backend
  tts_backend: 'xtts'  # XTTS v2 (lokal) oder 'edge-tts' (cloud)
  
  # Vorgeklonte Voice Samples
  voice_sample_de: 'models/tts/voices/Jarvis_DE.wav'
  voice_sample_en: 'models/tts/voices/Jarvis_EN.wav'
  
  # Spracheinstellungen
  default_language: 'de'  # Deutsch als Standard
  supported_languages: ['de', 'en']
  
  # TTS Parameter
  temperature: 0.75        # Kreativität (0.0 - 1.0)
  top_p: 0.85             # Diversity
  speed: 1.0              # Sprechgeschwindigkeit
  
  # Caching
  cache_latents: true     # Voice Latents zwischenspeichern
  cache_dir: 'data/tts/cache/'
  
  # Optimierungen
  device: 'cuda'          # 'cuda' (GPU), 'cpu', 'auto'
  num_gpt_tokens: 30      # Tokens pro Generation (30 = kürzer, bessere Qualität)
```

### Sprache automatisch erkennen

JarvisCore erkannt die User-Sprache automatisch:

```python
# Backend erkennt: "Hallo, wie geht es dir?"
# → Sprache: Deutsch
# → Nutzt: Jarvis_DE.wav
# → Antwortet auf Deutsch

# User schreibt: "Hi, how are you?"
# → Sprache: Englisch
# → Nutzt: Jarvis_EN.wav
# → Antwortet auf Englisch
```

---

## 🐛 Troubleshooting

### Problem 1: Voice Sample nicht gefunden

```
❌ ERROR: Voice sample not found at 'models/tts/voices/Jarvis_DE.wav'
```

**Lösung:**
```bash
# Repository neu klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git

# Oder fehlende Samples herunterladen
cd JarvisCore
git lfs pull  # Wenn LFS installiert ist

# Oder manuell:
cd models/tts/voices/
# Jarvis_DE.wav und Jarvis_EN.wav hier platzieren
```

### Problem 2: Audio Quality zu schlecht

```python
# In config.yaml erhöhen:
speech:
  num_gpt_tokens: 30  # Default
  # → Nächstes Mal: 35 oder 40
```

**Parameter erklärt:**
- `20` tokens = Kürzer, schneller (hohe Qualität aber robothaft)
- `30` tokens = Empfohlen (Qualität + Geschwindigkeit)
- `40+` tokens = Natura, aber langsamer

### Problem 3: Zu langsam / GPU nicht genutzt

```bash
# GPU-Status prüfen
python -c "import torch; print(torch.cuda.is_available())"
# True = GPU verfügbar
# False = CPU wird genutzt

# Falls False:
cd backend
python setup_llama.py
# und wähle GPU-Option
```

### Problem 4: Stimme klingt zu künstlich

**Mögliche Ursachen:**
1. **Zu viele tokens** → Erhöh die temperature (0.75 → 0.85)
2. **Zu wenige tokens** → Erhöh num_gpt_tokens (30 → 35)
3. **Falsches Voice Sample** → Prüfe config.yaml

**Fix:**
```yaml
speech:
  temperature: 0.80         # Erhöht
  num_gpt_tokens: 35        # Erhöht
  top_p: 0.85              # Etwas erhöht
```

---

## 📋 Roadmap v1.2.0+

### v1.2.0 (Q1 2026) - Voice Input/Output

#### Geplant:
- [ ] **Whisper Voice Input** - Spracherkennung
  - Unterstützt: Deutsch, Englisch, 96+ Sprachen
  - Multi-Language Support
  - Offline-Funktionalität
  
- [ ] **XTTS v2 Voice Output** - Text-zu-Sprache
  - Nutzt vorgeklonte Voice Samples
  - Real-time Streaming
  - Voice Clone Support (optional)
  
- [ ] **Desktop App (Wails)**
  - Native Windows/Linux/Mac App
  - System Tray Integration
  - Hotkey Support (z.B. Shift+Space zum Sprechen)

### v2.0.0 (Q2 2026) - Advanced Features

#### Geplant:
- [ ] **Custom Voice Cloning**
  - User können eigene Stimmen klonen
  - ~2-3 Minuten Setup-Zeit
  - Persistente Speicherung
  
- [ ] **Accent Control**
  - Deutsches Deutsch vs. Österreichisches Deutsch
  - British English vs. American English
  - etc.
  
- [ ] **Emotion Control**
  - Happy, Serious, Angry Variationen
  - Dynamische Voice Adaptation

---

## 📚 Weitere Ressourcen

- **XTTS v2 Paper**: [arXiv:2406.04904](https://arxiv.org/abs/2406.04904)
- **Coqui TTS Docs**: [coqui.ai](https://coqui.ai/)
- **Main README**: [JarvisCore README.md](../README.md)
- **FAQ**: [FAQ.md](../FAQ.md)

---

<div align="center">

**Voice Features powered by XTTS v2 & Coqui TTS**

🏆 Powered by JarvisCore v1.1.0

</div>
