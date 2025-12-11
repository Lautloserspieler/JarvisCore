import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RefreshCw, Trash2, Download } from "lucide-react";
import { apiRequest } from "@/lib/api";

interface Log {
  id: string;
  timestamp: string;
  level: string;
  category: string;
  message: string;
  metadata: Record<string, any>;
}

interface LogStats {
  total: number;
  byLevel: Record<string, number>;
  byCategory: Record<string, number>;
  timeRange: { start: string; end: string };
}

const LogsTab = () => {
  const [logs, setLogs] = useState<Log[]>([]);
  const [stats, setStats] = useState<LogStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const [logsData, statsData] = await Promise.all([
          apiRequest<Log[]>('/api/logs'),
          apiRequest<LogStats>('/api/logs/stats')
        ]);
        setLogs(logsData);
        setStats(statsData);
      } catch (error) {
        console.error('Fehler beim Laden der Protokolle:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'debug': return 'text-gray-500';
      case 'info': return 'text-blue-500';
      case 'warning': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      case 'critical': return 'text-red-700';
      default: return 'text-gray-500';
    }
  };

  const getLevelBadge = (level: string) => {
    switch (level.toLowerCase()) {
      case 'debug': return 'default';
      case 'info': return 'default';
      case 'warning': return 'default';
      case 'error': return 'destructive';
      case 'critical': return 'destructive';
      default: return 'default';
    }
  };

  const filteredLogs = filters.size > 0
    ? logs.filter(log => filters.has(log.level.toLowerCase()))
    : logs;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-muted-foreground">Lade Protokolle...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Log Stats */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-5">
          {Object.entries(stats.byLevel).map(([level, count]) => (
            <Card key={level} className="holo-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium capitalize">{level}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{count}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Log Viewer */}
      <Card className="holo-panel">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>System-Protokolle</CardTitle>
              <CardDescription>Echtzeit-Protokollierung aller Systemereignisse</CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Aktualisieren
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Exportieren
              </Button>
              <Button variant="outline" size="sm">
                <Trash2 className="h-4 w-4 mr-2" />
                Löschen
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Level Filters */}
          <div className="flex gap-4 mb-4">
            {['debug', 'info', 'warning', 'error', 'critical'].map(level => (
              <div key={level} className="flex items-center space-x-2">
                <Checkbox
                  id={level}
                  checked={filters.has(level)}
                  onCheckedChange={(checked) => {
                    const newFilters = new Set(filters);
                    if (checked) {
                      newFilters.add(level);
                    } else {
                      newFilters.delete(level);
                    }
                    setFilters(newFilters);
                  }}
                />
                <label htmlFor={level} className="text-sm capitalize cursor-pointer">
                  {level}
                </label>
              </div>
            ))}
          </div>

          <ScrollArea className="h-[400px] w-full rounded-md border border-border/40 p-4">
            <div className="space-y-2 font-mono text-sm">
              {filteredLogs.map((log) => (
                <div key={log.id} className="flex items-start gap-3 p-2 rounded hover:bg-accent/50">
                  <span className="text-muted-foreground whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleTimeString('de-DE')}
                  </span>
                  <Badge variant={getLevelBadge(log.level) as any} className="uppercase text-xs">
                    {log.level}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {log.category}
                  </Badge>
                  <span className={getLevelColor(log.level)}>{log.message}</span>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default LogsTab;
