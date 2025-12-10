import { useState, useEffect } from 'react'
import { Loader2, CheckCircle, Cpu, Download, AlertCircle } from 'lucide-react'
import { getLLMModels, loadLLMModel, unloadLLMModel } from '../lib/api'

interface ModelDownloadProgress {
  model: string
  status: 'downloading' | 'completed' | 'error'
  progress?: number
  message?: string
}

export default function ModelManager() {
  const [models, setModels] = useState<any>(null)
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [downloadProgress, setDownloadProgress] = useState<Map<string, ModelDownloadProgress>>(new Map())

  useEffect(() => {
    loadModels()
    const interval = setInterval(loadModels, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // WebSocket für Download-Progress
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'model_download_progress') {
          setDownloadProgress(prev => {
            const newMap = new Map(prev)
            newMap.set(data.model, {
              model: data.model,
              status: data.status,
              progress: data.progress,
              message: data.message,
            })
            return newMap
          })
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    return () => {
      ws.close()
    }
  }, [])

  const loadModels = async () => {
    try {
      const data = await getLLMModels()
      setModels(data)
    } catch (err) {
      console.error('Failed to load models:', err)
    }
  }

  const handleLoadModel = async (modelKey: string) => {
    setLoading(modelKey)
    setError(null)
    try {
      await loadLLMModel(modelKey)
      await loadModels()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(null)
    }
  }

  const handleUnloadModel = async () => {
    setLoading('unload')
    setError(null)
    try {
      await unloadLLMModel()
      await loadModels()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(null)
    }
  }

  const handleDownloadModel = async (modelKey: string) => {
    setError(null)
    
    // Set initial downloading state
    setDownloadProgress(prev => {
      const newMap = new Map(prev)
      newMap.set(modelKey, {
        model: modelKey,
        status: 'downloading',
        progress: 0,
      })
      return newMap
    })

    try {
      const response = await fetch('/api/llm/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'download', model: modelKey }),
      })

      if (!response.ok) {
        throw new Error('Download failed')
      }

      const result = await response.json()
      
      if (result.success) {
        setDownloadProgress(prev => {
          const newMap = new Map(prev)
          newMap.set(modelKey, {
            model: modelKey,
            status: 'completed',
            progress: 100,
          })
          return newMap
        })
        await loadModels()
      } else {
        throw new Error('Download failed')
      }
    } catch (err: any) {
      setError(err.message)
      setDownloadProgress(prev => {
        const newMap = new Map(prev)
        newMap.set(modelKey, {
          model: modelKey,
          status: 'error',
          message: err.message,
        })
        return newMap
      })
    }
  }

  const getDownloadProgress = (modelKey: string): ModelDownloadProgress | null => {
    return downloadProgress.get(modelKey) || null
  }

  return (
    <div className="jarvis-card jarvis-glow p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Cpu className="w-6 h-6 text-jarvis-cyan" />
          <h3 className="text-xl font-bold">LLM Models</h3>
        </div>
        {models?.current && (
          <button
            onClick={handleUnloadModel}
            disabled={loading === 'unload'}
            className="jarvis-button text-sm"
          >
            {loading === 'unload' ? 'Unloading...' : 'Unload Current'}
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* Current Model */}
      {models?.current && (
        <div className="mb-4 p-4 bg-jarvis-cyan/10 border border-jarvis-cyan/50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="font-bold text-jarvis-cyan">Currently Loaded</span>
          </div>
          <p className="text-lg font-mono">{models.current}</p>
        </div>
      )}

      {/* Available Models */}
      <div className="space-y-3">
        {models?.available && Object.entries(models.available).map(([key, model]: [string, any]) => {
          const isLoaded = models.current === key
          const isLoading = loading === key
          const downloadInfo = getDownloadProgress(key)
          const isDownloading = downloadInfo?.status === 'downloading'
          const downloadCompleted = downloadInfo?.status === 'completed'
          const downloadError = downloadInfo?.status === 'error'

          return (
            <div
              key={key}
              className={`p-4 rounded-lg border transition-all ${
                isLoaded
                  ? 'bg-jarvis-cyan/20 border-jarvis-cyan'
                  : 'bg-jarvis-dark/50 border-jarvis-cyan/20 hover:border-jarvis-cyan/50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  {isLoaded && <CheckCircle className="w-5 h-5 text-green-500" />}
                  <div>
                    <h4 className="font-bold text-lg">{model.name || key}</h4>
                    {model.downloaded === false && (
                      <span className="text-xs text-gray-500">Not downloaded</span>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2">
                  {/* Download Button */}
                  {model.downloaded === false && !isDownloading && !downloadCompleted && (
                    <button
                      onClick={() => handleDownloadModel(key)}
                      disabled={isDownloading}
                      className="px-3 py-2 rounded-lg font-orbitron text-sm bg-jarvis-blue/10 border border-jarvis-blue text-jarvis-blue hover:bg-jarvis-blue hover:text-jarvis-darker transition-all flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      <span>Download</span>
                    </button>
                  )}

                  {/* Load Button */}
                  {(model.downloaded !== false || downloadCompleted) && (
                    <button
                      onClick={() => handleLoadModel(key)}
                      disabled={isLoaded || isLoading || isDownloading}
                      className={`px-4 py-2 rounded-lg font-orbitron text-sm transition-all ${
                        isLoaded
                          ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                          : isLoading
                          ? 'bg-jarvis-cyan/50 text-jarvis-darker'
                          : 'bg-jarvis-cyan/10 border border-jarvis-cyan text-jarvis-cyan hover:bg-jarvis-cyan hover:text-jarvis-darker'
                      }`}
                    >
                      {isLoading ? (
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Loading...</span>
                        </div>
                      ) : isLoaded ? (
                        'Loaded'
                      ) : (
                        'Load Model'
                      )}
                    </button>
                  )}
                </div>
              </div>

              {/* Download Progress */}
              {isDownloading && (
                <div className="mt-3">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-jarvis-blue">Downloading...</span>
                    <span className="text-jarvis-cyan font-mono">{downloadInfo.progress || 0}%</span>
                  </div>
                  <div className="w-full h-2 bg-jarvis-dark rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-jarvis-blue to-jarvis-cyan transition-all duration-300"
                      style={{ width: `${downloadInfo.progress || 0}%` }}
                    />
                  </div>
                  {downloadInfo.message && (
                    <p className="text-xs text-gray-400 mt-1">{downloadInfo.message}</p>
                  )}
                </div>
              )}

              {/* Download Complete */}
              {downloadCompleted && (
                <div className="mt-3 p-2 bg-green-500/10 border border-green-500/30 rounded text-sm text-green-500 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  <span>Download completed!</span>
                </div>
              )}

              {/* Download Error */}
              {downloadError && (
                <div className="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  <span>{downloadInfo.message || 'Download failed'}</span>
                </div>
              )}

              {/* Model Info */}
              <div className="grid grid-cols-2 gap-2 text-sm text-gray-400 mt-2">
                {model.size && (
                  <div>
                    <span className="text-gray-500">Size:</span>{' '}
                    <span className="text-white">{model.size}</span>
                  </div>
                )}
                {model.type && (
                  <div>
                    <span className="text-gray-500">Type:</span>{' '}
                    <span className="text-white">{model.type}</span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {!models?.available && (
        <div className="text-center text-gray-500 py-8">
          <p>No models available</p>
        </div>
      )}
    </div>
  )
}
