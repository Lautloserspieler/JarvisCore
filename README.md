<div align="center">

# 🤖 J.A.R.V.I.S. Core

**Native Desktop AI Assistant mit 3 lokalen LLMs, Voice Control & Knowledge Base**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org)
[![Wails](https://img.shields.io/badge/Wails-v2-red.svg)](https://wails.io)
[![Vue](https://img.shields.io/badge/Vue-3-42b883.svg)](https://vuejs.org)

**Komplett offline. Privacy-first. Open Source.**

[Features](#-features) •
[Quick Start](#-quick-start) •
[Installation](#-installation) •
[Dokumentation](#-dokumentation) •
[Contributing](#-contributing)

![JarvisCore Banner](https://via.placeholder.com/800x200/1a1a2e/eaeaea?text=J.A.R.V.I.S.+Core)

</div>

---

## 📖 Über J.A.R.V.I.S. Core

**J.A.R.V.I.S. Core** ist ein **vollständig offline funktionierender** KI-Assistent mit nativer Desktop-Oberfläche. Inspiriert von Tony Starks legendärem AI-Assistenten, bietet J.A.R.V.I.S. Core fortschrittliche Funktionen wie:

- 🧠 **3 lokale LLMs** (Llama 3, Phi-3, Mistral) - keine Cloud, volle Privacy
- 🎤 **Voice Control** - Sprachsteuerung mit Whisper & Piper TTS
- 📚 **Knowledge Base** - Semantische Suche mit lokalen Embeddings
- 🔌 **Plugin System** - Erweiterbar durch eigene Module
- 🖥️ **Native Desktop UI** - Cross-Platform (Windows, Linux, macOS)
- 🔒 **100% Offline** - Alle Daten bleiben lokal

---

## ✨ Features

### 🤖 Lokale AI-Modelle

- **3 LLMs zur Auswahl:** Llama 3 (8B), Phi-3 (3.8B), Mistral (7B)
- **Automatisches Modell-Routing** - Wählt das beste Modell pro Task
- **CUDA & CPU Support** - GPU-beschleunigt oder CPU-only
- **Quantisierte Modelle** - 4-bit/8-bit für effiziente Nutzung

### 🎤 Voice & Speech

- **Speech Recognition** - Whisper-basiert, mehrsprachig
- **Text-to-Speech** - Piper TTS, natürliche Stimmen
- **Hotword Detection** - "Hey Jarvis" Wake Word
- **Voice Cloning** - Eigene Stimme trainieren

### 📚 Knowledge Management

- **Semantic Search** - Finde relevante Informationen
- **Local Knowledge Base** - Markdown, PDFs, Code importieren
- **Auto-Expansion** - KI erweitert Wissen automatisch
- **Context-Aware** - Berücksichtigt Gesprächskontext

### 🔌 Plugin System

- **Modular Architecture** - Einfach erweiterbar
- **Built-in Plugins:** Wetter, News, Kalender, System Control
- **Custom Plugins** - Eigene Plugins in Python entwickeln
- **Plugin Manager** - Plugins aktivieren/deaktivieren in UI

### 🖥️ Desktop UI (Wails)

- **Native Performance** - Go Backend + Vue 3 Frontend
- **Cross-Platform** - Windows, Linux, macOS
- **Modern Design** - Dark/Light Theme, responsive
- **Systemtray Integration** - Läuft im Hintergrund
- **Real-time Updates** - WebSocket-basiert

### 🔒 Privacy & Security

- **100% Offline** - Keine Cloud-Verbindung erforderlich
- **Adaptive Security** - Lernende Zugriffskontrolle
- **Encrypted Storage** - Sensitive Daten verschlüsselt
- **Safe Execution** - Sandboxed Command Execution

---

## 🚀 Quick Start

### Voraussetzungen

- **Python** 3.11+ (64-bit)
- **Go** 1.21+ (für Desktop UI)
- **Wails** v2 (für Desktop UI)
- **CUDA** 12.1+ (optional, für GPU-Beschleunigung)

### Installation (3 Schritte)

```bash
# 1. Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2. Setup ausführen (automatisch)
python scripts/bootstrap.py --run

# 3. Desktop UI starten
cd desktop
wails dev
```

**Das war's!** 🎉 J.A.R.V.I.S. läuft jetzt lokal auf deinem System.

---

## 📦 Installation

### Option 1: Automatisches Setup (Empfohlen)

```bash
# CPU-only (kein CUDA)
python scripts/bootstrap.py --cpu --run

# Mit CUDA (GPU)
python scripts/bootstrap.py --run

# Nur Setup, nicht starten
python scripts/bootstrap.py
```

### Option 2: Manuelles Setup

```bash
# 1. Virtuelle Umgebung erstellen
python -m venv venv

# 2. Aktivieren
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. LLM-Modelle herunterladen
python scripts/download_models.py

# 5. Starten
python main.py
```

### Desktop UI bauen

```bash
cd desktop

# Development Mode (Hot-Reload)
wails dev

# Production Build
wails build
# → Binary in: desktop/build/bin/
```

---

## 🎯 Nutzung

### Python Backend starten

```bash
# Standard
python main.py

# Mit Debug-Logging
python main.py --debug

# Spezifisches LLM wählen
python main.py --llm llama3
```

### Desktop UI starten

```bash
# Development
cd desktop && wails dev

# Production Binary
./desktop/build/bin/JarvisCore  # Linux/macOS
desktop\build\bin\JarvisCore.exe  # Windows
```

### Unified Launcher (Beides zusammen)

```bash
# Development Mode
python start_jarvis.py --dev

# Production Mode
python start_jarvis.py

# Nur Backend
python start_jarvis.py --backend
```

---

## 🗂️ Projekt-Struktur

```
JarvisCore/
├── core/                  # 💻 Python Core Module
│   ├── memory/           # Gedächtnis-System
│   ├── speech/           # Sprach-Erkennung/-Synthese
│   ├── llm/              # LLM-Integration
│   ├── knowledge/        # Wissens-Verwaltung
│   └── security/         # Sicherheits-Layer
│
├── desktop/              # 🖥️ Wails Desktop App
│   ├── frontend/         # Vue 3 UI
│   ├── backend/          # Go Backend
│   └── build/            # Compiled Binaries
│
├── plugins/              # 🔌 Plugin-System
│   ├── weather/
│   ├── calendar/
│   └── system_control/
│
├── models/               # 🧠 LLM Models (lokal)
├── data/                 # 📚 Knowledge Base
├── config/               # ⚙️ Konfiguration
├── scripts/              # 🤖 Automatisierungs-Scripts
├── tests/                # 🧪 Unit Tests
└── docs/                 # 📖 Dokumentation
```

---

## 📚 Dokumentation

### Haupt-Dokumentation

- **[Architektur](docs/ARCHITECTURE.md)** - System-Übersicht
- **[Security](docs/SECURITY.md)** - Sicherheits-Richtlinien
- **[Performance](docs/PERFORMANCE.md)** - Optimierungs-Tipps
- **[Changelog](docs/CHANGELOG.md)** - Release Notes

### Entwickler-Guides

- **[Auto-Refactor](docs/AUTO_REFACTOR.md)** - Automatisches Refactoring
- **[Root Cleanup](docs/ROOT_CLEANUP.md)** - Projekt-Organisation
- **[UI Consolidation](docs/UI_CONSOLIDATION.md)** - Desktop-App Migration
- **[Refactoring Guide](docs/REFACTORING_GUIDE.md)** - Modul-Reorganisation

### Quick References

- **[Quick Cleanup](QUICK_CLEANUP.md)** - Schnell-Referenz für Cleanup
- **[Desktop README](desktop/README.md)** - Desktop UI Dokumentation

---

## 🛠️ Technologie-Stack

### Backend (Python)

- **LLM:** llama-cpp-python, transformers
- **Speech:** faster-whisper, piper-tts
- **Embeddings:** sentence-transformers
- **Vector DB:** chromadb, faiss
- **API:** FastAPI, WebSocket

### Frontend (Desktop UI)

- **Framework:** Wails v2 (Go + Web)
- **UI:** Vue 3, TypeScript, Tailwind CSS
- **Build:** Vite
- **State:** Pinia

### Infrastructure

- **OS:** Windows, Linux, macOS
- **GPU:** CUDA 12.1+ (optional)
- **Storage:** SQLite, JSON

---

## 🎨 Screenshots

<div align="center">

### Desktop UI - Chat Interface
![Chat](https://via.placeholder.com/600x400/1a1a2e/eaeaea?text=Chat+Interface)

### Knowledge Base Browser
![Knowledge](https://via.placeholder.com/600x400/1a1a2e/eaeaea?text=Knowledge+Base)

### Settings & Model Selection
![Settings](https://via.placeholder.com/600x400/1a1a2e/eaeaea?text=Settings)

</div>

---

## 🤝 Contributing

Beiträge sind willkommen! Bitte beachte:

1. **Fork** das Repository
2. **Branch** erstellen: `git checkout -b feature/amazing-feature`
3. **Commit** Änderungen: `git commit -m 'feat: add amazing feature'`
4. **Push** zum Branch: `git push origin feature/amazing-feature`
5. **Pull Request** öffnen

### Entwickler-Setup

```bash
# Development Dependencies
pip install -r requirements-dev.txt

# Pre-commit Hooks installieren
pre-commit install

# Tests ausführen
pytest

# Code-Formatierung
black .
ruff check .
```

---

## 📄 Lizenz

**Apache License 2.0**

Dieses Projekt ist unter der Apache 2.0 Lizenz lizenziert - siehe [LICENSE](LICENSE) für Details.

**Wichtige Hinweise:**
- ✅ Kommerzielle Nutzung erlaubt
- ✅ Modifikation erlaubt
- ✅ Distribution erlaubt
- ⚠️ Haftungsausschluss - Keine Garantien
- ⚠️ Patent Grant - Siehe Lizenz

---

## 🙏 Danksagungen

- **Meta AI** - Llama Modelle
- **Microsoft** - Phi-3 Modelle
- **Mistral AI** - Mistral Modelle
- **OpenAI** - Whisper Speech Recognition
- **Rhasspy** - Piper TTS
- **Wails** - Desktop Framework
- **Vue.js** - UI Framework

---

## 📞 Kontakt & Support

- **GitHub Issues:** [Bug Reports & Feature Requests](https://github.com/Lautloserspieler/JarvisCore/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Lautloserspieler/JarvisCore/discussions)
- **Email:** emeyer@fn.de

---

## 🗺️ Roadmap

### Version 1.1 (Q1 2026)
- [ ] Multi-Modal Support (Vision + Audio)
- [ ] Plugin Marketplace
- [ ] Cloud Sync (optional, encrypted)
- [ ] Mobile Companion App

### Version 1.2 (Q2 2026)
- [ ] Advanced Memory System (Long-term Learning)
- [ ] Multi-User Support
- [ ] API für externe Apps
- [ ] Docker Container

### Version 2.0 (Q3 2026)
- [ ] Distributed Computing (Multi-Device)
- [ ] Advanced Voice Cloning
- [ ] Real-time Translation
- [ ] Smart Home Integration

---

<div align="center">

**Made with ❤️ by [@Lautloserspieler](https://github.com/Lautloserspieler)**

⭐ **Star dieses Projekt wenn es dir gefällt!** ⭐

[⬆ Back to Top](#-jarvis-core)

</div>
