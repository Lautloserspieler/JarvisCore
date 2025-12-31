# ❓ Frequently Asked Questions (FAQ)

**Willkommen bei JARVIS Core!** Hier findest du Antworten auf die häufigsten Fragen.

[🇬🇧 English FAQ](./FAQ_EN.md) | [🐛 Issues](https://github.com/Lautloserspieler/JarvisCore/issues) | [📚 Docs](./docs/)

---

## 📚 Inhaltsverzeichnis

### [Allgemein](#allgemein-1)
- [Was ist JARVIS Core?](#was-ist-jarvis-core)
- [Ist JARVIS wirklich 100% lokal?](#ist-jarvis-wirklich-100-lokal)
- [Kostet JARVIS etwas?](#kostet-jarvis-etwas)
- [Welche Betriebssysteme werden unterstützt?](#welche-betriebssysteme-werden-unterstützt)

### [Installation & Setup](#installation--setup-1)
- [Wie installiere ich JARVIS?](#wie-installiere-ich-jarvis)
- [Brauche ich eine GPU?](#brauche-ich-eine-gpu)
- [Welche GPU wird unterstützt?](#welche-gpu-wird-unterstützt)
- [Wie viel RAM brauche ich?](#wie-viel-ram-brauche-ich)
- [Wie viel Speicherplatz wird benötigt?](#wie-viel-speicherplatz-wird-benötigt)

### [Modelle](#modelle-1)
- [Welche AI-Modelle kann ich nutzen?](#welche-ai-modelle-kann-ich-nutzen)
- [Wie downloade ich ein Modell?](#wie-downloade-ich-ein-modell)
- [Welches Modell ist am schnellsten?](#welches-modell-ist-am-schnellsten)
- [Kann ich eigene Modelle nutzen?](#kann-ich-eigene-modelle-nutzen)
- [Wie groß sind die Modelle?](#wie-groß-sind-die-modelle)

### [Performance](#performance-1)
- [Wie schnell ist JARVIS?](#wie-schnell-ist-jarvis)
- [Warum ist mein JARVIS langsam?](#warum-ist-mein-jarvis-langsam)
- [Kann ich die Performance verbessern?](#kann-ich-die-performance-verbessern)
- [AMD GPU - Warum so langsam?](#amd-gpu---warum-so-langsam)

### [Features & Nutzung](#features--nutzung-1)
- [Kann JARVIS Bilder generieren?](#kann-jarvis-bilder-generieren)
- [Funktioniert Spracherkennung?](#funktioniert-spracherkennung)
- [Kann JARVIS im Internet suchen?](#kann-jarvis-im-internet-suchen)
- [Wie aktiviere ich Plugins?](#wie-aktiviere-ich-plugins)
- [Kann ich meinen Chat-Verlauf speichern?](#kann-ich-meinen-chat-verlauf-speichern)

### [Troubleshooting](#troubleshooting-1)
- [JARVIS startet nicht - was tun?](#jarvis-startet-nicht---was-tun)
- [Port bereits belegt - wie beheben?](#port-bereits-belegt---wie-beheben)
- [Module not found Error](#module-not-found-error)
- [GPU wird nicht erkannt](#gpu-wird-nicht-erkannt)
- [Frontend lädt nicht](#frontend-lädt-nicht)

### [Sicherheit & Privatsphäre](#sicherheit--privatsphäre-1)
- [Werden meine Daten gesammelt?](#werden-meine-daten-gesammelt)
- [Ist JARVIS sicher?](#ist-jarvis-sicher)
- [Wo werden Chat-Daten gespeichert?](#wo-werden-chat-daten-gespeichert)
- [Kann ich Telemetrie deaktivieren?](#kann-ich-telemetrie-deaktivieren)

### [Entwicklung & Community](#entwicklung--community-1)
- [Kann ich zu JARVIS beitragen?](#kann-ich-zu-jarvis-beitragen)
- [Wie melde ich Bugs?](#wie-melde-ich-bugs)
- [Gibt es einen Discord/Community?](#gibt-es-einen-discordcommunity)
- [Roadmap - Was kommt als nächstes?](#roadmap---was-kommt-als-nächstes)

---

## Allgemein

### Was ist JARVIS Core?

**JARVIS Core** ist ein **lokaler AI-Assistent**, inspiriert von Tony Starks JARVIS aus Iron Man. Anders als ChatGPT, Claude oder Gemini läuft JARVIS **komplett auf deinem Computer** - ohne Cloud, ohne Datenweitergabe, mit voller Kontrolle.

**Key Features:**
- 🔒 **100% Lokal** - Keine Internetverbindung nach der Installation
- 🆓 **Kostenlos** - Open-Source, keine Abos, keine versteckten Kosten
- ⚡ **Schnell** - GPU-beschleunigt (NVIDIA CUDA)
- 🎨 **Modern** - Holographische UI inspiriert von Iron Man
- 🔌 **Erweiterbar** - Plugin-System für zusätzliche Features

---

### Ist JARVIS wirklich 100% lokal?

**Ja!** Nach der Installation benötigt JARVIS **keine Internetverbindung** mehr.

**Was lokal läuft:**
- ✅ AI-Modelle (GGUF Dateien auf deiner Festplatte)
- ✅ Alle Chats und Konversationen
- ✅ Plugins (außer Weather-Plugin braucht API)
- ✅ Frontend & Backend Server

**Was Internet braucht:**
- 🌐 **Initiale Installation** - Python packages, npm modules
- 🌐 **Model-Downloads** - GGUF Dateien von HuggingFace
- 🌐 **Plugin-APIs** - Weather Plugin braucht OpenWeatherMap

**Nach Setup:** Du kannst JARVIS **komplett offline** nutzen!

---

### Kostet JARVIS etwas?

**Nein! JARVIS ist 100% kostenlos.**

- ✅ **Open-Source** - Apache 2.0 Lizenz
- ✅ **Keine Abos** - Kein monatlicher/jährlicher Preis
- ✅ **Keine API-Kosten** - Kein OpenAI/Anthropic API nötig
- ✅ **Keine versteckten Kosten** - Alles gratis

**Optional kostenpflichtig:**
- 💵 **Weather Plugin** - OpenWeatherMap API (~0€ für Free Tier)
- 💵 **Stromkosten** - GPU-Nutzung erhöht Energieverbrauch minimal

---

### Welche Betriebssysteme werden unterstützt?

**Offizielle Unterstützung:**
- ✅ **Windows 10/11** - Vollständig getestet
- ✅ **Linux** - Ubuntu 20.04+, Debian, Fedora, Arch
- ✅ **macOS** - macOS 11+ (Big Sur und neuer)

**Voraussetzungen:**
- Python 3.11+
- Node.js 18+
- Git

---

## Installation & Setup

### Wie installiere ich JARVIS?

**Quick Start (empfohlen):**

```bash
# 1. Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. llama.cpp Setup (automatisch!)
cd backend && python setup_llama.py && cd ..

# 4. Frontend Setup
cd frontend && npm install && cd ..

# 5. JARVIS starten
python main.py
```

**Ausführliche Anleitung:** [README.md](./README.md#installation--start)

---

### Brauche ich eine GPU?

**Nein, aber empfohlen!**

**Ohne GPU (CPU only):**
- ✅ Funktioniert einwandfrei
- ⚡ 5-10 tokens/Sekunde
- 💻 Nutze kleine Modelle (Llama 3.2 3B, Phi-3 Mini)
- 🐌 Langsam bei großen Modellen (7B+)

**Mit NVIDIA GPU (CUDA):**
- ✅ Deutlich schneller
- ⚡⚡⚡ 30-50 tokens/Sekunde
- 🚀 Große Modelle (7B-13B) laufen flüssig
- 🎮 Gaming-GPUs (RTX 3060+) perfekt

**Empfehlung:** CPU reicht für Chat, GPU für Power-User!

---

### Welche GPU wird unterstützt?

| GPU-Typ | Support | Setup | Performance |
|---------|---------|-------|-------------|
| **NVIDIA (CUDA)** | ✅ Voll | Automatisch | ⚡⚡⚡ 30-50 tok/s |
| **AMD (ROCm)** | ⚠️ Experimentell | Komplex | ⚡⚡ 25-40 tok/s |
| **Intel Arc** | 🔄 Geplant | v1.2.0 | ⚡⚡ 20-35 tok/s |
| **Apple Silicon (Metal)** | 🔄 Geplant | v1.3.0 | ⚡⚡ 25-40 tok/s |
| **CPU (x64 AVX2)** | ✅ Voll | Automatisch | ⚡ 5-10 tok/s |

**AMD GPU Nutzer:** ROCm Installation ist sehr komplex - **nutze CPU-Version!**

**NVIDIA Empfehlung:**
- Minimum: GTX 1660 (6GB VRAM)
- Empfohlen: RTX 3060 (12GB VRAM)
- Optimal: RTX 4070+ (12GB+ VRAM)

---

### Wie viel RAM brauche ich?

**Minimum: 8 GB**
- ✅ Kleine Modelle (3B) - 4-6 GB RAM
- ⚠️ Mittlere Modelle (7B) - knapp, kann swappen
- ❌ Große Modelle (13B+) - nicht nutzbar

**Empfohlen: 16 GB**
- ✅ Kleine Modelle (3B) - perfekt
- ✅ Mittlere Modelle (7B) - gut
- ✅ Große Modelle (13B) - möglich

**Optimal: 32 GB+**
- ✅ Alle Modelle problemlos
- ✅ Mehrere Modelle gleichzeitig
- ✅ Großer Chat-Kontext (32K tokens)

---

### Wie viel Speicherplatz wird benötigt?

**Basis-Installation: ~2 GB**
- Python packages: ~500 MB
- Node modules: ~800 MB
- JARVIS Code: ~200 MB
- Logs/Config: ~50 MB

**Pro Modell: 2-15 GB**
- Llama 3.2 3B: ~2.0 GB
- Qwen 2.5 7B: ~5.2 GB
- Mistral 7B: ~7.5 GB
- Llama 3.1 70B: ~40 GB (falls geplant)

**Empfohlener freier Speicher: 20 GB+**

---

## Modelle

### Welche AI-Modelle kann ich nutzen?

**Pre-configured (7 Modelle):**

1. **Llama 3.2 3B** - Klein, schnell, Chat
2. **Phi-3 Mini** - Kompakt, effizient
3. **Qwen 2.5 7B** - Vielseitig, multilingual
4. **Mistral 7B Nemo** - Code, technisch
5. **DeepSeek Coder 6.7B** - Programmierung
6. **DeepSeek R1 8B** - Advanced Reasoning
7. **Llama 3.1 8B** - General Purpose

**Custom Models:**
- ✅ Alle GGUF-kompatiblen Modelle von HuggingFace
- ✅ Eigene Fine-Tunes (GGUF Format)
- ✅ Ollama Model Library (via Import)

Siehe: [Model List](./docs/MODEL_LIST.md)

---

### Wie downloade ich ein Modell?

**Via UI (empfohlen):**

1. JARVIS starten: `python main.py`
2. Browser: http://localhost:5050
3. **Models Tab** öffnen
4. Modell wählen → **Download** klicken
5. Quantization wählen (Q4_K_M empfohlen)
6. Warten (2-15 GB Download)
7. **Load** klicken zum Aktivieren

**Via CLI (fortgeschritten):**

```bash
python core/model_downloader.py --model llama-3.2-3b --quantization Q4_K_M
```

---

### Welches Modell ist am schnellsten?

**Für CPU:**
1. 🥇 **Llama 3.2 3B** - 8-12 tok/s
2. 🥈 **Phi-3 Mini** - 7-10 tok/s
3. 🥉 **Qwen 2.5 7B** - 5-8 tok/s

**Für GPU (NVIDIA):**
1. 🥇 **Llama 3.2 3B** - 50-80 tok/s
2. 🥈 **Phi-3 Mini** - 45-70 tok/s
3. 🥉 **Qwen 2.5 7B** - 35-50 tok/s

**Empfehlung:** Starte mit **Llama 3.2 3B** - beste Balance!

---

### Kann ich eigene Modelle nutzen?

**Ja!** Jedes GGUF-Format Modell funktioniert.

**So geht's:**

1. GGUF-Datei herunterladen (HuggingFace)
2. In `models/llm/` kopieren
3. In UI: Models Tab → "Add Custom Model"
4. Pfad auswählen → Laden

**Konvertierung (falls nötig):**
```bash
# PyTorch → GGUF
python llama.cpp/convert.py /path/to/model
```

Siehe: [Custom Models Guide](./docs/CUSTOM_MODELS.md)

---

### Wie groß sind die Modelle?

| Modell | Unquantized | Q4_K_M | Q5_K_M | Q8_0 |
|--------|-------------|--------|--------|------|
| **3B** | ~6 GB | ~2.0 GB | ~2.5 GB | ~3.5 GB |
| **7B** | ~14 GB | ~4.5 GB | ~5.5 GB | ~7.5 GB |
| **13B** | ~26 GB | ~8 GB | ~10 GB | ~14 GB |
| **70B** | ~140 GB | ~40 GB | ~50 GB | ~75 GB |

**Empfehlung:** Q4_K_M = beste Kompression bei guter Qualität

---

## Performance

### Wie schnell ist JARVIS?

**Benchmark (Tokens pro Sekunde):**

| Hardware | Llama 3B | Qwen 7B | Mistral 7B |
|----------|----------|---------|------------|
| **RTX 4090** | 80-100 | 50-70 | 45-65 |
| **RTX 4070** | 60-80 | 40-55 | 35-50 |
| **RTX 3060** | 40-60 | 30-45 | 25-40 |
| **AMD Ryzen 9** | 10-15 | 6-10 | 5-8 |
| **Intel i7** | 8-12 | 5-8 | 4-7 |

**Zum Vergleich:**
- ChatGPT (Cloud): ~20-40 tok/s
- Claude (Cloud): ~25-45 tok/s
- JARVIS (RTX 3060): ~30-45 tok/s ✅

---

### Warum ist mein JARVIS langsam?

**Mögliche Gründe:**

1. **Zu großes Modell**
   - 🔧 Lösung: Nutze kleineres Modell (3B statt 7B)

2. **CPU statt GPU**
   - 🔧 Lösung: GPU aktivieren (CUDA setup)

3. **Zu wenig RAM**
   - 🔧 Lösung: Kleineres Modell oder RAM upgrade

4. **Langer Chat-Kontext**
   - 🔧 Lösung: Chat löschen oder Context Window reduzieren

5. **Hintergrund-Apps**
   - 🔧 Lösung: Andere GPU-Apps schließen

---

### Kann ich die Performance verbessern?

**Ja! Mehrere Möglichkeiten:**

**1. GPU nutzen (größter Impact!)**
```bash
cd backend
python setup_llama.py  # Wähle CUDA
```

**2. Kleineres Modell wählen**
- Llama 3.2 3B statt Qwen 7B
- Q4 statt Q8 Quantization

**3. Context Window reduzieren**
- Settings → Max Context: 2048 statt 8192

**4. Batch Size erhöhen**
- Settings → Batch Size: 512 (GPU) / 128 (CPU)

**5. Thread Count optimieren**
- CPU: Nutze Kernel/2 (z.B. 8 Kerne = 4 Threads)

Siehe: [Performance Guide](./docs/PERFORMANCE.md)

---

### AMD GPU - Warum so langsam?

**ROCm ist komplex und instabil.**

**Probleme:**
- ❌ Komplizierte Installation (~2-3h)
- ❌ Häufige Fehler und Crashes
- ❌ Schlechte Treiber-Unterstützung
- ❌ Nur bestimmte AMD GPUs unterstützt
- ❌ Windows ROCm = experimental

**Empfehlung: Nutze CPU-Version!**

CPU (5-10 tok/s) ist **stabiler** als ROCm mit Problemen.

**Zukunft:** Intel Arc Support (v1.2.0) wird besser sein.

---

## Features & Nutzung

### Kann JARVIS Bilder generieren?

**Aktuell: Nein.**

**Geplant für v2.0+ (Q2 2026):**
- Stable Diffusion Integration
- Lokale Image Generation
- Text-to-Image & Image-to-Image

**Workaround:** Nutze externes Tool (Automatic1111, ComfyUI)

---

### Funktioniert Spracherkennung?

**Teilweise.**

**Was funktioniert:**
- ✅ Voice Input (Web Speech API)
- ✅ Browser-basiert (Chrome, Edge)
- ✅ Visualisierung in UI

**Was NICHT funktioniert:**
- ❌ Voice Output (TTS) - geplant v1.2.0
- ❌ Offline Voice Input - geplant v1.2.0 (Whisper)

**Roadmap:**
- v1.2.0: Whisper (Speech-to-Text) + XTTS (Text-to-Speech)

---

### Kann JARVIS im Internet suchen?

**Aktuell: Nein.**

**Geplant:**
- v1.2.0: Web Search Plugin (Google/DuckDuckGo API)
- v2.0.0: Integrated Web Browsing

**Workaround:** Kopiere Infos manuell in Chat

---

### Wie aktiviere ich Plugins?

**So geht's:**

1. JARVIS starten
2. **Plugins Tab** öffnen
3. Plugin auswählen (z.B. Weather)
4. **"Aktivieren"** klicken
5. Falls API-Key nötig → Modal öffnet sich
6. API-Key eingeben → Speichern
7. Plugin ist aktiv! ✅

**Verfügbare Plugins:**
- ☀️ Weather (braucht OpenWeatherMap API)
- ⏰ Timer
- 📝 Notes
- 📰 News

**Eigene Plugins:** Siehe [Plugin Development](./docs/PLUGIN_DEV.md)

---

### Kann ich meinen Chat-Verlauf speichern?

**Ja! Automatisch.**

**Wo gespeichert:**
- `data/conversations/` - Alle Chats als JSON
- `data/memory/` - Kontext und Erinnerungen

**Export:**
- Settings → Export Chat (als JSON/TXT)

**Löschen:**
- Chat Tab → "Clear History"
- Oder manuell: `data/conversations/` löschen

---

## Troubleshooting

### JARVIS startet nicht - was tun?

**Checklist:**

1. **Python Version prüfen:**
```bash
python --version  # Muss 3.11+ sein
```

2. **Dependencies installiert?**
```bash
pip install -r requirements.txt
cd frontend && npm install
```

3. **Ports frei?**
```bash
# Windows
netstat -ano | findstr :5050
netstat -ano | findstr :5050

# Linux/Mac
lsof -i :5050
lsof -i :5050
```

4. **Logs checken:**
```bash
cat logs/backend.log
cat logs/frontend.log
```

5. **Neustart:**
```bash
python main.py
```

---

### Port bereits belegt - wie beheben?

**Lösung 1: Prozess beenden**

```bash
# Windows
netstat -ano | findstr :5050
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5050
kill -9 <PID>
```

**Lösung 2: Port ändern**

Bearbeite `backend/.env`:
```env
BACKEND_PORT=5051  # Statt 5050
FRONTEND_PORT=5001  # Statt 5000
```

---

### Module not found Error

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Lösung:**
```bash
# Backend Dependencies
cd backend
pip install -r requirements.txt

# Frontend Dependencies  
cd frontend
npm install

# Core Dependencies
cd ..
pip install -r requirements.txt
```

---

### GPU wird nicht erkannt

**Checklist:**

1. **NVIDIA GPU vorhanden?**
```bash
nvidia-smi  # Zeigt GPU Info
```

2. **CUDA installiert?**
```bash
nvcc --version  # CUDA Compiler
```

3. **llama.cpp mit CUDA?**
```bash
cd backend
python setup_llama.py  # Neu installieren
```

4. **Treiber aktuell?**
- NVIDIA: GeForce Experience updaten
- Minimum: CUDA 11.8 Treiber

---

### Frontend lädt nicht

**Mögliche Ursachen:**

**1. Backend nicht gestartet:**
```bash
# Backend manuell starten
cd backend
python main.py
```

**2. Port-Konflikt:**
- Siehe: [Port bereits belegt](#port-bereits-belegt---wie-beheben)

**3. Browser-Cache:**
- Strg+F5 (Hard Refresh)
- Oder: Inkognito-Modus testen

**4. npm Build Fehler:**
```bash
cd frontend
npm run build
```

---

## Sicherheit & Privatsphäre

### Werden meine Daten gesammelt?

**Nein! Absolut nicht.**

**JARVIS sammelt:**
- ❌ Keine Telemetrie
- ❌ Keine Analytics
- ❌ Keine Crash Reports
- ❌ Keine Chat-Logs an Server
- ❌ Keine Nutzungsstatistiken

**Alles bleibt lokal:**
- ✅ Chats: `data/conversations/`
- ✅ Config: `config/settings.json`
- ✅ Logs: `logs/`

**100% Privacy by Design** 🔒

---

### Ist JARVIS sicher?

**Ja! Mehrere Sicherheitsebenen:**

**Code-Level:**
- ✅ **Open-Source** - Code ist einsehbar
- ✅ **Keine Third-Party Tracking**
- ✅ **Input Validation** - Schutz vor Injection
- ✅ **API Key Encryption** - Sichere Speicherung

**System-Level:**
- ✅ **Local-Only** - Keine Cloud-Verbindung
- ✅ **Sandboxed Plugins** - Isolierte Ausführung
- ✅ **No Sudo Required** - Läuft als User

**Updates:**
- ✅ **Dependabot** - Automatische Security Updates
- ✅ **CI/CD Scans** - Code Quality Checks

Siehe: [SECURITY.md](./SECURITY.md)

---

### Wo werden Chat-Daten gespeichert?

**Lokale Ordner:**

```
JarvisCore/
└── data/
    ├── conversations/     # Alle Chats (JSON)
    ├── memory/             # Kontext & Erinnerungen
    └── user_data/          # Notizen, Einstellungen
```

**Format:** JSON (plain text, nicht verschlüsselt)

**Löschen:**
```bash
rm -rf data/conversations/*  # Alle Chats löschen
```

**Backup:**
```bash
cp -r data/ backup_$(date +%Y%m%d)/
```

---

### Kann ich Telemetrie deaktivieren?

**Nicht nötig - es gibt keine!**

JARVIS hat **keinerlei Telemetrie** eingebaut.

**Proof:** Suche im Code nach:
```bash
grep -r "analytics" .
grep -r "telemetry" .
grep -r "tracking" .
# = Keine Treffer außer Kommentare
```

**Network Activity:**
- Nach Installation: 0 Requests an externe Server
- Nur lokal: localhost:5050

---

## Entwicklung & Community

### Kann ich zu JARVIS beitragen?

**Ja! Contributions sind willkommen! 🤝**

**Wie:**

1. **Fork** das Repository
2. **Branch** erstellen: `feature/meine-idee`
3. **Coden** + Tests schreiben
4. **Commit**: `git commit -m 'feat: Meine Idee'`
5. **Push**: `git push origin feature/meine-idee`
6. **Pull Request** erstellen

**Was wird gebraucht:**
- 🐛 Bug Fixes
- ✨ Neue Features
- 📚 Dokumentation
- 🌐 Übersetzungen
- 🔌 Plugins
- 🎨 UI/UX Improvements

Siehe: [CONTRIBUTING.md](./CONTRIBUTING.md)

---

### Wie melde ich Bugs?

**GitHub Issues:**

1. Gehe zu: [Issues](https://github.com/Lautloserspieler/JarvisCore/issues)
2. Klick "New Issue"
3. Wähle Template: "Bug Report"
4. Fülle aus:
   - Was passiert?
   - Was sollte passieren?
   - Schritte zum Reproduzieren
   - Logs (falls vorhanden)
   - System Info (OS, Python, GPU)

**Oder:** Direkter Link zum [Bug Report](https://github.com/Lautloserspieler/JarvisCore/issues/new?template=bug_report.md)

---

### Gibt es einen Discord/Community?

**Geplant für nach Launch!**

**Aktuell:**
- 🐛 **GitHub Issues** - Bugs & Feature Requests
- 💬 **GitHub Discussions** - Community Q&A (kommt bald)

**Bald:**
- 💬 **Discord Server** - Community Chat (Q1 2026)
- 🐦 **Twitter/X** - Updates & News
- 📧 **Newsletter** - Release Notes

Stay tuned! 🚀

---

### Roadmap - Was kommt als nächstes?

**v1.2.0 (Q1 2026):**
- 🎤 Voice Input (Whisper)
- 🔊 Voice Output (XTTS v2)
- 🖥️ Desktop App (Wails)
- 🐳 Docker Support
- 🔌 Mehr Plugins

**v2.0.0 (Q2 2026):**
- 📚 RAG System (Dokument-Suche)
- 🗃️ Vector Database
- 👥 Multi-User Support
- ☁️ Cloud Deployment Option

**v3.0+ (2027+):**
- 🤖 Multi-Agent System
- 📸 Image Generation (Stable Diffusion)
- 🔍 Web Browsing
- 🎬 Video Analysis

Siehe: [CHANGELOG.md](./CHANGELOG.md#unreleased---future-plans)

---

## 💬 Weitere Hilfe

**Docs:**
- [📚 README](./README.md)
- [📖 Documentation](./docs/)
- [🔒 Security](./SECURITY.md)
- [🤝 Contributing](./CONTRIBUTING.md)

**Support:**
- [🐛 GitHub Issues](https://github.com/Lautloserspieler/JarvisCore/issues)
- [💬 Discussions](https://github.com/Lautloserspieler/JarvisCore/discussions) (coming soon)

**Contact:**
- 📧 Email: security@jarviscore.de (Security only)
- 🐦 Twitter: @JarvisCore (coming soon)

---

<div align="center">

**Made with ❤️ by Lautloserspieler**

*"Sometimes you gotta run before you can walk."* - Tony Stark

[⭐ Star on GitHub](https://github.com/Lautloserspieler/JarvisCore) | [🐛 Report Bug](https://github.com/Lautloserspieler/JarvisCore/issues) | [💡 Request Feature](https://github.com/Lautloserspieler/JarvisCore/issues)

</div>
