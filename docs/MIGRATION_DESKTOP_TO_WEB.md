# 🔄 Migration: Desktop UI → Web UI

**From:** DearPyGui/ImGui Desktop App  
**To:** React Web UI + FastAPI

---

## Why Migrate?

### Problems with old Desktop UI:
- ❌ Windows-only
- ❌ No remote access
- ❌ Outdated design
- ❌ Hard to maintain
- ❌ No mobile support

### Benefits of Web UI:
- ✅ Cross-platform (Windows, Linux, Mac)
- ✅ Remote access via browser
- ✅ Modern JARVIS design (Orbitron, cyan glows)
- ✅ Mobile-friendly
- ✅ Real-time updates (WebSocket)
- ✅ Easy to deploy

---

## Quick Start

### 1. Install Web Dependencies

```bash
# Backend (already installed)
pip install fastapi uvicorn websockets

# Frontend
cd frontend
npm install
npm run build
```

### 2. Start Web UI

```bash
# Option 1: Production mode (serves built frontend)
python main_web.py

# Option 2: Development mode
# Terminal 1: Backend
python main_web.py

# Terminal 2: Frontend dev server
cd frontend
npm run dev
```

### 3. Open Browser

```
http://localhost:8000
```

---

## Feature Mapping

### Old Desktop UI → New Web UI

| Old Feature | New Location |
|-------------|-------------|
| **System Metrics** | Dashboard Tab (live graphs) |
| **Chat** | Chat Tab (with history) |
| **Model Management** | Models Tab (download/status) |
| **Plugin Control** | Plugins Tab |
| **Settings** | Settings Tab |
| **Logs** | Logs Tab (live streaming) |
| **Memory** | Memory Tab (new!) |

---

## What Changed?

### Removed
- `desktop/jarvis_imgui_app_full.py`
- `dearpygui` dependency
- Windows-specific code

### Added
- `frontend/` - React + TypeScript UI
- `api/jarvis_api.py` - FastAPI backend
- `main_web.py` - Web server entry point
- WebSocket for real-time updates
- REST API endpoints

---

## Configuration

### data/settings.json

```json
{
  "desktop_app": {
    "enabled": false  // ❌ Disable old UI
  },
  "web_ui": {
    "enabled": true,  // ✅ Enable new UI
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

---

## API Endpoints

### REST API

```
GET  /api/health              - Health check
GET  /api/system/metrics      - System metrics
GET  /api/llm/status          - LLM status
GET  /api/llm/models          - Available models
POST /api/llm/load            - Load model
POST /api/llm/unload          - Unload model
GET  /api/plugins             - Plugin list
POST /api/chat/message        - Send message
GET  /api/logs                - Get logs
```

### WebSocket

```
ws://localhost:8000/ws

Client → Server:
  {"type": "ping"}
  {"type": "chat", "text": "..."}
  {"type": "voice_start"}
  {"type": "voice_end"}

Server → Client:
  {"type": "pong"}
  {"type": "chat_response", "text": "..."}
  {"type": "state_change", "state": "listening"}
  {"type": "metrics_update", "data": {...}}
```

---

## Deployment

### Development

```bash
# Hot reload for both frontend and backend
python main_web.py
```

### Production

```bash
# Build frontend
cd frontend
npm run build

# Start with gunicorn
cd ..
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.jarvis_api:app --bind 0.0.0.0:8000
```

### Docker (Coming Soon)

```bash
docker build -t jarvis .
docker run -p 8000:8000 jarvis
```

---

## Troubleshooting

### Frontend not loading?

```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

### API not responding?

```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Check logs
tail -f logs/jarvis.log
```

### WebSocket not connecting?

- Check CORS settings in `api/jarvis_api.py`
- Ensure port 8000 is not blocked
- Check browser console for errors

---

## FAQ

**Q: Can I still use the old Desktop UI?**  
A: Yes, but it's deprecated. Checkout an older commit if needed.

**Q: Will my data be migrated?**  
A: Yes! `data/settings.json` and all models remain unchanged.

**Q: Is the Web UI slower?**  
A: No! WebSocket ensures real-time updates just like the desktop app.

**Q: Can I access JARVIS from my phone?**  
A: Yes! The Web UI is responsive and works on mobile browsers.

**Q: Is it secure?**  
A: For local use, yes. For remote access, add authentication (see docs).

---

## Next Steps

1. ✅ Migrate to Web UI
2. 🔜 Add authentication for remote access
3. 🔜 PWA support (install as app)
4. 🔜 Mobile app (React Native)

---

**Need help?** Open an issue: https://github.com/Lautloserspieler/JarvisCore/issues
