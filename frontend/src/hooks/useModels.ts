// frontend/src/hooks/useModels.ts
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

interface ModelInfo {
  display_name: string
  description: string
  parameters: string
  size_gb: number
  context_length: number
  downloaded: boolean
  strengths?: string[]
}

interface DownloadProgress {
  model: string
  status: string
  downloaded: number
  total: number
  percent: number
  speed: number
  speed_mbps: number
  eta: string
  error?: string
}

interface ModelVariant {
  name: string
  url: string
  quantization: string
  size_estimate: string
}

export function useModels() {
  const models = ref<Record<string, ModelInfo>>({})
  const activeDownloads = ref<Record<string, DownloadProgress>>({})
  let eventSource: EventSource | null = null

  const loadModels = async () => {
    try {
      const response = await axios.get('/api/models/available')
      if (response.data.success) {
        models.value = response.data.models
      }
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }

  const startDownload = async (modelKey: string, quantization: string = 'Q4_K_M') => {
    try {
      const response = await axios.post('/api/models/download', {
        model_key: modelKey,
        quantization
      })

      if (response.data.success) {
        // Start listening to progress
        connectProgressStream()
      }
    } catch (error: any) {
      console.error('Failed to start download:', error)
      const message = error.response?.data?.error || 'Download failed to start'
      alert(message)
    }
  }

  const cancelDownload = async (modelKey: string) => {
    try {
      await axios.post('/api/models/cancel', {
        model_key: modelKey
      })
      
      delete activeDownloads.value[modelKey]
    } catch (error) {
      console.error('Failed to cancel download:', error)
    }
  }

  const deleteModel = async (modelKey: string) => {
    try {
      const response = await axios.post('/api/models/delete', {
        model_key: modelKey
      })

      if (response.data.success) {
        await loadModels()
      }
    } catch (error) {
      console.error('Failed to delete model:', error)
      alert('Delete failed')
    }
  }

  const getVariants = async (modelKey: string): Promise<ModelVariant[]> => {
    try {
      const response = await axios.get('/api/models/variants', {
        params: { model_key: modelKey }
      })

      if (response.data.success) {
        return response.data.variants
      }
    } catch (error) {
      console.error('Failed to get variants:', error)
    }
    return []
  }

  const connectProgressStream = () => {
    if (eventSource) return

    eventSource = new EventSource('/api/models/download/progress')

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        // Update active downloads
        Object.assign(activeDownloads.value, data)

        // Remove completed/failed downloads after 2 seconds
        for (const [key, progress] of Object.entries(data)) {
          const p = progress as DownloadProgress
          if (p.status === 'completed') {
            setTimeout(() => {
              delete activeDownloads.value[key]
              loadModels() // Refresh model list
            }, 2000)
          } else if (p.status === 'error' || p.status === 'failed') {
            // Keep error visible longer
            setTimeout(() => {
              delete activeDownloads.value[key]
            }, 5000)
          }
        }
      } catch (err) {
        console.error('Failed to parse SSE data:', err)
      }
    }

    eventSource.onerror = () => {
      console.error('SSE connection error')
      eventSource?.close()
      eventSource = null
      
      // Retry connection after 5 seconds if there are active downloads
      if (Object.keys(activeDownloads.value).length > 0) {
        setTimeout(connectProgressStream, 5000)
      }
    }
  }

  onMounted(() => {
    connectProgressStream()
  })

  onUnmounted(() => {
    eventSource?.close()
  })

  return {
    models,
    activeDownloads,
    loadModels,
    startDownload,
    cancelDownload,
    deleteModel,
    getVariants
  }
}
