import { useState, useEffect } from 'react'
import { Activity, Cpu, HardDrive, Mic, MessageSquare, Settings, Zap } from 'lucide-react'
import VoiceVisualizer from '../components/VoiceVisualizer'
import { getHealth, getSystemMetrics, getLLMStatus } from '../lib/api'

export default function Index() {
  const [health, setHealth] = useState<any>(null)
  const [metrics, setMetrics] = useState<any>(null)
  const [llmStatus, setLLMStatus] = useState<any>(null)
  const [listening, setListening] = useState(false)

  useEffect(() => {
    // Initial load
    loadData()

    // Refresh every 2 seconds
    const interval = setInterval(loadData, 2000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [healthData, metricsData, llmData] = await Promise.all([
        getHealth(),
        getSystemMetrics(),
        getLLMStatus(),
      ])
      setHealth(healthData)
      setMetrics(metricsData)
      setLLMStatus(llmData)
    } catch (error) {
      console.error('Failed to load data:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-jarvis-darker via-jarvis-dark to-jarvis-darker">
      {/* Header */}
      <header className="border-b border-jarvis-cyan/20 backdrop-blur-md">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-jarvis-cyan/20 border-2 border-jarvis-cyan flex items-center justify-center animate-pulse-slow">
                <Zap className="w-6 h-6 text-jarvis-cyan" />
              </div>
              <div>
                <h1 className="text-2xl font-bold font-orbitron tracking-wider text-jarvis-cyan">
                  J.A.R.V.I.S.
                </h1>
                <p className="text-xs text-gray-400">Just A Rather Very Intelligent System</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Status Badge */}
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-jarvis-dark/50 border border-jarvis-cyan/30">
                <div className={`w-2 h-2 rounded-full ${
                  health?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'
                } animate-pulse`} />
                <span className="text-sm">{health?.running ? 'Online' : 'Offline'}</span>
              </div>

              <button className="jarvis-button">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - System Metrics */}
          <div className="space-y-6">
            {/* CPU */}
            <div className="jarvis-card jarvis-glow p-6">
              <div className="flex items-center gap-3 mb-4">
                <Cpu className="w-6 h-6 text-jarvis-cyan" />
                <h3 className="text-lg font-bold">CPU</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Auslastung</span>
                  <span className="text-jarvis-cyan font-mono">
                    {metrics?.summary?.cpu_percent?.toFixed(1) || '0.0'}%
                  </span>
                </div>
                <div className="w-full h-2 bg-jarvis-dark rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-jarvis-cyan to-jarvis-blue transition-all duration-300"
                    style={{ width: `${metrics?.summary?.cpu_percent || 0}%` }}
                  />
                </div>
              </div>
            </div>

            {/* RAM */}
            <div className="jarvis-card jarvis-glow p-6">
              <div className="flex items-center gap-3 mb-4">
                <Activity className="w-6 h-6 text-jarvis-cyan" />
                <h3 className="text-lg font-bold">RAM</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Verwendet</span>
                  <span className="text-jarvis-cyan font-mono">
                    {((metrics?.summary?.memory_used_gb || 0)).toFixed(1)} GB / 
                    {((metrics?.summary?.memory_total_gb || 0)).toFixed(1)} GB
                  </span>
                </div>
                <div className="w-full h-2 bg-jarvis-dark rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-jarvis-cyan to-jarvis-blue transition-all duration-300"
                    style={{ width: `${metrics?.summary?.memory_percent || 0}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Storage */}
            <div className="jarvis-card jarvis-glow p-6">
              <div className="flex items-center gap-3 mb-4">
                <HardDrive className="w-6 h-6 text-jarvis-cyan" />
                <h3 className="text-lg font-bold">Storage</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Verwendet</span>
                  <span className="text-jarvis-cyan font-mono">
                    {metrics?.summary?.disk_percent?.toFixed(1) || '0.0'}%
                  </span>
                </div>
                <div className="w-full h-2 bg-jarvis-dark rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-jarvis-cyan to-jarvis-blue transition-all duration-300"
                    style={{ width: `${metrics?.summary?.disk_percent || 0}%` }}
                  />
                </div>
              </div>
            </div>

            {/* LLM Status */}
            <div className="jarvis-card jarvis-glow p-6">
              <h3 className="text-lg font-bold mb-4">LLM Status</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Model</span>
                  <span className="text-jarvis-cyan">{llmStatus?.current || 'None'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Status</span>
                  <span className={llmStatus?.active ? 'text-green-500' : 'text-gray-500'}>
                    {llmStatus?.active ? 'Loaded' : 'Not Loaded'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Center Column - Chat & Voice */}
          <div className="lg:col-span-2 space-y-6">
            {/* Voice Visualizer */}
            <div className="jarvis-card jarvis-glow p-8">
              <div className="flex flex-col items-center gap-6">
                <VoiceVisualizer listening={listening} />
                
                <button
                  onClick={() => setListening(!listening)}
                  className={`px-8 py-4 rounded-full font-orbitron text-lg transition-all ${
                    listening
                      ? 'bg-jarvis-cyan text-jarvis-darker shadow-lg shadow-jarvis-cyan/50'
                      : 'bg-jarvis-cyan/10 border-2 border-jarvis-cyan text-jarvis-cyan hover:bg-jarvis-cyan/20'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Mic className="w-6 h-6" />
                    <span>{listening ? 'Listening...' : 'Activate'}</span>
                  </div>
                </button>
              </div>
            </div>

            {/* Chat */}
            <div className="jarvis-card jarvis-glow p-6">
              <div className="flex items-center gap-3 mb-4">
                <MessageSquare className="w-6 h-6 text-jarvis-cyan" />
                <h3 className="text-lg font-bold">Chat</h3>
              </div>
              
              {/* Messages */}
              <div className="h-64 overflow-y-auto mb-4 space-y-3">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-jarvis-cyan/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold">J</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-300">
                      Willkommen! Wie kann ich Ihnen helfen?
                    </p>
                  </div>
                </div>
              </div>

              {/* Input */}
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="Nachricht eingeben..."
                  className="jarvis-input"
                />
                <button className="jarvis-button">
                  Senden
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-jarvis-cyan/20 mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-gray-500">
          <p>J.A.R.V.I.S. v{health?.version || '2.0.0'} • Built with ❤️ by the JARVIS Team</p>
        </div>
      </footer>
    </div>
  )
}
