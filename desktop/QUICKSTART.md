# Desktop UI - Quick Start Guide

## 📚 Inhaltsverzeichnis

1. [Installation](#installation)
2. [Development](#development)
3. [API Usage](#api-usage)
4. [WebSocket](#websocket)
5. [Build](#build)
6. [Troubleshooting](#troubleshooting)

---

## Installation

### Voraussetzungen

```bash
# 1. Go installieren (1.21+)
go version

# 2. Node.js installieren (18+)
node --version

# 3. Wails CLI installieren
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# 4. Wails Doctor (Check)
wails doctor
```

### Dependencies installieren

```bash
cd JarvisCore/desktop

# Makefile nutzen
make install

# ODER manuell:
cd frontend && npm install && cd ..
cd backend && go mod download && cd ..
```

---

## Development

### Terminal 1: JarvisCore Backend

```bash
cd JarvisCore
python main.py
```

✅ Backend läuft auf http://127.0.0.1:5050

### Terminal 2: Desktop UI

```bash
cd desktop

# Mit Makefile
make dev

# ODER direkt
wails dev
```

✅ Desktop-App öffnet sich automatisch

### Hot Reload

- **Vue.js:** Auto-Reload bei Änderungen in `frontend/src/`
- **Go:** Auto-Reload bei Änderungen in `backend/`
- **CSS:** Instant-Update

---

## API Usage

### Wails Composable (empfohlen)

```javascript
// In Vue Component
import { useWails } from '../composables/useWails'

export default {
  setup() {
    const { api, isDevelopment, wailsReady } = useWails()
    
    const sendMessage = async () => {
      const response = await api.ProcessCommand("Hallo")
      console.log(response)
    }
    
    return { sendMessage, isDevelopment }
  }
}
```

### Verfügbare API-Methoden

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|---------------|
| `ProcessCommand(text)` | `string` | `string` | Nachricht senden |
| `GetSystemStatus()` | - | `object` | System-Metriken |
| `GetConversationHistory(limit)` | `number` | `array` | Chat-Verlauf |
| `ListModels()` | - | `array` | Modelle abrufen |
| `LoadModel(key)` | `string` | `void` | Modell laden |
| `GetPlugins()` | - | `array` | Plugins abrufen |
| `TogglePlugin(name, enabled)` | `string, bool` | `void` | Plugin toggle |

### Error Handling

```javascript
try {
  const response = await api.ProcessCommand(text)
} catch (error) {
  console.error('API Error:', error)
  alert(`Fehler: ${error.message}`)
}
```

---

## WebSocket

### Live-Updates empfangen

```javascript
import { useWebSocket } from '../composables/useWebSocket'

export default {
  setup() {
    const { connected, systemMetrics } = useWebSocket()
    
    watch(systemMetrics, (newMetrics) => {
      console.log('Live Update:', newMetrics)
      // UI automatisch aktualisieren
    })
    
    return { connected, systemMetrics }
  }
}
```

### Event Types

- `system_metrics` - Alle 2s (CPU, RAM, GPU, Disk)
- `chat_message` - Nach Command
- `model_loaded` - Nach Model-Load
- `plugin_toggled` - Nach Plugin-Toggle

---

## Build

### Development Build

```bash
cd desktop
make dev
```

### Production Build

```bash
cd desktop
make build

# Output:
# Windows: ./build/bin/jarvis-desktop.exe
# Linux:   ./build/bin/jarvis-desktop
# macOS:   ./build/bin/jarvis-desktop.app
```

### Platform-spezifische Builds

```bash
# Windows
make build-windows

# Linux
make build-linux

# macOS
make build-macos
```

### Binary Testen

```bash
# 1. JarvisCore starten
cd JarvisCore
python main.py

# 2. Binary ausführen (anderes Terminal)
cd desktop/build/bin
./jarvis-desktop.exe  # Windows
./jarvis-desktop      # Linux/macOS
```

---

## Troubleshooting

### Wails nicht gefunden

```bash
# Wails neu installieren
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# PATH prüfen
wails version
```

### "window.go is undefined"

- **Ursache:** Wails noch nicht initialisiert
- **Lösung:** `useWails()` Composable nutzt automatischen Fallback
- **Check:** Dev-Mode Banner in UI sichtbar?

### Backend nicht erreichbar

```bash
# 1. JarvisCore läuft?
curl http://127.0.0.1:5050/api/status

# 2. Port bereits belegt?
netstat -an | findstr 5050  # Windows
lsof -i :5050               # Linux/macOS

# 3. JarvisCore neu starten
cd JarvisCore
python main.py
```

### Build-Fehler

```bash
# Clean und neu bauen
cd desktop
make clean
make install
make build
```

### Frontend-Fehler

```bash
# Node modules neu installieren
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
wails dev
```

### Go-Dependencies-Fehler

```bash
cd backend
go mod tidy
go mod download
cd ..
wails dev
```

---

## Nützliche Commands

```bash
# Development
make dev              # Dev-Modus starten
make build            # Production Build
make clean            # Build-Artefakte löschen
make install          # Dependencies installieren

# Wails Commands
wails dev             # Development starten
wails build           # Build erstellen
wails doctor          # System-Check

# Go Commands
go mod tidy           # Dependencies aufräumen
go test ./...         # Tests ausführen
go fmt ./...          # Code formatieren

# Frontend Commands
npm install           # Dependencies installieren
npm run dev           # Vite Dev-Server
npm run build         # Production Build
```

---

## Weitere Ressourcen

- 📚 [Wails Integration Guide](docs/WAILS_INTEGRATION.md)
- 🔌 [WebSocket Documentation](docs/WEBSOCKET.md)
- 🏛️ [Architecture Overview](docs/ARCHITECTURE.md)
- 📡 [API Reference](docs/API.md)
- 🐛 [GitHub Issues](https://github.com/Lautloserspieler/JarvisCore/issues)

---

## Quick Tips

✅ **Development:** Immer zuerst JarvisCore Backend starten  
✅ **Production:** Binary + JarvisCore Backend zusammen verteilen  
✅ **API Calls:** `useWails()` Composable nutzen (auto-fallback)  
✅ **Live Updates:** `useWebSocket()` für Echtzeit-Daten  
✅ **Errors:** Try-Catch um API-Calls + User-friendly Messages  
✅ **Performance:** WebSocket statt Polling für Live-Metriken  
