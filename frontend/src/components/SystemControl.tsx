import { Power, RotateCcw, Play, Pause } from 'lucide-react'

interface SystemControlProps {
  listening: boolean
  onToggleListening: () => void
}

export default function SystemControl({ listening, onToggleListening }: SystemControlProps) {
  return (
    <div className="jarvis-card jarvis-glow p-6">
      <h3 className="text-lg font-bold mb-4">System Control</h3>
      
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={onToggleListening}
          className={`p-4 rounded-lg font-orbitron transition-all flex items-center justify-center gap-2 ${
            listening
              ? 'bg-jarvis-cyan text-jarvis-darker shadow-lg shadow-jarvis-cyan/50'
              : 'bg-jarvis-cyan/10 border border-jarvis-cyan text-jarvis-cyan hover:bg-jarvis-cyan/20'
          }`}
        >
          {listening ? (
            <>
              <Pause className="w-5 h-5" />
              <span>Stop Listening</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              <span>Start Listening</span>
            </>
          )}
        </button>

        <button className="p-4 bg-jarvis-cyan/10 border border-jarvis-cyan/50 rounded-lg hover:bg-jarvis-cyan/20 transition-all font-orbitron text-jarvis-cyan flex items-center justify-center gap-2">
          <RotateCcw className="w-5 h-5" />
          <span>Restart</span>
        </button>

        <button className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg hover:bg-red-500/20 transition-all font-orbitron text-red-500 flex items-center justify-center gap-2 col-span-2">
          <Power className="w-5 h-5" />
          <span>Shutdown</span>
        </button>
      </div>
    </div>
  )
}
