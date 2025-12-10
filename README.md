# 🤖 J.A.R.V.I.S. Core

**Just A Rather Very Intelligent System**

Ein modularer, erweiterbarer KI-Assistent mit LLM-Integration, Wissensdatenbank und Speech-Processing.

---

## 🚀 Quick Start

### Installation

```bash
# 1. Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2. Automatisches Setup
python setup.py

# 3. Virtuelle Umgebung aktivieren
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 4. JARVIS starten
python main_web.py

# 5. Browser öffnen
# http://localhost:8000
```

---

## 🌐 Web UI

**Die neue futuristische Web-Oberfläche!**

### Features
- ✨ JARVIS-Design (Arc Reactor inspiriert)
- 💬 Realtime Chat mit WebSocket
- 📊 System Metrics Dashboard
- 🧠 Model Management
- 🧩 Plugin Control
- 📜 Live Logs
- 🎙️ Voice Visualizer

### Starten

```bash
# Production (serve built frontend)
python main_web.py

# Development (hot reload)
python main_web.py
```

**URL:** http://localhost:8000  
**API Docs:** http://localhost:8000/api/docs

---

## 📚 Dokumentation

### Guides
- [Web UI Setup](docs/WEB_UI_MIGRATION.md)
- [API Documentation](docs/API.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Migration Guide](docs/MIGRATION_DESKTOP_TO_WEB.md)

### Architecture
- [System Overview](docs/ARCHITECTURE.md)
- [Plugin System](docs/PLUGINS.md)
- [LLM Integration](docs/LLM.md)
- [Design System](docs/DESIGN_SYSTEM_JARVIS.md)

---

## ⚙️ Features

### 🧠 LLM Integration
- **llama.cpp** Backend
- Mehrere Modelle (Llama3, Mistral, Phi3, Gemma2)
- GPU-Acceleration (CUDA/ROCm/Metal)
- Streaming-Antworten

### 📚 Wissensdatenbank
- Wikipedia Integration
- Wikidata SPARQL
- PubMed Medical Research
- Semantic Scholar
- OpenStreetMap Geocoding
- ISBN Lookup (OpenLibrary)

### 🎙️ Speech
- **Speech-to-Text:** faster-whisper
- **Text-to-Speech:** Coqui TTS
- Wake-Word Detection
- Voice Commands

### 📡 Web Interface
- FastAPI Backend
- React + TypeScript Frontend
- WebSocket für Realtime Updates
- Responsive Design
- Mobile-friendly

### 🔌 Remote Control
- WebSocket Server
- REST API
- Multi-Client Support

---

## 📦 Tech Stack

### Backend
- **Python 3.11+**
- FastAPI + Uvicorn
- llama-cpp-python
- faster-whisper
- Coqui TTS

### Frontend
- **React 18+**
- TypeScript
- Vite
- Tailwind CSS
- Orbitron + Space Grotesk Fonts

### LLM
- llama.cpp
- GGUF Models
- CUDA/ROCm/Metal Support

---

## 📁 Projektstruktur

```
JarvisCore/
├── api/                  # FastAPI Backend
│   └── jarvis_api.py
├── frontend/             # React Web UI
│   ├── src/
│   │   ├── pages/
│   │   │   └── Index.tsx
│   │   ├── components/
│   │   │   └── VoiceVisualizer.tsx
│   │   └── lib/
│   │       └── api.ts
│   ├── package.json
│   └── vite.config.ts
├── core/                 # Python Core
│   ├── jarvis.py
│   ├── command_processor.py
│   ├── llm_manager.py
│   └── ...
├── plugins/              # Knowledge Plugins
│   ├── wikipedia.py
│   ├── wikidata.py
│   └── ...
├── data/                 # User Data
│   ├── settings.json
│   └── secure/
├── models/               # LLM Models
│   ├── llm/
│   ├── stt/
│   └── tts/
├── logs/                 # Logs
├── main_web.py           # Web UI Entry Point
├── setup.py              # Automated Setup
├── requirements.txt
└── README.md
```

---

## 🔧 Development

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Dev server (hot reload)
npm run dev
# http://localhost:5173

# Build for production
npm run build
```

### Backend Development

```bash
# Start with auto-reload
uvicorn api.jarvis_api:app --reload --port 8000
```

### Run Tests

```bash
pytest tests/
```

---

## ⚠️ Migration von alter Desktop UI

**Die alte DearPyGui/ImGui Desktop UI wurde entfernt!**

➡️ Verwende jetzt die **Web UI**: [Migration Guide](docs/MIGRATION_DESKTOP_TO_WEB.md)

### Quick Migration

```bash
# Old (deprecated)
# python desktop/jarvis_imgui_app_full.py

# New
python main_web.py
# http://localhost:8000
```

---

## 🐛 Troubleshooting

### ModuleNotFoundError

```bash
# Fix: Install in venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Pandas Conflict

```bash
python scripts/fix_pandas_conflict.py
```

### Frontend not loading

```bash
cd frontend
npm install
npm run build
```

**Mehr:** [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

---

## 📜 License

MIT License - siehe [LICENSE](LICENSE)

---

## 👥 Contributing

Contributions sind willkommen!

1. Fork the repo
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

---

## 📧 Contact

- **GitHub:** [Lautloserspieler](https://github.com/Lautloserspieler)
- **Issues:** [GitHub Issues](https://github.com/Lautloserspieler/JarvisCore/issues)

---

## ⭐ Star History

Wenn dir JARVIS gefällt, gib dem Projekt einen Stern! ⭐

---

**Built with ❤️ by the JARVIS Team**
