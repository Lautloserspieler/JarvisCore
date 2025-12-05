# WebSocket Integration

## Überblick

Die Desktop-UI nutzt ein **WebSocket-ähnliches System** für Live-Updates zwischen Go Backend und Vue.js Frontend.

> **Wichtig:** Wails nutzt kein natives WebSocket-Protokol, sondern **Wails Runtime Events** für bidirektionale Kommunikation.

## Architektur

```
Go Backend (WebSocket Hub)
    │
    │ Broadcasts
    ↓
Wails Runtime
    │
    │ Events
    ↓
Vue.js Frontend (Event Listeners)
```

## Backend: WebSocket Hub

### Initialisierung

```go
// internal/app/app.go
func (a *App) Startup(ctx context.Context) {
    a.StartWebSocketHub()  // Hub starten
}

func (a *App) StartWebSocketHub() {
    a.wsHub = websocket.NewHub()
    go a.wsHub.Run()
    go a.broadcastSystemMetrics()  // Auto-Broadcaster
}
```

### Broadcasting

```go
// Nachricht an alle Clients broadcasten
a.BroadcastMessage("event_type", map[string]interface{}{
    "key": "value",
})
```

### Automatische Broadcasts

**System-Metriken (alle 2 Sekunden):**

```go
func (a *App) broadcastSystemMetrics() {
    ticker := time.NewTicker(2 * time.Second)
    defer ticker.Stop()
    
    for {
        select {
        case <-ticker.C:
            metrics, _ := a.GetSystemStatus()
            a.wsHub.BroadcastJSON("system_metrics", metrics)
        }
    }
}
```

## Frontend: Event Listeners

### useWebSocket Composable

```javascript
import { useWebSocket } from '../composables/useWebSocket'

const { connected, systemMetrics } = useWebSocket()

// Automatisch aktualisiert wenn Backend broadcastet
watch(systemMetrics, (newMetrics) => {
    console.log('Live Update:', newMetrics)
})
```

### Manuelle Event-Subscription (Wails Runtime)

```javascript
import { EventsOn } from '@wailsapp/runtime'

EventsOn('system_metrics', (data) => {
    console.log('Neue Metriken:', data)
})
```

## Event Types

### `system_metrics`

Automatisch alle 2 Sekunden:

```json
{
  "cpu": 45.2,
  "memory": 62.8,
  "disk": 38.5,
  "gpu": 23.1
}
```

**Verwendung:**
- SystemMonitor Live-Updates
- Dashboard-Metriken

### `chat_message`

Nach erfolgreichem Command:

```json
{
  "role": "assistant",
  "text": "Antwort von J.A.R.V.I.S."
}
```

**Verwendung:**
- Multi-Window Chat-Sync
- Notification-System

### `model_loaded`

Nach Model-Load:

```json
{
  "model": "mistral"
}
```

**Verwendung:**
- ModelManager UI-Update
- Status-Notifications

### `plugin_toggled`

Nach Plugin-Toggle:

```json
{
  "plugin": "Wikipedia",
  "enabled": true
}
```

**Verwendung:**
- PluginManager UI-Sync

## Implementierungsbeispiele

### System-Monitor mit Live-Updates

```vue
<template>
  <div>
    <span v-if="wsConnected" class="live-indicator">
      <span class="pulse"></span> Live
    </span>
    <div>CPU: {{ metrics.cpu }}%</div>
  </div>
</template>

<script>
import { useWebSocket } from '../composables/useWebSocket'

export default {
  setup() {
    const { connected: wsConnected, systemMetrics } = useWebSocket()
    const metrics = ref({ cpu: 0 })
    
    watch(systemMetrics, (newMetrics) => {
      if (newMetrics) {
        metrics.value = newMetrics
      }
    })
    
    return { wsConnected, metrics }
  }
}
</script>
```

### Chat mit Multi-Window Sync

```javascript
import { EventsOn } from '@wailsapp/runtime'

EventsOn('chat_message', (message) => {
  // Nachricht in Chat-Verlauf einfügen
  messages.value.push(message)
  scrollToBottom()
})
```

## Performance

### Hub-Kapazität

```go
type Hub struct {
    clients    map[string]*Client
    broadcast  chan Message  // Buffer: 256 Messages
}
```

- **Buffer:** 256 Messages
- **Clients:** Unbegrenzt (Memory-Limited)
- **Broadcast:** Non-Blocking (skip bei vollem Buffer)

### Optimierung

1. **Throttling:** System-Metriken alle 2s (nicht jede Sekunde)
2. **Conditional Broadcasting:** Nur wenn Clients verbunden
3. **Non-Blocking:** Channel-Operations mit `select` + `default`

## Error Handling

### Backend

```go
func (h *Hub) Broadcast(message Message) {
    select {
    case h.broadcast <- message:
        // Message gequeued
    default:
        log.Println("⚠️  Broadcast Buffer voll")
    }
}
```

### Frontend

```javascript
const { connected, systemMetrics } = useWebSocket()

if (!connected.value) {
    // Fallback: Polling
    setInterval(fetchMetrics, 5000)
}
```

## Testing

### Backend testen

```bash
go test ./internal/websocket
```

### Frontend testen

```javascript
import { mount } from '@vue/test-utils'
import SystemMonitor from './SystemMonitor.vue'

test('WebSocket Updates', async () => {
  const wrapper = mount(SystemMonitor)
  // Mock WebSocket data
  wrapper.vm.systemMetrics = { cpu: 50 }
  await wrapper.vm.$nextTick()
  expect(wrapper.text()).toContain('50%')
})
```

## Best Practices

1. **Immer `useWebSocket()` Composable nutzen**
   - Automatisches Lifecycle-Management
   - Cleanup bei Component Unmount

2. **Fallback implementieren**
   - Polling falls WebSocket nicht connected
   - Graceful Degradation

3. **Debounce bei häufigen Updates**
   - UI nicht bei jedem Broadcast re-rendern
   - `watch` mit `debounce` nutzen

4. **Error Boundaries**
   - WebSocket-Fehler nicht ganze App crashen lassen

## Migration von HTTP zu WebSocket

### Vorher (Polling)

```javascript
setInterval(async () => {
  const metrics = await api.GetSystemStatus()  // HTTP Request
  updateUI(metrics)
}, 2000)
```

### Nachher (WebSocket)

```javascript
const { systemMetrics } = useWebSocket()

watch(systemMetrics, (metrics) => {
  updateUI(metrics)  // Automatisch bei Broadcast
})
```

**Vorteile:**
- ✅ Weniger HTTP-Requests
- ✅ Echtzeit-Updates
- ✅ Bessere Performance
- ✅ Weniger Latenz

## Weitere Infos

- Wails Runtime: https://wails.io/docs/reference/runtime/intro
- Go Channels: https://go.dev/tour/concurrency/2
- Vue.js Watch: https://vuejs.org/api/reactivity-core.html#watch
