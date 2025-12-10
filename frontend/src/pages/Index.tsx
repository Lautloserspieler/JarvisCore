import { useState, useEffect } from 'react'
import { Activity, Cpu, HardDrive, Mic, Settings as SettingsIcon, Zap } from 'lucide-react'
import VoiceVisualizer from '../components/VoiceVisualizer'
import ModelManager from '../components/ModelManager'
import PluginManager from '../components/PluginManager'
import SettingsPanel from '../components/SettingsPanel'
import ChatBox from '../components/ChatBox'
import SystemControl from '../components/SystemControl'
import { getHealth, getSystemMetrics, getLLMStatus } from '../lib/api'

type Tab = 'dashboard' | 'models' | 'plugins' | 'chat'

export default function Index() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')
  const [health, setHealth] = useState<any>(null)
  const [metrics, setMetrics] = useState<any>(null)
  const [llmStatus, setLLMStatus] = useState<any>(null)
  const [listening, setListening] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  useEffect(() => {
    loadData()
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

  // Helper: Get metric with fallback
  const getMetric = (path: string, fallback: number = 0): number => {
    try {
      const parts = path.split('.')
      let value: any = metrics
      for (const part of parts) {
        if (value && typeof value === 'object') {
          value = value[part]
        } else {
          return fallback
        }
      }
      return typeof value === 'number' ? value : fallback
    } catch {
      return fallback
    }
  }

  const cpuPercent = getMetric('summary.cpu_percent', 0)
  const memoryPercent = getMetric('summary.memory_percent', 0)
  const memoryUsed = getMetric('summary.memory_used_gb', 0)
  const memoryTotal = getMetric('summary.memory_total_gb', 0)
  const diskPercent = getMetric('summary.disk_percent', 0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-jarvis-darker via-jarvis-dark to-jarvis-darker">
      {/* Header */}
      <header className="border-b border-jarvis-cyan/20 backdrop-blur-md sticky top-0 z-40">
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

              <button 
                onClick={() => setShowSettings(true)}
                className="jarvis-button"
              >
                <SettingsIcon className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex gap-2 mt-4">
            {[
              { id: 'dashboard', label: 'Dashboard' },
              { id: 'models', label: 'Models' },
              { id: 'plugins', label: 'Plugins' },
              { id: 'chat', label: 'Chat' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as Tab)}
                className={`px-4 py-2 rounded-lg font-orbitron transition-all ${
                  activeTab === tab.id
                    ? 'bg-jarvis-cyan/20 border border-jarvis-cyan text-jarvis-cyan'
                    : 'border border-jarvis-cyan/20 text-gray-400 hover:border-jarvis-cyan/50 hover:text-jarvis-cyan'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
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
                      {cpuPercent.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-jarvis-dark rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-jarvis-cyan to-jarvis-blue transition-all duration-300"
                      style={{ width: `${cpuPercent}%` }}
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
                      {memoryUsed.toFixed(1)} GB / {memoryTotal.toFixed(1)} GB
                    </span>
                  </div>
                  <div className="w-full h-2 bg-jarvis-dark rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-jarvis-cyan to-jarvis-blue transition-all duration-300"
                      style={{ width: `${memoryPercent}%` }}
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
                      {diskPercent.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-jarvis-dark rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-jarvis-cyan to-jarvis-blue transition-all duration-300"
                      style={{ width: `${diskPercent}%` }}
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

              {/* System Control */}
              <SystemControl 
                listening={listening}
                onToggleListening={() => setListening(!listening)}
              />
            </div>

            {/* Center Column - Voice */}
            <div className="lg:col-span-2">
              <div className="jarvis-card jarvis-glow p-8 h-full flex flex-col items-center justify-center">
                <VoiceVisualizer listening={listening} />
                
                <button
                  onClick={() => setListening(!listening)}
                  className={`mt-8 px-8 py-4 rounded-full font-orbitron text-lg transition-all ${
                    listening
                      ? 'bg-jarvis-cyan text-jarvis-darker shadow-lg shadow-jarvis-cyan/50'
                      : 'bg-jarvis-cyan/10 border-2 border-jarvis-cyan text-jarvis-cyan hover:bg-jarvis-cyan/20'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Mic className="w-6 h-6" />
                    <span>{listening ? 'Listening...' : 'Activate Voice'}</span>
                  </div>
                </button>

                <p className="text-sm text-gray-400 mt-4">
                  {listening ? 'Ich höre zu...' : 'Klicken zum Aktivieren'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Models Tab */}
        {activeTab === 'models' && (
          <div className="max-w-4xl mx-auto">
            <ModelManager />
          </div>
        )}

        {/* Plugins Tab */}
        {activeTab === 'plugins' && (
          <div className="max-w-4xl mx-auto">
            <PluginManager />
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <div className="max-w-6xl mx-auto h-[calc(100vh-250px)]">
            <ChatBox />
          </div>
        )}
      </main>

      {/* Settings Modal */}
      {showSettings && (
        <SettingsPanel onClose={() => setShowSettings(false)} />
      )}

      {/* Footer */}
      <footer className="border-t border-jarvis-cyan/20 mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-gray-500">
          <p>J.A.R.V.I.S. v{health?.version || '2.0.0'} • Built with ❤️ by the JARVIS Team</p>
        </div>
      </footer>
    </div>
  )
}
