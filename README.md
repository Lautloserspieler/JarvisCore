# 🤖 J.A.R.V.I.S. Core - Desktop Edition

> **Just A Rather Very Intelligent System** - Native Desktop AI Assistant with Advanced Capabilities

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
- [🚀 Schnellstart](#-schnellstart)
- [🎨 Desktop UI](#-desktop-ui-features)
- [📡 Backend API](#-backend-api)
- [⚙️ Konfiguration](#-konfiguration)
- [🛠️ Entwicklung](#-entwicklung)
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

- **🎓 Reinforcement Learning**
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

- **🔒 Security Features**
  - Passphrase-based Authentication
  - TOTP 2FA Support (Google Authenticator)
  - Encrypted Memory Storage

---

## 🏗️ **Architektur**

```
┌─────────────────────────────────────────────────────────────┐
│                  Desktop UI (Native App)                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Frontend: Vue 3 + TypeScript + Vite                  │  │
│  │  - 11 Responsive Views                                 │  │
│  │  - WebSocket Live-Updates                             │  │
│  │  - Voice Recording + Visualizer                       │  │
│  └─────────────────────┬─────────────────────────────────┘  │
│                        │ Wails Bridge (IPC)                  │
│  ┌─────────────────────▼─────────────────────────────────┐  │
│  │  Backend: Go + Wails v2                               │  │
│  │  - HTTP API Proxy (→ Python Backend)                  │  │
│  │  - WebSocket Manager                                   │  │
│  │  - Single Binary Compilation                          │  │
│  └─────────────────────┬─────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────┘
                         │ HTTP/WebSocket
          ┌──────────────▼──────────────┐
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
| **Voice** | Whisper (OpenAI), Web Audio API |
| **Security** | bcrypt, pyotp (TOTP) |

---

## 📦 **Installation**

### **Voraussetzungen**

#### **Python Backend**
```bash
# Python 3.10 oder höher
python --version

# Empfohlen: Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

#### **Desktop UI (Go + Wails)**
```bash
# Go 1.21 oder höher
go version

# Node.js 18+ (für Frontend)
node --version

# Wails CLI installieren
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

### **Installation Schritte**

```bash
# 1. Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2. Python Dependencies
pip install -r requirements.txt

# 3. Desktop UI Dependencies (optional)
cd desktop/frontend
npm install
cd ../..

# 4. Konfiguration
cp config/settings.example.py config/settings.py
vim config/settings.py  # Einstellungen anpassen
```

---

## 🚀 **Schnellstart**

### **⭐ Empfohlen: Unified Launcher (1 Befehl!)**

```bash
# 🚀 EINFACHSTE METHODE - Startet Backend + Desktop UI automatisch

# Windows:
start_jarvis.bat

# Linux/macOS:
chmod +x start_jarvis.sh
./start_jarvis.sh

# Oder direkt mit Python:
python start_jarvis.py

# Optionen:
python start_jarvis.py --dev      # Development Mode (Hot-Reload)
python start_jarvis.py --build    # Desktop Binary bauen
python start_jarvis.py --backend  # Nur Backend (kein UI)
```

**Das war's! 🎉 Backend + Desktop UI starten automatisch.**

---

### **Alternative: Manueller Start (2 Terminals)**

#### **Terminal 1: Python Backend**
```bash
cd JarvisCore
python main.py

# Warte auf:
# ✅ API: http://127.0.0.1:5050
# ✅ WebSocket: ws://127.0.0.1:8765
```

#### **Terminal 2: Desktop UI**
```bash
cd desktop
make dev
# oder: wails dev

# ✅ App öffnet automatisch
```

---

### **Production Build**

```bash
# Desktop Binary bauen
python start_jarvis.py --build

# Oder manuell:
cd desktop
make build

# Output:
# ✅ Windows: build/bin/jarvis-desktop.exe (~28MB)
# ✅ Linux:   build/bin/jarvis-desktop
# ✅ macOS:   build/bin/jarvis-desktop.app
```

**Deployment:**
```bash
# Backend muss laufen
python main.py &

# Binary starten
./desktop/build/bin/jarvis-desktop
```

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
| **Settings** | ⚙️ | Audio, Config |
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
cd desktop && make dev

# Production Build
python start_jarvis.py --build
```

---

## 🔄 **Migration (Web UI → Desktop)**

**Web UI wurde am 05.12.2025 entfernt!**

Siehe [MIGRATION.md](MIGRATION.md) für Details.

**Kurz:**
```bash
# ALT (Web UI)
python main.py  # → Browser öffnet auf :8080

# NEU (Desktop UI)
python start_jarvis.py  # → Backend + Desktop starten automatisch
```

---

## 🐛 **Troubleshooting**

### **"Backend startet nicht"**
```bash
pip install -r requirements.txt
lsof -ti:5050 | xargs kill -9  # Port freigeben (Linux/macOS)
netstat -ano | findstr :5050   # Port prüfen (Windows)
```

### **"Desktop UI startet nicht"**
```bash
# Wails installieren
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# Frontend Dependencies
cd desktop/frontend && npm install

# Binary fehlt? Baue neu:
python start_jarvis.py --build
```

### **"LLM Modell lädt nicht"**
```bash
# Modell herunterladen über UI: Models View → Download Button
# Oder manuell von Hugging Face:
# https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct-GGUF
# Datei nach models/llm/ kopieren
```

### **"WebSocket Connection Failed"**
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

### **v1.1 (Q1 2026)**
- [ ] System Tray Integration
- [ ] Global Hotkeys
- [ ] Multi-Language Support
- [ ] Mehr LLM Modelle (Qwen, Phi-3)

### **v1.2 (Q2 2026)**
- [ ] Wake Word Detection
- [ ] Screen Capture & Analysis
- [ ] Calendar Integration
- [ ] Smart Home Integration
- [ ] Cloud Sync

### **v2.0 (Q3 2026)**
- [ ] Distributed Architecture
- [ ] Browser Extension
- [ ] Plugin Marketplace
- [ ] Enterprise Features
- [ ] Cloud-LLM Option (OpenAI, Anthropic)

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
