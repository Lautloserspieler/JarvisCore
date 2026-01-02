# JarvisCore Architektur

## Übersicht

JARVIS Core ist ein modulares KI-Assistenten-System mit folgender Architektur:

```
[🎨 React Frontend] ↔️ [WebSocket/REST] ↔️ [🚀 FastAPI Backend] ↔️ [🧠 Core-Module]
```

---

## System-Komponenten

### 1. Frontend (React + TypeScript)

**Technologie-Stack:**
- React 18 + TypeScript
- Vite (Build-Tool)
- shadcn/ui (UI-Komponenten)
- TanStack Query (State Management)
- WebSocket (Echtzeitkommunikation)

**Struktur:**
```
frontend/src/
├── components/
│   ├── ui/           # shadcn/ui Base-Komponenten
│   ├── tabs/         # Tab-Komponenten (Chat, Dashboard, etc.)
│   ├── models/       # Model-Management-Komponenten
│   └── *.tsx         # Haupt-Komponenten
├── services/        # API & WebSocket Services
├── hooks/           # Custom React Hooks
├── pages/           # Seiten-Komponenten
└── lib/             # Utilities
```

**Hauptansichten:**
- 💬 **Chat** - Text & Voice-Interaktion
- 📊 **Dashboard** - System-Übersicht
- 🧠 **Memory** - Konversations-Historie
- 📦 **Models** - Model-Management & Downloads
- 🔌 **Plugins** - Plugin-Verwaltung
- 📝 **Logs** - System-Logs
- ⚙️ **Settings** - Einstellungen

---

### 2. Backend (FastAPI)

**Hauptdatei:** `backend/main.py`

**Verantwortlichkeiten:**
- REST-API-Endpunkte
- WebSocket-Server
- SSE (Server-Sent Events) für Progress-Tracking
- Core-Module-Integration

**API-Kategorien:**
```python
/api/chat/*        # Chat-Sessions & Messages
/api/models/*      # Model-Management & Downloads
/api/plugins/*     # Plugin-Control
/api/memory/*      # Memory-System
/api/logs/*        # System-Logs
/ws                # WebSocket-Endpoint
```

**Ports:**
- Backend: `5050` (HTTP/WebSocket)
- Frontend: `5000` (Development)

---

### 3. Core-Module (`core/`)

#### 📦 **Model-Management**

**Dateien:**
- `llm_manager.py` - High-Level LLM-Management
- `model_downloader.py` - Download-Engine mit Resume-Support
- `model_registry.py` - Multi-Registry Path Parsing
- `model_manifest.py` - Metadata & Version Management

**Features:**
- Ollama-Style Model Paths (`mistral`, `hf.co/user/repo`)
- Resume-Downloads (HTTP Range Requests)
- SHA256-Verifizierung
- Multi-Registry (HuggingFace, Ollama, Custom)
- Progress-Callbacks für UI-Integration

**Datenfluss:**
```
Frontend Request 
  → Backend API (/api/models/download)
  → model_downloader.py (Download + Progress)
  → SSE Stream (/api/models/download/progress)
  → Frontend (Live-Updates)
```

---

#### 🧠 **LLM & Inference**

**Dateien:**
- `llm_manager.py` - Model Loading & Unloading
- `llm_router.py` - Task-basiertes Model-Routing
- `async_llm_wrapper.py` - Async LLM-Zugriff

**Status:**
- ✅ Model Download & Management
- ⚠️ Lokale Inferenz geplant (llama.cpp, v1.1.0)

---

#### 🎙️ **Speech & Audio**

**Dateien:**
- `speech_recognition.py` - STT (Whisper/Faster-Whisper)
- `text_to_speech.py` - TTS (XTTS v2 / pyttsx3)
- `audio_playback.py` - Audio-Wiedergabe
- `hotword_manager.py` - Wake-Word-Erkennung

**Features:**
- Multi-Backend STT/TTS
- Voice-Biometrics
- Audio-Visualisierung

---

#### 📚 **Knowledge & Memory**

**Dateien:**
- `knowledge_manager.py` - Knowledge-Base-Management
- `local_knowledge_scanner.py` - Lokale Dateien scannen
- `local_knowledge_importer.py` - Import in Knowledge-Base
- `crawler_client.py` - Web-Crawler-Client
- `memory_manager.py` - Konversations-Memory
- `long_term_memory.py` - Persistentes Memory
- `short_term_memory.py` - Session-Memory
- `vector_memory.py` - Embedding-basiertes Memory

**Features:**
- Semantic Search (Sentence-BERT)
- Knowledge-Base mit Wikipedia/OpenLibrary/Semantic Scholar
- Vector-Embeddings für Context-Retrieval
- Timeline-Visualisierung

---

#### 🔌 **Plugins**

**Datei:** `plugin_manager.py`

**Plugin-Ordner:** `plugins/`

**Verfügbare Plugins:**
- Wikipedia-Integration
- OpenStreetMap
- PubMed/Semantic Scholar
- Wikidata
- OpenLibrary

**Plugin-Schnittstelle:**
```python
class Plugin:
    def initialize(self): pass
    def execute(self, query: str) -> dict: pass
    def shutdown(self): pass
```

---

#### 🔒 **Security**

**Dateien:**
- `security_protocol.py` - Security-Protokoll & Safe-Mode
- `security_manager.py` - Security-Management
- `adaptive_access_control.py` - Zugriffskontrolle
- `sensitive_safe.py` - Sensible Daten-Verwaltung
- `safe_shell.py` - Sichere Shell-Befehle

**Features:**
- Role-Based Access Control
- Safe-Mode für sensible Aktionen
- Audit-Logs
- Optional: TOTP 2FA

---

#### 💻 **System Control**

**Dateien:**
- `system_control.py` - System-Aktionen (Apps, Befehle)
- `system_monitor.py` - Ressourcen-Monitoring

**Features:**
- CPU/RAM/GPU/Disk-Monitoring
- Prozess-Management
- System-Befehle (Whitelisted)

---

#### 🔄 **Communication**

**Dateien:**
- `websocket_gateway.py` - WebSocket-Server
- `api_manager.py` - API-Request-Management

**WebSocket-Events:**
```typescript
// Client → Server
{ type: "chat_message", message: "...", sessionId: "..." }

// Server → Client
{ type: "chat_response", response: "...", sessionId: "..." }
{ type: "model_loaded", model: "mistral" }
{ type: "download_progress", percent: 45.2, speed: 12.5 }
```

---

## Datenfluss-Diagramme

### Model-Download-Flow

```
╭────────────────╮
│ Frontend (UI) │
╰───────┬───────╯
        │
        │ POST /api/models/download
        │ { model_key: "mistral", quantization: "Q4_K_M" }
        │
        ↓
╭───────┴────────────╮
│ Backend (FastAPI) │
╰───────┬────────────╯
        │
        │ model_downloader.download_model()
        │
        ↓
╭───────┴─────────────────────╮
│ Core (model_downloader) │
│ 1. Parse Model Path      │
│ 2. Resolve Registry URL  │
│ 3. HTTP Range Request    │
│ 4. Resume if interrupted │
│ 5. SHA256 Verification   │
╰───────┬─────────────────────╯
        │
        │ Progress Callbacks
        │ { percent, speed_mbps, eta_seconds }
        │
        ↓
╭───────┴───────────────────╮
│ SSE Stream              │
│ GET /api/models/        │
│     download/progress    │
╰───────┬───────────────────╯
        │
        │ Live Updates
        │
        ↓
╭───────┴─────────────────╮
│ Frontend (Download   │
│ Queue Component)     │
╰────────────────────────╯
```

---

### Chat-Interaktion-Flow

```
User Input (Text/Voice)
  ↓
Frontend (Chat Component)
  ↓ WebSocket
Backend (WebSocket Handler)
  ↓
command_processor.py (Intent-Erkennung)
  ↓
llm_manager.py (Model-Auswahl)
  ↓
[Lokale LLM Inferenz] (geplant v1.1)
  ↓
Response
  ↓ WebSocket
Frontend (Display)
  ↓ (optional)
text_to_speech.py (TTS)
  ↓
Audio Output
```

---

## Konfiguration

### Settings-Dateien

**Haupt-Settings:** `data/settings.json`
- Template: `data/settings.template.json`
- Nicht versioniert (enthält API-Keys)

**Weitere Configs:**
- `config/intents.json` - Intent-Muster
- `config/plugins.json` - Plugin-Konfiguration
- `config/persona.json` - JARVIS-Persönlichkeit

**Environment Variables:**
- `JARVIS_BACKEND_PORT` - Backend-Port (default: 5050)
- `JARVIS_FRONTEND_PORT` - Frontend-Port (default: 5000)
- `HUGGINGFACE_TOKEN` - HuggingFace-Token für private Repos
- `LOG_LEVEL` - Logging-Level (DEBUG/INFO/WARNING/ERROR)

---

## Deployment

### Entwicklung

```bash
# Ein-Befehl-Start
python main.py

# Oder manuell
# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Production (geplant)

```bash
# Docker
docker-compose up -d

# Oder nativ
python main.py --production
```

---

## Sicherheit

### Best Practices

1. **Secrets Management:**
   - Niemals API-Keys in Git committen
   - `.env` Dateien nutzen
   - `data/settings.json` ist in `.gitignore`

2. **Safe-Mode:**
   - System-Befehle nur über Whitelist
   - Pfad-Validierung für File-Operations
   - Audit-Logging aller kritischen Aktionen

3. **Network Security:**
   - CORS für bekannte Domains konfigurieren
   - Rate-Limiting für API-Endpunkte
   - WebSocket-Token-Authentication (optional)

---

## Erweiterbarkeit

### Plugin entwickeln

```python
# plugins/my_plugin.py
class MyPlugin:
    def initialize(self):
        """Init-Phase"""
        pass
    
    def execute(self, query: str) -> dict:
        """Query verarbeiten"""
        return {
            "success": True,
            "data": {"result": "..."}
        }
    
    def shutdown(self):
        """Cleanup"""
        pass
```

### Neuen Core-Service hinzufügen

```python
# core/my_service.py
class MyService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def process(self, data):
        # Service-Logik
        pass
```

---

## Technische Details

### Performance-Optimierungen

- **Async/Await** in Backend für Non-Blocking I/O
- **WebSocket** für latenzarme Echtzeitkommunikation
- **SSE** für effiziente Progress-Streams
- **TanStack Query** für intelligentes Caching im Frontend
- **Code-Splitting** in Vite für kleinere Bundles

### Skalierbarkeit

- **Horizontale Skalierung:** Backend kann auf mehrere Instanzen verteilt werden
- **Load Balancing:** NGINX/Caddy vor Backend-Instanzen
- **Database:** Geplant für v1.1 (PostgreSQL)
- **Cache:** Redis für Session-Daten (geplant v1.2)

---

## Troubleshooting

### Port bereits belegt

```bash
export JARVIS_BACKEND_PORT=5051
export JARVIS_FRONTEND_PORT=5001
python main.py
```

### Downloads schlagen fehl

```bash
# Debug-Modus
export LOG_LEVEL=DEBUG
python main.py

# HuggingFace Token setzen
export HUGGINGFACE_TOKEN="hf_..."
```

### Frontend baut nicht

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## Weitere Ressourcen

- [README.md](../README.md) - Haupt-Dokumentation
- [LLM_DOWNLOAD_SYSTEM.md](./LLM_DOWNLOAD_SYSTEM.md) - Download-System Details
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) - Feature-Status
- [CHANGELOG.md](./CHANGELOG.md) - Versions-Historie

---

**Stand:** 16. Dezember 2025
