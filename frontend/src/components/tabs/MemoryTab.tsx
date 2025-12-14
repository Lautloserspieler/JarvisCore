import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Brain, Trash2, RefreshCw } from "lucide-react";
import { apiRequest } from "@/lib/api";

interface Memory {
  id: string;
  type: string;
  content: string;
  timestamp: string;
  relevance: number;
}

interface MemoryStats {
  totalMemories: number;
  byType: Record<string, number>;
  storageUsed: number;
  lastUpdated: string;
}

const MemoryTab = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMemories = async () => {
      try {
        const [memoriesData, statsData] = await Promise.all([
          apiRequest<Memory[]>('/api/memory'),
          apiRequest<MemoryStats>('/api/memory/stats')
        ]);
        setMemories(memoriesData);
        setStats(statsData);
      } catch (error) {
        console.error('Fehler beim Laden des Gedächtnisses:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMemories();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-muted-foreground">Lade Gedächtnis...</div>
      </div>
    );
  }

  const storagePercentage = stats ? (stats.storageUsed / 10000000) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Memory Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gesamte Erinnerungen</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalMemories || 0}</div>
            <p className="text-xs text-muted-foreground mt-2">Gespeicherte Einträge</p>
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Speichernutzung</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats ? (stats.storageUsed / 1024).toFixed(1) : 0} KB
            </div>
            <Progress value={storagePercentage} className="mt-2" />
          </CardContent>
        </Card>

        <Card className="holo-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Letzte Aktualisierung</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-bold">
              {stats?.lastUpdated ? new Date(stats.lastUpdated).toLocaleTimeString('de-DE') : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-2">Heute</p>
          </CardContent>
        </Card>
      </div>

      {/* Memory Types */}
      {stats && stats.byType && Object.keys(stats.byType).length > 0 && (
        <Card className="holo-panel">
          <CardHeader>
            <CardTitle>Erinnerungstypen</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.byType).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{type}</span>
                  <Badge variant="outline">{count}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Memories */}
      <Card className="holo-panel">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Kürzliche Erinnerungen</CardTitle>
              <CardDescription>Zuletzt gespeicherte Informationen</CardDescription>
            </div>
            <Button variant="outline" size="sm">
              <Trash2 className="h-4 w-4 mr-2" />
              Alle löschen
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {memories.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Noch keine Erinnerungen gespeichert</p>
            </div>
          ) : (
            <div className="space-y-4">
              {memories.map((memory) => (
                <div key={memory.id} className="p-4 rounded-lg border border-border/40 bg-card/50">
                  <div className="flex items-start justify-between mb-2">
                    <Badge variant="outline" className="text-xs">
                      {memory.type}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(memory.timestamp).toLocaleString('de-DE')}
                    </span>
                  </div>
                  <p className="text-sm">{memory.content}</p>
                  <div className="mt-2">
                    <Progress value={memory.relevance * 100} className="h-1" />
                    <span className="text-xs text-muted-foreground mt-1">
                      Relevanz: {(memory.relevance * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default MemoryTab;
