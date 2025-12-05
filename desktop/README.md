# 🖥️ J.A.R.V.I.S. Desktop UI

**Native Desktop-Oberfläche für JarvisCore mit Wails + Vue.js**

---

## 🎯 Überblick

Diese Desktop-Anwendung bietet eine native, performante Alternative zur Web-UI von JarvisCore.

### Vorteile gegenüber Web-UI
- ✅ **Native Performance** - Kein Browser-Overhead
- ✅ **System-Integration** - Tray-Icon, Shortcuts, Benachrichtigungen
- ✅ **Single Binary** - Nur ~20-30MB
- ✅ **Offline-First** - Keine Port-Konflikte
- ✅ **Cross-Platform** - Windows, Linux, macOS

---

## 🏗️ Architektur

```
desktop/
├── backend/              # Go Backend
│   ├── cmd/jarvis/      # Main entry
│   └── internal/        # Core logic
│       ├── app/         # App manager
│       └── bridge/      # JarvisCore bridge
├── frontend/            # Vue.js UI
│   ├── src/
│   │   ├── components/  # Vue components
│   │   └── App.vue      # Root
│   └── package.json
└── wails.json           # Wails config
```

### Kommunikation

```
Vue.js Frontend
    ↓ Wails Bridge
Go Backend
    ↓ HTTP/WebSocket
JarvisCore Python (localhost:5050)
    ↓
LLM / STT / TTS / Plugins
```

---

## ⚡ Quick Start

### Prerequisites

- Go 1.21+
- Node.js 18+
- Wails CLI: `go install github.com/wailsapp/wails/v2/cmd/wails@latest`

### Installation

```bash
cd desktop

# Frontend dependencies
cd frontend
npm install
cd ..

# Go dependencies
cd backend
go mod download
cd ..
```

### Development

```bash
# Terminal 1: Start JarvisCore
cd ..
python main.py

# Terminal 2: Start Desktop UI
cd desktop
wails dev
```

### Build

```bash
cd desktop
wails build

# Output: ./build/bin/jarvis-desktop[.exe]
```

---

## 🎨 Features

- 💬 **Chat Interface** - Wie Web-UI, aber nativ
- 📊 **System Monitor** - Live CPU/RAM/GPU Metriken
- 🧠 **Model Manager** - LLM-Verwaltung
- 🔌 **Plugin Manager** - Plugin-Steuerung
- 🎤 **Voice Input** - Integrierte Sprachsteuerung
- ⚙️ **Settings** - Konfiguration

---

## 🔧 Development

Siehe separate Dokumentation:
- [Architecture](./docs/ARCHITECTURE.md)
- [Development Guide](./docs/DEVELOPMENT.md)
- [API Reference](./docs/API.md)
