// API Base URL
const API_BASE = '/api'

// Generic fetch wrapper
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`)
  }

  return response.json()
}

// Health Check
export const getHealth = () => fetchAPI<{
  status: string
  running: boolean
  version: string
}>('/health')

// System Metrics
export const getSystemMetrics = (details = false) => fetchAPI<any>(
  `/system/metrics?details=${details}`
)

// LLM Status
export const getLLMStatus = () => fetchAPI<any>('/llm/status')

// LLM Models
export const getLLMModels = () => fetchAPI<any>('/llm/models')

// Load LLM Model
export const loadLLMModel = (model: string) => fetchAPI<any>('/llm/load', {
  method: 'POST',
  body: JSON.stringify({ model }),
})

// Unload LLM Model
export const unloadLLMModel = () => fetchAPI<any>('/llm/unload', {
  method: 'POST',
})

// Get Plugins
export const getPlugins = () => fetchAPI<any>('/plugins')

// Send Chat Message
export const sendChatMessage = (text: string, stream = false) => fetchAPI<any>('/chat/message', {
  method: 'POST',
  body: JSON.stringify({ text, stream }),
})

// Get Logs
export const getLogs = (lines = 100) => fetchAPI<any>(`/logs?lines=${lines}`)

// WebSocket Helper
export class JarvisWebSocket {
  private ws: WebSocket | null = null
  private reconnectTimer: number | null = null

  constructor(
    private url: string = 'ws://localhost:8000/ws',
    private onMessage?: (data: any) => void,
    private onConnect?: () => void,
    private onDisconnect?: () => void
  ) {}

  connect() {
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.onConnect?.()
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.onMessage?.(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.onDisconnect?.()
      this.scheduleReconnect()
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, 3000)
  }
}
