import { useEffect, useState, useMemo } from "react";

export type CoreState = "idle" | "listening" | "processing" | "speaking" | "error";

interface JarvisCoreProps {
  state?: CoreState;
  isActive?: boolean;
  size?: "sm" | "md" | "lg";
}

const createHexPath = (cx: number, cy: number, r: number) => {
  const points = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 2;
    points.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
  }
  return `M${points.join("L")}Z`;
};

const JarvisCore = ({ state = "idle", isActive = true, size = "lg" }: JarvisCoreProps) => {
  const [pulseIntensity, setPulseIntensity] = useState(1);
  const [rotationSpeed, setRotationSpeed] = useState(1);
  const [energyLevel, setEnergyLevel] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    let energyInterval: NodeJS.Timeout;

    switch (state) {
      case "listening":
        interval = setInterval(() => {
          setPulseIntensity(0.85 + Math.random() * 0.3);
        }, 60);
        setRotationSpeed(2.5);
        energyInterval = setInterval(() => {
          setEnergyLevel(prev => (prev + 5) % 100);
        }, 50);
        break;
      case "processing":
        interval = setInterval(() => {
          setPulseIntensity(0.7 + Math.random() * 0.5);
        }, 40);
        setRotationSpeed(4);
        energyInterval = setInterval(() => {
          setEnergyLevel(prev => (prev + 10) % 100);
        }, 30);
        break;
      case "speaking":
        interval = setInterval(() => {
          setPulseIntensity(0.9 + Math.sin(Date.now() / 80) * 0.2);
        }, 25);
        setRotationSpeed(1.8);
        energyInterval = setInterval(() => {
          setEnergyLevel(prev => (prev + 3) % 100);
        }, 60);
        break;
      case "error":
        interval = setInterval(() => {
          setPulseIntensity(Math.random() > 0.5 ? 1.2 : 0.6);
        }, 100);
        setRotationSpeed(0.3);
        break;
      default:
        setPulseIntensity(1);
        setRotationSpeed(1);
        setEnergyLevel(0);
    }

    return () => {
      if (interval) clearInterval(interval);
      if (energyInterval) clearInterval(energyInterval);
    };
  }, [state]);

  const sizeConfig = useMemo(() => ({
    sm: { container: "w-32 h-32", core: 60, hexSize: 45 },
    md: { container: "w-48 h-48", core: 90, hexSize: 70 },
    lg: { container: "w-72 h-72", core: 135, hexSize: 105 },
  }), []);

  const currentSize = sizeConfig[size];

  const stateColors = useMemo(() => {
    switch (state) {
      case "listening":
        return { primary: "hsl(195 100% 60%)", secondary: "hsl(185 100% 50%)", glow: "185 100% 50%", intensity: 0.9 };
      case "processing":
        return { primary: "hsl(200 100% 65%)", secondary: "hsl(195 100% 55%)", glow: "195 100% 55%", intensity: 1 };
      case "speaking":
        return { primary: "hsl(185 100% 60%)", secondary: "hsl(195 100% 50%)", glow: "190 100% 55%", intensity: 0.85 };
      case "error":
        return { primary: "hsl(0 80% 50%)", secondary: "hsl(350 70% 45%)", glow: "0 80% 50%", intensity: 1.2 };
      default:
        return { primary: "hsl(185 80% 45%)", secondary: "hsl(195 70% 40%)", glow: "185 70% 40%", intensity: 0.5 };
    }
  }, [state]);

  const statusText = useMemo(() => {
    if (!isActive) return "OFFLINE";
    switch (state) {
      case "listening": return "LISTENING";
      case "processing": return "PROCESSING";
      case "speaking": return "SPEAKING";
      case "error": return "ERROR";
      default: return "STANDBY";
    }
  }, [state, isActive]);

  const svgSize = size === "lg" ? 288 : size === "md" ? 192 : 128;
  const center = svgSize / 2;

  return (
    <div className={`relative flex items-center justify-center ${currentSize.container}`}>
      <svg width={svgSize} height={svgSize} viewBox={`0 0 ${svgSize} ${svgSize}`} className="absolute">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <radialGradient id="coreGradient">
            <stop offset="0%" stopColor={stateColors.primary} />
            <stop offset="100%" stopColor={stateColors.secondary} />
          </radialGradient>
        </defs>

        {/* Rotating hexagon */}
        <path
          d={createHexPath(center, center, currentSize.hexSize)}
          fill="none"
          stroke={stateColors.primary}
          strokeWidth="2"
          opacity={0.6 * pulseIntensity}
          style={{ transformOrigin: "center", animation: `spin ${30 / rotationSpeed}s linear infinite` }}
        />

        {/* Core circle */}
        <circle
          cx={center}
          cy={center}
          r={currentSize.core}
          fill="url(#coreGradient)"
          opacity={0.3 * pulseIntensity}
          filter="url(#glow)"
          style={{ animation: `pulse 2s ease-in-out infinite` }}
        />

        <circle
          cx={center}
          cy={center}
          r={currentSize.core * 0.7}
          fill="none"
          stroke={stateColors.primary}
          strokeWidth="2"
          opacity={0.8 * pulseIntensity}
        />
      </svg>

      <div className="text-center z-10">
        <div className="text-xs font-mono tracking-widest" style={{ color: stateColors.primary }}>
          {statusText}
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
      `}</style>
    </div>
  );
};

export default JarvisCore;
