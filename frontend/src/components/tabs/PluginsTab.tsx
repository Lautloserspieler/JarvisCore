import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Puzzle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  status: string;
}

const PluginsTab = () => {
  const { toast } = useToast();
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<{[key: string]: boolean}>({});

  // Load plugins on mount
  useEffect(() => {
    loadPlugins();
  }, []);

  const loadPlugins = async () => {
    try {
      const response = await fetch('http://localhost:5050/api/plugins');
      if (response.ok) {
        const data = await response.json();
        // Filter out demo plugins
        const filtered = data.filter((p: Plugin) => 
          !['calculator_plugin', 'system_info_plugin', 'time_plugin'].includes(p.id)
        );
        setPlugins(filtered);
      }
    } catch (error) {
      console.error('Fehler beim Laden der Plugins:', error);
      toast({
        title: 'Fehler',
        description: 'Plugins konnten nicht geladen werden',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const togglePlugin = async (pluginId: string, enabled: boolean) => {
    setToggling(prev => ({ ...prev, [pluginId]: true }));
    
    try {
      const endpoint = enabled 
        ? `http://localhost:5050/api/plugins/${pluginId}/enable`
        : `http://localhost:5050/api/plugins/${pluginId}/disable`;
      
      const response = await fetch(endpoint, { method: 'POST' });
      
      if (response.ok) {
        const result = await response.json();
        
        // Update local state
        setPlugins(prev => 
          prev.map(p => 
            p.id === pluginId ? { ...p, enabled } : p
          )
        );
        
        toast({
          title: 'Erfolg',
          description: result.message || (enabled ? 'Plugin aktiviert' : 'Plugin deaktiviert')
        });
      } else {
        throw new Error('Plugin konnte nicht geändert werden');
      }
    } catch (error) {
      console.error('Fehler beim Umschalten des Plugins:', error);
      toast({
        title: 'Fehler',
        description: enabled ? 'Plugin konnte nicht aktiviert werden' : 'Plugin konnte nicht deaktiviert werden',
        variant: 'destructive'
      });
    } finally {
      setToggling(prev => ({ ...prev, [pluginId]: false }));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-muted-foreground">Lade Plugins...</div>
      </div>
    );
  }

  const enabledPlugins = plugins.filter(p => p.enabled);
  const disabledPlugins = plugins.filter(p => !p.enabled);

  return (
    <div className="space-y-6">
      {/* Enabled Plugins */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Aktive Plugins</h3>
          <Badge variant="outline">{enabledPlugins.length} aktiv</Badge>
        </div>
        {enabledPlugins.length === 0 ? (
          <Card className="holo-card">
            <CardContent className="py-6">
              <p className="text-center text-muted-foreground">Keine Plugins aktiviert</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {enabledPlugins.map((plugin) => (
              <Card key={plugin.id} className="holo-card">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Puzzle className="h-4 w-4" />
                        {plugin.name}
                      </CardTitle>
                      <CardDescription>{plugin.description || 'Kein Beschreibung verfügbar'}</CardDescription>
                    </div>
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
                      <span>{plugin.author || 'Unbekannt'}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Status:</span>
                      <Badge variant="outline" className="text-xs">{plugin.status}</Badge>
                    </div>
                  </div>
                  <Button 
                    onClick={() => togglePlugin(plugin.id, false)}
                    disabled={toggling[plugin.id]}
                    className="w-full"
                  >
                    {toggling[plugin.id] ? 'Lädt...' : 'Deaktivieren'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Disabled Plugins */}
      {disabledPlugins.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Verfügbare Plugins</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {disabledPlugins.map((plugin) => (
              <Card key={plugin.id} className="holo-card">
                <CardHeader>
                  <CardTitle className="text-base">{plugin.name}</CardTitle>
                  <CardDescription>{plugin.description || 'Kein Beschreibung verfügbar'}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Version:</span>
                      <span>{plugin.version}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Autor:</span>
                      <span>{plugin.author || 'Unbekannt'}</span>
                    </div>
                  </div>
                  <Button 
                    onClick={() => togglePlugin(plugin.id, true)}
                    disabled={toggling[plugin.id] || plugin.status !== 'available'}
                    variant="default"
                    className="w-full"
                  >
                    {toggling[plugin.id] ? 'Lädt...' : 'Aktivieren'}
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
