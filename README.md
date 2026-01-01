# 🤖 JARVIS Core System

<div align="center">

**Just A Rather Very Intelligent System**

[![CI/CD](https://github.com/Lautloserspieler/JarvisCore/actions/workflows/ci.yml/badge.svg)](https://github.com/Lautloserspieler/JarvisCore/actions/workflows/ci.yml)
[![Release](https://github.com/Lautloserspieler/JarvisCore/actions/workflows/release.yml/badge.svg)](https://github.com/Lautloserspieler/JarvisCore/actions/workflows/release.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-cyan.svg)](https://golang.org)
[![Vue](https://img.shields.io/badge/Vue-3.5+-green.svg)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF-orange.svg)](https://github.com/ggerganov/llama.cpp)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Lautloserspieler/JarvisCore?style=social)](https://github.com/Lautloserspieler/JarvisCore)

Ein moderner KI-Assistent mit holographischer UI und **vollständig lokaler llama.cpp Inferenz**

[🇬🇧 English Version](./README_GB.md) | [📚 Docs](./docs/) | [❓ FAQ](./FAQ.md) | [🔒 Security](./SECURITY.md)

</div>

---

## 🚀 Quickstart

- **Schnellstart (manuell)**: [README_QUICKSTART.md](./README_QUICKSTART.md)
- **Fehlerbehebung**: [FAQ](./FAQ.md)

## ✨ Features

### 🧠 KI-Engine
- ✅ **llama.cpp Lokale Inferenz** - Vollständig implementiert und funktionsfähig!
- ✅ **Automatische GPU-Erkennung** - NVIDIA CUDA Support
- ✅ **7 GGUF-Modelle** - Mistral, Qwen, DeepSeek, Llama und mehr
- ✅ **Chat mit History** - Kontext-bewusste Konversationen
- ✅ **Bis 32K Context** - Lange Konversationen möglich
- ✅ **System-Prompts** - JARVIS-Persönlichkeit konfigurierbar

### 🎙️ Voice Control (v1.2.0 geplant)
> ⚠️ **Hinweis:** Voice-Features (TTS/Whisper) sind aktuell **nicht Teil des Releases**. Die folgenden Punkte sind Roadmap/Entwicklung.
- 🔄 **Voice Input** - Whisper-basierte Spracherkennung (in Entwicklung)
- 🔄 **Voice Output** - XTTS v2 mit vorgeklonten JARVIS-Stimmen (in Entwicklung)
- ✅ **Vorgeklonte Voice-Samples** - Deutsch & Englisch (DE/EN v2.2)
- ✅ **Automatische Sprach-Erkennung** - Deutsch/Englisch Support
- ⚡ **Keine langwierige Berechnung** - Voice Samples vorkonfiguriert

### 🎨 Frontend (Vue 3)
- ✅ **Holographische UI** - Beeindruckende JARVIS-inspirierte Benutzeroberfläche
- ✅ **Echtzeit-Chat** - WebSocket-basierte Live-Kommunikation
- ✅ **Sprach-Interface** - Voice-Input mit visueller Rückmeldung
- ✅ **Multi-Tab Navigation** - Chat, Dashboard, Memory, Models, Settings
- ✅ **Model-Management** - Download und Verwaltung von KI-Modellen
- ✅ **Plugin System** - Wetter, Timer, Notizen, News uvm.
- ✅ **Responsive Design** - Funktioniert auf allen Bildschirmgrößen
- ✅ **Dark Theme** - Cyberpunk-Ästhetik mit leuchtenden Effekten

### 🚀 Backend (Python + FastAPI)
- ✅ **FastAPI Server** - Hochperformanter Python Backend
- ✅ **llama.cpp Integration** - Native GGUF-Model-Inferenz
- ✅ **WebSocket Support** - Echtzeitkommunikation
- ✅ **RESTful API** - Vollständige REST-Endpunkte
- ✅ **Plugin System** - Erweiterbare Architektur
- ✅ **Memory Storage** - Konversationshistorie & Kontext

---

## 🎙️ Voice Samples - Sofort einsatzbereit!

JarvisCore enthält **vorgeklonte JARVIS-Voice-Samples**, die keine langwierige Berechnung erfordern:
> ⚠️ **Hinweis:** Die Voice-Pipeline selbst ist im aktuellen Release **noch nicht enthalten**.

### ✨ Vorteile der Vorgeklonten Stimmen

| Feature | Vorteil |
|---------|----------|
| ⚡ **Zeitersparnis** | 5-7 Minuten schneller beim ersten Start |
| 💻 **Schwache PCs** | Funktioniert auch auf alten/schwachen Computern |
| 🎯 **Sofort einsatzbereit** | Einfach klonen und starten - keine Wartezeit |
| 🌍 **Multilingualität** | Deutsch & Englisch Support (v2.2 optimiert) |
| 🔊 **Natürlicher Klang** | Hochwertig geclonte JARVIS-Stimmen |

### 📦 Enthalten

- **`Jarvis_DE.wav`** - Deutsche JARVIS-Stimme (natürlich, optimiert v2.2)
- **`Jarvis_EN.wav`** - Englische JARVIS-Stimme (natürlich, optimiert v2.2)

**Speicherort:** `models/tts/voices/`

Siehe [models/tts/voices/README.md](./models/tts/voices/README.md) für technische Details.

---

## 💻 Voraussetzungen

- **Python 3.11+** - [python.org](https://python.org)
- **Node.js 18+** - [nodejs.org](https://nodejs.org)
- **Git** - [git-scm.com](https://git-scm.com)
- **(Optional)** NVIDIA GPU mit CUDA für beschleunigte Inferenz

---

## 🚀 Installation & Start

### 📦 Manuelle Installation (Empfohlen)

#### Option A: Neue Methode (v1.2.0-dev) - Empfohlen

```bash
# Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Installiere JarvisCore mit essentiellen Features
pip install -e ".[all]"

# Installiere Frontend Dependencies
cd frontend
npm install
cd ..

# Starte JARVIS (Web-Modus)
jarviscore web
```

Danach öffnet sich automatisch: **http://localhost:5050**

#### Option B: Mit GPU Support (NVIDIA CUDA)

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Mit CUDA Support
pip install -e ".[tts,cuda]"

cd frontend && npm install && cd ..
jarviscore web
```

#### Option C: Development Setup (Mit Testing Tools)

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Mit allen Dev-Tools
pip install -e ".[dev,tts,cuda]"

cd frontend && npm install && cd ..

# Tests
pytest

# Start (Web-Modus)
jarviscore web
```

#### Option D: Alte Methode (v1.1.0 - Legacy, wird entfernt)

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

pip install -r requirements.txt  # Legacy
cd backend && python setup_llama.py && cd ..
cd frontend && npm install && cd ..
python scripts/start_web.py
```

> 💡 **Tipp:** Neue Methoden sind kürzer und übersichtlicher!

---

## 🔄 Start-Modi (Web/Desk/Prod)

**Welche Variante ist richtig?**

- **Web**: Backend + Frontend (Vite). Ideal für Entwicklung/Testing im Browser.
- **Desktop**: Backend + Wails Dev Mode. Für UI-Entwicklung am Desktop.
- **Prod**: Backend + Desktop-Binary. Für lokale Produktion/Demo ohne Dev-Tools.

**Kurzbeispiele:**

```bash
# Web UI im Browser
jarviscore web

# Desktop UI (Dev)
jarviscore desktop

# Desktop UI (Production Binary)
jarviscore prod
```

Alternativ kannst du die Skripte direkt nutzen:

```bash
python scripts/start_web.py
python scripts/start_desktop.py
python scripts/start_production.py
```

## 🔄 CLI Commands (NEU in v1.2.0-dev)

```bash
# Web Mode (Development) - EMPFOHLEN
jarviscore web
# Öffnet automatisch http://localhost:5050

# Desktop Mode (Wails Dev)
jarviscore desktop

# Production Mode (Desktop Binary)
jarviscore prod

# Hilfe anzeigen
jarviscore --help
```

---

## 📦 Dependency Management (Neu in v1.2.0-dev)

### Old Way ❌ (Legacy, wird entfernt)
```bash
pip install -r requirements.txt
# Problem: Alle Dependencies, auch wenn nicht nötig
# Hinweis: requirements*.txt sind Legacy und werden schrittweise entfernt.
```

### New Way ✅
```bash
# Wähle genau, was du brauchst!
pip install -e "."              # Minimal
pip install -e ".[tts]"         # + Text-to-Speech
pip install -e ".[cuda]"        # + GPU Support (NVIDIA)
pip install -e ".[dev]"         # + Development Tools
pip install -e ".[ci]"          # + CI/CD Tools
pip install -e ".[all]"         # Alles zusammen

# Kombinationen möglich
pip install -e ".[dev,tts,cuda]"
```

### Verfügbare Extras

| Extra | Inhalt | Größe |
|-------|--------|-------|
| `tts` | XTTS v2 Voice Synthesis | ~500 MB |
| `cuda` | PyTorch with CUDA (NVIDIA) | ~2 GB |
| `dev` | Testing, Linting, Documentation | ~300 MB |
| `ci` | CI/CD Tools | ~100 MB |
| `all` | Alles zusammen | ~3 GB |

### 📚 Mehr Infos

Siehe [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) für vollständige v1.1 → v1.2 Migration

---

## 🌐 Zugriffspunkte

Nach dem Start erreichst du:

- 🎨 **Frontend UI**: http://localhost:5050
- 🔧 **Backend API**: http://localhost:5050
- 📚 **API-Dokumentation**: http://localhost:5050/docs
- 🔌 **WebSocket**: ws://localhost:5050/ws

---

## 🧠 llama.cpp Lokale Inferenz

**NEU in v1.1.0** - Production-ready mit automatischer GPU-Erkennung!

### Features
- 🚀 **GPU-Acceleration** - CUDA automatisch erkannt
- 🎯 **GGUF-Support** - Alle llama.cpp-kompatiblen Modelle
- 💬 **Chat-Modus** - History mit bis zu 32K Context
- ⚡ **Performance** - 30-50 tokens/sec (NVIDIA), 5-10 tokens/sec (CPU)

### GPU Support

| GPU-Typ | Support | Installation | Performance | Empfehlung |
|---------|---------|--------------|-------------|------------|
| **NVIDIA** | ✅ CUDA | Automatisch | ⚡⚡⚡ 30-50 tok/s | ⭐ Empfohlen |
| **AMD** | ⚠️ ROCm | Komplex | ⚡⚡⚡ 25-40 tok/s |In Entwicklung 👉 **Nutze CPU-Version** |
| **Intel Arc** | 🔄 oneAPI | Coming Soon | ⚡⚡ 20-35 tok/s | In Entwicklung |
| **CPU** | ✅ Standard | Automatisch | ⚡ 5-10 tok/s | ✅ Funktioniert |

#### 💡 Hinweis für AMD GPU Nutzer:

**ROCm Setup ist komplex und erfordert:**
- Visual Studio Build Tools
- ROCm SDK Installation (~5 GB)
- Spezifische Treiber-Versionen
- Mehrere Neustarts
- Komplizierte Pfad-Konfiguration

**👉 Empfehlung: Nutze die CPU-Version!**
```bash
cd backend && python setup_llama.py
# Wähle Option 3: CPU-Version
```

**Vorteile CPU-Version:**
- ✅ Sofort einsatzbereit
- ✅ Keine komplexe Konfiguration
- ✅ Stabil und zuverlässig
- ✅ 5-10 tokens/sec (ausreichend für Chat)
- ✅ Kleinere Modelle (3B) laufen flüssig

### Verfügbare Modelle

| Model | Größe | Use Case | CPU Performance |
|-------|-------|----------|----------------|
| **Llama 3.2 3B** | ~2.0 GB | Klein, schnell | ⚡⚡⚡ 8-12 tok/s |
| **Phi-3 Mini** | ~2.3 GB | Kompakt, Chat | ⚡⚡⚡ 7-10 tok/s |
| **Qwen 2.5 7B** | ~5.2 GB | Vielseitig | ⚡⚡ 5-8 tok/s |
| **Mistral 7B Nemo** | ~7.5 GB | Code, technisch | ⚡⚡ 4-7 tok/s |
| **DeepSeek R1 8B** | ~6.9 GB | Analysen | ⚡ 3-6 tok/s |

**👉 Empfehlung für CPU: Nutze Llama 3.2 3B oder Phi-3 Mini für beste Performance!**

---

## 🔧 Manuelle llama.cpp Installation

Falls das automatische Script nicht funktioniert:

### NVIDIA GPU (CUDA)

```bash
cd backend
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir --no-binary llama-cpp-python
```

### CPU Only (Empfohlen für AMD)

```bash
cd backend
pip uninstall llama-cpp-python -y
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### AMD GPU (ROCm) - Nur für Experten

⚠️ **Achtung:** Sehr komplex! Nur für erfahrene Nutzer empfohlen.

1. **ROCm installieren** (~5 GB): https://rocm.docs.amd.com/
2. **Visual Studio Build Tools** installieren
3. **Neustart erforderlich**
4. **Dann:**
```bash
cd backend
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DLLAMA_HIPBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir --no-binary llama-cpp-python
```

---

## 📦 Model-Download-System

JARVIS Core nutzt ein **Ollama-inspiriertes Download-System**:

### Features
- 🔄 **Multi-Registry-Support** - HuggingFace, Ollama, Custom URLs
- 📦 **Resume-Downloads** - Unterbrochene Downloads fortsetzen
- ✅ **SHA256-Verifizierung** - Automatische Integritätsprüfung
- 📊 **Live-Progress** - Speed, ETA, Fortschrittsbalken
- 🔐 **HuggingFace Token** - Support für private Repos

### Models verwalten

1. **JARVIS starten**: `jarviscore web` oder `python scripts/start_web.py`
2. **Web-UI öffnen**: http://localhost:5050
3. **Models-Tab**: Navigation zur Model-Verwaltung
4. **Model downloaden**: Klick "Download" → Wähle Quantization
5. **Model laden**: Klick "Load" bei heruntergeladenem Modell
6. **Chat starten**: Gehe zu "Chat" Tab und schreibe

Weitere Infos: [docs/LLM_DOWNLOAD_SYSTEM.md](./docs/LLM_DOWNLOAD_SYSTEM.md)

---

## 🔌 Plugin System

**NEU in v1.1.0** - Erweiterbare Plugin-Architektur!

### Verfügbare Plugins

| Plugin | Beschreibung | API-Key |
|--------|--------------|----------|
| ☀️ **Weather** | OpenWeatherMap Integration | ✅ Erforderlich |
| ⏰ **Timer** | Timer & Erinnerungen | ❌ Nicht nötig |
| 📝 **Notes** | Schnelle Notizen | ❌ Nicht nötig |
| 📰 **News** | RSS News Feeds | ❌ Nicht nötig |

### Plugin aktivieren

1. Öffne **Plugins Tab** in der UI
2. Klicke **"Aktivieren"** beim gewünschten Plugin
3. Falls API-Key nötig → Modal öffnet sich automatisch
4. Gib API-Key ein → Wird sicher in `config/settings.json` gespeichert
5. Plugin ist aktiviert! ✅

---

## 📁 Projektstruktur

```
JarvisCore/
├── pyproject.toml          # Centralized Configuration
├── main.py                 # Unified Launcher
├── requirements.txt        # Legacy (deprecated, wird entfernt)
├── jarviscore/             # CLI Package
│   ├── __init__.py
│   └── cli.py
├── scripts/                # Launcher Scripts
│   ├── start_web.py
│   ├── start_desktop.py
│   ├── start_production.py
│   └── start_jarvis.py     # Legacy Wrapper
├── core/                   # Core Python Modules
│   ├── llama_inference.py # llama.cpp Engine
│   ├── model_downloader.py
│   └── ...
├── backend/                # Python/FastAPI Backend
│   ├── main.py
│   ├── setup_llama.py     # Auto GPU Setup
│   ├── plugin_manager.py
│   └── requirements*.txt  # Legacy (deprecated, wird entfernt)
├── frontend/               # Vue 3 Frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── plugins/                # Plugin System
│   ├── weather_plugin.py
│   ├── timer_plugin.py
│   └── ...
├── models/                 # Models
│   ├── llm/               # GGUF LLM Models
│   └── tts/               # Voice Samples
│       └── voices/        # Pre-cloned JARVIS voices
├── config/                 # Configuration
├── data/                   # User Data
├── docs/                   # Documentation
└── README.md
```

---

## 🐛 Troubleshooting

### Problem: GPU nicht erkannt

```bash
# GPU-Status prüfen
nvidia-smi  # NVIDIA

# llama.cpp neu installieren
cd backend
python setup_llama.py
```

### Problem: Port bereits belegt

```bash
# Windows
netstat -ano | findstr :5050

# Linux/Mac
lsof -i :5050
```

### Problem: Module nicht gefunden

```bash
# Neue Methode
pip install -e ".[tts]"

# Oder alte Methode (Legacy)
pip install -r requirements.txt
cd frontend && npm install
```

### Problem: AMD GPU - ROCm Installation zu komplex

**Lösung: Nutze CPU-Version!**
```bash
cd backend
python setup_llama.py
# Wähle Option 3
```

Weitere Hilfe: [❓ FAQ](./FAQ.md) | [📚 Troubleshooting](./docs/TROUBLESHOOTING.md) | [📋 Migration Guide](./MIGRATION_GUIDE.md)

---

## ⚙️ Konfiguration (.env)

Die vollständige Liste aller Umgebungsvariablen findest du in der Vorlage: [`.env.example`](./.env.example).
Eine kurze Einordnung, welche Variablen wofür gedacht sind (LLM, TTS, Plugins, Feature-Flags), gibt es hier:
[📘 Konfiguration & Env-Variablen](./docs/CONFIGURATION.md).

---

## 🎯 Roadmap

### ✅ v1.1.0 (Current) - Dezember 2025
- ✅ Vue 3 Frontend
- ✅ Production-ready llama.cpp
- ✅ Automatische GPU-Erkennung
- ✅ Plugin System mit API-Key Management
- ✅ Model Download System
- ✅ Vorgeklonte Voice Samples (DE/EN v2.2)

### 🔄 v1.2.0 (Q1 2026) - NEW!
- ✅ **Consolidated Dependency Management** (pyproject.toml)
- ✅ **CLI Entry Points** (jarviscore web/desktop/prod)
- ✅ **Enhanced Configuration** (50+ settings in .env.example)
- ✅ **GPU Selection** (NVIDIA CUDA / AMD ROCm / CPU)
- 🔄 Voice Input (Whisper)
- 🔄 Voice Output (XTTS v2)
- 🔄 Desktop App (Wails)
- 🔄 Enhanced Memory System
- 🔄 Docker Support

### 📋 v2.0.0 - Q2 2026
- RAG Implementation
- Vector Database
- Multi-User Support
- Cloud Deployment

Siehe auch: [📋 CHANGELOG](./CHANGELOG.md) für detaillierte Release Notes

---

## 🤝 Contributing

Beiträge sind willkommen! Bitte lies [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

### Quick Start für Contributors

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/amazing-feature`)
3. Commit deine Änderungen (`git commit -m 'feat: Add amazing feature'`)
4. Push zum Branch (`git push origin feature/amazing-feature`)
5. Erstelle einen Pull Request

**Neuer Development Setup:**
```bash
# Installation mit allen Dev-Tools
pip install -e ".[dev,ci,tts,cuda]"

# Tests ausführen
pytest

# Code formatieren
black .
ruff check .
```

---

## 📄 Lizenz

**Apache License 2.0** mit zusätzlicher kommerzieller Einschränkung.

Vollständige Lizenz: [LICENSE](./LICENSE)

---

## 🙏 Danksagungen

- Inspiriert von JARVIS aus Iron Man
- Gebaut mit [Vue 3](https://vuejs.org/)
- Backend mit [FastAPI](https://fastapi.tiangolo.com/)
- Lokale Inferenz mit [llama.cpp](https://github.com/ggerganov/llama.cpp)

---

## 📚 Weitere Dokumentation

- [🎮 GPU Selection Guide](./docs/GPU_SELECTION.md) - NEW!
- [⚙️ Konfiguration (.env)](./docs/CONFIGURATION.md)
- [📋 Migration Guide v1.1 → v1.2](MIGRATION_GUIDE.md)
- [🏗️ Architecture Refactor Plan](ARCHITECTURE_REFACTOR.md)
- [Quick Start Guide](docs/README_QUICKSTART.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [LLM Download System](docs/LLM_DOWNLOAD_SYSTEM.md)
- [Performance Guide](docs/PERFORMANCE.md)
- [Voice Samples Guide](models/tts/voices/README.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [FAQ](FAQ.md)
- [Changelog](CHANGELOG.md)

---

<div align="center">

**Erstellt mit ❤️ von Lautloserspieler**

*"Manchmal muss man rennen, bevor man gehen kann."* - Tony Stark

**Version:** 1.1.0 | **v1.2.0-dev Phase 1 ✅** | **Release:** 02. Januar 2026

[⭐ Star us on GitHub](https://github.com/Lautloserspieler/JarvisCore) | [🐛 Report Bug](https://github.com/Lautloserspieler/JarvisCore/issues) | [💡 Request Feature](https://github.com/Lautloserspieler/JarvisCore/issues)

</div>
