import { useEffect, useRef } from 'react'

interface VoiceVisualizerProps {
  listening: boolean
}

export default function VoiceVisualizer({ listening }: VoiceVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    const radius = 80

    let angle = 0

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Outer glow ring
      const gradient = ctx.createRadialGradient(centerX, centerY, radius * 0.5, centerX, centerY, radius * 1.5)
      gradient.addColorStop(0, 'rgba(0, 240, 255, 0.3)')
      gradient.addColorStop(0.5, 'rgba(0, 240, 255, 0.1)')
      gradient.addColorStop(1, 'rgba(0, 240, 255, 0)')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Pulsating circles
      for (let i = 0; i < 3; i++) {
        const pulseRadius = radius + (listening ? Math.sin(angle + i) * 20 : 0)
        const alpha = listening ? 0.3 - (i * 0.1) : 0.1

        ctx.beginPath()
        ctx.arc(centerX, centerY, pulseRadius + (i * 15), 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(0, 240, 255, ${alpha})`
        ctx.lineWidth = 2
        ctx.stroke()
      }

      // Core circle
      const coreGradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius)
      coreGradient.addColorStop(0, listening ? 'rgba(0, 240, 255, 0.8)' : 'rgba(0, 240, 255, 0.3)')
      coreGradient.addColorStop(1, 'rgba(0, 240, 255, 0)')
      ctx.fillStyle = coreGradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
      ctx.fill()

      // Rotating arcs
      if (listening) {
        for (let i = 0; i < 3; i++) {
          ctx.beginPath()
          ctx.arc(
            centerX,
            centerY,
            radius + 30,
            angle + (i * Math.PI * 2 / 3),
            angle + (i * Math.PI * 2 / 3) + Math.PI / 3
          )
          ctx.strokeStyle = 'rgba(0, 240, 255, 0.6)'
          ctx.lineWidth = 3
          ctx.stroke()
        }
      }

      angle += listening ? 0.05 : 0.01
      animationRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [listening])

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={300}
        height={300}
        className="max-w-full"
      />
    </div>
  )
}
