import { Cpu, Database, Wifi, Zap } from "lucide-react";

interface StatusPanelProps {
  stats?: {
    cpu: number;
    memory: number;
    network: number;
    power: number;
  };
}

const StatusPanel = ({ stats = { cpu: 45, memory: 62, network: 98, power: 100 } }: StatusPanelProps) => {
  const statusItems = [
    { icon: Cpu, label: "CPU", value: stats.cpu, unit: "%" },
    { icon: Database, label: "Memory", value: stats.memory, unit: "%" },
    { icon: Wifi, label: "Network", value: stats.network, unit: "%" },
    { icon: Zap, label: "Power", value: stats.power, unit: "%" },
  ];

  return (
    <div className="flex gap-4 p-4 border-t">
      {statusItems.map((item) => {
        const Icon = item.icon;
        return (
          <div key={item.label} className="flex items-center gap-2 flex-1">
            <Icon className="h-4 w-4 text-muted-foreground" />
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground">{item.label}</span>
              <span className="text-sm font-medium">{item.value}{item.unit}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatusPanel;
