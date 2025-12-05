# 🖥️ J.A.R.V.I.S. Desktop UI

**Native Desktop-Oberfläche für JarvisCore mit Wails + Vue.js + Go**

---

## 🎯 Überblick

Diese Desktop-Anwendung bietet eine native, performante Alternative zur Web-UI von JarvisCore mit **Wails Bindings** und **WebSocket Live-Updates**.

### Vorteile gegenüber Web-UI
- ✅ **Native Performance** - Kein Browser-Overhead
- ✅ **System-Integration** - Tray-Icon, Shortcuts, Benachrichtigungen
- ✅ **Single Binary** - Nur ~20-30MB
- ✅ **Offline-First** - Keine Port-Konflikte
- ✅ **Cross-Platform** - Windows, Linux, macOS
- ✅ **Live-Updates** - WebSocket für Echtzeit-Metriken
- ✅ **Auto-Fallback** - Funktioniert auch ohne Backend

---

## 📚 Quick Links

- 🚀 **[Quick Start Guide](QUICKSTART.md)** - Installation & Development
- 🔌 **[WebSocket Integration](docs/WEBSOCKET.md)** - Live-Updates System
- 🏛️ **[Architecture](docs/ARCHITECTURE.md)** - System-Design
- 📡 **[API Reference](docs/API.md)** - Backend-Methoden
- ⚙️ **[Wails Integration](docs/WAILS_INTEGRATION.md)** - Bindings Guide

---

## 🏛️ Architektur

```
desktop/
├── backend/              # Go Backend
│   ├── cmd/jarvis/      # Main entry
│   └── internal/
│       ├── app/         # App manager + WebSocket Hub
│       ├── bridge/      # HTTP Bridge zu JarvisCore
│       └── websocket/   # WebSocket Hub
├── frontend/            # Vue.js UI
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── composables/ # Wails & WebSocket helpers
│   │   └── App.vue
│   └── package.json
├── docs/                # Dokumentation
├── wails.json           # Wails config
└── Makefile             # Build automation
```

### Kommunikationsflow

```
Vue.js Frontend
    │ useWails() Composable
    ↓ window.go.app.App.Method()
Wails Bridge
    ↓
Go Backend
    ├─→ HTTP Bridge → JarvisCore Python (localhost:5050)
    └─→ WebSocket Hub → Live Updates zu Frontend
```

---

## ⚡ Quick Start

### Prerequisites

```bash
# 1. Go installieren (1.21+)
go version

# 2. Node.js installieren (18+)
node --version

# 3. Wails CLI installieren
go install github.com/wailsapp/wails/v2/cmd/wails@latest
wails doctor  # System-Check
```

### Installation

```bash
cd JarvisCore/desktop

# Makefile nutzen (empfohlen)
make install

# ODER manuell:
cd frontend && npm install && cd ..
cd backend && go mod download && cd ..
```

### Development

```bash
# Terminal 1: JarvisCore Backend starten
cd JarvisCore
python main.py
# ✅ Backend läuft auf http://127.0.0.1:5050

# Terminal 2: Desktop UI starten
cd desktop
make dev
# ODER: wails dev
# ✅ Desktop-App öffnet sich
```

**Hot Reload aktiviert:**
- Vue.js: Auto-Reload bei Änderungen
- Go: Auto-Reload bei Änderungen
- CSS: Instant-Update

### Production Build

```bash
cd desktop
make build

# Output:
# Windows: ./build/bin/jarvis-desktop.exe
# Linux:   ./build/bin/jarvis-desktop
# macOS:   ./build/bin/jarvis-desktop.app
```

**Binary verteilen:**

1. Binary kopieren: `build/bin/jarvis-desktop[.exe]`
2. JarvisCore Python muss laufen: `python main.py`
3. Binary starten: `./jarvis-desktop`

---

## 🌟 Features

### ✅ Implementiert

- 💬 **Chat Interface**
  - Text-Eingabe mit Enter-Support
  - Chat-Verlauf mit Timestamps
  - Loading-Animation während Processing
  - Wails API-Integration mit Fallback
  
- 📊 **System Monitor** 
  - Live CPU/RAM/GPU/Disk Metriken
  - WebSocket Live-Updates (alle 2s)
  - Farbcodierte Progress-Bars
  - Live-Indicator wenn WebSocket connected
  
- 🧠 **Model Manager**
  - Modelle auflisten
  - Modelle laden/entladen
  - Status-Anzeige (geladen/nicht geladen)
  
- 🔌 **Plugin Manager**
  - Plugins auflisten
  - Plugins aktivieren/deaktivieren
  - Toggle mit visueller Checkbox
  
- ⚙️ **Settings**
  - JarvisCore URL konfigurieren
  - API Token setzen
  - Theme-Auswahl (Dark/Light)
  
- 🔌 **WebSocket Live-Updates**
  - System-Metriken alle 2s
  - Chat-Message Broadcasting
  - Model-Load Events
  - Plugin-Toggle Events

### 🚧 In Entwicklung

- 🎤 Voice Recording Integration
- 🔔 System Notifications
- 🎨 Theme Customization
- 💾 Tray-Icon Support

---

## 🛠️ API Integration

### Wails Composable (empfohlen)

Alle Vue-Komponenten nutzen `useWails()` für API-Calls:

```javascript
import { useWails } from '../composables/useWails'

export default {
  setup() {
    const { api, isDevelopment, wailsReady } = useWails()
    
    const sendMessage = async () => {
      try {
        const response = await api.ProcessCommand("Hallo")
        console.log(response)
      } catch (error) {
        console.error('API Error:', error)
      }
    }
    
    return { sendMessage }
  }
}
```

**Vorteile:**
- ✅ Automatischer Fallback zu simulierten Daten
- ✅ Dev-Mode Detection
- ✅ Error Handling
- ✅ TypeScript-Ready

### Verfügbare Methoden

| Methode | Beschreibung |
|---------|---------------|
| `ProcessCommand(text)` | Nachricht an J.A.R.V.I.S. senden |
| `GetSystemStatus()` | System-Metriken abrufen |
| `GetConversationHistory(limit)` | Chat-Verlauf laden |
| `ListModels()` | Verfügbare Modelle |
| `LoadModel(key)` | Modell laden |
| `GetPlugins()` | Plugin-Liste |
| `TogglePlugin(name, enabled)` | Plugin aktivieren/deaktivieren |

Siehe: [API Reference](docs/API.md)

---

## 🔌 WebSocket Integration

### useWebSocket Composable

```javascript
import { useWebSocket } from '../composables/useWebSocket'

export default {
  setup() {
    const { connected, systemMetrics } = useWebSocket()
    
    // Automatisch aktualisiert bei Broadcast
    watch(systemMetrics, (newMetrics) => {
      console.log('Live Update:', newMetrics)
    })
    
    return { connected, systemMetrics }
  }
}
```

**Live-Events:**
- `system_metrics` - Alle 2 Sekunden
- `chat_message` - Nach Command
- `model_loaded` - Nach Model-Load
- `plugin_toggled` - Nach Toggle

Siehe: [WebSocket Documentation](docs/WEBSOCKET.md)

---

## 📚 Dokumentation

- **🚀 [QUICKSTART.md](QUICKSTART.md)** - Installation, Development, Build
- **🔌 [WEBSOCKET.md](docs/WEBSOCKET.md)** - WebSocket-System erklärt
- **🏛️ [ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System-Design & Flow
- **📡 [API.md](docs/API.md)** - Backend API-Referenz
- **⚙️ [WAILS_INTEGRATION.md](docs/WAILS_INTEGRATION.md)** - Wails Bindings Guide

---

## 🔧 Development Commands

```bash
# Development
make dev              # Dev-Modus starten
make build            # Production Build
make clean            # Build-Artefakte löschen
make install          # Dependencies installieren

# Platform-spezifische Builds
make build-windows    # Windows Binary
make build-linux      # Linux Binary
make build-macos      # macOS Binary
```

---

## 🐛 Troubleshooting

### "window.go is undefined"

- **Ursache:** Wails noch nicht initialisiert
- **Lösung:** `useWails()` nutzt automatischen Fallback
- **Check:** Dev-Mode Banner sichtbar?

### Backend nicht erreichbar

```bash
# 1. JarvisCore läuft?
curl http://127.0.0.1:5050/api/status

# 2. JarvisCore neu starten
cd JarvisCore
python main.py
```

### Build-Fehler

```bash
cd desktop
make clean
make install
make build
```

Weitere Lösungen: [QUICKSTART.md - Troubleshooting](QUICKSTART.md#troubleshooting)

---

## 🤝 Contributing

Beiträge willkommen! Bitte lies die [CONTRIBUTING.md](../CONTRIBUTING.md) im Haupt-Repository.

**Development Workflow:**

1. Fork & Clone
2. Feature-Branch erstellen
3. Änderungen vornehmen
4. Tests durchführen (`make dev`)
5. Pull Request erstellen

---

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/Lautloserspieler/JarvisCore/issues)
- **Docs:** [docs/](docs/)
- **Wails:** [wails.io/docs](https://wails.io/docs/)

---

## 🌟 Highlights

✅ **Wails Bindings** - Nahtlose Go ↔️ Vue.js Integration  
✅ **WebSocket Hub** - Echtzeit-Updates ohne Polling  
✅ **Auto-Fallback** - Funktioniert auch im Dev-Mode ohne Backend  
✅ **Single Binary** - ~20-30MB, keine Dependencies  
✅ **Hot Reload** - Schnelles Entwickeln  
✅ **Cross-Platform** - Windows, Linux, macOS aus einer Codebase  
