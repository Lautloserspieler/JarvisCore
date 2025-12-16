# 🤖 JARVIS Core System

<div align="center">

**Just A Rather Very Intelligent System**

A modern AI assistant with holographic UI inspired by Iron Man's JARVIS

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-cyan.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[🇩🇪 Deutsche Version](./README.md)

</div>

---

## ✨ Features

### 🎨 Frontend
- ✅ **Holographic UI** - Stunning JARVIS-inspired interface
- ✅ **Real-time Chat** - WebSocket-based live communication
- ✅ **Voice Interface** - Visual voice input feedback
- ✅ **Multi-tab Navigation** - Chat, Dashboard, Memory, Models, Plugins, Logs, Settings
- ✅ **Model Management** - Download and manage AI models (Ollama-style)
- ✅ **Download Queue** - Live progress tracking with speed & ETA
- ✅ **Responsive Design** - Works on all screen sizes
- ✅ **Dark Theme** - Cyberpunk aesthetic with glowing effects

### 🚀 Backend
- ✅ **FastAPI Server** - High-performance async API
- ✅ **WebSocket Support** - Real-time bidirectional communication
- ✅ **RESTful API** - Complete REST endpoints
- ✅ **LLM Download System** - Ollama-inspired multi-registry system
- ✅ **Model Management** - Switch between AI models
- ✅ **Plugin System** - Extensible architecture
- ✅ **Memory Storage** - Conversation history & context
- ✅ **System Logs** - Comprehensive logging

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone the repository
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Start everything with one command!
python main.py
```

That's it! The unified `main.py` script will:
1. ✅ Check all requirements
2. ✅ Install missing dependencies
3. ✅ Start the backend server
4. ✅ Start the frontend dev server
5. ✅ Open your browser automatically

---

## 🌐 Access Points

Once started, you can access:

- 🎨 **Frontend UI**: http://localhost:5000
- 🔧 **Backend API**: http://localhost:5050
- 📚 **API Documentation**: http://localhost:5050/docs
- 🔌 **WebSocket**: ws://localhost:5050/ws

---

## 📦 Model Download System

JARVIS Core uses an **Ollama-inspired download system** for AI models:

### Features
- 🔄 **Multi-Registry Support** - HuggingFace, Ollama, Custom URLs
- 📦 **Resume Downloads** - Interrupted downloads are resumed
- ✅ **SHA256 Verification** - Automatic integrity checking
- 📊 **Live Progress** - Download speed, ETA, progress bar
- 🎯 **Quantization Variants** - Q4_K_M, Q5_K_M, Q6_K, Q8_0
- 🔐 **HuggingFace Token** - Support for private repositories

### Managing Models

1. **Open Web UI**: http://localhost:5050
2. **Models Tab**: Navigate to model management
3. **Download Model**: 
   - Click "Download" on desired model
   - Select quantization variant (e.g., Q4_K_M)
   - Download starts automatically
4. **Download Queue**: 
   - Sticky bottom panel shows all active downloads
   - Live updates: Speed (MB/s), ETA, Percentage
   - Cancel with "Cancel" button

### Available Models

| Model | Size | Features | Status |
|-------|------|----------|--------|
| **Mistral 7B Nemo** | ~4-8 GB | Chat, Instruction | ✅ Available |
| **Qwen 2.5 7B** | ~4-8 GB | Multilingual, Code | ✅ Available |
| **DeepSeek Coder 6.7B** | ~4-7 GB | Code Specialist | ✅ Available |

More info: [LLM_DOWNLOAD_SYSTEM.md](./docs/LLM_DOWNLOAD_SYSTEM.md)

---

## 📁 Project Structure

```
JarvisCore/
├── main.py                 # 🚀 Unified startup script
├── core/                   # 🧠 Core modules
│   ├── llm_manager.py     # LLM management
│   ├── model_downloader.py # Download engine
│   ├── model_registry.py   # Multi-registry
│   ├── model_manifest.py   # Metadata management
│   └── ...                # Additional modules
├── backend/
│   ├── main.py            # FastAPI server
│   ├── requirements.txt   # Python dependencies
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   │   ├── ui/       # shadcn/ui components
│   │   │   ├── tabs/     # Tab components
│   │   │   ├── models/   # Model management components
│   │   │   └── *.tsx     # Main components
│   │   ├── services/      # API & WebSocket services
│   │   ├── hooks/         # Custom React hooks
│   │   ├── pages/         # Page components
│   │   └── lib/           # Utilities
│   ├── package.json
│   └── vite.config.ts
├── docs/                   # 📚 Documentation
│   ├── LLM_DOWNLOAD_SYSTEM.md
│   ├── ARCHITECTURE.md
│   └── ...
└── README.md
```

---

## 🛠️ Development

### Manual Start (Development Mode)

#### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🔌 API Endpoints

### Chat
- `GET /api/chat/sessions` - Get all chat sessions
- `POST /api/chat/sessions` - Create new session
- `POST /api/chat/messages` - Send message

### Models
- `GET /api/models` - List all models
- `GET /api/models/available` - Available models with status
- `GET /api/models/active` - Get active model
- `POST /api/models/{id}/activate` - Activate model
- `POST /api/models/download` - Start model download
- `GET /api/models/download/progress` - Download progress (SSE)
- `POST /api/models/cancel` - Cancel download
- `GET /api/models/variants` - Get quantization variants
- `DELETE /api/models/delete` - Delete model

### Plugins
- `GET /api/plugins` - List all plugins
- `POST /api/plugins/{id}/enable` - Enable plugin
- `POST /api/plugins/{id}/disable` - Disable plugin

### Memory
- `GET /api/memory` - Get memories
- `POST /api/memory/search` - Search memories
- `GET /api/memory/stats` - Memory statistics

### Logs
- `GET /api/logs` - Get system logs
- `GET /api/logs/stats` - Log statistics

---

## 🎨 Technology Stack

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: shadcn/ui (Radix UI + Tailwind CSS)
- **Routing**: React Router
- **State Management**: TanStack Query
- **WebSocket**: Native WebSocket API
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI
- **Server**: Uvicorn
- **WebSocket**: FastAPI WebSocket
- **Type Safety**: Pydantic
- **HTTP Client**: httpx (for downloads)

---

## 🎯 Features Roadmap

### Current (v1.0.0)
- ✅ Basic UI with all tabs
- ✅ WebSocket integration
- ✅ REST API endpoints
- ✅ Unified startup script
- ✅ Model download system (Ollama-style)
- ✅ Live progress tracking
- ✅ Multi-registry support

### Planned (v1.1.0)
- 🔄 Local LLM inference (llama.cpp integration)
- 🔄 Voice input/output
- 🔄 Database integration (PostgreSQL)
- 🔄 User authentication
- 🔄 Multi-user support

### Future (v2.0.0)
- 📋 Advanced plugin marketplace
- 📋 Docker deployment
- 📋 Cloud deployment (AWS/GCP)
- 📋 Mobile app
- 📋 RAG (Retrieval-Augmented Generation)
- 📋 Knowledge base integration

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

**Apache License 2.0** with additional commercial restriction.

This project is licensed under the Apache License 2.0 with the following **additional restriction**:

> **Commercial use, sale, or redistribution of this software is prohibited without prior written permission from the copyright holder.**

This restriction applies only to the original J.A.R.V.I.S. source code and associated assets created by Lautloserspieler. All included third-party components (such as language models, speech libraries, or external APIs) remain under their respective licenses.

Full license: [LICENSE](./LICENSE)

---

## 🙏 Acknowledgments

- Inspired by JARVIS from Iron Man
- Built with [shadcn/ui](https://ui.shadcn.com/)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Download system inspired by [Ollama](https://ollama.ai/)

---

## 📚 Additional Documentation

- [LLM Download System](./docs/LLM_DOWNLOAD_SYSTEM.md) - Detailed download system documentation
- [Architecture](./docs/ARCHITECTURE.md) - System architecture overview
- [Quick Start Guide](./README_QUICKSTART.md) - Detailed quick start guide
- [Backend API](./backend/README.md) - Backend-specific documentation

---

<div align="center">

**Made with ❤️ by the JARVIS Team**

*"Sometimes you gotta run before you can walk."* - Tony Stark

**Last updated:** December 16, 2025

</div>
