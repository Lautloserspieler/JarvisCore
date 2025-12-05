# 🤖 J.A.R.V.I.S. Core - Desktop Edition

> **Just A Rather Very Intelligent System** - Native Desktop AI Assistant with Advanced Capabilities

[![Release](https://img.shields.io/github/v/release/Lautloserspieler/JarvisCore?label=Release)](https://github.com/Lautloserspieler/JarvisCore/releases)
[![Downloads](https://img.shields.io/github/downloads/Lautloserspieler/JarvisCore/total?label=Downloads)](https://github.com/Lautloserspieler/JarvisCore/releases)
[![Stars](https://img.shields.io/github/stars/Lautloserspieler/JarvisCore?style=social)](https://github.com/Lautloserspieler/JarvisCore/stargazers)
[![Issues](https://img.shields.io/github/issues/Lautloserspieler/JarvisCore)](https://github.com/Lautloserspieler/JarvisCore/issues)
[![Last Commit](https://img.shields.io/github/last-commit/Lautloserspieler/JarvisCore)](https://github.com/Lautloserspieler/JarvisCore/commits/main)


[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org)
[![Wails](https://img.shields.io/badge/Wails-v2-673ab8.svg)](https://wails.io)
[![Vue](https://img.shields.io/badge/Vue-3.0-42b883.svg)](https://vuejs.org)

---

## 📋 **Inhaltsverzeichnis**

- [✨ Features](#-features)
- [🏗️ Architektur](#-architektur)
- [📦 Installation](#-installation)
  - [👤 Windows](#-windows-installation)
  - [🐧 Linux / macOS](#-linux--macos-installation)
- [🚀 Schnellstart](#-schnellstart)
  - [👤 Windows Start](#-windows-start)
  - [🐧 Linux / macOS Start](#-linux--macos-start)
- [🎨 Desktop UI](#-desktop-ui-features)
- [📡 Backend API](#-backend-api)
- [⚙️ Konfiguration](#-konfiguration)
- [🛠️ Entwicklung](#-entwicklung)
- [⚠️ Known Limitations](#-known-limitations-v100)
- [🔄 Migration](#-migration-web--desktop)
- [🐛 Troubleshooting](#-troubleshooting)
- [📊 Performance](#-performance)
- [🎯 Roadmap](#-roadmap)
- [⚖️ Lizenz](#-lizenz)

---

## ✨ **Features**

### **🎯 Core Capabilities**

- **🧠 Local LLM System**
  - 3 lokale Sprachmodelle von Hugging Face
  - **LLaMA 3 (8B)** - Conversation & Creative Tasks
  - **Mistral/Hermes (7B)** - Code & Technical Tasks
  - **DeepSeek R1 (8B)** - Analysis & Research
  - Automatischer Download über Model Manager UI
  - GGUF Format mit llama-cpp-python
  - GPU-Acceleration Support (CUDA)
  - Intelligente Modellwahl basierend auf Task-Type
  - **Komplett offline & kostenlos** (keine API Keys)

- **📚 Knowledge Base System**
  - Automatisches Web-Crawling & Indexierung
  - Vector-basierte Semantic Search (Sentence-BERT)
  - Real-time Knowledge Feed mit Progress-Tracking

- **🧠 Advanced Memory System**
  - Langzeit-Memory mit Timeline-Visualisierung
  - Context-basiertes Memory-Retrieval
  - Semantic Search über Memory-Einträge

- **🎯 Reinforcement Learning**
  - Adaptive Command Recognition
  - User-specific Pattern Learning
  - Top-Command Analytics & Optimization

- **🔌 Plugin System**
  - Hot-loading von Custom Plugins
  - Enable/Disable ohne Neustart
  - Extensible Plugin API

- **🎙️ Voice Control**
  - Spracheingabe via Whisper (OpenAI)
  - Real-time Audio Visualizer
  - Hands-free Operation
  - **XTTS v2 Integration** (Backend bereits vorhanden)
    - Neural Text-to-Speech
    - Voice Cloning Support
    - High-Quality German Voice

- **🔒 Security Features**
  - Passphrase-based Authentication
  - TOTP 2FA Support (Google Authenticator)
  - Encrypted Memory Storage

---

## 🏗️ **Architektur**

```
┌─────────────────────────────────────────────────────────────┐
│                  Desktop UI (Native App)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Frontend: Vue 3 + TypeScript + Vite                  │  │
│  │  - 11 Responsive Views                                 │  │
│  │  - WebSocket Live-Updates                             │  │
│  │  - Voice Recording + Visualizer                       │  │
│  └─────────────────────┬─────────────────────────────────────┘  │
│                        │ Wails Bridge (IPC)                  │
│  ┌─────────────────────┴─────────────────────────────────────┐  │
│  │  Backend: Go + Wails v2                               │  │
│  │  - HTTP API Proxy (→ Python Backend)                  │  │
│  │  - WebSocket Manager                                   │  │
│  │  - Single Binary Compilation                          │  │
│  └─────────────────────┬─────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP/WebSocket
          ┌──────────┴──────────┐
          │   Python Backend (Core)     │
          │  ┌────────────────────────┐ │
          │  │ JarvisCore Engine      │ │
          │  │ - NLP Processing       │ │
          │  │ - Local LLM Manager    │ │
          │  │ - Knowledge Manager    │ │
          │  │ - Memory System        │ │
          │  │ - Plugin Orchestrator  │ │
          │  └────────────────────────┘ │
          │                              │
          │  HTTP API (Port 5050)        │
          │  WebSocket (Port 8765)       │
          └──────────────────────────────┘
```

### **Tech Stack**

| Layer | Technologien |
|-------|-------------|
| **Frontend** | Vue 3, TypeScript, Vite, Axios, WebSocket API |
| **Desktop Bridge** | Go 1.21+, Wails v2, Gorilla WebSocket |
| **Backend** | Python 3.10+, asyncio, aiohttp, FastAPI |
| **AI/ML** | llama-cpp-python, Hugging Face Models (GGUF), Sentence-BERT |
| **Database** | JSON-based Storage (Memory, Knowledge, Training Data) |
| **Voice** | Whisper (OpenAI), XTTS v2 (Coqui), Web Audio API |
| **Security** | bcrypt, pyotp (TOTP) |

---

## 📦 **Installation**

### 👤 **Windows Installation**

#### **1. Voraussetzungen prüfen**

```cmd
# Python 3.10+ installieren
python --version

# Go 1.21+ installieren
go version

# Node.js 18+ installieren
node --version
```

#### **2. Repository klonen**

```cmd
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore
```

#### **3. Python Virtual Environment erstellen**

```cmd
# Virtual Environment erstellen
python -m venv venv

# Aktivieren
venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt
```

#### **4. Wails CLI installieren**

```cmd
# Wails installieren
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# Path prüfen (falls wails nicht gefunden wird)
# Füge hinzu: %USERPROFILE%\go\bin zu PATH
```

#### **5. Desktop UI Dependencies**

```cmd
# In desktop/frontend Ordner
cd desktop\frontend
npm install
cd ..\..
```

#### **6. Konfiguration**

```cmd
# Settings kopieren
copy config\settings.example.py config\settings.py

# Einstellungen anpassen (optional)
notepad config\settings.py
```

**✅ Installation abgeschlossen!**

---

### 🐧 **Linux / macOS Installation**

#### **1. Voraussetzungen prüfen**

```bash
# Python 3.10+ installieren
python3 --version

# Go 1.21+ installieren
go version

# Node.js 18+ installieren
node --version
```

**Falls nicht installiert:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv golang nodejs npm

# macOS (Homebrew)
brew install python@3.10 go node

# Fedora
sudo dnf install python3 golang nodejs npm
```

#### **2. Repository klonen**

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore
```

#### **3. Python Virtual Environment erstellen**

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

#### **4. Wails CLI installieren**

```bash
# Wails installieren
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# Path prüfen
which wails

# Falls nicht gefunden, zu .bashrc/.zshrc hinzufügen:
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### **5. Desktop UI Dependencies**

```bash
# In desktop/frontend Ordner
cd desktop/frontend
npm install
cd ../..
```

#### **6. Konfiguration**

```bash
# Settings kopieren
cp config/settings.example.py config/settings.py

# Einstellungen anpassen (optional)
vim config/settings.py  # oder nano/gedit
```

**✅ Installation abgeschlossen!**

---

## 🚀 **Schnellstart**

### 👤 **Windows Start**

#### **⭐ Empfohlen: Unified Launcher (1 Klick!)**

```cmd
# Methode 1: Batch-Datei (Doppelklick)
start_jarvis.bat

# Methode 2: Python-Launcher
python start_jarvis.py

# Mit Optionen:
python start_jarvis.py --dev      REM Development Mode
python start_jarvis.py --build    REM Binary bauen
python start_jarvis.py --backend  REM Nur Backend
```

**Das war's! 🎉 Backend + Desktop UI starten automatisch.**

---

#### **Alternative: Manueller Start (2 Terminals)**

**Terminal 1: Backend starten**
```cmd
cd JarvisCore
venv\Scripts\activate
python main.py

REM Warte auf:
REM ✅ API: http://127.0.0.1:5050
REM ✅ WebSocket: ws://127.0.0.1:8765
```

**Terminal 2: Desktop UI starten**
```cmd
cd JarvisCore\desktop
wails dev

REM ✅ App öffnet automatisch
```

---

#### **Production Binary bauen**

```cmd
REM Automatisch bauen
python start_jarvis.py --build

REM Manuell bauen
cd desktop
wails build

REM Binary starten
.\build\bin\jarvis-desktop.exe
```

**Output:** `desktop/build/bin/jarvis-desktop.exe` (~28MB)

---

### 🐧 **Linux / macOS Start**

#### **⭐ Empfohlen: Unified Launcher (1 Befehl!)**

```bash
# Methode 1: Shell-Script
chmod +x start_jarvis.sh
./start_jarvis.sh

# Methode 2: Python-Launcher
python start_jarvis.py

# Mit Optionen:
python start_jarvis.py --dev      # Development Mode
python start_jarvis.py --build    # Binary bauen
python start_jarvis.py --backend  # Nur Backend
```

**Das war's! 🎉 Backend + Desktop UI starten automatisch.**

---

#### **Alternative: Manueller Start (2 Terminals)**

**Terminal 1: Backend starten**
```bash
cd JarvisCore
source venv/bin/activate
python main.py

# Warte auf:
# ✅ API: http://127.0.0.1:5050
# ✅ WebSocket: ws://127.0.0.1:8765
```

**Terminal 2: Desktop UI starten**
```bash
cd JarvisCore/desktop
wails dev

# ✅ App öffnet automatisch
```

---

#### **Production Binary bauen**

```bash
# Automatisch bauen
python start_jarvis.py --build

# Manuell bauen
cd desktop
wails build

# Binary starten
./build/bin/jarvis-desktop         # Linux
open ./build/bin/jarvis-desktop.app  # macOS
```

**Output:**
- **Linux:** `desktop/build/bin/jarvis-desktop`
- **macOS:** `desktop/build/bin/jarvis-desktop.app`

---

## 🎨 **Desktop UI Features**

### **11 Haupt-Ansichten**

| View | Icon | Features |
|------|------|----------|
| **Chat** | 💬 | Text & Voice Input, Streaming, Visualizer |
| **System** | 📊 | CPU/RAM/GPU Monitoring, Live-Updates |
| **Models** | 🧠 | LLM Download, Load/Unload, 3 Models |
| **Plugins** | 🔌 | Enable/Disable, Configuration |
| **Knowledge** | 📚 | Crawling Feed, Stats, Search |
| **Memory** | 🧠 | Timeline, Search, Export |
| **Logs** | 📋 | Real-time Streaming, Filters |
| **Training** | 🎯 | RL Stats, Top Commands |
| **Commands** | 🎮 | Pattern Editor, Testing |
| **Settings** | ⚙️ | Audio, Config, Updates |
| **Security** | 🔒 | Passphrase/TOTP Overlay (Global) |

---

## 📡 **Backend API**

### **HTTP Endpoints**

```python
# System
GET  /api/status              # Backend Status
GET  /api/system/metrics      # CPU/RAM/GPU

# Chat
POST /api/command             # Send Message

# Models
GET  /api/models              # List Models (llama3, mistral, deepseek)
POST /api/models/load         # Load Model
POST /api/models/download     # Download Model from Hugging Face

# Knowledge
GET  /api/knowledge/stats     # KB Stats

# Memory
GET  /api/memory              # Memory Timeline
POST /api/memory/search       # Search

# Logs
GET  /api/logs                # Get Logs
POST /api/logs/clear          # Clear Logs

# Training
GET  /api/training            # RL Stats

# Commands
GET  /api/commands            # List Commands
POST /api/commands            # Add Command

# Plugins
GET  /api/plugins             # List Plugins
POST /api/plugins/toggle      # Enable/Disable
```

### **WebSocket Events**

```javascript
// Connect
ws://127.0.0.1:8765

// Events
- system_metrics      // Live CPU/RAM/GPU
- chat_message        // New Messages
- knowledge_progress  // Crawling Progress
- memory_update       // Memory Changes
- security_challenge  // 2FA Prompt
- log_entry           // New Log
- training_progress   // RL Updates
- model_download      // Model Download Progress
```

---

## ⚙️ **Konfiguration**

**config/settings.py:**

```python
# LLM Settings
DEFAULT_MODEL = "llama3"  # oder "mistral", "deepseek"
LLM_MAX_CACHED_MODELS = 2  # Wie viele Modelle im RAM halten
LLM_CPU_THREADS = 8        # CPU Threads für Inference
LLAMA_USE_GPU = 1          # GPU aktivieren (CUDA)
LLAMA_GPU_LAYERS = -1      # -1 = alle Layer auf GPU

# Backend
API_HOST = "127.0.0.1"
API_PORT = 5050
WEBSOCKET_PORT = 8765

# Security
SECURITY_PASSPHRASE = "your-passphrase"
TOTP_SECRET = "BASE32SECRET"

# Logging
LOG_LEVEL = "INFO"
```

---

## 🛠️ **Entwicklung**

### **Projekt-Struktur**

```
JarvisCore/
├── start_jarvis.py              # ⭐ Unified Launcher
├── start_jarvis.bat             # Windows Launcher
├── start_jarvis.sh              # Linux/macOS Launcher
├── main.py                      # Backend Entry
├── config/settings.py           # Configuration
├── core/
│   ├── llm_manager.py           # LLM Manager (3 Models)
│   ├── llm_router.py            # Intelligente Modellwahl
│   ├── xtts_manager.py          # XTTS v2 Manager
│   ├── xttsv2_tts.py            # XTTS v2 TTS Engine
│   ├── xttsv2_clone.py          # Voice Cloning
│   └── ...
├── models/llm/                  # LLM Download-Ordner
├── plugins/                     # Plugin System
├── data/                        # Storage
└── desktop/                     # Desktop UI
    ├── main.go                  # Go Entry
    ├── frontend/                # Vue 3
    │   ├── src/components/
    │   └── package.json
    └── backend/internal/        # Go Bridge
```

### **Development Commands**

```bash
# Unified Launcher (empfohlen)
python start_jarvis.py --dev

# Oder manuell:
# Backend
python main.py

# Frontend (Standalone)
cd desktop/frontend && npm run dev

# Full Desktop (Wails)
cd desktop && wails dev

# Production Build
python start_jarvis.py --build
```

---

## ⚠️ **Known Limitations (v1.0.0)**

> **Diese Punkte sind bekannt und werden in kommenden Updates adressiert.**

### **🔒 Security**

- **Token-System ist rudimentär**
  - Desktop-Backend nutzt generierten Random-Token
  - Keine persistente Token-Verwaltung
  - Keine Token-Rotation
  - 🛠️ **Fix geplant:** v1.0.1 - Config-basiertes Token-Management
  - 🛠️ **Fix geplant:** v1.1.0 - Token-Pairing über UI

- **Shell-Command-Injection-Risiken**
  - `system_control.py` nutzt `shell=True` an mehreren Stellen
  - User-Input-Validierung muss auditiert werden
  - 🛠️ **Fix geplant:** v1.0.1 - Shell-Call Audit + Whitelisting
  - 🛠️ **Fix geplant:** v1.1.0 - Komplett auf `shell=False` migrieren

### **🏛️ Code Quality**

- **`system_control.py` ist zu groß (~1500+ Zeilen)**
  - Mischt Prozess-Management, Dateisystem, Netzwerk, Power, Shell
  - Schwer wartbar und testbar
  - 🛠️ **Fix geplant:** v1.1.0 - Aufteilung in Module:
    - `system_processes.py`
    - `system_files.py`
    - `system_network.py`
    - `system_power.py`
    - `system_shell.py` (extra gesichert)

- **TTS-Code ist fragmentiert**
  - Mehrere parallele Implementierungen: `xtts_tts.py`, `xtts_tts_fixed.py`, `xttsv2_tts.py`, `reliable_tts.py`
  - Entwicklungshistorie, aber verwirrend
  - 🛠️ **Fix geplant:** v1.1.0 - Einheitliche TTS-API + Legacy-Cleanup

- **Exception Handling unvollständig**
  - Einige `bare except:` Blöcke ohne Logging (bereits teilweise gefixt)
  - 🛠️ **Fix geplant:** v1.0.1 - Komplettes Exception-Audit

### **⚙️ Performance**

- **Whisper lädt beim Start**
  - `load_strategy = "startup"` verzögert Start auf schwächeren Maschinen
  - 🛠️ **Fix geplant:** v1.3.0 - Lazy Loading + UI-Toggle

- **Keine Shutdown-Sequenz**
  - Threads/Queues werden teils unsauber gestoppt
  - Potential für Deadlocks
  - 🛠️ **Fix geplant:** v1.3.0 - Lifecycle-Manager

### **✅ Testing**

- **Test-Coverage gering**
  - Nur 1 Testmodul (`test_crawler_guard.py`)
  - Keine Unit-Tests für Core-Module
  - Keine Integrationstests
  - 🛠️ **Fix geplant:** v1.2.0 - Test-Suite für:
    - `config.Settings`
    - `knowledge_manager`
    - `system_control` (Teile)
    - Desktop Bridge (Go ↔ Python)

### **📝 Dokumentation**

- **Type-Hints fehlen teilweise**
  - Erschwert statische Analyse (mypy, pyright)
  - 🛠️ **Fix geplant:** v1.3.0 - Schrittweise Typisierung

---

### **📌 Hinweis**

**Diese Limitierungen beeinträchtigen NICHT die Kernfunktionalität!**

Das System ist **voll funktionsfähig** für:
- ✅ Chat mit 3 LLM-Modellen
- ✅ Voice Control
- ✅ Knowledge Base
- ✅ Memory System
- ✅ System Monitoring
- ✅ Plugin Management

Die genannten Punkte sind **Code-Quality- und Security-Verbesserungen** für Production-Readiness.

---

## 🔄 **Migration (Web UI → Desktop)**

**Web UI wurde am 05.12.2025 entfernt!**

Siehe [docs/MIGRATION.md](docs/MIGRATION.md) für Details.

**Kurz:**
```bash
# ALT (Web UI)
python main.py  # → Browser öffnet auf :8080

# NEU (Desktop UI)
python start_jarvis.py  # → Backend + Desktop starten automatisch
```

---

## 🐛 **Troubleshooting**

### **Windows**

#### **"Backend startet nicht"**
```cmd
# Dependencies neu installieren
pip install -r requirements.txt

# Port freigeben
netstat -ano | findstr :5050
taskkill /PID <PID> /F
```

#### **"Desktop UI startet nicht"**
```cmd
# Wails prüfen
wails doctor

# Frontend Dependencies
cd desktop\frontend
npm install

# Binary neu bauen
python start_jarvis.py --build
```

#### **"LLM Modell lädt nicht"**
```cmd
# Über UI herunterladen: Models View → Download Button
# Oder manuell: https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct-GGUF
# Datei nach models\llm\ kopieren
```

---

### **Linux / macOS**

#### **"Backend startet nicht"**
```bash
# Dependencies neu installieren
pip install -r requirements.txt

# Port freigeben
lsof -ti:5050 | xargs kill -9
```

#### **"Desktop UI startet nicht"**
```bash
# Wails prüfen
wails doctor

# Frontend Dependencies
cd desktop/frontend
npm install

# Binary neu bauen
python start_jarvis.py --build
```

#### **"LLM Modell lädt nicht"**
```bash
# Über UI herunterladen: Models View → Download Button
# Oder manuell: https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct-GGUF
# Datei nach models/llm/ kopieren
```

#### **"WebSocket Connection Failed"**
```bash
# Backend läuft?
curl http://127.0.0.1:5050/api/status

# WebSocket Port frei?
netstat -an | grep 8765
```

---

## 📊 **Performance**

### **System Requirements**

| Komponente | Minimum | Empfohlen |
|------------|---------|------------|
| **CPU** | 4 Cores @ 2.5 GHz | 8 Cores @ 3.5 GHz |
| **RAM** | 8 GB | 16 GB |
| **GPU** | - | NVIDIA RTX 3060+ (für GPU-Acceleration) |
| **Disk** | 10 GB (+ 5-7GB pro LLM) | 50 GB |

### **Benchmarks**
```
Startup:         2-3s (Desktop) + 3-5s (Backend)
Memory:          120 MB (Desktop) + 400 MB (Backend)
Binary Size:     28 MB
LLM Inference:   ~50 tokens/s (CPU), ~200 tokens/s (GPU)
```

---

## 🎯 **Roadmap**

### **v1.0.1 (Dezember 2025)** - Security Hardening
- [ ] Token-Management aus Config
- [ ] Shell-Command Audit + Whitelisting
- [ ] Exception-Handling Audit
- [ ] 🔄 **Auto-Update System** (bereits implementiert!)

### **v1.1 (Q1 2026)** - Code Cleanup & Features
- [ ] `system_control.py` Refactoring (Modul-Split)
- [ ] TTS-Konsolidierung (einheitliche API)
- [ ] System Tray Integration
- [ ] Global Hotkeys
- [ ] Multi-Language Support (EN, DE, FR)

### **v1.2 (Q2 2026)** - Testing & Stability
- [ ] Test-Suite (60%+ Coverage)
- [ ] CI/CD Pipeline (GitHub Actions)
- [ ] Performance-Profiling
- [ ] **XTTS UI Integration** 🎙️
  - Voice Training Interface
  - Latents Manager
  - Voice Sample Recorder

### **v1.3 (Q3 2026)** - Advanced Features
- [ ] Lifecycle-Manager (sauberes Shutdown)
- [ ] Lazy Loading für STT/TTS
- [ ] Type-Hints (vollständig)
- [ ] **RAG-System** (Vector-DB)
- [ ] **Code Execution Sandbox**

### **v2.0 (Q4 2026)** - Enterprise
- [ ] Distributed Architecture
- [ ] Browser Extension
- [ ] Plugin Marketplace
- [ ] Cloud-LLM Option

---

## ⚖️ **Lizenz**

**Proprietary License** - © 2025 Lautloserspieler

Dieses Projekt ist privat. Kommerzielle Nutzung nur nach Genehmigung.

---

## 📞 **Support**

- **Issues:** [GitHub Issues](https://github.com/Lautloserspieler/JarvisCore/issues)
- **Email:** emeyer@fn.de

---

<div align="center">

**Built with ❤️ using Python, Go, Vue 3, Wails, and llama.cpp**

⭐ **Star this project if you like it!**

</div>
