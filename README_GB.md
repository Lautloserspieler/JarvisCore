# 🤖 JARVIS Core System

<div align="center">

**Just A Rather Very Intelligent System**

A modern AI assistant with holographic UI and **fully local llama.cpp inference**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-cyan.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-blue.svg)](https://typescriptlang.org)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF-orange.svg)](https://github.com/ggerganov/llama.cpp)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[🇩🇪 Deutsche Version](./README.md)

</div>

---

## ✨ Features

### 🧠 AI Engine (NEW v1.0.1!)
- ✅ **llama.cpp Local Inference** - Fully implemented and production-ready!
- ✅ **GPU Acceleration** - Automatic CUDA detection (30-50 tok/s)
- ✅ **4 GGUF Models** - Mistral, Qwen, DeepSeek, Llama 2 (Q4_K_M)
- ✅ **Chat with History** - Context-aware conversations
- ✅ **Up to 32K Context** - Long conversations possible
- ✅ **System Prompts** - Configurable JARVIS personality

### 🎨 Frontend
- ✅ **Holographic UI** - Stunning JARVIS-inspired interface
- ✅ **Real-time Chat** - WebSocket-based live communication with **real AI**
- ✅ **Voice Interface** - Visual voice input feedback
- ✅ **Multi-tab Navigation** - Chat, Dashboard, Memory, Models, Plugins, Logs, Settings
- ✅ **Model Management** - Download and manage AI models (Ollama-style)
- ✅ **Download Queue** - Live progress tracking with speed & ETA
- ✅ **Responsive Design** - Works on all screen sizes
- ✅ **Dark Theme** - Cyberpunk aesthetic with glowing effects

### 🚀 Backend
- ✅ **FastAPI Server** - High-performance async API
- ✅ **llama.cpp Integration** - Native GGUF model inference
- ✅ **WebSocket Support** - Real-time bidirectional communication
- ✅ **RESTful API** - Complete REST endpoints
- ✅ **LLM Download System** - Ollama-inspired multi-registry system
- ✅ **Model Management** - Load/unload models at runtime
- ✅ **Plugin System** - Extensible architecture
- ✅ **Memory Storage** - Conversation history & context
- ✅ **System Logs** - Comprehensive logging

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn
- **(Optional)** NVIDIA GPU with CUDA for accelerated inference

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
2. ✅ Install missing dependencies (including llama-cpp-python)
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

## 🧠 llama.cpp Local Inference

**NEW in v1.0.1** - Fully implemented and production-ready!

### Features
- 🚀 **GPU Acceleration** - CUDA automatically detected, all layers on GPU
- 🎯 **GGUF Support** - All llama.cpp-compatible models
- 💬 **Chat Mode** - History support with up to 32K context
- ⚡ **Performance** - 30-50 tokens/sec (GPU), 5-10 tokens/sec (CPU)
- 🧵 **Thread-Safe** - Parallel requests possible
- 💾 **Memory-Efficient** - Automatic model loading/unloading

### Available Models

| Model | Size | Use Case | Performance |
|-------|------|----------|-------------|
| **Mistral 7B Nemo** | ~7.5 GB | Code, technical details | ⚡⚡⚡ |
| **Qwen 2.5 7B** | ~5.2 GB | Versatile, multilingual | ⚡⚡⚡ |
| **DeepSeek R1 8B** | ~6.9 GB | Analysis, reasoning | ⚡⚡ |
| **Llama 2 7B** | ~4.0 GB | Creative, chat | ⚡⚡⚡ |

### Usage

```python
from core.llama_inference import llama_runtime

# Load model
llama_runtime.load_model(
    model_path="models/llm/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
    model_name="mistral",
    n_ctx=8192,        # 8K context window
    n_gpu_layers=-1    # All layers on GPU
)

# Chat with history
result = llama_runtime.chat(
    message="Explain quantum computing to me",
    history=[
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hello! How can I help you?"}
    ],
    system_prompt="You are JARVIS, a helpful AI assistant.",
    temperature=0.7,
    max_tokens=512
)

print(result['text'])  # Real AI response!
print(f"{result['tokens_per_second']:.1f} tok/s")  # Performance tracking
```

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

1. **Open Web UI**: http://localhost:5000
2. **Models Tab**: Navigate to model management
3. **Download Model**: 
   - Click "Download" on desired model
   - Select quantization variant (e.g., Q4_K_M)
   - Download starts automatically
4. **Load Model**:
   - Click "Load" on downloaded model
   - Wait for "✓ Model loaded successfully"
5. **Start Chat**:
   - Go to "Chat" tab
   - Write message
   - Get **real AI response** with llama.cpp!

More info: [LLM_DOWNLOAD_SYSTEM.md](./docs/LLM_DOWNLOAD_SYSTEM.md)

---

## 📁 Project Structure

```
JarvisCore/
├── main.py                 # 🚀 Unified startup script
├── core/                   # 🧠 Core modules
│   ├── llama_inference.py # ⭐ NEW: llama.cpp Inference Engine
│   ├── llm_manager.py     # LLM management
│   ├── model_downloader.py # Download engine
│   ├── model_registry.py   # Multi-registry
│   ├── model_manifest.py   # Metadata management
│   └── ...                # Additional modules
├── backend/
│   ├── main.py            # FastAPI server with llama.cpp
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
├── models/llm/            # 📦 Place GGUF models here
├── docs/                   # 📚 Documentation
│   ├── LLM_DOWNLOAD_SYSTEM.md
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
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
- `WS /ws` - WebSocket chat with llama.cpp AI responses
- `GET /api/chat/sessions` - Get all chat sessions
- `POST /api/chat/sessions` - Create new session

### Models
- `GET /api/models` - List all models
- `GET /api/models/active` - Get active model
- `POST /api/models/{id}/load` - Load model (llama.cpp)
- `POST /api/models/unload` - Unload model
- `POST /api/models/download` - Start model download
- `GET /api/models/download/progress` - Download progress (SSE)
- `POST /api/models/cancel` - Cancel download
- `DELETE /api/models/delete` - Delete model

### System
- `GET /api/health` - Health check with llama.cpp status
- `GET /api/logs` - Get system logs

---

## 🎨 Technology Stack

### AI & Inference
- **llama.cpp** - Native GGUF model inference
- **llama-cpp-python** - Python bindings for llama.cpp
- **CUDA** - GPU acceleration (optional)

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

### ✅ Current (v1.0.1) - December 16, 2025
- ✅ **llama.cpp Local Inference** - PRODUCTION READY!
- ✅ GPU Acceleration (CUDA)
- ✅ Chat with History Support
- ✅ 4 GGUF Models Preconfigured
- ✅ Model Download System (Ollama-style)
- ✅ Live Progress Tracking
- ✅ Multi-Registry Support
- ✅ WebSocket Chat with Real AI
- ✅ Basic UI with All Tabs

### Planned (v1.2.0) - Q1 2026
- 🔄 Voice Input (Whisper STT)
- 🔄 Voice Output (XTTS v2 TTS)
- 🔄 Model Switching Without Restart
- 🔄 Better Memory Integration
- 🔄 Performance Optimizations

### Future (v2.0.0) - Q2 2026
- 📋 RAG (Retrieval-Augmented Generation)
- 📋 Vector Database (ChromaDB/FAISS)
- 📋 Multi-User Support
- 📋 User Authentication
- 📋 Cloud Deployment (AWS/GCP)
- 📋 Mobile App
- 📋 Advanced Plugin Marketplace

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
- Local inference with [llama.cpp](https://github.com/ggerganov/llama.cpp)
- Download system inspired by [Ollama](https://ollama.ai/)

---

## 📚 Additional Documentation

- [LLM Download System](./docs/LLM_DOWNLOAD_SYSTEM.md) - Detailed download system documentation
- [Architecture](./docs/ARCHITECTURE.md) - System architecture overview
- [Implementation Status](./IMPLEMENTATION_STATUS.md) - Feature status and roadmap
- [Changelog](./docs/CHANGELOG.md) - Version history
- [Backend API](./backend/README.md) - Backend-specific documentation

---

<div align="center">

**Made with ❤️ by the JARVIS Team**

*"Sometimes you gotta run before you can walk."* - Tony Stark

**Version:** 1.0.1 | **Last updated:** December 16, 2025, 11:15 CET

</div>
