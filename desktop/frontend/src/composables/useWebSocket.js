/**
 * WebSocket Composable für Live-Updates
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useWails } from './useWails'

export function useWebSocket() {
  const { wailsReady } = useWails()
  
  const connected = ref(false)
  const messages = ref([])
  const systemMetrics = ref(null)
  
  let eventListeners = []
  
  const subscribeToEvents = () => {
    if (!wailsReady.value || !window.runtime) return
    
    // Subscribe to Wails Runtime Events
    // TODO: Wails Runtime Events API nutzen
    
    // Placeholder: Poll für System-Metriken
    const pollInterval = setInterval(async () => {
      try {
        const metrics = await window.go.app.App.GetSystemStatus()
        systemMetrics.value = metrics
      } catch (error) {
        console.error('Fehler beim Abrufen der Metriken:', error)
      }
    }, 2000)
    
    eventListeners.push(() => clearInterval(pollInterval))
    connected.value = true
  }
  
  const unsubscribeFromEvents = () => {
    eventListeners.forEach(cleanup => cleanup())
    eventListeners = []
    connected.value = false
  }
  
  onMounted(() => {
    if (wailsReady.value) {
      subscribeToEvents()
    }
  })
  
  onUnmounted(() => {
    unsubscribeFromEvents()
  })
  
  return {
    connected,
    messages,
    systemMetrics
  }
}
