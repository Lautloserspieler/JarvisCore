import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Cpu, HardDrive, Wifi, Zap, Thermometer, Activity } from "lucide-react";

interface SystemMetrics {
  cpu: number;
  ram: number;
  gpu: number;
  temperature: number;
  power: number;
  network: number;
}

const DashboardTab = () => {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: 45,
    ram: 62,
    gpu: 38,
    temperature: 52,
    power: 78,
    network: 85,
  });
  const [history, setHistory] = useState<number[][]>([[], [], []]);

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics((prev) => ({
        cpu: Math.max(5, Math.min(95, prev.cpu + (Math.random() - 0.5) * 10)),
        ram: Math.max(30, Math.min(90, prev.ram + (Math.random() - 0.5) * 5)),
        gpu: Math.max(10, Math.min(85, prev.gpu + (Math.random() - 0.5) * 8)),
        temperature: Math.max(35, Math.min(80, prev.temperature + (Math.random() - 0.5) * 3)),
        power: Math.max(50, Math.min(100, prev.power + (Math.random() - 0.5) * 4)),
        network: Math.max(20, Math.min(100, prev.network + (Math.random() - 0.5) * 15)),
      }));
      setHistory((prev) => [
        [...prev[0].slice(-99), metrics.cpu],
        [...prev[1].slice(-99), metrics.ram],
        [...prev[2].slice(-99), metrics.gpu],
      ]);
    }, 1000);
    return () => clearInterval(interval);
  }, [metrics]);

  const MetricCard = ({
    title,
    value,
    icon: Icon,
    color,
    suffix = "%",
  }: {
    title: string;
    value: number;
    icon: React.ElementType;
    color: string;
    suffix?: string;
  }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value.toFixed(1)}{suffix}</div>
        <Progress value={value} className="mt-2" />
      </CardContent>
    </Card>
  );

  const MiniGraph = ({ data, color }: { data: number[]; color: string }) => {
    const max = Math.max(...data, 100);
    const min = Math.min(...data, 0);
    const range = max - min || 1;
    return (
      <svg className="w-full h-20" viewBox="0 0 100 20">
        {data.slice(-50).map((value, i) => (
          <rect
            key={i}
            x={i * 2}
            y={20 - ((value - min) / range) * 20}
            width="1.5"
            height={((value - min) / range) * 20}
            className={color}
          />
        ))}
      </svg>
    );
  };

  return (
    <div className="space-y-4 p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard title="CPU Usage" value={metrics.cpu} icon={Cpu} color="text-blue-500" />
        <MetricCard title="RAM Usage" value={metrics.ram} icon={HardDrive} color="text-green-500" />
        <MetricCard title="GPU Usage" value={metrics.gpu} icon={Activity} color="text-purple-500" />
        <MetricCard title="Temperature" value={metrics.temperature} icon={Thermometer} color="text-orange-500" suffix="°C" />
        <MetricCard title="Power" value={metrics.power} icon={Zap} color="text-yellow-500" suffix="W" />
        <MetricCard title="Network" value={metrics.network} icon={Wifi} color="text-cyan-500" suffix=" Mbps" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>CPU History</CardTitle>
          </CardHeader>
          <CardContent>
            <MiniGraph data={history[0]} color="fill-blue-500" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>RAM History</CardTitle>
          </CardHeader>
          <CardContent>
            <MiniGraph data={history[1]} color="fill-green-500" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>GPU History</CardTitle>
          </CardHeader>
          <CardContent>
            <MiniGraph data={history[2]} color="fill-purple-500" />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span className="text-muted-foreground">CPU Model:</span>
            <span className="font-medium">Intel Core i9-13900K</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Total RAM:</span>
            <span className="font-medium">64 GB DDR5</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">GPU Model:</span>
            <span className="font-medium">NVIDIA RTX 4090</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Uptime:</span>
            <span className="font-medium">3d 14h 22m</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardTab;
