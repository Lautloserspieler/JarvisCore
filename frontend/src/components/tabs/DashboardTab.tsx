import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Activity, Cpu, HardDrive, Zap, Database, Globe } from "lucide-react";
import { apiRequest } from "@/lib/api";

interface SystemInfo {
  cpu: {
    cores: number;
    threads: number;
    utilization: number;
    name: string;
  };
  gpu: {
    name: string;
    utilization: number;
    memory_used: number;
    memory_total: number;
    available: boolean;
  };
  memory: {
    total: number;
    used: number;
    available: number;
    percent: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    percent: number;
  };
  network: {
    status: string;
    interfaces: number;
  };
  uptime: string;
}

const DashboardTab = () => {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        const data = await apiRequest<{ system: SystemInfo }>('/api/system/info');
        setSystemInfo(data.system || data as any);
        setError(null);
      } catch (error) {
        console.error('Fehler beim Laden der Systeminfos:', error);
        setError('Verbindung zum Backend fehlgeschlagen');
      } finally {
        setLoading(false);
      }
    };

    fetchSystemInfo();
    const interval = setInterval(fetchSystemInfo, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-muted-foreground">Lade System-Informationen...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-destructive">{error}</div>
      </div>
    );
  }

  if (!systemInfo) return null;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Auslastung</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemInfo.cpu.utilization.toFixed(1)}%</div>
            <Progress value={systemInfo.cpu.utilization} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {systemInfo.cpu.cores} Kerne / {systemInfo.cpu.threads} Threads
            </p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">RAM Nutzung</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemInfo.memory.used}GB / {systemInfo.memory.total}GB
            </div>
            <Progress value={systemInfo.memory.percent} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {systemInfo.memory.percent.toFixed(1)}% belegt
            </p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GPU</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemInfo.gpu.available ? `${systemInfo.gpu.utilization.toFixed(1)}%` : 'N/A'}
            </div>
            <Progress value={systemInfo.gpu.utilization} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">{systemInfo.gpu.name}</p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Speicher</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemInfo.disk.used.toFixed(1)}GB / {systemInfo.disk.total.toFixed(1)}GB
            </div>
            <Progress value={systemInfo.disk.percent} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {systemInfo.disk.percent.toFixed(1)}% belegt
            </p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Netzwerk</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemInfo.network.status}</div>
            <Badge variant="outline" className="mt-2">
              {systemInfo.network.interfaces} Schnittstellen
            </Badge>
            <p className="text-xs text-muted-foreground mt-2">Stabile Verbindung</p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Laufzeit</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemInfo.uptime}</div>
            <Badge variant="outline" className="mt-2 bg-green-500/10 text-green-500 border-green-500/20">
              Online
            </Badge>
            <p className="text-xs text-muted-foreground mt-2">Alle Systeme aktiv</p>
          </CardContent>
        </Card>
      </div>

      <Card className="holo-panel">
        <CardHeader>
          <CardTitle>Aktive Dienste</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium">JARVIS Core</p>
                <p className="text-xs text-muted-foreground">Haupt-KI-System</p>
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                Online
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium">WebSocket Server</p>
                <p className="text-xs text-muted-foreground">Echtzeit-Kommunikation</p>
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                Verbunden
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium">API Server</p>
                <p className="text-xs text-muted-foreground">REST API Schnittstelle</p>
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                Aktiv
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardTab;
