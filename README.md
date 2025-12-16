# 🤖 JARVIS Core System

<div align="center">

**Just A Rather Very Intelligent System**

Ein moderner KI-Assistent mit holographischer UI und **vollständig lokaler llama.cpp Inferenz**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-cyan.svg)](https://golang.org)
[![Vue](https://img.shields.io/badge/Vue-3.5+-green.svg)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
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

### 🚀 Backend (Python + Go)
- ✅ **FastAPI Server** - Hochperformanter Python Backend
- ✅ **Go Microservices** - Gateway, Memory, Speech Services
- ✅ **llama.cpp Integration** - Native GGUF-Model-Inferenz
- ✅ **WebSocket Support** - Echtzeitkommunikation
- ✅ **RESTful API** - Vollständige REST-Endpunkte
- ✅ **Plugin System** - Erweiterbare Architektur
- ✅ **Memory Storage** - Konversationshistorie & Kontext

---

## 🚀 Schnellstart

### Voraussetzungen
- **Docker** & **Docker Compose** (empfohlen)
- *ODER* Python 3.11+, Go 1.21+, Node.js 18+
- **(Optional)** NVIDIA GPU mit CUDA für beschleunigte Inferenz

### 🐳 Installation mit Docker (Empfohlen)

```bash
# Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Alle Services mit Docker Compose starten
docker-compose up -d

# Logs verfolgen
docker-compose logs -f
```

**Das war's!** Docker Compose startet automatisch:
- ✅ Backend (Python/FastAPI)
- ✅ Frontend (Vue 3 + Vite)
- ✅ Go Gateway Service
- ✅ Memory Service
- ✅ Speech Service

### 🔧 Alternative: Manueller Start (Development)

Wenn du ohne Docker entwickeln möchtest:

```bash
# Mit dem einheitlichen Launcher
python main.py
```

Das `main.py` Script:
1. ✅ Prüft alle Anforderungen
2. ✅ Installiert fehlende Abhängigkeiten
3. ✅ Startet Backend & Frontend parallel
4. ✅ Öffnet Browser automatisch

**Oder manuell je Service:**

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend (separates Terminal)
cd frontend
npm install
npm run dev

# Go Services (separates Terminal)
cd go-services/gateway
go run cmd/gateway/main.go
```

---

## 🌐 Zugriffspunkte

Nach dem Start erreichst du:

- 🎨 **Frontend UI**: http://localhost:5000
- 🔧 **Backend API**: http://localhost:5050
- 🌐 **Go Gateway**: http://localhost:8080
- 📚 **API-Dokumentation**: http://localhost:5050/docs
- 🔌 **WebSocket**: ws://localhost:5050/ws

---

## 🧠 llama.cpp Lokale Inferenz

**NEU in v1.1.0** - Production-ready mit Docker-Support!

### Features
- 🚀 **GPU-Acceleration** - CUDA automatisch erkannt
- 🎯 **GGUF-Support** - Alle llama.cpp-kompatiblen Modelle
- 💬 **Chat-Modus** - History mit bis zu 32K Context
- ⚡ **Performance** - 30-50 tokens/sec (GPU), 5-10 tokens/sec (CPU)
- 🐳 **Docker-Ready** - Plug & Play Container-Deployment

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

1. **Web-UI öffnen**: http://localhost:5000
2. **Models-Tab**: Navigation zur Model-Verwaltung
3. **Model downloaden**: Klick "Download" → Wähle Quantization
4. **Model laden**: Klick "Load" bei heruntergeladenem Modell
5. **Chat starten**: Gehe zu "Chat" Tab und schreibe

Weitere Infos: [docs/LLM_DOWNLOAD_SYSTEM.md](./docs/LLM_DOWNLOAD_SYSTEM.md)

---

## 📁 Projektstruktur

```
JarvisCore/
├── docker-compose.yml      # 🐳 Docker Orchestration
├── main.py                 # 🚀 Unified Launcher (dev)
├── core/                   # 🧠 Core Python Modules
│   ├── llama_inference.py # llama.cpp Engine
│   ├── model_downloader.py
│   └── ...
├── backend/                # 🔧 Python/FastAPI Backend
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── frontend/               # 🎨 Vue 3 Frontend
│   ├── Dockerfile
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── go-services/            # ⚡ Go Microservices
│   ├── gateway/           # API Gateway
│   ├── memory/            # Memory Service
│   └── speech/            # Speech Processing
├── models/llm/             # 📦 GGUF Models
├── docs/                   # 📚 Documentation
└── README.md
```

---

## 🐳 Docker Commands

```bash
# Starten
docker-compose up -d

# Stoppen
docker-compose down

# Logs anzeigen
docker-compose logs -f

# Neu builden
docker-compose build

# Services neustarten
docker-compose restart

# Bestimmten Service neustarten
docker-compose restart backend
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
- **Go**: Fiber (Microservices)
- **AI**: llama.cpp + CUDA
- **WebSocket**: FastAPI WebSocket

### Infrastructure
- **Container**: Docker + Docker Compose
- **Reverse Proxy**: Go Gateway
- **Storage**: Local File System

---

## 🎯 Roadmap

### ✅ v1.1.0 (Current) - Dezember 2025
- ✅ Docker Compose Setup
- ✅ Go Microservices
- ✅ Vue 3 Migration
- ✅ Production-ready llama.cpp
- ✅ Community Documentation

### 🔄 v1.2.0 - Q1 2026
- Voice Input (Whisper)
- Voice Output (XTTS v2)
- Desktop App (Wails)
- Enhanced Memory System

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
- Microservices mit [Go Fiber](https://gofiber.io/)
- Containerisierung mit [Docker](https://docker.com)

---

## 📚 Weitere Dokumentation

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [LLM Download System](docs/LLM_DOWNLOAD_SYSTEM.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Changelog](docs/CHANGELOG.md)

---

<div align="center">

**Erstellt mit ❤️ von Lautloserspieler**

*"Manchmal muss man rennen, bevor man gehen kann."* - Tony Stark

**Version:** 1.1.0 | **Release:** 02. Januar 2026

[⭐ Star us on GitHub](https://github.com/Lautloserspieler/JarvisCore) | [🐛 Report Bug](https://github.com/Lautloserspieler/JarvisCore/issues) | [💡 Request Feature](https://github.com/Lautloserspieler/JarvisCore/issues)

</div>
