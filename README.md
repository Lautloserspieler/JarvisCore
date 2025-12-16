# 🤖 JARVIS Core System

<div align="center">

**Just A Rather Very Intelligent System**

Ein moderner KI-Assistent mit holographischer UI und **vollständig lokaler llama.cpp Inferenz**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-cyan.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-blue.svg)](https://typescriptlang.org)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF-orange.svg)](https://github.com/ggerganov/llama.cpp)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[🇬🇧 English Version](./README_GB.md)

</div>

---

## ✨ Features

### 🧠 KI-Engine (NEU v1.0.1!)
- ✅ **llama.cpp Lokale Inferenz** - Vollständig implementiert und funktionsfähig!
- ✅ **GPU-Acceleration** - Automatische CUDA-Erkennung (30-50 tok/s)
- ✅ **4 GGUF-Modelle** - Mistral, Qwen, DeepSeek, Llama 2 (Q4_K_M)
- ✅ **Chat mit History** - Kontext-bewusste Konversationen
- ✅ **Bis 32K Context** - Lange Konversationen möglich
- ✅ **System-Prompts** - JARVIS-Persönlichkeit konfigurierbar

### 🎨 Frontend
- ✅ **Holographische UI** - Beeindruckende JARVIS-inspirierte Benutzeroberfläche
- ✅ **Echtzeit-Chat** - WebSocket-basierte Live-Kommunikation mit **echter AI**
- ✅ **Sprach-Interface** - Visuelle Voice-Input-Rückmeldung
- ✅ **Multi-Tab Navigation** - Chat, Dashboard, Memory, Models, Plugins, Logs, Settings
- ✅ **Model-Management** - Download und Verwaltung von KI-Modellen (Ollama-Style)
- ✅ **Download-Queue** - Live-Progress-Tracking mit Speed & ETA
- ✅ **Responsive Design** - Funktioniert auf allen Bildschirmgrößen
- ✅ **Dark Theme** - Cyberpunk-Ästhetik mit leuchtenden Effekten

### 🚀 Backend
- ✅ **FastAPI Server** - Hochperformanter Async-API-Server
- ✅ **llama.cpp Integration** - Native GGUF-Model-Inferenz
- ✅ **WebSocket Support** - Echtzeitkommunikation in beide Richtungen
- ✅ **RESTful API** - Vollständige REST-Endpunkte
- ✅ **LLM Download-System** - Ollama-inspiriertes Multi-Registry-System
- ✅ **Model Management** - Laden/Entladen von Modellen zur Laufzeit
- ✅ **Plugin System** - Erweiterbare Architektur
- ✅ **Memory Storage** - Konversationshistorie & Kontext
- ✅ **System Logs** - Umfassendes Logging

---

## 🚀 Schnellstart

### Voraussetzungen
- Python 3.8+
- Node.js 18+
- npm oder yarn
- **(Optional)** NVIDIA GPU mit CUDA für beschleunigte Inferenz

### Installation

```bash
# Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Alles mit einem Befehl starten!
python main.py
```

Das war's! Das einheitliche `main.py` Script wird:
1. ✅ Alle Anforderungen prüfen
2. ✅ Fehlende Abhängigkeiten installieren (inkl. llama-cpp-python)
3. ✅ Backend-Server starten
4. ✅ Frontend-Dev-Server starten
5. ✅ Browser automatisch öffnen

---

## 🌐 Zugriffspunkte

Nach dem Start erreichst du:

- 🎨 **Frontend UI**: http://localhost:5000
- 🔧 **Backend API**: http://localhost:5050
- 📚 **API-Dokumentation**: http://localhost:5050/docs
- 🔌 **WebSocket**: ws://localhost:5050/ws

---

## 🧠 llama.cpp Lokale Inferenz

**NEU in v1.0.1** - Vollständig implementiert und production-ready!

### Features
- 🚀 **GPU-Acceleration** - CUDA automatisch erkannt, alle Layers auf GPU
- 🎯 **GGUF-Support** - Alle llama.cpp-kompatiblen Modelle
- 💬 **Chat-Modus** - History-Support mit bis zu 32K Context
- ⚡ **Performance** - 30-50 tokens/sec (GPU), 5-10 tokens/sec (CPU)
- 🧵 **Thread-Safe** - Parallele Requests möglich
- 💾 **Memory-Efficient** - Automatisches Model Loading/Unloading

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
    n_ctx=8192,        # 8K Context-Window
    n_gpu_layers=-1    # Alle Layers auf GPU
)

# Chat mit History
result = llama_runtime.chat(
    message="Erkläre mir Quantencomputing",
    history=[
        {"role": "user", "content": "Hallo!"},
        {"role": "assistant", "content": "Hallo! Wie kann ich dir helfen?"}
    ],
    system_prompt="Du bist JARVIS, ein hilfreicher deutscher KI-Assistent.",
    temperature=0.7,
    max_tokens=512
)

print(result['text'])  # Echte AI-Antwort!
print(f"{result['tokens_per_second']:.1f} tok/s")  # Performance-Tracking
```

---

## 📦 Model-Download-System

JARVIS Core nutzt ein **Ollama-inspiriertes Download-System** für KI-Modelle:

### Features
- 🔄 **Multi-Registry-Support** - HuggingFace, Ollama, Custom URLs
- 📦 **Resume-Downloads** - Unterbrochene Downloads werden fortgesetzt
- ✅ **SHA256-Verifizierung** - Automatische Integritätsprüfung
- 📊 **Live-Progress** - Download-Speed, ETA, Fortschrittsbalken
- 🎯 **Quantization-Varianten** - Q4_K_M, Q5_K_M, Q6_K, Q8_0
- 🔐 **HuggingFace Token** - Support für private Repositories

### Models verwalten

1. **Web-UI öffnen**: http://localhost:5000
2. **Models-Tab**: Navigation zur Model-Verwaltung
3. **Model downloaden**: 
   - Klick auf "Download" bei gewünschtem Modell
   - Wähle Quantization-Variante (z.B. Q4_K_M)
   - Download startet automatisch
4. **Model laden**:
   - Klick "Load" bei heruntergeladenem Modell
   - Warte auf "✓ Model loaded successfully"
5. **Chat starten**:
   - Gehe zu "Chat" Tab
   - Schreibe Nachricht
   - Erhalte **echte AI-Antwort** mit llama.cpp!

Weitere Infos: [LLM_DOWNLOAD_SYSTEM.md](./docs/LLM_DOWNLOAD_SYSTEM.md)

---

## 📁 Projektstruktur

```
JarvisCore/
├── main.py                 # 🚀 Einheitliches Startup-Script
├── core/                   # 🧠 Core-Module
│   ├── llama_inference.py # ⭐ NEU: llama.cpp Inference Engine
│   ├── llm_manager.py     # LLM-Management
│   ├── model_downloader.py # Download-Engine
│   ├── model_registry.py   # Multi-Registry
│   ├── model_manifest.py   # Metadata-Management
│   └── ...                # Weitere Module
├── backend/
│   ├── main.py            # FastAPI-Server mit llama.cpp
│   ├── requirements.txt   # Python-Abhängigkeiten
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/    # React-Komponenten
│   │   │   ├── ui/       # shadcn/ui Komponenten
│   │   │   ├── tabs/     # Tab-Komponenten
│   │   │   ├── models/   # Model-Management-Komponenten
│   │   │   └── *.tsx     # Haupt-Komponenten
│   │   ├── services/      # API & WebSocket Services
│   │   ├── hooks/         # Custom React Hooks
│   │   ├── pages/         # Seiten-Komponenten
│   │   └── lib/           # Utilities
│   ├── package.json
│   └── vite.config.ts
├── models/llm/            # 📦 GGUF-Modelle hier ablegen
├── docs/                   # 📚 Dokumentation
│   ├── LLM_DOWNLOAD_SYSTEM.md
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   └── ...
└── README.md
```

---

## 🛠️ Entwicklung

### Manueller Start (Development-Modus)

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

## 🔌 API-Endpunkte

### Chat
- `WS /ws` - WebSocket-Chat mit llama.cpp AI-Responses
- `GET /api/chat/sessions` - Alle Chat-Sessions abrufen
- `POST /api/chat/sessions` - Neue Session erstellen

### Models
- `GET /api/models` - Alle Modelle auflisten
- `GET /api/models/active` - Aktives Modell abrufen
- `POST /api/models/{id}/load` - Modell laden (llama.cpp)
- `POST /api/models/unload` - Modell entladen
- `POST /api/models/download` - Model-Download starten
- `GET /api/models/download/progress` - Download-Progress (SSE)
- `POST /api/models/cancel` - Download abbrechen
- `DELETE /api/models/delete` - Modell löschen

### System
- `GET /api/health` - Health-Check mit llama.cpp Status
- `GET /api/logs` - System-Logs abrufen

---

## 🎨 Technologie-Stack

### KI & Inferenz
- **llama.cpp** - Native GGUF-Model-Inferenz
- **llama-cpp-python** - Python-Bindings für llama.cpp
- **CUDA** - GPU-Acceleration (optional)

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
- **HTTP Client**: httpx (für Downloads)

---

## 🎯 Features-Roadmap

### ✅ Aktuell (v1.0.1) - 16. Dezember 2025
- ✅ **llama.cpp Lokale Inferenz** - PRODUCTION READY!
- ✅ GPU-Acceleration (CUDA)
- ✅ Chat mit History-Support
- ✅ 4 GGUF-Modelle vorkonfiguriert
- ✅ Model-Download-System (Ollama-Style)
- ✅ Live-Progress-Tracking
- ✅ Multi-Registry-Support
- ✅ WebSocket-Chat mit echter AI
- ✅ Basis-UI mit allen Tabs

### Geplant (v1.2.0) - Q1 2026
- 🔄 Voice Input (Whisper STT)
- 🔄 Voice Output (XTTS v2 TTS)
- 🔄 Model-Switching ohne Neustart
- 🔄 Bessere Memory-Integration
- 🔄 Performance-Optimierungen

### Zukunft (v2.0.0) - Q2 2026
- 📋 RAG (Retrieval-Augmented Generation)
- 📋 Vector-Database (ChromaDB/FAISS)
- 📋 Multi-User-Support
- 📋 Benutzer-Authentifizierung
- 📋 Cloud-Deployment (AWS/GCP)
- 📋 Mobile App
- 📋 Advanced Plugin-Marketplace

---

## 🤝 Mitwirken

Beiträge sind willkommen! Bitte fühle dich frei, einen Pull Request einzureichen.

---

## 📄 Lizenz

**Apache License 2.0** mit zusätzlicher kommerzieller Einschränkung.

Dieses Projekt ist unter der Apache License 2.0 lizenziert mit folgender **zusätzlicher Einschränkung**:

> **Kommerzielle Nutzung, Verkauf oder Weitervertrieb dieser Software ist ohne vorherige schriftliche Genehmigung des Copyright-Inhabers untersagt.**

Diese Einschränkung gilt nur für den originalen J.A.R.V.I.S. Quellcode und zugehörige Assets von Lautloserspieler. Alle enthaltenen Drittanbieter-Komponenten (wie Sprachmodelle, Speech-Libraries oder externe APIs) unterliegen ihren jeweiligen Lizenzen.

Vollständige Lizenz: [LICENSE](./LICENSE)

---

## 🙏 Danksagungen

- Inspiriert von JARVIS aus Iron Man
- Gebaut mit [shadcn/ui](https://ui.shadcn.com/)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Lokale Inferenz mit [llama.cpp](https://github.com/ggerganov/llama.cpp)
- Download-System inspiriert von [Ollama](https://ollama.ai/)

---

## 📚 Weitere Dokumentation

- [LLM Download-System](./docs/LLM_DOWNLOAD_SYSTEM.md) - Detaillierte Dokumentation des Download-Systems
- [Architektur](./docs/ARCHITECTURE.md) - System-Architektur-Übersicht
- [Implementation Status](./IMPLEMENTATION_STATUS.md) - Feature-Status und Roadmap
- [Changelog](./docs/CHANGELOG.md) - Versions-Historie
- [Backend-API](./backend/README.md) - Backend-spezifische Dokumentation

---

<div align="center">

**Erstellt mit ❤️ vom JARVIS-Team**

*"Manchmal muss man rennen, bevor man gehen kann."* - Tony Stark

**Version:** 1.0.1 | **Stand:** 16. Dezember 2025, 11:15 CET

</div>
