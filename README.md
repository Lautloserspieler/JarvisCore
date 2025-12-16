# 🤖 JARVIS Core System

<div align="center">

**Just A Rather Very Intelligent System**

Ein moderner KI-Assistent mit holographischer UI inspiriert von Iron Mans JARVIS

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-cyan.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[🇬🇧 English Version](./README_GB.md)

</div>

---

## ✨ Features

### 🎨 Frontend
- ✅ **Holographische UI** - Beeindruckende JARVIS-inspirierte Benutzeroberfläche
- ✅ **Echtzeit-Chat** - WebSocket-basierte Live-Kommunikation
- ✅ **Sprach-Interface** - Visuelle Voice-Input-Rückmeldung
- ✅ **Multi-Tab Navigation** - Chat, Dashboard, Memory, Models, Plugins, Logs, Settings
- ✅ **Model-Management** - Download und Verwaltung von KI-Modellen (Ollama-Style)
- ✅ **Download-Queue** - Live-Progress-Tracking mit Speed & ETA
- ✅ **Responsive Design** - Funktioniert auf allen Bildschirmgrößen
- ✅ **Dark Theme** - Cyberpunk-Ästhetik mit leuchtenden Effekten

### 🚀 Backend
- ✅ **FastAPI Server** - Hochperformanter Async-API-Server
- ✅ **WebSocket Support** - Echtzeitkommunikation in beide Richtungen
- ✅ **RESTful API** - Vollständige REST-Endpunkte
- ✅ **LLM Download-System** - Ollama-inspiriertes Multi-Registry-System
- ✅ **Model Management** - Wechseln zwischen KI-Modellen
- ✅ **Plugin System** - Erweiterbare Architektur
- ✅ **Memory Storage** - Konversationshistorie & Kontext
- ✅ **System Logs** - Umfassendes Logging

---

## 🚀 Schnellstart

### Voraussetzungen
- Python 3.8+
- Node.js 18+
- npm oder yarn

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
2. ✅ Fehlende Abhängigkeiten installieren
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

1. **Web-UI öffnen**: http://localhost:5050
2. **Models-Tab**: Navigation zur Model-Verwaltung
3. **Model downloaden**: 
   - Klick auf "Download" bei gewünschtem Modell
   - Wähle Quantization-Variante (z.B. Q4_K_M)
   - Download startet automatisch
4. **Download-Queue**: 
   - Sticky Bottom Panel zeigt alle aktiven Downloads
   - Live-Updates: Speed (MB/s), ETA, Prozent
   - Abbrechen mit "Cancel"-Button

### Verfügbare Modelle

| Model | Größe | Features | Status |
|-------|-------|----------|--------|
| **Mistral 7B Nemo** | ~4-8 GB | Chat, Instruction | ✅ Verfügbar |
| **Qwen 2.5 7B** | ~4-8 GB | Multilingual, Code | ✅ Verfügbar |
| **DeepSeek Coder 6.7B** | ~4-7 GB | Code-Spezialist | ✅ Verfügbar |

Weitere Infos: [LLM_DOWNLOAD_SYSTEM.md](./docs/LLM_DOWNLOAD_SYSTEM.md)

---

## 📁 Projektstruktur

```
JarvisCore/
├── main.py                 # 🚀 Einheitliches Startup-Script
├── core/                   # 🧠 Core-Module
│   ├── llm_manager.py     # LLM-Management
│   ├── model_downloader.py # Download-Engine
│   ├── model_registry.py   # Multi-Registry
│   ├── model_manifest.py   # Metadata-Management
│   └── ...                # Weitere Module
├── backend/
│   ├── main.py            # FastAPI-Server
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
├── docs/                   # 📚 Dokumentation
│   ├── LLM_DOWNLOAD_SYSTEM.md
│   ├── ARCHITECTURE.md
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
- `GET /api/chat/sessions` - Alle Chat-Sessions abrufen
- `POST /api/chat/sessions` - Neue Session erstellen
- `POST /api/chat/messages` - Nachricht senden

### Models
- `GET /api/models` - Alle Modelle auflisten
- `GET /api/models/available` - Verfügbare Modelle mit Status
- `GET /api/models/active` - Aktives Modell abrufen
- `POST /api/models/{id}/activate` - Modell aktivieren
- `POST /api/models/download` - Model-Download starten
- `GET /api/models/download/progress` - Download-Progress (SSE)
- `POST /api/models/cancel` - Download abbrechen
- `GET /api/models/variants` - Quantization-Varianten abrufen
- `DELETE /api/models/delete` - Modell löschen

### Plugins
- `GET /api/plugins` - Alle Plugins auflisten
- `POST /api/plugins/{id}/enable` - Plugin aktivieren
- `POST /api/plugins/{id}/disable` - Plugin deaktivieren

### Memory
- `GET /api/memory` - Erinnerungen abrufen
- `POST /api/memory/search` - Erinnerungen durchsuchen
- `GET /api/memory/stats` - Memory-Statistiken

### Logs
- `GET /api/logs` - System-Logs abrufen
- `GET /api/logs/stats` - Log-Statistiken

---

## 🎨 Technologie-Stack

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

### Aktuell (v1.0.0)
- ✅ Basis-UI mit allen Tabs
- ✅ WebSocket-Integration
- ✅ REST-API-Endpunkte
- ✅ Einheitliches Startup-Script
- ✅ Model-Download-System (Ollama-Style)
- ✅ Live-Progress-Tracking
- ✅ Multi-Registry-Support

### Geplant (v1.1.0)
- 🔄 Lokale LLM-Inferenz (llama.cpp Integration)
- 🔄 Voice Input/Output
- 🔄 Datenbank-Integration (PostgreSQL)
- 🔄 Benutzer-Authentifizierung
- 🔄 Multi-User-Support

### Zukunft (v2.0.0)
- 📋 Erweiterter Plugin-Marketplace
- 📋 Docker-Deployment
- 📋 Cloud-Deployment (AWS/GCP)
- 📋 Mobile App
- 📋 RAG (Retrieval-Augmented Generation)
- 📋 Knowledge-Base-Integration

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
- Download-System inspiriert von [Ollama](https://ollama.ai/)

---

## 📚 Weitere Dokumentation

- [LLM Download-System](./docs/LLM_DOWNLOAD_SYSTEM.md) - Detaillierte Dokumentation des Download-Systems
- [Architektur](./docs/ARCHITECTURE.md) - System-Architektur-Übersicht
- [Schnellstart](./README_QUICKSTART.md) - Ausführlicher Schnellstart-Guide
- [Backend-API](./backend/README.md) - Backend-spezifische Dokumentation

---

<div align="center">

**Erstellt mit ❤️ vom JARVIS-Team**

*"Manchmal muss man rennen, bevor man gehen kann."* - Tony Stark

**Stand:** 16. Dezember 2025

</div>
