import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Puzzle, Key } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import ApiKeyModal from "@/components/ApiKeyModal";

interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  status: string;
  requires_api_key?: boolean;
  api_key_info?: {
    api_key_name: string;
    api_key_label: string;
    api_key_url: string;
    api_key_description: string;
  };
}

const PluginsTab = () => {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<{[key: string]: boolean}>({});
  
  // API Key Modal State
  const [apiKeyModalOpen, setApiKeyModalOpen] = useState(false);
  const [pendingPlugin, setPendingPlugin] = useState<Plugin | null>(null);

  // Load plugins on mount
  useEffect(() => {
    loadPlugins();
  }, []);

  const loadPlugins = async () => {
    try {
      const response = await fetch('http://localhost:5050/api/plugins');
      if (response.ok) {
        const data = await response.json();
        const filtered = data.filter((p: Plugin) => 
          !['calculator_plugin', 'system_info_plugin', 'time_plugin'].includes(p.id)
        );
        setPlugins(filtered);
      }
    } catch (error) {
      console.error('Fehler beim Laden der Plugins:', error);
      toast({
        title: t('common.error'),
        description: t('plugins.loadError'),
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
      const result = await response.json();
      
      if (response.ok && result.success) {
        setPlugins(prev => 
          prev.map(p => 
            p.id === pluginId ? { ...p, enabled } : p
          )
        );
        
        toast({
          title: t('common.success'),
          description: result.message || (enabled ? t('plugins.enabled') : t('plugins.disabled'))
        });
      } else if (result.requires_api_key && result.api_key_info) {
        const plugin = plugins.find(p => p.id === pluginId);
        if (plugin) {
          setPendingPlugin({
            ...plugin,
            api_key_info: result.api_key_info
          });
          setApiKeyModalOpen(true);
        }
      } else {
        throw new Error(result.error || t('common.error'));
      }
    } catch (error) {
      console.error('Fehler:', error);
      toast({
        title: t('common.error'),
        description: t('pluginsTab.actionFailed'),
        variant: 'destructive'
      });
    } finally {
      setToggling(prev => ({ ...prev, [pluginId]: false }));
    }
  };

  const handleApiKeySuccess = async () => {
    if (pendingPlugin) {
      await togglePlugin(pendingPlugin.id, true);
      setPendingPlugin(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-muted-foreground">{t('pluginsTab.loading')}</div>
      </div>
    );
  }

  const enabledPlugins = plugins.filter(p => p.enabled);
  const disabledPlugins = plugins.filter(p => !p.enabled);

  return (
    <>
      <div className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">{t('pluginsTab.activePlugins')}</h3>
            <Badge variant="outline">{enabledPlugins.length} {t('pluginsTab.active')}</Badge>
          </div>
          {enabledPlugins.length === 0 ? (
            <Card className="holo-card">
              <CardContent className="py-6">
                <p className="text-center text-muted-foreground">{t('pluginsTab.noActive')}</p>
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
                          {plugin.requires_api_key && <Key className="h-3 w-3 text-muted-foreground" />}
                        </CardTitle>
                        <CardDescription>{plugin.description}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{t('pluginsTab.version')}:</span>
                        <span>{plugin.version}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{t('pluginsTab.author')}:</span>
                        <span>{plugin.author}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{t('pluginsTab.status')}:</span>
                        <Badge variant="outline" className="text-xs">{plugin.status}</Badge>
                      </div>
                    </div>
                    <Button 
                      onClick={() => togglePlugin(plugin.id, false)}
                      disabled={toggling[plugin.id]}
                      className="w-full"
                    >
                      {toggling[plugin.id] ? t('common.loading') : t('plugins.disable')}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {disabledPlugins.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">{t('pluginsTab.availablePlugins')}</h3>
            <div className="grid gap-4 md:grid-cols-2">
              {disabledPlugins.map((plugin) => (
                <Card key={plugin.id} className="holo-card">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      {plugin.name}
                      {plugin.requires_api_key && <Key className="h-4 w-4 text-amber-500" />}
                    </CardTitle>
                    <CardDescription>{plugin.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">{t('pluginsTab.version')}:</span>
                        <span>{plugin.version}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">{t('pluginsTab.author')}:</span>
                        <span>{plugin.author}</span>
                      </div>
                      {plugin.requires_api_key && (
                        <div className="flex items-center gap-2 text-amber-600">
                          <Key className="h-3 w-3" />
                          <span className="text-xs">{t('plugins.apiKeyRequired')}</span>
                        </div>
                      )}
                    </div>
                    <Button 
                      onClick={() => togglePlugin(plugin.id, true)}
                      disabled={toggling[plugin.id] || plugin.status !== 'available'}
                      variant="default"
                      className="w-full"
                    >
                      {toggling[plugin.id] ? t('common.loading') : t('plugins.enable')}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>

      {pendingPlugin && pendingPlugin.api_key_info && (
        <ApiKeyModal
          open={apiKeyModalOpen}
          onClose={() => {
            setApiKeyModalOpen(false);
            setPendingPlugin(null);
          }}
          apiKeyInfo={pendingPlugin.api_key_info}
          onSuccess={handleApiKeySuccess}
        />
      )}
    </>
  );
};

export default PluginsTab;
