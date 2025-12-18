import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Activity, Cpu, HardDrive, Zap, Database, Globe } from "lucide-react";
import { apiRequest } from "@/lib/api";

interface SystemInfo {
  cpu: {
    usage: number;
    count: number;
  };
  memory: {
    total: number;
    used: number;
    percent: number;
  };
  disk: {
    total: number;
    used: number;
    percent: number;
  };
  system: {
    platform: string;
    processor: string;
  };
  llama: {
    available: boolean;
    loaded: boolean;
    device: string;
    model_name?: string;
  };
}

const DashboardTab = () => {
  const { t } = useTranslation();
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        const data = await apiRequest<SystemInfo>('/api/system/info');
        setSystemInfo(data);
        setError(null);
      } catch (error) {
        console.error('Fehler beim Laden der Systeminfos:', error);
        setError(t('dashboardTab.connectionError'));
      } finally {
        setLoading(false);
      }
    };

    fetchSystemInfo();
    const interval = setInterval(fetchSystemInfo, 3000);
    return () => clearInterval(interval);
  }, [t]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-muted-foreground">{t('dashboardTab.loadingInfo')}</div>
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
            <CardTitle className="text-sm font-medium">{t('dashboardTab.cpuUsage')}</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemInfo.cpu.usage.toFixed(1)}%</div>
            <Progress value={systemInfo.cpu.usage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {systemInfo.cpu.count} {t('dashboardTab.cores')}
            </p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboardTab.ramUsage')}</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemInfo.memory.used.toFixed(1)}GB / {systemInfo.memory.total.toFixed(1)}GB
            </div>
            <Progress value={systemInfo.memory.percent} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {systemInfo.memory.percent.toFixed(1)}% {t('dashboardTab.used')}
            </p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboardTab.gpuDevice')}</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemInfo.llama.device}
            </div>
            <Badge 
              variant="outline" 
              className={systemInfo.llama.device === 'cuda' 
                ? 'mt-2 bg-green-500/10 text-green-500 border-green-500/20'
                : 'mt-2'
              }
            >
              {systemInfo.llama.available ? t('dashboardTab.available') : 'N/A'}
            </Badge>
            <p className="text-xs text-muted-foreground mt-2">
              {systemInfo.llama.loaded ? `${t('dashboardTab.model')}: ${systemInfo.llama.model_name}` : t('dashboardTab.noModel')}
            </p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboardTab.storage')}</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemInfo.disk.used.toFixed(1)}GB / {systemInfo.disk.total.toFixed(1)}GB
            </div>
            <Progress value={systemInfo.disk.percent} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {systemInfo.disk.percent.toFixed(1)}% {t('dashboardTab.used')}
            </p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboardTab.system')}</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemInfo.system.platform}</div>
            <p className="text-xs text-muted-foreground mt-2">
              {systemInfo.system.processor.substring(0, 30)}...
            </p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboardTab.status')}</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{t('dashboardTab.online')}</div>
            <Badge variant="outline" className="mt-2 bg-green-500/10 text-green-500 border-green-500/20">
              {t('dashboardTab.allSystemsActive')}
            </Badge>
          </CardContent>
        </Card>
      </div>

      <Card className="holo-panel">
        <CardHeader>
          <CardTitle>{t('dashboardTab.activeServices')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium">JARVIS Core</p>
                <p className="text-xs text-muted-foreground">{t('dashboardTab.mainAISystem')}</p>
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                {t('dashboardTab.online')}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium">llama.cpp Engine</p>
                <p className="text-xs text-muted-foreground">{t('dashboardTab.localInference')}</p>
              </div>
              <Badge 
                variant="outline" 
                className={systemInfo.llama.loaded 
                  ? 'bg-green-500/10 text-green-500 border-green-500/20'
                  : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
                }
              >
                {systemInfo.llama.loaded ? t('dashboardTab.loaded') : t('dashboardTab.standby')}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium">WebSocket Server</p>
                <p className="text-xs text-muted-foreground">{t('dashboardTab.realtimeComm')}</p>
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                {t('dashboardTab.connected')}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium">API Server</p>
                <p className="text-xs text-muted-foreground">{t('dashboardTab.restInterface')}</p>
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                {t('dashboardTab.active')}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardTab;
