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


A modern AI assistant with holographic UI and **fully local llama.cpp inference**

[🇩🇪 Deutsche Version](./README.md) | [📚 Docs](./docs/) | [❓ FAQ](./FAQ.md) | [🔒 Security](./SECURITY.md)

</div>

---

## 🚀 Quickstart

- **Pinokio (recommended)**: [PINOKIO.md](./PINOKIO.md)
- **Manual quickstart**: [README_QUICKSTART.md](./README_QUICKSTART.md)
- **Troubleshooting**: [FAQ](./FAQ.md)

## ✨ Features

### 🧠 AI Engine
- ✅ **llama.cpp Local Inference** - Fully implemented and production-ready!
- ✅ **Automatic GPU Detection** - NVIDIA CUDA Support
- ✅ **7 GGUF Models** - Mistral, Qwen, DeepSeek, Llama and more
- ✅ **Chat with History** - Context-aware conversations
- ✅ **Up to 32K Context** - Long conversations possible
- ✅ **System Prompts** - Configurable JARVIS personality

### 🎨 Frontend (Vue 3)
- ✅ **Holographic UI** - Stunning JARVIS-inspired user interface
- ✅ **Real-time Chat** - WebSocket-based live communication
- ✅ **Voice Interface** - Voice input with visual feedback
- ✅ **Multi-Tab Navigation** - Chat, Dashboard, Memory, Models, Settings
- ✅ **Model Management** - Download and manage AI models
- ✅ **Plugin System** - Weather, Timer, Notes, News and more
- ✅ **Responsive Design** - Works on all screen sizes
- ✅ **Dark Theme** - Cyberpunk aesthetic with glowing effects

### 🚀 Backend (Python + FastAPI)
- ✅ **FastAPI Server** - High-performance Python backend
- ✅ **llama.cpp Integration** - Native GGUF model inference
- ✅ **WebSocket Support** - Real-time communication
- ✅ **RESTful API** - Complete REST endpoints
- ✅ **Plugin System** - Extensible architecture
- ✅ **Memory Storage** - Conversation history & context

---

## 💻 Requirements

- **Python 3.11+** - [python.org](https://python.org)
- **Node.js 18+** - [nodejs.org](https://nodejs.org)
- **Git** - [git-scm.com](https://git-scm.com)
- **(Optional)** NVIDIA GPU with CUDA for accelerated inference

---

## 🚀 Installation & Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore
```

### Step 2: Install Base Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: llama.cpp Setup (🆕 Automatic!)

**NEW:** Automatic GPU detection and optimal installation!

```bash
cd backend
python setup_llama.py
```

**The script automatically detects:**
- ✅ NVIDIA GPU → Installs with CUDA Support (30-50 tok/s)
- ✅ AMD GPU → Recommends CPU version (see below)
- ✅ No GPU → Installs CPU version (5-10 tok/s)

**Example Output:**
```
╭──────────────────────────────────────────────────────╮
│   JARVIS Core - llama.cpp Setup Script              │
│      Automatic GPU Detection & Install               │
╰──────────────────────────────────────────────────────╯

[INFO] System: Windows AMD64
[INFO] Python: 3.11.5
[INFO] Detecting GPU...
[INFO] NVIDIA GPU detected!

Installing llama-cpp-python with NVIDIA CUDA support

✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅

[SUCCESS] llama-cpp-python installed successfully!
[INFO] GPU Mode: NVIDIA CUDA
[INFO] You can now run: python main.py
```

### Step 4: Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 5: Start JARVIS

```bash
python main.py
```

**That's it!** The `main.py` script:
- ✅ Automatically starts backend & frontend
- ✅ Opens browser at http://localhost:5050
- ✅ Backend runs on http://localhost:5050

---

## 🎮 Quick Start Alternative

### One-Liner Installation (Recommended)

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git && cd JarvisCore && pip install -r requirements.txt && cd backend && python setup_llama.py && cd ../frontend && npm install && cd .. && python main.py
```

---

## 🌐 Access Points

After starting, you can access:

- 🎨 **Frontend UI**: http://localhost:5050
- 🔧 **Backend API**: http://localhost:5050
- 📚 **API Documentation**: http://localhost:5050/docs
- 🔌 **WebSocket**: ws://localhost:5050/ws

---

## 🧠 llama.cpp Local Inference

**NEW in v1.1.0** - Production-ready with automatic GPU detection!

### Features
- 🚀 **GPU Acceleration** - CUDA automatically detected
- 🎯 **GGUF Support** - All llama.cpp-compatible models
- 💬 **Chat Mode** - History support with up to 32K context
- ⚡ **Performance** - 30-50 tokens/sec (NVIDIA), 5-10 tokens/sec (CPU)

### GPU Support

| GPU Type | Support | Installation | Performance | Recommendation |
|---------|---------|--------------|-------------|----------------|
| **NVIDIA** | ✅ CUDA | Automatic | ⚡⚡⚡ 30-50 tok/s | ⭐ Recommended |
| **AMD** | ⚠️ ROCm | Complex | ⚡⚡⚡ 25-40 tok/s | In Development 👉 **Use CPU Version** |
| **Intel Arc** | 🔄 oneAPI | Coming Soon | ⚡⚡ 20-35 tok/s | In Development |
| **CPU** | ✅ Standard | Automatic | ⚡ 5-10 tok/s | ✅ Works |

#### 💡 Note for AMD GPU Users:

**ROCm setup is complex and requires:**
- Visual Studio Build Tools
- ROCm SDK Installation (~5 GB)
- Specific driver versions
- Multiple restarts
- Complicated path configuration

**👉 Recommendation: Use the CPU version!**
```bash
python setup_llama.py
# Select Option 3: CPU Version
```

**CPU Version Advantages:**
- ✅ Ready to use immediately
- ✅ No complex configuration
- ✅ Stable and reliable
- ✅ 5-10 tokens/sec (sufficient for chat)
- ✅ Smaller models (3B) run smoothly

### Available Models

| Model | Size | Use Case | CPU Performance |
|-------|-------|----------|----------------|
| **Llama 3.2 3B** | ~2.0 GB | Small, fast | ⚡⚡⚡ 8-12 tok/s |
| **Phi-3 Mini** | ~2.3 GB | Compact, chat | ⚡⚡⚡ 7-10 tok/s |
| **Qwen 2.5 7B** | ~5.2 GB | Versatile | ⚡⚡ 5-8 tok/s |
| **Mistral 7B Nemo** | ~7.5 GB | Code, technical | ⚡⚡ 4-7 tok/s |
| **DeepSeek R1 8B** | ~6.9 GB | Analysis | ⚡ 3-6 tok/s |

**👉 CPU Recommendation: Use Llama 3.2 3B or Phi-3 Mini for best performance!**

---

## 🔧 Manual llama.cpp Installation

If the automatic script doesn't work:

### NVIDIA GPU (CUDA)

```bash
cd backend
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir --no-binary llama-cpp-python
```

### CPU Only (Recommended for AMD)

```bash
cd backend
pip uninstall llama-cpp-python -y
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### AMD GPU (ROCm) - For Experts Only

⚠️ **Warning:** Very complex! Only recommended for experienced users.

1. **Install ROCm** (~5 GB): https://rocm.docs.amd.com/
2. **Install Visual Studio Build Tools**
3. **Restart required**
4. **Then:**
```bash
cd backend
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DLLAMA_HIPBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir --no-binary llama-cpp-python
```

---

## 📦 Model Download System

JARVIS Core uses an **Ollama-inspired download system**:

### Features
- 🔄 **Multi-Registry Support** - HuggingFace, Ollama, Custom URLs
- 📦 **Resume Downloads** - Interrupted downloads can be resumed
- ✅ **SHA256 Verification** - Automatic integrity checking
- 📊 **Live Progress** - Speed, ETA, progress bar
- 🔐 **HuggingFace Token** - Support for private repositories

### Managing Models

1. **Start JARVIS**: `python main.py`
2. **Open Web UI**: http://localhost:5050
3. **Models Tab**: Navigate to model management
4. **Download Model**: Click "Download" → Select quantization
5. **Load Model**: Click "Load" on downloaded model
6. **Start Chat**: Go to "Chat" tab and type

More info: [docs/LLM_DOWNLOAD_SYSTEM.md](./docs/LLM_DOWNLOAD_SYSTEM.md)

---

## 🔌 Plugin System

**NEW in v1.1.0** - Extensible plugin architecture!

### Available Plugins

| Plugin | Description | API Key |
|--------|-------------|----------|
| ☀️ **Weather** | OpenWeatherMap Integration | ✅ Required |
| ⏰ **Timer** | Timers & Reminders | ❌ Not needed |
| 📝 **Notes** | Quick Notes | ❌ Not needed |
| 📰 **News** | RSS News Feeds | ❌ Not needed |

### Activating Plugins

1. Open **Plugins Tab** in the UI
2. Click **"Activate"** on the desired plugin
3. If API key required → Modal opens automatically
4. Enter API key → Stored securely in `config/settings.json`
5. Plugin activated! ✅

---

## 📁 Project Structure

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
│   ├── setup_llama.py     # 🆕 Auto GPU Setup
│   ├── plugin_manager.py
│   └── requirements.txt
├── frontend/               # 🎨 Vue 3 Frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── plugins/                # 🔌 Plugin System
│   ├── weather_plugin.py
│   ├── timer_plugin.py
│   └── ...
├── models/llm/             # 📦 GGUF Models
├── config/                 # ⚙️ Configuration
├── data/                   # 🗄️ User Data
├── docs/                   # 📚 Documentation
└── README.md
```

---

## 🐛 Troubleshooting

### Problem: GPU not detected

```bash
# Check GPU status
nvidia-smi  # NVIDIA

# Reinstall llama.cpp
cd backend
python setup_llama.py
```

### Problem: Port already in use

```bash
# Windows
netstat -ano | findstr :5050
netstat -ano | findstr :5050

# Linux/Mac
lsof -i :5050
lsof -i :5050
```

### Problem: Module not found

```bash
pip install -r requirements.txt
cd frontend && npm install
```

### Problem: AMD GPU - ROCm Installation too complex

**Solution: Use CPU version!**
```bash
cd backend
python setup_llama.py
# Select Option 3
```

More help: [❓ FAQ](./FAQ.md) | [📚 Troubleshooting](./docs/TROUBLESHOOTING.md)

---

## 🎯 Roadmap

### ✅ v1.1.0 (Current) - December 2025
- ✅ Vue 3 Frontend
- ✅ Production-ready llama.cpp
- ✅ Automatic GPU Detection
- ✅ Plugin System with API Key Management
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

See also: [📋 CHANGELOG](./CHANGELOG.md) for detailed release notes

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

---

## 📄 License

**Apache License 2.0** with additional commercial restriction.

Full license: [LICENSE](./LICENSE)

---

## 🙏 Acknowledgments

- Inspired by JARVIS from Iron Man
- Built with [Vue 3](https://vuejs.org/)
- Backend with [FastAPI](https://fastapi.tiangolo.com/)
- Local inference with [llama.cpp](https://github.com/ggerganov/llama.cpp)

---

## 📚 Additional Documentation

- [Quick Start Guide](docs/README_QUICKSTART.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [LLM Download System](docs/LLM_DOWNLOAD_SYSTEM.md)
- [Performance Guide](docs/PERFORMANCE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [FAQ](FAQ.md)
- [Changelog](CHANGELOG.md)

---

<div align="center">

**Made with ❤️ by Lautloserspieler**

*"Sometimes you gotta run before you can walk."* - Tony Stark

**Version:** 1.1.0 | **Release:** January 02, 2026

[⭐ Star us on GitHub](https://github.com/Lautloserspieler/JarvisCore) | [🐛 Report Bug](https://github.com/Lautloserspieler/JarvisCore/issues) | [💡 Request Feature](https://github.com/Lautloserspieler/JarvisCore/issues)

</div>
