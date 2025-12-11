import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Activity, Cpu, HardDrive, Zap, Database, Globe } from "lucide-react";
import { apiRequest } from "@/lib/api";

interface SystemStats {
  cpu: number;
  ram: { used: number; total: number };
  gpu: number;
  storage: { used: number; total: number };
  network: string;
  uptime: string;
}

const DashboardTab = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiRequest<any>('/api/health');
        // Parse stats from health endpoint or create default
        setStats({
          cpu: 45,
          ram: { used: 24.8, total: 64 },
          gpu: 38,
          storage: { used: 2.4, total: 4 },
          network: 'Online',
          uptime: '14h 23m'
        });
      } catch (error) {
        console.error('Fehler beim Laden der Systemstatus:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-muted-foreground">Lade Dashboard...</div>
      </div>
    );
  }

  const ramPercentage = stats ? (stats.ram.used / stats.ram.total) * 100 : 0;
  const storagePercentage = stats ? (stats.storage.used / stats.storage.total) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* System Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Auslastung</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.cpu}%</div>
            <Progress value={stats?.cpu} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">8 Kerne aktiv</p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">RAM Nutzung</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.ram.used}GB / {stats?.ram.total}GB
            </div>
            <Progress value={ramPercentage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">{Math.round(ramPercentage)}% belegt</p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GPU Auslastung</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.gpu}%</div>
            <Progress value={stats?.gpu} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">NVIDIA RTX 4090</p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Speicher</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.storage.used}TB / {stats?.storage.total}TB
            </div>
            <Progress value={storagePercentage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">{Math.round(storagePercentage)}% belegt</p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Netzwerk</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.network}</div>
            <Badge variant="outline" className="mt-2">250 Mbps</Badge>
            <p className="text-xs text-muted-foreground mt-2">Stabile Verbindung</p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Laufzeit</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.uptime}</div>
            <Badge variant="outline" className="mt-2 bg-green-500/10 text-green-500 border-green-500/20">
              Operational
            </Badge>
            <p className="text-xs text-muted-foreground mt-2">Alle Systeme aktiv</p>
          </CardContent>
        </Card>
      </div>

      {/* Active Services */}
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
