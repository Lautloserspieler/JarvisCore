import { useState, useEffect } from 'react'
import { Settings, Mic, Volume2, Zap } from 'lucide-react'

interface SettingsPanelProps {
  onClose: () => void
}

export default function SettingsPanel({ onClose }: SettingsPanelProps) {
  const [wakeWordEnabled, setWakeWordEnabled] = useState(true)
  const [speechMode, setSpeechMode] = useState('neutral')
  const [ttsEnabled, setTtsEnabled] = useState(true)

  const speechModes = [
    { value: 'neutral', label: 'Neutral' },
    { value: 'friendly', label: 'Friendly' },
    { value: 'professional', label: 'Professional' },
    { value: 'casual', label: 'Casual' },
  ]

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="jarvis-card jarvis-glow p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-jarvis-cyan" />
            <h2 className="text-2xl font-bold">Einstellungen</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-6">
          {/* Speech Recognition */}
          <section>
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Mic className="w-5 h-5 text-jarvis-cyan" />
              Spracherkennung
            </h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-jarvis-dark/50 rounded-lg">
                <div>
                  <p className="font-medium">Wake-Word Erkennung</p>
                  <p className="text-sm text-gray-400">Aktiviere JARVIS mit "Hey Jarvis"</p>
                </div>
                <button
                  onClick={() => setWakeWordEnabled(!wakeWordEnabled)}
                  className={`relative w-14 h-8 rounded-full transition-colors ${
                    wakeWordEnabled ? 'bg-jarvis-cyan' : 'bg-gray-600'
                  }`}
                >
                  <div className={`absolute top-1 w-6 h-6 bg-white rounded-full transition-transform ${
                    wakeWordEnabled ? 'translate-x-7' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              <div className="p-4 bg-jarvis-dark/50 rounded-lg">
                <p className="font-medium mb-3">Minimale Wortanzahl</p>
                <input
                  type="range"
                  min="1"
                  max="10"
                  defaultValue="3"
                  className="w-full accent-jarvis-cyan"
                />
                <div className="flex justify-between text-sm text-gray-400 mt-1">
                  <span>1</span>
                  <span>10</span>
                </div>
              </div>
            </div>
          </section>

          {/* Text-to-Speech */}
          <section>
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Volume2 className="w-5 h-5 text-jarvis-cyan" />
              Text-to-Speech
            </h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-jarvis-dark/50 rounded-lg">
                <div>
                  <p className="font-medium">TTS Aktiviert</p>
                  <p className="text-sm text-gray-400">JARVIS spricht Antworten aus</p>
                </div>
                <button
                  onClick={() => setTtsEnabled(!ttsEnabled)}
                  className={`relative w-14 h-8 rounded-full transition-colors ${
                    ttsEnabled ? 'bg-jarvis-cyan' : 'bg-gray-600'
                  }`}
                >
                  <div className={`absolute top-1 w-6 h-6 bg-white rounded-full transition-transform ${
                    ttsEnabled ? 'translate-x-7' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              <div className="p-4 bg-jarvis-dark/50 rounded-lg">
                <p className="font-medium mb-3">Sprachmodus</p>
                <div className="grid grid-cols-2 gap-2">
                  {speechModes.map(mode => (
                    <button
                      key={mode.value}
                      onClick={() => setSpeechMode(mode.value)}
                      className={`p-3 rounded-lg font-orbitron transition-all ${
                        speechMode === mode.value
                          ? 'bg-jarvis-cyan/20 border-2 border-jarvis-cyan text-jarvis-cyan'
                          : 'bg-jarvis-dark border border-jarvis-cyan/30 text-gray-400 hover:border-jarvis-cyan/50'
                      }`}
                    >
                      {mode.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* System */}
          <section>
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-jarvis-cyan" />
              System
            </h3>
            
            <div className="space-y-4">
              <div className="p-4 bg-jarvis-dark/50 rounded-lg">
                <p className="font-medium mb-3">Debug Level</p>
                <select className="jarvis-input">
                  <option value="DEBUG">Debug</option>
                  <option value="INFO">Info</option>
                  <option value="WARNING">Warning</option>
                  <option value="ERROR">Error</option>
                </select>
              </div>

              <div className="p-4 bg-jarvis-dark/50 rounded-lg">
                <p className="font-medium mb-2">Update-Intervall (Sekunden)</p>
                <input
                  type="number"
                  defaultValue="2"
                  min="1"
                  max="10"
                  className="jarvis-input"
                />
              </div>
            </div>
          </section>
        </div>

        {/* Actions */}
        <div className="mt-6 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 jarvis-button"
          >
            Schließen
          </button>
          <button className="flex-1 px-4 py-2 bg-jarvis-cyan text-jarvis-darker rounded-lg font-orbitron hover:bg-jarvis-cyan/80 transition-all">
            Speichern
          </button>
        </div>
      </div>
    </div>
  )
}
