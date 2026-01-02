import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, Download, Power, Brain, HardDrive, Cpu, CheckCircle, XCircle, Loader2, Lock } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { API_BASE_URL } from '@/lib/api';
import TokenDialog from '@/components/models/TokenDialog';
import ModelGalleryMount from '@/components/ModelGalleryMount';

interface Model {
  id: string;
  name: string;
  provider: string;
  size: string;
  hf_model: string;
  isActive: boolean;
  isDownloaded: boolean;
  requires_token: boolean;
  capabilities: string[];
}

interface DownloadStatus {
  is_downloading: boolean;
  current_model: string | null;
  progress: number;
}

const ModelsTab = () => {
  const { t, i18n } = useTranslation();
  const [models, setModels] = useState<Model[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeModel, setActiveModel] = useState<Model | null>(null);
  const [downloadStatus, setDownloadStatus] = useState<DownloadStatus>({
    is_downloading: false,
    current_model: null,
    progress: 0
  });
  const [activeSection, setActiveSection] = useState('installed');
  const [showTokenDialog, setShowTokenDialog] = useState(false);
  const [currentModel, setCurrentModel] = useState<Model | null>(null);
  const [hasToken, setHasToken] = useState(false);
  const { toast } = useToast();

  const lang = i18n.language.startsWith('de') ? 'de' : 'en';

  // Check if HF token is stored
  const checkTokenStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/hf-token/status`);
      const data = await response.json();
      setHasToken(data.has_token);
    } catch (error) {
      console.error('Failed to check token status:', error);
    }
  };

  // Fetch models from API
  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models`);
      const data = await response.json();
      setModels(data);
      
      // Get active model
      const activeResponse = await fetch(`${API_BASE_URL}/api/models/active`);
      const activeData = await activeResponse.json();
      setActiveModel(activeData);
    } catch (error) {
      console.error('Failed to fetch models:', error);
      toast({
        title: t('common.error'),
        description: t('modelsTab.loadError'),
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch download status
  const fetchDownloadStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models/download/status`);
      const data = await response.json();
      setDownloadStatus(data);
    } catch (error) {
      console.error('Failed to fetch download status:', error);
    }
  };

  // Download model
  const handleDownload = async (modelId: string, token?: string) => {
    const model = models.find(m => m.id === modelId);
    if (!model) return;

    // Check if token is needed and we don't have one
    if (model.requires_token && !hasToken && !token) {
      setCurrentModel(model);
      setShowTokenDialog(true);
      return;
    }

    try {
      toast({
        title: t('modelsTab.downloadStarted'),
        description: t('modelsTab.downloading', { model: modelId })
      });

      const body: any = {};
      if (token) {
        body.token = token;
      }

      const response = await fetch(`${API_BASE_URL}/api/models/${modelId}/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await response.json();
      
      if (data.requires_token) {
        // Show token dialog
        setCurrentModel(model);
        setShowTokenDialog(true);
        return;
      }
      
      if (data.success) {
        toast({
          title: t('modelsTab.downloadComplete'),
          description: data.message
        });
        fetchModels();
      } else {
        toast({
          title: t('modelsTab.downloadFailed'),
          description: data.message,
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Download failed:', error);
      toast({
        title: t('common.error'),
        description: t('modelsTab.downloadError'),
        variant: 'destructive'
      });
    }
  };

  // Handle token dialog submit
  const handleTokenSubmit = async ({ token, remember }: { token: string, remember: boolean }) => {
    console.log('[TokenDialog] Submit:', { remember, hasToken: !!token });
    
    try {
      // Save token if remember is checked
      if (remember) {
        console.log('[TokenDialog] Saving token to backend...');
        const response = await fetch(`${API_BASE_URL}/api/hf-token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token })
        });
        const result = await response.json();
        
        if (result.success) {
          setHasToken(true);
          console.log('[TokenDialog] Token saved successfully');
        } else {
          console.error('[TokenDialog] Failed to save token:', result);
        }
      }
      
      // Close dialog
      setShowTokenDialog(false);
      
      // Start download with token (ALWAYS pass token, backend will use stored one if available)
      if (currentModel) {
        console.log('[TokenDialog] Starting download with token...');
        await handleDownload(currentModel.id, token);
      }
    } catch (error) {
      console.error('Failed to save token:', error);
      toast({
        title: t('common.error'),
        description: lang === 'de' ? 'Fehler beim Speichern des Tokens' : 'Failed to save token',
        variant: 'destructive'
      });
    }
  };

  // Load model
  const handleLoad = async (modelId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models/${modelId}/load`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: t('modelsTab.modelLoaded'),
          description: data.message
        });
        fetchModels();
      } else {
        toast({
          title: t('modelsTab.loadFailed'),
          description: data.message,
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Load failed:', error);
      toast({
        title: t('common.error'),
        description: t('modelsTab.loadError'),
        variant: 'destructive'
      });
    }
  };

  // Unload model
  const handleUnload = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models/unload`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: t('modelsTab.modelUnloaded'),
          description: t('modelsTab.allUnloaded')
        });
        fetchModels();
      }
    } catch (error) {
      console.error('Unload failed:', error);
    }
  };

  // Poll for download progress
  useEffect(() => {
    checkTokenStatus();
    fetchModels();
    fetchDownloadStatus();

    const interval = setInterval(() => {
      fetchDownloadStatus();
      if (downloadStatus.is_downloading) {
        fetchModels();
      }
    }, 1000); // Poll every second during download

    return () => clearInterval(interval);
  }, [downloadStatus.is_downloading]);

  const getStatusBadge = (model: Model) => {
    const isDownloading = downloadStatus.is_downloading && downloadStatus.current_model === model.id;
    
    if (isDownloading) {
      return (
        <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">
          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
          {downloadStatus.progress.toFixed(1)}%
        </Badge>
      );
    }
    
    if (model.isActive) {
      return (
        <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
          <CheckCircle className="w-3 h-3 mr-1" />
          {t('modelsTab.active').toUpperCase()}
        </Badge>
      );
    }
    
    if (model.isDownloaded) {
      return (
        <Badge className="bg-primary/20 text-primary border-primary/50">
          <CheckCircle className="w-3 h-3 mr-1" />
          {t('modelsTab.downloaded')}
        </Badge>
      );
    }
    
    return (
      <Badge className="bg-muted text-muted-foreground border-border">
        <XCircle className="w-3 h-3 mr-1" />
        {t('modelsTab.notDownloaded')}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <Tabs value={activeSection} onValueChange={setActiveSection} className="space-y-6">
      <TabsList className="grid w-full grid-cols-2 lg:w-auto">
        <TabsTrigger value="installed">Installiert</TabsTrigger>
        <TabsTrigger value="gallery">Gallery</TabsTrigger>
      </TabsList>

      <TabsContent value="installed" className="space-y-6">
        {/* Actions Bar */}
        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchModels}
            className="border-primary/30 hover:bg-primary/10"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            {t('common.refresh')}
          </Button>
          
          {activeModel && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleUnload}
              className="border-destructive/30 hover:bg-destructive/10 text-destructive"
            >
              <Power className="w-4 h-4 mr-2" />
              {t('modelsTab.unloadModel')}
            </Button>
          )}
        </div>

        {/* Active Model Info */}
        {activeModel && activeModel.loaded && (
          <Card className="bg-green-500/5 border-green-500/30">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                {t('modelsTab.activeModel')}: {activeModel.name || activeModel.id}
              </CardTitle>
            </CardHeader>
          </Card>
        )}

        {/* Download Progress Bar (Global) */}
        {downloadStatus.is_downloading && (
          <Card className="bg-blue-500/5 border-blue-500/30">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                {t('modelsTab.downloadRunning')}: {downloadStatus.current_model}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{t('modelsTab.progress')}</span>
                  <span className="text-primary font-medium">{downloadStatus.progress.toFixed(1)}%</span>
                </div>
                <Progress value={downloadStatus.progress} className="h-2" />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Models Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {models.map((model) => {
            const isDownloading = downloadStatus.is_downloading && downloadStatus.current_model === model.id;
            
            return (
              <Card
                key={model.id}
                className={`bg-card/50 border-border/50 backdrop-blur-sm transition-all hover:border-primary/30 ${
                  model.isActive ? 'border-green-500/30 bg-green-500/5' : ''
                } ${isDownloading ? 'border-blue-500/30 bg-blue-500/5' : ''}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-display flex items-center gap-2">
                      <Brain className="w-5 h-5 text-primary" />
                      {model.name}
                      {/* Token Required Badge */}
                      {model.requires_token && (
                        <Badge className="bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 border-yellow-500/50">
                          <Lock className="w-3 h-3" />
                        </Badge>
                      )}
                    </CardTitle>
                    {getStatusBadge(model)}
                  </div>
                </CardHeader>
                
                <CardContent>
                  <div className="space-y-3 text-sm">
                    {/* Provider */}
                    <div className="flex items-center justify-between text-muted-foreground">
                      <span className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4" />
                        {t('modelsTab.provider')}
                      </span>
                      <span className="text-foreground">{model.provider}</span>
                    </div>

                    {/* Size */}
                    <div className="flex items-center justify-between text-muted-foreground">
                      <span className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4" />
                        {t('modelsTab.size')}
                      </span>
                      <span className="text-foreground">{model.size}</span>
                    </div>

                    {/* Capabilities */}
                    <div className="flex flex-wrap gap-1">
                      {model.capabilities.map((cap) => (
                        <Badge key={cap} variant="outline" className="text-xs">
                          {cap}
                        </Badge>
                      ))}
                    </div>

                    {/* Download Progress (Per Model) */}
                    {isDownloading && (
                      <div className="space-y-2 pt-2 border-t border-border/50">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">{t('modelsTab.downloading')}...</span>
                          <span className="text-primary font-medium">{downloadStatus.progress.toFixed(1)}%</span>
                        </div>
                        <Progress value={downloadStatus.progress} className="h-2" />
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-2 pt-2">
                      {!model.isDownloaded && !isDownloading && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1 border-primary/30"
                          onClick={() => handleDownload(model.id)}
                          disabled={downloadStatus.is_downloading}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          {t('modelsTab.download')}
                        </Button>
                      )}
                      
                      {isDownloading && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1 border-blue-500/30 text-blue-400"
                          disabled
                        >
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          {downloadStatus.progress.toFixed(0)}%
                        </Button>
                      )}
                      
                      {model.isDownloaded && !model.isActive && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1 border-accent/30"
                          onClick={() => handleLoad(model.id)}
                        >
                          <Cpu className="w-4 h-4 mr-2" />
                          {t('modelsTab.load')}
                        </Button>
                      )}
                      
                      {model.isActive && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1 border-green-500/30 text-green-400"
                          disabled
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          {t('modelsTab.active')}
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Token Dialog */}
        {showTokenDialog && currentModel && (
          <TokenDialog
            modelName={currentModel.name}
            language={lang}
            onClose={() => setShowTokenDialog(false)}
            onSubmit={handleTokenSubmit}
          />
        )}
      </TabsContent>

      <TabsContent value="gallery" className="space-y-4">
        <ModelGalleryMount />
      </TabsContent>
    </Tabs>
  );
};

export default ModelsTab;
