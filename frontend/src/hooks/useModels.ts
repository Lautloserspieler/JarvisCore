import { useState, useEffect } from 'react'
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
  const [models, setModels] = useState<Record<string, ModelInfo>>({})
  const [activeDownloads, setActiveDownloads] = useState<Record<string, DownloadProgress>>({})
  let eventSource: EventSource | null = null

  const loadModels = async () => {
    try {
      const response = await axios.get('/api/models/available')
      if (response.data.success) {
        setModels(response.data.models)
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
        connectProgressStream()
      }
    } catch (error: any) {
      console.error('Failed to start download:', error)
      const message = error.response?.data?.error || 'Download konnte nicht gestartet werden'
      alert(message)
    }
  }

  const cancelDownload = async (modelKey: string) => {
    try {
      await axios.post('/api/models/cancel', {
        model_key: modelKey
      })
      
      setActiveDownloads(prev => {
        const updated = { ...prev }
        delete updated[modelKey]
        return updated
      })
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
      alert('Löschen fehlgeschlagen')
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
        
        setActiveDownloads(prev => {
          const updated = { ...prev, ...data }
          
          // Remove completed/failed downloads after delay
          Object.entries(data).forEach(([key, progress]) => {
            const p = progress as DownloadProgress
            if (p.status === 'completed') {
              setTimeout(() => {
                setActiveDownloads(current => {
                  const newState = { ...current }
                  delete newState[key]
                  return newState
                })
                loadModels()
              }, 2000)
            } else if (p.status === 'error' || p.status === 'failed') {
              setTimeout(() => {
                setActiveDownloads(current => {
                  const newState = { ...current }
                  delete newState[key]
                  return newState
                })
              }, 5000)
            }
          })
          
          return updated
        })
      } catch (err) {
        console.error('Failed to parse SSE data:', err)
      }
    }

    eventSource.onerror = () => {
      console.error('SSE connection error')
      eventSource?.close()
      eventSource = null
      
      // Retry if there are active downloads
      if (Object.keys(activeDownloads).length > 0) {
        setTimeout(connectProgressStream, 5000)
      }
    }
  }

  useEffect(() => {
    connectProgressStream()
    
    return () => {
      eventSource?.close()
    }
  }, [])

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
