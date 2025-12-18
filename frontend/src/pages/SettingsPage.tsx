import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
import { Download, Upload, RotateCcw, Save, Settings2, Zap, Shield, Database, Plug, Globe } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useLanguage } from '@/hooks/useLanguage';

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
  const { t } = useTranslation();
  const { currentLanguage, switchLanguage } = useLanguage();
  const { toast } = useToast();
  
  // State
  const [llamaSettings, setLlamaSettings] = useState<LlamaSettings>({
    temperature: 0.7,
    top_p: 0.9,
    top_k: 40,
    repeat_penalty: 1.1,
    max_tokens: 2048,
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

  const [systemPrompt, setSystemPrompt] = useState(
    currentLanguage === 'de' 
      ? 'Du bist JARVIS, ein hilfreicher deutscher KI-Assistent. Antworte präzise und freundlich.'
      : 'You are JARVIS, a helpful AI assistant. Respond precisely and in a friendly manner.'
  );
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loadingPlugins, setLoadingPlugins] = useState<{[key: string]: boolean}>({});

  // Load settings on mount
  useEffect(() => {
    loadSettings();
    loadModelInfo();
    loadPlugins();
  }, []);

  // Update system prompt when language changes
  useEffect(() => {
    setSystemPrompt(
      currentLanguage === 'de'
        ? 'Du bist JARVIS, ein hilfreicher deutscher KI-Assistent. Antworte präzise und freundlich.'
        : 'You are JARVIS, a helpful AI assistant. Respond precisely and in a friendly manner.'
    );
  }, [currentLanguage]);

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
        const filtered = data.filter((p: Plugin) => 
          !['calculator_plugin', 'system_info_plugin', 'time_plugin'].includes(p.id)
        );
        setPlugins(filtered);
      }
    } catch (error) {
      console.error('Failed to load plugins:', error);
      toast({
        title: t('common.error'),
        description: t('plugins.loadError'),
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
        
        setPlugins(prev => 
          prev.map(p => 
            p.id === pluginId ? { ...p, enabled } : p
          )
        );
        
        toast({
          title: t('common.success'),
          description: result.message || (enabled ? t('plugins.enabled') : t('plugins.disabled'))
        });
      } else {
        throw new Error('Plugin konnte nicht geändert werden');
      }
    } catch (error) {
      console.error('Error toggling plugin:', error);
      toast({
        title: t('common.error'),
        description: enabled ? t('plugins.enableError') : t('plugins.disableError'),
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
          title: t('llm.settingsSaved'),
          description: t('llm.settingsSavedDesc')
        });
      }
    } catch (error) {
      toast({
        title: t('common.error'),
        description: t('llm.saveError'),
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
    a.download = `jarvis-${t('settings.export').toLowerCase()}-${Date.now()}.json`;
    a.click();

    toast({
      title: t('settings.exportSuccess'),
      description: t('settings.exportDesc')
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
          title: t('settings.importSuccess'),
          description: t('settings.importDesc')
        });
      } catch (error) {
        toast({
          title: t('settings.importError'),
          description: t('settings.importErrorDesc'),
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
      max_tokens: 2048,
      context_window: 8192,
      n_gpu_layers: -1,
      n_threads: 8,
      stream_mode: false
    });

    toast({
      title: t('advanced.resetSuccess'),
      description: t('advanced.resetSuccessDesc')
    });
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">{t('settings.title')}</h1>
          <p className="text-muted-foreground">{t('settings.description')}</p>
        </div>
        <div className="flex gap-2">
          {/* Language Switcher */}
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => switchLanguage(currentLanguage === 'de' ? 'en' : 'de')}
            title={t('language.label')}
          >
            <Globe className="w-4 h-4 mr-2" />
            {currentLanguage === 'de' ? 'EN' : 'DE'}
          </Button>
          
          <Button variant="outline" onClick={exportSettings}>
            <Download className="w-4 h-4 mr-2" />
            {t('settings.export')}
          </Button>
          <label>
            <Button variant="outline" asChild>
              <span>
                <Upload className="w-4 h-4 mr-2" />
                {t('settings.import')}
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
            {t('tabs.llm').replace('🧠 ', '')}
          </TabsTrigger>
          <TabsTrigger value="plugins">
            <Plug className="w-4 h-4 mr-2" />
            {t('tabs.plugins').replace('🔌 ', '')}
          </TabsTrigger>
          <TabsTrigger value="ui">
            <Settings2 className="w-4 h-4 mr-2" />
            {t('tabs.ui').replace('🎨 ', '')}
          </TabsTrigger>
          <TabsTrigger value="api">
            <Database className="w-4 h-4 mr-2" />
            {t('tabs.api').replace('🔗 ', '')}
          </TabsTrigger>
          <TabsTrigger value="advanced">
            <Shield className="w-4 h-4 mr-2" />
            {t('tabs.advanced').replace('⚙️ ', '')}
          </TabsTrigger>
        </TabsList>

        {/* LLM Parameters Tab */}
        <TabsContent value="llama" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('llm.title').replace('🧠 ', '')}</CardTitle>
              <CardDescription>
                {t('llm.description')}
                {modelInfo && (
                  <div className="mt-2 text-sm">
                    <span className="font-semibold">{t('llm.activeModel')}:</span> {modelInfo.model} ({modelInfo.device})
                  </div>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Enable LLM Switch */}
              <div className="flex items-center justify-between p-4 bg-accent/50 rounded-lg">
                <div className="space-y-0.5">
                  <Label className="text-base">{t('llm.enable')}</Label>
                  <p className="text-sm text-muted-foreground">
                    {t('llm.enableDesc')}
                  </p>
                </div>
                <Switch
                  checked={true}
                  disabled
                />
              </div>

              <Separator />

              {/* Context Length */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>{t('llm.contextLength')}</Label>
                  <span className="text-sm text-muted-foreground">{llamaSettings.context_window} Tokens</span>
                </div>
                <Slider
                  value={[llamaSettings.context_window]}
                  onValueChange={(val) => setLlamaSettings({ ...llamaSettings, context_window: val[0] })}
                  min={512}
                  max={8192}
                  step={512}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  {llamaSettings.context_window} {t('llm.contextLengthDesc')}
                </p>
              </div>

              <Separator />

              {/* Temperature */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>{t('llm.temperature')}</Label>
                  <span className="text-sm text-muted-foreground">{llamaSettings.temperature}</span>
                </div>
                <Slider
                  value={[llamaSettings.temperature]}
                  onValueChange={(val) => setLlamaSettings({ ...llamaSettings, temperature: val[0] })}
                  min={0}
                  max={2}
                  step={0.1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>0.0 ({t('llm.precise')})</span>
                  <span>2.0 ({t('llm.creative')})</span>
                </div>
              </div>

              <div className="pt-4">
                <Button onClick={saveLlamaSettings} className="w-full">
                  <Save className="w-4 h-4 mr-2" />
                  {t('llm.saveSettings')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Plugins Tab */}
        <TabsContent value="plugins" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('plugins.title').replace('🔌 ', '')}</CardTitle>
              <CardDescription>{t('plugins.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              {plugins.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>{t('plugins.noPlugins')}</p>
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
                          <span className="text-xs bg-muted px-2 py-1 rounded">{t('plugins.version')}{plugin.version}</span>
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
                          t('common.loading')
                        ) : plugin.enabled ? (
                          t('plugins.disable')
                        ) : (
                          t('plugins.enable')
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
              <CardTitle>{t('ui.title').replace('🎨 ', '')}</CardTitle>
              <CardDescription>{t('ui.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>{t('ui.theme')}</Label>
                <Select value={uiSettings.theme} onValueChange={(val: any) => setUISettings({ ...uiSettings, theme: val }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dark">{t('ui.dark').replace('🌙 ', '')}</SelectItem>
                    <SelectItem value="light">{t('ui.light').replace('☀️ ', '')}</SelectItem>
                    <SelectItem value="auto">{t('ui.auto').replace('🔄 ', '')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>{t('ui.fontSize')}</Label>
                <Select value={uiSettings.fontSize} onValueChange={(val: any) => setUISettings({ ...uiSettings, fontSize: val }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="small">{t('ui.small')}</SelectItem>
                    <SelectItem value="medium">{t('ui.medium')}</SelectItem>
                    <SelectItem value="large">{t('ui.large')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <Label>{t('ui.autoScroll')}</Label>
                <Switch
                  checked={uiSettings.autoScroll}
                  onCheckedChange={(val) => setUISettings({ ...uiSettings, autoScroll: val })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label>{t('ui.notifications').replace('🔔 ', '')}</Label>
                <Switch
                  checked={uiSettings.notifications}
                  onCheckedChange={(val) => setUISettings({ ...uiSettings, notifications: val })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label>{t('ui.soundEffects').replace('🔊 ', '')}</Label>
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
              <CardTitle>{t('api.title').replace('🔗 ', '')}</CardTitle>
              <CardDescription>{t('api.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>{t('api.backendUrl')}</Label>
                <Input
                  value={apiSettings.backend_url}
                  onChange={(e) => setAPISettings({ ...apiSettings, backend_url: e.target.value })}
                  placeholder={t('api.backendUrlPlaceholder')}
                />
              </div>

              <div className="space-y-2">
                <Label>{t('api.websocketUrl')}</Label>
                <Input
                  value={apiSettings.ws_url}
                  onChange={(e) => setAPISettings({ ...apiSettings, ws_url: e.target.value })}
                  placeholder={t('api.websocketUrlPlaceholder')}
                />
              </div>

              <div className="space-y-2">
                <Label>{t('api.timeout')}</Label>
                <Input
                  type="number"
                  value={apiSettings.timeout}
                  onChange={(e) => setAPISettings({ ...apiSettings, timeout: parseInt(e.target.value) })}
                />
              </div>

              <div className="space-y-2">
                <Label>{t('api.retryAttempts')}</Label>
                <Input
                  type="number"
                  value={apiSettings.retry_attempts}
                  onChange={(e) => setAPISettings({ ...apiSettings, retry_attempts: parseInt(e.target.value) })}
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>{t('api.apiKey')}</Label>
                <Input
                  type="password"
                  value={apiSettings.api_key}
                  onChange={(e) => setAPISettings({ ...apiSettings, api_key: e.target.value })}
                  placeholder={t('api.apiKeyPlaceholder')}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Tab */}
        <TabsContent value="advanced" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('advanced.title').replace('⚙️ ', '')}</CardTitle>
              <CardDescription>{t('advanced.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>{t('advanced.systemPrompt')}</Label>
                <Textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  rows={6}
                  placeholder={t('advanced.systemPromptPlaceholder')}
                />
                <p className="text-xs text-muted-foreground">
                  {t('advanced.systemPromptDesc')}
                </p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>{t('advanced.dangerZone')}</Label>
                <Button variant="destructive" onClick={resetToDefaults} className="w-full">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  {t('advanced.resetAll')}
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