# 🤖 JARVIS Core System

<div align="center">

**Just A Rather Very Intelligent System**

A modern AI assistant with a beautiful holographic UI inspired by Iron Man's JARVIS

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-cyan.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-blue.svg)](https://typescriptlang.org)

</div>

---

## ✨ Features

### 🎨 Frontend
- ✅ **Holographic UI** - Stunning JARVIS-inspired interface
- ✅ **Real-time Chat** - WebSocket-based live communication
- ✅ **Voice Interface** - Visual voice input feedback
- ✅ **Multi-tab Navigation** - Chat, Dashboard, Memory, Models, Plugins, Logs, Settings
- ✅ **Responsive Design** - Works on all screen sizes
- ✅ **Dark Theme** - Cyberpunk aesthetic with glowing effects

### 🚀 Backend
- ✅ **FastAPI Server** - High-performance async API
- ✅ **WebSocket Support** - Real-time bidirectional communication
- ✅ **RESTful API** - Complete REST endpoints
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

- 🎨 **Frontend UI**: http://localhost:8080
- 🔧 **Backend API**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs
- 🔌 **WebSocket**: ws://localhost:8000/ws

---

## 📁 Project Structure

```
JarvisCore/
├── main.py                 # 🚀 Unified startup script
├── backend/
│   ├── main.py            # FastAPI server
│   ├── requirements.txt   # Python dependencies
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   │   ├── ui/       # shadcn/ui components
│   │   │   ├── tabs/     # Tab components
│   │   │   └── *.tsx     # Main components
│   │   ├── services/      # API & WebSocket services
│   │   ├── hooks/         # Custom React hooks
│   │   ├── pages/         # Page components
│   │   └── lib/           # Utilities
│   ├── package.json
│   └── vite.config.ts
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
- `GET /api/models/active` - Get active model
- `POST /api/models/{id}/activate` - Set active model

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

---

## 🎯 Features Roadmap

### Current (v1.0.0)
- ✅ Basic UI with all tabs
- ✅ WebSocket integration
- ✅ REST API endpoints
- ✅ Unified startup script

### Planned (v1.1.0)
- 🔄 Real AI model integration (OpenAI, Anthropic)
- 🔄 Voice input/output
- 🔄 Database integration (PostgreSQL)
- 🔄 User authentication
- 🔄 Multi-user support

### Future (v2.0.0)
- 📋 Advanced plugin marketplace
- 📋 Docker deployment
- 📋 Cloud deployment (AWS/GCP)
- 📋 Mobile app

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License - feel free to use this project for any purpose.

---

## 🙏 Acknowledgments

- Inspired by JARVIS from Iron Man
- Built with [shadcn/ui](https://ui.shadcn.com/)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)

---

<div align="center">

**Made with ❤️ by the JARVIS Team**

*"Sometimes you gotta run before you can walk."* - Tony Stark

</div>
