# Desktop UI - API Reference

## Go Backend API

Alle Funktionen können vom Vue.js Frontend via Wails aufgerufen werden.

### `ProcessCommand(text string) (string, error)`
Sendet Nachricht an JarvisCore.

**Beispiel:**
```javascript
import { ProcessCommand } from '../wailsjs/go/app/App'

const response = await ProcessCommand("Wie spät ist es?")
```

### `GetSystemStatus() (map[string]interface{}, error)`
Holt System-Metriken.

**Rückgabe:**
```json
{
  "cpu": 45.2,
  "memory": 62.8,
  "disk": 38.5,
  "gpu": 23.1
}
```

### `GetConversationHistory(limit int) ([]map[string]interface{}, error)`
Holt Chat-Verlauf.

### `ListModels() ([]map[string]interface{}, error)`
Holt verfügbare Modelle.

### `LoadModel(modelKey string) error`
Lädt Modell.

### `GetPlugins() ([]map[string]interface{}, error)`
Holt Plugin-Liste.

### `TogglePlugin(pluginName string, enabled bool) error`
Aktiviert/Deaktiviert Plugin.

## JarvisCore REST API

Die Go-Bridge kommuniziert mit diesen Endpoints:

- `POST /api/chat` - Nachricht senden
- `GET /api/chat/history` - Verlauf abrufen
- `GET /api/system/metrics` - System-Metriken
- `GET /api/models` - Modelle abrufen
- `POST /api/models/load` - Modell laden
- `GET /api/plugins` - Plugins abrufen
- `POST /api/plugins/toggle` - Plugin toggle
