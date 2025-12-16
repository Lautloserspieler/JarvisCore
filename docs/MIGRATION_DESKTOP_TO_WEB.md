# 🔄 Migration: Desktop UI → Web UI

**Von:** DearPyGui/ImGui Desktop App  
**Zu:** React Web UI + FastAPI

---

## Warum migrieren?

### Probleme mit alter Desktop UI:
- ❌ Nur Windows
- ❌ Kein Remote-Zugriff
- ❌ Veraltetes Design
- ❌ Schwer zu warten
- ❌ Kein Mobile-Support

### Vorteile der Web UI:
- ✅ Cross-Platform (Windows, Linux, Mac)
- ✅ Remote-Zugriff über Browser
- ✅ Modernes JARVIS-Design (Orbitron, Cyan-Glows)
- ✅ Mobile-freundlich
- ✅ Echtzeit-Updates (WebSocket)
- ✅ Einfach zu deployen

---

## Quick Start

### 1. Web-Dependencies installieren

```bash
# Backend (bereits installiert)
pip install fastapi uvicorn websockets

# Frontend
cd frontend
npm install
npm run build
```

### 2. Web UI starten

```bash
# Option 1: Production-Modus (serviert gebautes Frontend)
python main_web.py

# Option 2: Entwicklungs-Modus
# Terminal 1: Backend
python main_web.py

# Terminal 2: Frontend Dev-Server
cd frontend
npm run dev
```

### 3. Browser öffnen

```
http://localhost:8000
```

---

## Feature-Mapping

### Alte Desktop UI → Neue Web UI

| Alte Feature | Neue Location |
|-------------|----------|
| **System-Metriken** | Dashboard Tab (Live-Graphen) |
| **Chat** | Chat Tab (mit History) |
| **Modell-Management** | Models Tab (Download/Status) |
| **Plugin-Control** | Plugins Tab |
| **Einstellungen** | Settings Tab |
| **Logs** | Logs Tab (Live-Streaming) |
| **Memory** | Memory Tab (Neu!) |

---

## Was hat sich geändert?

### Entfernt
- `desktop/jarvis_imgui_app_full.py`
- `dearpygui` Abhängigkeit
- Windows-spezifischer Code

### Hinzugefügt
- `frontend/` - React + TypeScript UI
- `api/jarvis_api.py` - FastAPI Backend
- `main_web.py` - Web-Server Einstiegspunkt
- WebSocket für Echtzeit-Updates
- REST-API Endpunkte

---

## Konfiguration

### data/settings.json

```json
{
  "desktop_app": {
    "enabled": false  // ❌ Alte UI deaktivieren
  },
  "web_ui": {
    "enabled": true,  // ✅ Neue UI aktivieren
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

---

## API-Endpunkte

### REST-API

```
GET  /api/health              - Health Check
GET  /api/system/metrics      - System-Metriken
GET  /api/llm/status          - LLM-Status
GET  /api/llm/models          - Verfügbare Modelle
POST /api/llm/load            - Modell laden
POST /api/llm/unload          - Modell entladen
GET  /api/plugins             - Plugin-Liste
POST /api/chat/message        - Nachricht senden
GET  /api/logs                - Logs abrufen
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

### Entwicklung

```bash
# Hot-Reload für Frontend und Backend
python main_web.py
```

### Production

```bash
# Frontend bauen
cd frontend
npm run build

# Mit Gunicorn starten
cd ..
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.jarvis_api:app --bind 0.0.0.0:8000
```

### Docker (Bald verfügbar)

```bash
docker build -t jarvis .
docker run -p 8000:8000 jarvis
```

---

## Troubleshooting

### Frontend lädt nicht?

```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

### API antwortet nicht?

```bash
# Prüfe ob Backend läuft
curl http://localhost:8000/api/health

# Logs prüfen
tail -f logs/jarvis.log
```

### WebSocket verbindet sich nicht?

- CORS-Einstellungen in `api/jarvis_api.py` prüfen
- Stellt sicher, dass Port 8000 nicht blockiert ist
- Browser-Konsole auf Fehler prüfen

---

## FAQ

**F: Kann ich die alte Desktop UI immer noch nutzen?**  
A: Ja, aber sie ist veraltet. Checkout einen älteren Commit wenn nötig.

**F: Werden meine Daten migriert?**  
A: Ja! `data/settings.json` und alle Modelle bleiben unverändert.

**F: Ist die Web UI langsamer?**  
A: Nein! WebSocket stellt Echtzeit-Updates wie die Desktop App sicher.

**F: Kann ich JARVIS von meinem Handy aus zugreifen?**  
A: Ja! Die Web UI ist responsive und funktioniert auf Mobile-Browsern.

**F: Ist das sicher?**  
A: Für lokale Nutzung ja. Für Remote-Zugriff Authentifizierung hinzufügen (siehe Docs).

---

## Nächste Schritte

1. ✅ Zu Web UI migrieren
2. 🔜 Authentifizierung für Remote-Zugriff hinzufügen
3. 🔜 PWA-Support (als App installierbar)
4. 🔜 Mobile App (React Native)

---

**Hilfe benötigt?** Issue öffnen: https://github.com/Lautloserspieler/JarvisCore/issues