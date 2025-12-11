import { useEffect, useState } from "react";

interface VoiceVisualizerProps {
  isActive: boolean;
  barCount?: number;
}

const VoiceVisualizer = ({ isActive, barCount = 20 }: VoiceVisualizerProps) => {
  const [bars, setBars] = useState<number[]>(Array(barCount).fill(0.3));

  useEffect(() => {
    if (!isActive) {
      setBars(Array(barCount).fill(0.3));
      return;
    }

    const interval = setInterval(() => {
      setBars(prev => prev.map(() => Math.random() * 0.7 + 0.3));
    }, 50);

    return () => clearInterval(interval);
  }, [isActive, barCount]);

  return (
    <div className="flex items-center justify-center gap-1 h-16">
      {bars.map((height, index) => (
        <div
          key={index}
          className="w-1 bg-gradient-to-t from-blue-500 to-cyan-400 rounded-full transition-all duration-75"
          style={{ height: `${height * 100}%` }}
        />
      ))}
    </div>
  );
};

export default VoiceVisualizer;
