import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Puzzle, Settings, Trash2 } from "lucide-react";
import { apiRequest } from "@/lib/api";

interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  isEnabled: boolean;
  isInstalled: boolean;
  category: string;
  capabilities: string[];
}

const PluginsTab = () => {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlugins = async () => {
      try {
        const data = await apiRequest<Plugin[]>('/api/plugins');
        setPlugins(data);
      } catch (error) {
        console.error('Fehler beim Laden der Plugins:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlugins();
  }, []);

  const togglePlugin = async (pluginId: string) => {
    setPlugins(plugins.map(p => 
      p.id === pluginId ? { ...p, isEnabled: !p.isEnabled } : p
    ));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-muted-foreground">Lade Plugins...</div>
      </div>
    );
  }

  const installedPlugins = plugins.filter(p => p.isInstalled);
  const availablePlugins = plugins.filter(p => !p.isInstalled);

  return (
    <div className="space-y-6">
      {/* Installed Plugins */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Installierte Plugins</h3>
          <Badge variant="outline">{installedPlugins.length} aktiv</Badge>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {installedPlugins.map((plugin) => (
            <Card key={plugin.id} className="holo-card">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Puzzle className="h-4 w-4" />
                      {plugin.name}
                    </CardTitle>
                    <CardDescription>{plugin.description}</CardDescription>
                  </div>
                  <Switch
                    checked={plugin.isEnabled}
                    onCheckedChange={() => togglePlugin(plugin.id)}
                  />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Version:</span>
                    <span>{plugin.version}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Autor:</span>
                    <span>{plugin.author}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Kategorie:</span>
                    <Badge variant="outline" className="text-xs">{plugin.category}</Badge>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {plugin.capabilities.map((cap) => (
                    <Badge key={cap} variant="secondary" className="text-xs">
                      {cap}
                    </Badge>
                  ))}
                </div>
                <div className="flex gap-2 pt-2">
                  <Button variant="outline" size="sm" className="flex-1">
                    <Settings className="h-4 w-4 mr-2" />
                    Konfigurieren
                  </Button>
                  <Button variant="outline" size="sm">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Available Plugins */}
      {availablePlugins.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Verfügbare Plugins</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {availablePlugins.map((plugin) => (
              <Card key={plugin.id} className="holo-card">
                <CardHeader>
                  <CardTitle className="text-base">{plugin.name}</CardTitle>
                  <CardDescription>{plugin.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full">
                    Installieren
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PluginsTab;
