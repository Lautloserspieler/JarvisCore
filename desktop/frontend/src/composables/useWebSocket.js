/**
 * WebSocket Composable für Live-Updates
 * Erweitert mit Security Challenge, Knowledge Feed, Memory Updates
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useWails } from './useWails'

export function useWebSocket() {
  const { wailsReady } = useWails()
  
  // Connection State
  const connected = ref(false)
  
  // Chat & Messages
  const messages = ref([])
  
  // System Metrics
  const systemMetrics = ref(null)
  
  // Security Challenge
  const securityChallenge = ref({
    active: false,
    command: '',
    message: '',
    hint: ''
  })
  
  // Knowledge Feed (live updates)
  const knowledgeFeed = ref([])
  
  // Memory Updates
  const memoryUpdate = ref(null)
  
  // Model Download Progress
  const modelDownloads = ref({})
  
  // Plugin Updates
  const pluginUpdate = ref(null)
  
  // Training Status
  const trainingStatus = ref(null)
  
  // Speech Status
  const speechStatus = ref({
    available: false,
    enabled: false,
    listening: false
  })
  
  let eventListeners = []
  
  /**
   * Handle incoming WebSocket events
   */
  const handleEvent = (event) => {
    const { type, payload, timestamp } = event
    
    switch (type) {
      // Chat Messages
      case 'assistant_message':
      case 'user_message':
        messages.value.push({
          role: type === 'assistant_message' ? 'assistant' : 'user',
          text: payload?.text,
          timestamp: timestamp || Date.now() / 1000
        })
        break
      
      // System Metrics
      case 'system_metrics':
        systemMetrics.value = payload
        break
      
      // Security Challenge
      case 'security_challenge':
        securityChallenge.value = {
          active: Boolean(payload?.active),
          command: payload?.command || '',
          message: payload?.hint || 'Passphrase erforderlich',
          hint: payload?.hint || ''
        }
        break
      
      case 'security_result':
        securityChallenge.value = { active: false }
        break
      
      // Knowledge Feed
      case 'knowledge_progress':
        const text = typeof payload === 'string' 
          ? payload 
          : payload?.message || JSON.stringify(payload)
        const ts = new Date(timestamp ? timestamp * 1000 : Date.now()).toLocaleTimeString()
        
        knowledgeFeed.value.unshift({ text, ts })
        knowledgeFeed.value = knowledgeFeed.value.slice(0, 12)
        break
      
      // Memory Updates
      case 'memory_update':
        memoryUpdate.value = payload
        break
      
      // Model Download Progress
      case 'model_download_progress':
        const model = payload?.model
        if (model) {
          modelDownloads.value[model] = {
            status: payload.status || 'in_progress',
            downloaded: payload.downloaded || 0,
            total: payload.total || 0,
            percent: payload.percent,
            message: payload.message,
            speed: payload.speed,
            eta: payload.eta,
            updated_at: Date.now()
          }
          
          // Clean up completed/failed downloads after 3s
          if (['completed', 'error', 'failed', 'already_exists'].includes(payload.status)) {
            setTimeout(() => {
              delete modelDownloads.value[model]
            }, 3000)
          }
        }
        break
      
      // Plugin Updates
      case 'plugin_toggled':
      case 'plugin_loaded':
        pluginUpdate.value = payload
        break
      
      // Training Updates
      case 'training_started':
      case 'training_completed':
        trainingStatus.value = payload
        break
      
      // Speech Status
      case 'status':
        if (payload?.speech_status) {
          speechStatus.value = {
            available: payload.speech_status.available !== false,
            enabled: payload.speech_status.enabled !== false,
            listening: Boolean(payload.speech_status.listening),
            wake_word_enabled: Boolean(payload.speech_status.wake_word_enabled),
            speech_mode: payload.speech_status.speech_mode || payload.speech_status.active_mode
          }
        }
        break
      
      // Context Updates
      case 'context_update':
        // Context updates können in anderen Komponenten gehandled werden
        break
      
      default:
        console.log('[WebSocket] Unhandled event type:', type, payload)
    }
  }
  
  /**
   * Subscribe to WebSocket events via Wails Runtime
   */
  const subscribeToEvents = () => {
    if (!wailsReady.value || !window.runtime) return
    
    // TODO: Wails Runtime Events API nutzen wenn verfügbar
    // runtime.EventsOn('websocket_event', handleEvent)
    
    // Fallback: Polling für System-Metriken
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
  
  /**
   * Unsubscribe from all events
   */
  const unsubscribeFromEvents = () => {
    eventListeners.forEach(cleanup => cleanup())
    eventListeners = []
    connected.value = false
  }
  
  /**
   * Manually trigger event (for testing)
   */
  const triggerEvent = (type, payload) => {
    handleEvent({ type, payload, timestamp: Date.now() / 1000 })
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
    // Connection
    connected,
    
    // Chat & Messages
    messages,
    
    // System
    systemMetrics,
    
    // Security
    securityChallenge,
    
    // Knowledge
    knowledgeFeed,
    
    // Memory
    memoryUpdate,
    
    // Models
    modelDownloads,
    
    // Plugins
    pluginUpdate,
    
    // Training
    trainingStatus,
    
    // Speech
    speechStatus,
    
    // Methods
    triggerEvent
  }
}
