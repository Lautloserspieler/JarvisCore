# 🤖 JARVIS Core System

<div align="center">

**Just A Rather Very Intelligent System**

Ein moderner KI-Assistent mit holographischer UI und **vollständig lokaler llama.cpp Inferenz**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-cyan.svg)](https://golang.org)
[![Vue](https://img.shields.io/badge/Vue-3.5+-green.svg)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF-orange.svg)](https://github.com/ggerganov/llama.cpp)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

[🇬🇧 English Version](./README_GB.md)

</div>

---

## ✨ Features

### 🧠 KI-Engine
- ✅ **llama.cpp Lokale Inferenz** - Vollständig implementiert und funktionsfähig!
- ✅ **GPU-Acceleration** - Automatische CUDA-Erkennung (30-50 tok/s)
- ✅ **4 GGUF-Modelle** - Mistral, Qwen, DeepSeek, Llama 2 (Q4_K_M)
- ✅ **Chat mit History** - Kontext-bewusste Konversationen
- ✅ **Bis 32K Context** - Lange Konversationen möglich
- ✅ **System-Prompts** - JARVIS-Persönlichkeit konfigurierbar

### 🎨 Frontend (Vue 3)
- ✅ **Holographische UI** - Beeindruckende JARVIS-inspirierte Benutzeroberfläche
- ✅ **Echtzeit-Chat** - WebSocket-basierte Live-Kommunikation
- ✅ **Sprach-Interface** - Voice-Input mit visueller Rückmeldung
- ✅ **Multi-Tab Navigation** - Chat, Dashboard, Memory, Models, Settings
- ✅ **Model-Management** - Download und Verwaltung von KI-Modellen
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

## 💻 Voraussetzungen

- **Python 3.11+** - [python.org](https://python.org)
- **Node.js 18+** - [nodejs.org](https://nodejs.org)
- **Git** - [git-scm.com](https://git-scm.com)
- **(Optional)** NVIDIA GPU mit CUDA für beschleunigte Inferenz

---

## 🚀 Installation & Start

### Windows

```powershell
# Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Python Dependencies installieren
pip install -r requirements.txt

# Frontend Dependencies installieren
cd frontend
npm install
cd ..

# JARVIS starten
python main.py
```

### Linux / macOS

```bash
# Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Python Dependencies installieren
pip install -r requirements.txt

# Frontend Dependencies installieren
cd frontend
npm install
cd ..

# JARVIS starten
python main.py
```

**Das war's!** Das `main.py` Script:
- ✅ Startet automatisch Backend & Frontend
- ✅ Öffnet Browser bei http://localhost:5000
- ✅ Backend läuft auf http://localhost:5050

---

## 🌐 Zugriffspunkte

Nach dem Start erreichst du:

- 🎨 **Frontend UI**: http://localhost:5000
- 🔧 **Backend API**: http://localhost:5050
- 📚 **API-Dokumentation**: http://localhost:5050/docs
- 🔌 **WebSocket**: ws://localhost:5050/ws

---

## 🧠 llama.cpp Lokale Inferenz

**NEU in v1.1.0** - Production-ready!

### Features
- 🚀 **GPU-Acceleration** - CUDA automatisch erkannt
- 🎯 **GGUF-Support** - Alle llama.cpp-kompatiblen Modelle
- 💬 **Chat-Modus** - History mit bis zu 32K Context
- ⚡ **Performance** - 30-50 tokens/sec (GPU), 5-10 tokens/sec (CPU)

### Verfügbare Modelle

| Model | Größe | Use Case | Performance |
|-------|-------|----------|-------------|
| **Mistral 7B Nemo** | ~7.5 GB | Code, technische Details | ⚡⚡⚡ |
| **Qwen 2.5 7B** | ~5.2 GB | Vielseitig, multilingual | ⚡⚡⚡ |
| **DeepSeek R1 8B** | ~6.9 GB | Analysen, Reasoning | ⚡⚡ |
| **Llama 2 7B** | ~4.0 GB | Kreativ, Chat | ⚡⚡⚡ |

### Verwendung

```python
from core.llama_inference import llama_runtime

# Modell laden
llama_runtime.load_model(
    model_path="models/llm/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
    model_name="mistral",
    n_ctx=8192,
    n_gpu_layers=-1
)

# Chat mit History
result = llama_runtime.chat(
    message="Erkläre mir Quantencomputing",
    history=[...],
    system_prompt="Du bist JARVIS...",
    temperature=0.7
)
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

1. **JARVIS starten**: `python main.py`
2. **Web-UI öffnen**: http://localhost:5000
3. **Models-Tab**: Navigation zur Model-Verwaltung
4. **Model downloaden**: Klick "Download" → Wähle Quantization
5. **Model laden**: Klick "Load" bei heruntergeladenem Modell
6. **Chat starten**: Gehe zu "Chat" Tab und schreibe

Weitere Infos: [docs/LLM_DOWNLOAD_SYSTEM.md](./docs/LLM_DOWNLOAD_SYSTEM.md)

---

## 📁 Projektstruktur

```
JarvisCore/
├── main.py                 # 🚀 Unified Launcher
├── requirements.txt        # 📦 Python Dependencies
├── core/                   # 🧠 Core Python Modules
│   ├── llama_inference.py # llama.cpp Engine
│   ├── model_downloader.py
│   └── ...
├── backend/                # 🔧 Python/FastAPI Backend
│   ├── main.py
│   └── requirements.txt
├── frontend/               # 🎨 Vue 3 Frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── models/llm/             # 📦 GGUF Models
├── config/                 # ⚙️ Configuration
├── data/                   # 🗄️ User Data
├── docs/                   # 📚 Documentation
└── README.md
```

---

## 🔧 Development

### Backend separat starten

```bash
cd backend
pip install -r requirements.txt
python main.py
# Läuft auf http://localhost:5050
```

### Frontend separat starten

```bash
cd frontend
npm install
npm run dev
# Läuft auf http://localhost:5173
```

### Tests ausführen

```bash
# Backend-Tests
cd backend
pytest tests/ -v

# Frontend-Tests
cd frontend
npm run test
```

---

## 🔌 API-Endpunkte

### Chat
- `WS /ws` - WebSocket-Chat mit AI
- `GET /api/chat/sessions` - Chat-Sessions
- `POST /api/chat/sessions` - Neue Session

### Models
- `GET /api/models` - Alle Modelle
- `POST /api/models/{id}/load` - Modell laden
- `POST /api/models/download` - Download starten
- `DELETE /api/models/delete` - Modell löschen

### System
- `GET /api/health` - Health-Check
- `GET /api/logs` - System-Logs

Vollständige API-Docs: http://localhost:5050/docs

---

## 🎨 Technologie-Stack

### Frontend
- **Framework**: Vue 3 + TypeScript
- **Build**: Vite
- **UI**: Tailwind CSS + Custom Components
- **State**: Pinia
- **WebSocket**: Native API

### Backend
- **Python**: FastAPI + Uvicorn
- **AI**: llama.cpp + CUDA
- **WebSocket**: FastAPI WebSocket
- **Storage**: Local File System

---

## 🐛 Troubleshooting

### Problem: Port bereits belegt

```bash
# Windows
netstat -ano | findstr :5000
netstat -ano | findstr :5050

# Linux/Mac
lsof -i :5000
lsof -i :5050

# Prozess beenden und neu starten
```

### Problem: Module nicht gefunden

```bash
# Alle Dependencies neu installieren
pip install -r requirements.txt
cd frontend && npm install
```

### Problem: CUDA nicht erkannt

```bash
# CUDA-Installation prüfen
nvidia-smi

# Python CUDA-Bindings installieren
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

Weitere Hilfe: [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)

---

## 🎯 Roadmap

### ✅ v1.1.0 (Current) - Dezember 2025
- ✅ Vue 3 Frontend
- ✅ Production-ready llama.cpp
- ✅ Community Documentation
- ✅ Model Download System

### 🔄 v1.2.0 - Q1 2026
- Voice Input (Whisper)
- Voice Output (XTTS v2)
- Desktop App (Wails)
- Enhanced Memory System
- Docker Support

### 📋 v2.0.0 - Q2 2026
- RAG Implementation
- Vector Database
- Multi-User Support
- Cloud Deployment
- Mobile App

---

## 🤝 Contributing

Beiträge sind willkommen! Bitte lies [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

### Quick Start für Contributors

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/amazing-feature`)
3. Commit deine Änderungen (`git commit -m 'feat: Add amazing feature'`)
4. Push zum Branch (`git push origin feature/amazing-feature`)
5. Erstelle einen Pull Request

Bitte beachte:
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Coding Standards](CONTRIBUTING.md#coding-standards)

---

## 📄 Lizenz

**Apache License 2.0** mit zusätzlicher kommerzieller Einschränkung.

Dieses Projekt ist unter der Apache License 2.0 lizenziert mit folgender **zusätzlicher Einschränkung**:

> **Kommerzielle Nutzung, Verkauf oder Weitervertrieb dieser Software ist ohne vorherige schriftliche Genehmigung des Copyright-Inhabers untersagt.**

Vollständige Lizenz: [LICENSE](./LICENSE)

---

## 🔒 Security

Sicherheitslücken bitte **nicht** als GitHub Issue melden. Nutze stattdessen:
- GitHub Security Advisory
- Email (siehe [SECURITY.md](SECURITY.md))

Weitere Infos: [SECURITY.md](SECURITY.md)

---

## 🙏 Danksagungen

- Inspiriert von JARVIS aus Iron Man
- Gebaut mit [Vue 3](https://vuejs.org/)
- Backend mit [FastAPI](https://fastapi.tiangolo.com/)
- Lokale Inferenz mit [llama.cpp](https://github.com/ggerganov/llama.cpp)
- Containerisierung mit [Docker](https://docker.com) (coming in v1.2)

---

## 📚 Weitere Dokumentation

- [Quick Start Guide](docs/README_QUICKSTART.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [LLM Download System](docs/LLM_DOWNLOAD_SYSTEM.md)
- [Performance Guide](docs/PERFORMANCE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Changelog](docs/CHANGELOG.md)

---

<div align="center">

**Erstellt mit ❤️ von Lautloserspieler**

*"Manchmal muss man rennen, bevor man gehen kann."* - Tony Stark

**Version:** 1.1.0 | **Release:** 02. Januar 2026

[⭐ Star us on GitHub](https://github.com/Lautloserspieler/JarvisCore) | [🐛 Report Bug](https://github.com/Lautloserspieler/JarvisCore/issues) | [💡 Request Feature](https://github.com/Lautloserspieler/JarvisCore/issues)

</div>