# Wails Integration Guide

## Überblick

Die Desktop-UI nutzt **Wails Bindings** zur Kommunikation zwischen Vue.js Frontend und Go Backend.

## Architektur

```
Vue.js (Frontend)
    │
    │ window.go.app.App.MethodName()
    ↓
Wails Runtime (Bridge)
    │
    ↓ Go Method Call
Go Backend (internal/app/app.go)
    │
    ↓ HTTP Request
JarvisCore Python Backend (localhost:5050)
```

## Wails Bindings aktivieren

### 1. Go Backend

Methoden in `internal/app/app.go` werden automatisch exportiert:

```go
// ProcessCommand ist automatisch als JavaScript-Funktion verfügbar
func (a *App) ProcessCommand(text string) (string, error) {
    return a.bridge.SendMessage(text)
}
```

### 2. Wails Build

Bei `wails dev` oder `wails build` werden automatisch TypeScript-Bindings generiert:

```bash
cd desktop
wails dev  # Generiert: frontend/wailsjs/go/app/App.js
```

### 3. Vue.js Frontend

**Option A: Direkter Zugriff (nach Build)**

```javascript
// Auto-generierte Bindings nutzen
import { ProcessCommand } from '../wailsjs/go/app/App'

const response = await ProcessCommand("Hallo")
```

**Option B: Window-Objekt (immer verfügbar)**

```javascript
const response = await window.go.app.App.ProcessCommand("Hallo")
```

**Option C: Composable mit Fallback (empfohlen)**

```javascript
import { useWails } from '../composables/useWails'

const { api } = useWails()
const response = await api.ProcessCommand("Hallo")
```

## Verfügbare API-Methoden

### Chat

```javascript
// Nachricht senden
const response = await api.ProcessCommand(text)

// Verlauf abrufen
const history = await api.GetConversationHistory(50)
```

### System

```javascript
// System-Metriken
const metrics = await api.GetSystemStatus()
// { cpu: 45.2, memory: 62.8, disk: 38.5, gpu: 23.1 }
```

### Modelle

```javascript
// Modelle auflisten
const models = await api.ListModels()

// Modell laden
await api.LoadModel('mistral')
```

### Plugins

```javascript
// Plugins auflisten
const plugins = await api.GetPlugins()

// Plugin togglen
await api.TogglePlugin('Wikipedia', true)
```

## WebSocket Integration

### Backend (Go)

WebSocket Hub wird automatisch in `app.Startup()` gestartet:

```go
func (a *App) Startup(ctx context.Context) {
    a.bridge = bridge.NewJarvisCoreBridge("http://127.0.0.1:5050")
    a.StartWebSocketHub()  // ✅ WebSocket aktiviert
}
```

### Frontend (Vue.js)

```javascript
import { useWebSocket } from '../composables/useWebSocket'

const { connected, systemMetrics } = useWebSocket()

// systemMetrics wird automatisch alle 2s aktualisiert
watch(systemMetrics, (newMetrics) => {
    console.log('Neue Metriken:', newMetrics)
})
```

### Broadcasting Events

Go Backend broadcast automatisch bei wichtigen Events:

```go
// Nach erfolgreichem Command
a.BroadcastMessage("chat_message", map[string]interface{}{
    "role": "assistant",
    "text": response,
})

// Nach Model-Load
a.BroadcastMessage("model_loaded", map[string]interface{}{
    "model": modelKey,
})
```

## Development vs Production

### Development Mode

```bash
cd desktop
wails dev
```

- Hot Reload für Go und Vue.js
- Wails Bindings live generiert
- Dev-Tools verfügbar
- Fallback zu simulierten Daten falls Backend offline

### Production Build

```bash
cd desktop
wails build
```

- Optimierte Binaries
- Eingebettetes Frontend
- Keine Abhängigkeiten außer JarvisCore Python

## Error Handling

### Frontend

```javascript
try {
    const response = await api.ProcessCommand(text)
} catch (error) {
    console.error('Fehler:', error)
    // Fallback oder User-Notification
}
```

### Backend

```go
func (a *App) ProcessCommand(text string) (string, error) {
    response, err := a.bridge.SendMessage(text)
    if err != nil {
        return "", fmt.Errorf("Backend-Fehler: %w", err)
    }
    return response, nil
}
```

## Best Practices

1. **Immer useWails Composable nutzen**
   - Automatischer Fallback für Development
   - Konsistente API

2. **Error Handling implementieren**
   - Network-Fehler abfangen
   - User-friendly Messages

3. **Loading States zeigen**
   - User-Feedback während API-Calls

4. **WebSocket für Live-Updates nutzen**
   - Bessere UX durch Echtzeit-Daten
   - Weniger Polling-Requests

## Troubleshooting

### "window.go is undefined"

- Wails noch nicht initialisiert
- Lösung: `useWails()` Composable nutzt automatischen Fallback

### "Method not found"

- Go-Methode nicht exportiert (muss großen Anfangsbuchstaben haben)
- Wails Bindings nicht generiert (`wails dev` neu starten)

### Backend nicht erreichbar

- JarvisCore Python nicht gestartet
- Lösung: `python main.py` in JarvisCore-Root ausführen

## Weitere Infos

- Wails Docs: https://wails.io/docs/
- Vue.js Docs: https://vuejs.org/
- Go Docs: https://golang.org/doc/
