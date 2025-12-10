import { useState, useEffect } from 'react'
import { Puzzle, CheckCircle, XCircle } from 'lucide-react'
import { getPlugins } from '../lib/api'

export default function PluginManager() {
  const [plugins, setPlugins] = useState<any[]>([])

  useEffect(() => {
    loadPlugins()
    const interval = setInterval(loadPlugins, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadPlugins = async () => {
    try {
      const data = await getPlugins()
      setPlugins(data.plugins || [])
    } catch (err) {
      console.error('Failed to load plugins:', err)
    }
  }

  return (
    <div className="jarvis-card jarvis-glow p-6">
      <div className="flex items-center gap-3 mb-6">
        <Puzzle className="w-6 h-6 text-jarvis-cyan" />
        <h3 className="text-xl font-bold">Plugins</h3>
      </div>

      <div className="space-y-3">
        {plugins.map((plugin, index) => (
          <div
            key={index}
            className="p-4 bg-jarvis-dark/50 border border-jarvis-cyan/20 rounded-lg hover:border-jarvis-cyan/50 transition-all"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                {plugin.enabled ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-gray-500" />
                )}
                <h4 className="font-bold">{plugin.name || 'Unknown'}</h4>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                plugin.enabled
                  ? 'bg-green-500/20 text-green-500'
                  : 'bg-gray-500/20 text-gray-500'
              }`}>
                {plugin.enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>

            {plugin.description && (
              <p className="text-sm text-gray-400 mb-2">{plugin.description}</p>
            )}

            {plugin.commands && plugin.commands.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {plugin.commands.slice(0, 3).map((cmd: string, i: number) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-jarvis-cyan/10 border border-jarvis-cyan/30 rounded text-xs font-mono"
                  >
                    {cmd}
                  </span>
                ))}
                {plugin.commands.length > 3 && (
                  <span className="px-2 py-1 text-xs text-gray-500">
                    +{plugin.commands.length - 3} more
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {plugins.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          <p>No plugins loaded</p>
        </div>
      )}
    </div>
  )
}
