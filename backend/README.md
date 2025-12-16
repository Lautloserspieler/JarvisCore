# JARVIS Core Backend

## Übersicht
FastAPI Backend für JARVIS Core System mit WebSocket-Support und REST-API-Endpunkten.

## Features
- ✅ WebSocket für Echtzeitkommunikation
- ✅ REST-API-Endpunkte für alle Services
- ✅ CORS für Frontend-Verbindung aktiviert
- ✅ Type-Safe mit Pydantic-Models
- ✅ LLM Download-System (Ollama-Style)
- ✅ SSE (Server-Sent Events) für Progress-Tracking
- ✅ Model Management mit Multi-Registry-Support

## Installation

```bash
pip install -r requirements.txt
```

## Server starten

```bash
python main.py
```

Oder mit uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5050
```

## API-Endpunkte

### Health
- `GET /` - Root-Endpunkt
- `GET /api/health` - Health-Check

### WebSocket
- `WS /ws` - WebSocket-Verbindung für Echtzeitkommunikation

### Chat
- `GET /api/chat/sessions` - Alle Chat-Sessions abrufen
- `POST /api/chat/sessions` - Neue Chat-Session erstellen
- `POST /api/chat/messages` - Nachricht senden

### Models
- `GET /api/models` - Alle Modelle abrufen
- `GET /api/models/available` - Verfügbare Modelle mit Download-Status
- `GET /api/models/active` - Aktives Modell abrufen
- `POST /api/models/{id}/activate` - Modell aktivieren

#### Model Management (NEU in v1.0.1)
- `POST /api/models/download` - Model-Download starten
  ```json
  {
    "model_key": "mistral",
    "quantization": "Q4_K_M"
  }
  ```
- `GET /api/models/download/progress` - Download-Progress (SSE)
  - Server-Sent Events Stream
  - Liefert: `percent`, `speed_mbps`, `eta_seconds`, `status`
- `POST /api/models/cancel` - Download abbrechen
  ```json
  {
    "model_key": "mistral"
  }
  ```
- `GET /api/models/variants?model_key=mistral` - Quantization-Varianten abrufen
  - Liefert: Liste von URLs für Q4_K_M, Q5_K_M, Q6_K, Q8_0
- `DELETE /api/models/delete` - Modell löschen
  ```json
  {
    "model_key": "mistral"
  }
  ```

### Plugins
- `GET /api/plugins` - Alle Plugins abrufen
- `POST /api/plugins/{id}/enable` - Plugin aktivieren
- `POST /api/plugins/{id}/disable` - Plugin deaktivieren

### Memory
- `GET /api/memory` - Erinnerungen abrufen
- `GET /api/memory/stats` - Memory-Statistiken abrufen
- `POST /api/memory/search` - Erinnerungen durchsuchen

### Logs
- `GET /api/logs` - Logs abrufen
- `GET /api/logs/stats` - Log-Statistiken abrufen

## WebSocket-Nachrichtenformat

### Client zu Server
```json
{
  "type": "chat_message",
  "message": "Hallo JARVIS",
  "sessionId": "session-id"
}
```

### Server zu Client
```json
{
  "type": "chat_response",
  "messageId": "uuid",
  "response": "Hallo! Wie kann ich helfen?",
  "sessionId": "session-id",
  "timestamp": "2025-12-16T10:00:00Z"
}
```

## Server-Sent Events (SSE)

### Download-Progress-Stream

**Endpunkt:** `GET /api/models/download/progress`

**Response-Format:**
```
event: progress
data: {"model":"mistral","percent":45.2,"speed_mbps":12.5,"eta_seconds":120,"status":"downloading"}

event: progress
data: {"model":"mistral","percent":100.0,"speed_mbps":0.0,"eta_seconds":0,"status":"completed"}

event: error
data: {"model":"mistral","error":"Download failed: Connection timeout"}
```

**Status-Werte:**
- `downloading` - Download läuft
- `completed` - Download abgeschlossen
- `cancelled` - Download abgebrochen
- `error` - Fehler aufgetreten

## LLM Download-System

### Multi-Registry-Support

Das Backend unterstützt mehrere Model-Registries:

1. **HuggingFace** (Standard)
   - `hf.co/namespace/repo`
   - `huggingface.co/user/model-GGUF`

2. **Ollama Registry**
   - `ollama.ai/library/llama2`

3. **Custom URLs**
   - `custom.ai/org/model`
   - Vollständige HTTPS-URLs

### Vordefinierte Modelle

| Shortcut | Registry | Namespace | Repository | Größe |
|----------|----------|-----------|------------|-------|
| `mistral` | HuggingFace | second-state | Mistral-Nemo-Instruct-2407-GGUF | ~4-8 GB |
| `qwen` | HuggingFace | bartowski | Qwen2.5-7B-Instruct-GGUF | ~4-8 GB |
| `deepseek` | HuggingFace | bartowski | DeepSeek-Coder-V2-Lite-Instruct-GGUF | ~4-7 GB |

### Quantization-Varianten

| Variant | Qualität | Geschwindigkeit | Speicher | Use Case |
|---------|---------|----------------|----------|----------|
| **Q4_K_M** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ~4GB | **Standard** (balanced) |
| **Q4_K_S** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ~3.5GB | Schnell, weniger RAM |
| **Q5_K_M** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ~5GB | Höhere Qualität |
| **Q6_K** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ~6GB | Sehr hohe Qualität |
| **Q8_0** | ⭐⭐⭐⭐⭐⭐ | ⭐ | ~8GB | Maximum Qualität |

### Download-Features

- 🔄 **Resume-Support** - Unterbrochene Downloads werden fortgesetzt
- ✅ **SHA256-Verifizierung** - Automatische Integritätsprüfung
- 📊 **Progress-Tracking** - Live-Updates via SSE
- 🔐 **HuggingFace Token** - Support für private Repositories
- 📦 **Manifest-System** - Metadata-Management

## Environment Variables

Erstelle eine `.env` Datei:

```env
API_HOST=0.0.0.0
API_PORT=5050
CORS_ORIGINS=http://localhost:5000,http://localhost:5173
HUGGINGFACE_TOKEN=hf_YourTokenHere  # Optional für private Repos
```

## Projekt-Struktur

```
backend/
├── main.py                  # FastAPI Server
├── requirements.txt         # Python Dependencies
└── README.md               # Diese Datei

core/                       # Core-Module (Root-Level)
├── llm_manager.py          # LLM-Management
├── model_downloader.py     # Download-Engine
├── model_registry.py       # Multi-Registry
├── model_manifest.py       # Metadata-System
└── ...                     # Weitere Module
```

## Entwicklung

### Hot-Reload aktivieren

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5050
```

### Logging-Level setzen

```bash
export LOG_LEVEL=DEBUG
python main.py
```

### API-Dokumentation

Nach dem Start verfügbar unter:
- **Swagger UI**: http://localhost:5050/docs
- **ReDoc**: http://localhost:5050/redoc

## Troubleshooting

### Port 5050 bereits belegt

```bash
# Port in Umgebungsvariable ändern
export JARVIS_PORT=5051
python main.py
```

### Download schlägt fehl

```bash
# Debug-Modus aktivieren
export LOG_LEVEL=DEBUG
python main.py
```

### HuggingFace 403 Forbidden

```bash
# Token für private Repos setzen
export HUGGINGFACE_TOKEN="hf_YourTokenHere"
python main.py
```

## Dependencies

### Haupt-Dependencies
- `fastapi>=0.109.0` - Web-Framework
- `uvicorn>=0.27.0` - ASGI-Server
- `pydantic>=2.5.0` - Type-Safety
- `websockets>=12.0` - WebSocket-Support
- `httpx>=0.26.0` - HTTP-Client für Downloads

### Optional
- `transformers` - HuggingFace Models (geplant für v1.1)
- `torch` - PyTorch (geplant für v1.1)
- `llama-cpp-python` - llama.cpp Bindings (geplant für v1.1)

## Weitere Dokumentation

- [LLM Download-System](../docs/LLM_DOWNLOAD_SYSTEM.md)
- [Haupt-README](../README.md)
- [Changelog](../docs/CHANGELOG.md)

---

**Stand:** 16. Dezember 2025
