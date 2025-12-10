import { useState, useEffect } from 'react'
import { Download, Loader2, CheckCircle, XCircle, Cpu } from 'lucide-react'
import { getLLMModels, loadLLMModel, unloadLLMModel } from '../lib/api'

export default function ModelManager() {
  const [models, setModels] = useState<any>(null)
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadModels()
    const interval = setInterval(loadModels, 5000)
    return () => clearInterval(interval)
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
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
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
                  <h4 className="font-bold text-lg">{model.name || key}</h4>
                </div>
                <button
                  onClick={() => handleLoadModel(key)}
                  disabled={isLoaded || isLoading}
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
              </div>

              {/* Model Info */}
              <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
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
