import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Download, Upload, RotateCcw, Save, Settings2, Zap, Shield, Database, Plug } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface LlamaSettings {
  temperature: number;
  top_p: number;
  top_k: number;
  repeat_penalty: number;
  max_tokens: number;
  context_window: number;
  n_gpu_layers: number;
  n_threads: number;
  stream_mode: boolean;
}

interface UISettings {
  theme: 'dark' | 'light' | 'auto';
  fontSize: 'small' | 'medium' | 'large';
  autoScroll: boolean;
  notifications: boolean;
  soundEffects: boolean;
}

interface APISettings {
  backend_url: string;
  ws_url: string;
  timeout: number;
  retry_attempts: number;
  api_key: string;
}

interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  status: string;
}

const SettingsPage: React.FC = () => {
  const { toast } = useToast();
  
  // State
  const [llamaSettings, setLlamaSettings] = useState<LlamaSettings>({
    temperature: 0.7,
    top_p: 0.9,
    top_k: 40,
    repeat_penalty: 1.1,
    max_tokens: 512,
    context_window: 8192,
    n_gpu_layers: -1,
    n_threads: 8,
    stream_mode: false
  });

  const [uiSettings, setUISettings] = useState<UISettings>({
    theme: 'dark',
    fontSize: 'medium',
    autoScroll: true,
    notifications: true,
    soundEffects: false
  });

  const [apiSettings, setAPISettings] = useState<APISettings>({
    backend_url: 'http://localhost:5050',
    ws_url: 'ws://localhost:5050',
    timeout: 30000,
    retry_attempts: 3,
    api_key: ''
  });

  const [systemPrompt, setSystemPrompt] = useState('Du bist JARVIS, ein hilfreicher deutscher KI-Assistent. Antworte präzise und freundlich.');
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loadingPlugins, setLoadingPlugins] = useState<{[key: string]: boolean}>({});

  // Load settings on mount
  useEffect(() => {
    loadSettings();
    loadModelInfo();
    loadPlugins();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('http://localhost:5050/api/settings/llama');
      if (response.ok) {
        const data = await response.json();
        setLlamaSettings(data);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const loadModelInfo = async () => {
    try {
      const response = await fetch('http://localhost:5050/api/settings/llama/info');
      if (response.ok) {
        const data = await response.json();
        setModelInfo(data);
      }
    } catch (error) {
      console.error('Failed to load model info:', error);
    }
  };

  const loadPlugins = async () => {
    try {
      const response = await fetch('http://localhost:5050/api/plugins');
      if (response.ok) {
        const data = await response.json();
        // Filter out demo plugins (calculator, system_info, time_plugin)
        const filtered = data.filter((p: Plugin) => 
          !['calculator_plugin', 'system_info_plugin', 'time_plugin'].includes(p.id)
        );
        setPlugins(filtered);
      }
    } catch (error) {
      console.error('Failed to load plugins:', error);
      toast({
        title: 'Fehler',
        description: 'Plugins konnten nicht geladen werden',
        variant: 'destructive'
      });
    }
  };

  const togglePlugin = async (pluginId: string, enabled: boolean) => {
    setLoadingPlugins(prev => ({ ...prev, [pluginId]: true }));
    
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
      console.error('Error toggling plugin:', error);
      toast({
        title: 'Fehler',
        description: enabled ? 'Plugin konnte nicht aktiviert werden' : 'Plugin konnte nicht deaktiviert werden',
        variant: 'destructive'
      });
    } finally {
      setLoadingPlugins(prev => ({ ...prev, [pluginId]: false }));
    }
  };

  const saveLlamaSettings = async () => {
    try {
      const response = await fetch('http://localhost:5050/api/settings/llama', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(llamaSettings)
      });

      if (response.ok) {
        toast({
          title: 'Einstellungen gespeichert',
          description: 'llama.cpp Parameter aktualisiert'
        });
      }
    } catch (error) {
      toast({
        title: 'Fehler',
        description: 'Einstellungen konnten nicht gespeichert werden',
        variant: 'destructive'
      });
    }
  };

  const exportSettings = () => {
    const allSettings = {
      llama: llamaSettings,
      ui: uiSettings,
      api: apiSettings,
      systemPrompt
    };

    const blob = new Blob([JSON.stringify(allSettings, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `jarvis-einstellungen-${Date.now()}.json`;
    a.click();

    toast({
      title: 'Einstellungen exportiert',
      description: 'Konfiguration als JSON heruntergeladen'
    });
  };

  const importSettings = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target?.result as string);
        setLlamaSettings(imported.llama || llamaSettings);
        setUISettings(imported.ui || uiSettings);
        setAPISettings(imported.api || apiSettings);
        setSystemPrompt(imported.systemPrompt || systemPrompt);

        toast({
          title: 'Einstellungen importiert',
          description: 'Konfiguration erfolgreich geladen'
        });
      } catch (error) {
        toast({
          title: 'Import fehlgeschlagen',
          description: 'Ungültige Einstellungsdatei',
          variant: 'destructive'
        });
      }
    };
    reader.readAsText(file);
  };

  const resetToDefaults = () => {
    setLlamaSettings({
      temperature: 0.7,
      top_p: 0.9,
      top_k: 40,
      repeat_penalty: 1.1,
      max_tokens: 512,
      context_window: 8192,
      n_gpu_layers: -1,
      n_threads: 8,
      stream_mode: false
    });

    toast({
      title: 'Zurückgesetzt',
      description: 'Alle Einstellungen zurückgesetzt'
    });
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Einstellungen</h1>
          <p className="text-muted-foreground">Konfiguriere JARVIS Verhalten und Aussehen</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportSettings}>
            <Download className="w-4 h-4 mr-2" />
            Exportieren
          </Button>
          <label>
            <Button variant="outline" asChild>
              <span>
                <Upload className="w-4 h-4 mr-2" />
                Importieren
              </span>
            </Button>
            <input type="file" accept=".json" onChange={importSettings} className="hidden" />
          </label>
        </div>
      </div>

      <Tabs defaultValue="llama" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="llama">
            <Zap className="w-4 h-4 mr-2" />
            LLM
          </TabsTrigger>
          <TabsTrigger value="plugins">
            <Plug className="w-4 h-4 mr-2" />
            Plugins
          </TabsTrigger>
          <TabsTrigger value="ui">
            <Settings2 className="w-4 h-4 mr-2" />
            UI
          </TabsTrigger>
          <TabsTrigger value="api">
            <Database className="w-4 h-4 mr-2" />
            API
          </TabsTrigger>
          <TabsTrigger value="advanced">
            <Shield className="w-4 h-4 mr-2" />
            Erweitert
          </TabsTrigger>
        </TabsList>

        {/* LLM Parameters Tab */}
        <TabsContent value="llama" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>llama.cpp Inference Parameter</CardTitle>
              <CardDescription>
                Konfiguriere Textgenerierung
                {modelInfo && (
                  <div className="mt-2 text-sm">
                    <span className="font-semibold">Aktives Modell:</span> {modelInfo.model} ({modelInfo.device})
                  </div>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Temperature */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Temperatur</Label>
                  <span className="text-sm text-muted-foreground">{llamaSettings.temperature.toFixed(2)}</span>
                </div>
                <Slider
                  value={[llamaSettings.temperature]}
                  onValueChange={(val) => setLlamaSettings({ ...llamaSettings, temperature: val[0] })}
                  min={0}
                  max={2}
                  step={0.05}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Steuert Zufall. Niedriger = fokussiert, Höher = kreativ
                </p>
              </div>

              <Separator />

              {/* Top P */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Top-P (Nucleus Sampling)</Label>
                  <span className="text-sm text-muted-foreground">{llamaSettings.top_p.toFixed(2)}</span>
                </div>
                <Slider
                  value={[llamaSettings.top_p]}
                  onValueChange={(val) => setLlamaSettings({ ...llamaSettings, top_p: val[0] })}
                  min={0}
                  max={1}
                  step={0.05}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Kumulative Wahrscheinlichkeit. 0.9 = top 90% Token
                </p>
              </div>

              <Separator />

              {/* Top K */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Top-K</Label>
                  <span className="text-sm text-muted-foreground">{llamaSettings.top_k}</span>
                </div>
                <Slider
                  value={[llamaSettings.top_k]}
                  onValueChange={(val) => setLlamaSettings({ ...llamaSettings, top_k: val[0] })}
                  min={0}
                  max={100}
                  step={1}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Nur top K Token berücksichtigen. 40 = top 40 Token
                </p>
              </div>

              <Separator />

              {/* Repeat Penalty */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Wiederholungs-Strafe</Label>
                  <span className="text-sm text-muted-foreground">{llamaSettings.repeat_penalty.toFixed(2)}</span>
                </div>
                <Slider
                  value={[llamaSettings.repeat_penalty]}
                  onValueChange={(val) => setLlamaSettings({ ...llamaSettings, repeat_penalty: val[0] })}
                  min={1}
                  max={2}
                  step={0.05}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Bestrafe Wiederholungen. 1.0 = keine Strafe, 2.0 = stark
                </p>
              </div>

              <Separator />

              {/* Max Tokens */}
              <div className="space-y-2">
                <Label>Max Tokens</Label>
                <Input
                  type="number"
                  value={llamaSettings.max_tokens}
                  onChange={(e) => setLlamaSettings({ ...llamaSettings, max_tokens: parseInt(e.target.value) })}
                  min={128}
                  max={32768}
                />
                <p className="text-xs text-muted-foreground">
                  Maximale Antwort-Länge. Höher = länger
                </p>
              </div>

              <Separator />

              {/* Context Window */}
              <div className="space-y-2">
                <Label>Context Fenster</Label>
                <Select
                  value={llamaSettings.context_window.toString()}
                  onValueChange={(val) => setLlamaSettings({ ...llamaSettings, context_window: parseInt(val) })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2048">2K</SelectItem>
                    <SelectItem value="4096">4K</SelectItem>
                    <SelectItem value="8192">8K (Standard)</SelectItem>
                    <SelectItem value="16384">16K</SelectItem>
                    <SelectItem value="32768">32K</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Gesprächsspeicher. Größer = mehr VRAM
                </p>
              </div>

              <Separator />

              {/* GPU Layers */}
              <div className="space-y-2">
                <Label>GPU Layer</Label>
                <Input
                  type="number"
                  value={llamaSettings.n_gpu_layers}
                  onChange={(e) => setLlamaSettings({ ...llamaSettings, n_gpu_layers: parseInt(e.target.value) })}
                  min={-1}
                  max={modelInfo?.max_layers || 64}
                />
                <p className="text-xs text-muted-foreground">
                  -1 = Alle Layer auf GPU. Niedriger = weniger VRAM
                </p>
              </div>

              <Separator />

              {/* CPU Threads */}
              <div className="space-y-2">
                <Label>CPU Threads</Label>
                <Input
                  type="number"
                  value={llamaSettings.n_threads}
                  onChange={(e) => setLlamaSettings({ ...llamaSettings, n_threads: parseInt(e.target.value) })}
                  min={1}
                  max={navigator.hardwareConcurrency || 16}
                />
                <p className="text-xs text-muted-foreground">
                  CPU-Kerne. Empfohlen: {Math.max(4, Math.floor((navigator.hardwareConcurrency || 8) / 2))}
                </p>
              </div>

              <Separator />

              {/* Stream Mode */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Stream Modus</Label>
                  <p className="text-xs text-muted-foreground">
                    Echtzeit Token-Streaming (künftig)
                  </p>
                </div>
                <Switch
                  checked={llamaSettings.stream_mode}
                  onCheckedChange={(val) => setLlamaSettings({ ...llamaSettings, stream_mode: val })}
                  disabled
                />
              </div>

              <div className="pt-4">
                <Button onClick={saveLlamaSettings} className="w-full">
                  <Save className="w-4 h-4 mr-2" />
                  LLM Einstellungen speichern
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Plugins Tab */}
        <TabsContent value="plugins" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Installierte Plugins</CardTitle>
              <CardDescription>Verwalte Plugins und Erweiterungen</CardDescription>
            </CardHeader>
            <CardContent>
              {plugins.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>Keine Plugins verfügbar</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {plugins.map((plugin) => (
                    <div
                      key={plugin.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors"
                    >
                      <div className="flex-1">
                        <h3 className="font-semibold">{plugin.name}</h3>
                        <p className="text-sm text-muted-foreground">{plugin.description}</p>
                        <div className="flex gap-2 mt-1">
                          <span className="text-xs bg-muted px-2 py-1 rounded">v{plugin.version}</span>
                          <span className="text-xs bg-muted px-2 py-1 rounded">{plugin.author}</span>
                        </div>
                      </div>
                      <Button
                        onClick={() => togglePlugin(plugin.id, !plugin.enabled)}
                        disabled={loadingPlugins[plugin.id] || plugin.status !== 'available'}
                        variant={plugin.enabled ? 'default' : 'outline'}
                        size="sm"
                      >
                        {loadingPlugins[plugin.id] ? (
                          'Lädt...'
                        ) : plugin.enabled ? (
                          'Deaktivieren'
                        ) : (
                          'Aktivieren'
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* UI Settings Tab */}
        <TabsContent value="ui" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Benutzeroberäche</CardTitle>
              <CardDescription>Passe Aussehen und Verhalten an</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Thema</Label>
                <Select value={uiSettings.theme} onValueChange={(val: any) => setUISettings({ ...uiSettings, theme: val })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dark">Dunkel</SelectItem>
                    <SelectItem value="light">Hell</SelectItem>
                    <SelectItem value="auto">Automatisch</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Schriftgröße</Label>
                <Select value={uiSettings.fontSize} onValueChange={(val: any) => setUISettings({ ...uiSettings, fontSize: val })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="small">Klein</SelectItem>
                    <SelectItem value="medium">Mittel</SelectItem>
                    <SelectItem value="large">Groß</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <Label>Auto-Scroll</Label>
                <Switch
                  checked={uiSettings.autoScroll}
                  onCheckedChange={(val) => setUISettings({ ...uiSettings, autoScroll: val })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label>Benachrichtigungen</Label>
                <Switch
                  checked={uiSettings.notifications}
                  onCheckedChange={(val) => setUISettings({ ...uiSettings, notifications: val })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label>Soundeffekte</Label>
                <Switch
                  checked={uiSettings.soundEffects}
                  onCheckedChange={(val) => setUISettings({ ...uiSettings, soundEffects: val })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Settings Tab */}
        <TabsContent value="api" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Konfiguration</CardTitle>
              <CardDescription>Backend Verbindungseinstellungen</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Backend URL</Label>
                <Input
                  value={apiSettings.backend_url}
                  onChange={(e) => setAPISettings({ ...apiSettings, backend_url: e.target.value })}
                  placeholder="http://localhost:5050"
                />
              </div>

              <div className="space-y-2">
                <Label>WebSocket URL</Label>
                <Input
                  value={apiSettings.ws_url}
                  onChange={(e) => setAPISettings({ ...apiSettings, ws_url: e.target.value })}
                  placeholder="ws://localhost:5050"
                />
              </div>

              <div className="space-y-2">
                <Label>Timeout (ms)</Label>
                <Input
                  type="number"
                  value={apiSettings.timeout}
                  onChange={(e) => setAPISettings({ ...apiSettings, timeout: parseInt(e.target.value) })}
                />
              </div>

              <div className="space-y-2">
                <Label>Wiederholungsversuche</Label>
                <Input
                  type="number"
                  value={apiSettings.retry_attempts}
                  onChange={(e) => setAPISettings({ ...apiSettings, retry_attempts: parseInt(e.target.value) })}
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>API Schlüssel (Optional)</Label>
                <Input
                  type="password"
                  value={apiSettings.api_key}
                  onChange={(e) => setAPISettings({ ...apiSettings, api_key: e.target.value })}
                  placeholder="Leer für lokale Nutzung"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Tab */}
        <TabsContent value="advanced" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Erweiterte Einstellungen</CardTitle>
              <CardDescription>Expertenkonfiguration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>System Prompt</Label>
                <Textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  rows={6}
                  placeholder="Du bist JARVIS..."
                />
                <p className="text-xs text-muted-foreground">
                  Definiert JARVIS Persönlichkeit und Verhalten
                </p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>⚠️ Gefährliche Zone</Label>
                <Button variant="destructive" onClick={resetToDefaults} className="w-full">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Alle Einstellungen zurücksetzen
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SettingsPage;
