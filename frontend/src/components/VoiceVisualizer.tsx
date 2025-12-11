import { useEffect, useState } from 'react'
import '../styles/VoiceVisualizer.css'

interface VoiceVisualizerProps {
  isActive: boolean
  barCount?: number
}

const VoiceVisualizer = ({ isActive, barCount = 20 }: VoiceVisualizerProps) => {
  const [bars, setBars] = useState(Array(barCount).fill(0.3))

  useEffect(() => {
    if (!isActive) {
      setBars(Array(barCount).fill(0.3))
      return
    }

    const interval = setInterval(() => {
      setBars(prev => prev.map(() => Math.random() * 0.7 + 0.3))
    }, 50)

    return () => clearInterval(interval)
  }, [isActive, barCount])

  return (
    <div className="voice-visualizer">
      {bars.map((height, index) => (
        <div
          key={index}
          className="voice-bar"
          style={{
            height: `${height * 100}%`,
            animationDelay: `${index * 0.05}s`,
          }}
        />
      ))}
    </div>
  )
}

export default VoiceVisualizer
