import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { RefreshCw, Download, Power, Brain, HardDrive, Cpu, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Model {
  id: string;
  name: string;
  provider: string;
  size: string;
  hf_model: string;
  isActive: boolean;
  isDownloaded: boolean;
  capabilities: string[];
  downloadProgress?: {
    progress: number;
    status: string;
    message: string;
  };
}

const ModelsTab = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeModel, setActiveModel] = useState<Model | null>(null);
  const { toast } = useToast();

  const API_BASE = 'http://localhost:5050/api';

  // Fetch models from API
  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_BASE}/models`);
      const data = await response.json();
      setModels(data);
      
      // Get active model
      const activeResponse = await fetch(`${API_BASE}/models/active`);
      const activeData = await activeResponse.json();
      setActiveModel(activeData);
    } catch (error) {
      console.error('Failed to fetch models:', error);
      toast({
        title: 'Fehler',
        description: 'Modelle konnten nicht geladen werden',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Download model
  const handleDownload = async (modelId: string) => {
    try {
      const response = await fetch(`${API_BASE}/models/${modelId}/download`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: 'Download gestartet',
          description: data.message
        });
      } else {
        toast({
          title: 'Download fehlgeschlagen',
          description: data.message,
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Download failed:', error);
      toast({
        title: 'Fehler',
        description: 'Download konnte nicht gestartet werden',
        variant: 'destructive'
      });
    }
  };

  // Load model
  const handleLoad = async (modelId: string) => {
    try {
      const response = await fetch(`${API_BASE}/models/${modelId}/load`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: 'Modell geladen',
          description: data.message
        });
        fetchModels();
      } else {
        toast({
          title: 'Laden fehlgeschlagen',
          description: data.message,
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Load failed:', error);
      toast({
        title: 'Fehler',
        description: 'Modell konnte nicht geladen werden',
        variant: 'destructive'
      });
    }
  };

  // Unload model
  const handleUnload = async () => {
    try {
      const response = await fetch(`${API_BASE}/models/unload`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: 'Modell entladen',
          description: 'Alle Modelle wurden entladen'
        });
        fetchModels();
      }
    } catch (error) {
      console.error('Unload failed:', error);
    }
  };

  // WebSocket for real-time updates
  useEffect(() => {
    fetchModels();
    
    const ws = new WebSocket('ws://localhost:5050/ws');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Handle download progress updates
      if (data.type === 'model_download_progress') {
        setModels(prev => prev.map(model => {
          if (model.id === data.modelId) {
            return {
              ...model,
              downloadProgress: {
                progress: data.progress,
                status: 'downloading',
                message: data.message
              }
            };
          }
          return model;
        }));
      }
      
      // Refresh models on download complete
      if (data.type === 'model_download_complete') {
        fetchModels();
      }
    };
    
    // Poll for updates every 2 seconds during downloads
    const interval = setInterval(() => {
      if (models.some(m => m.downloadProgress)) {
        fetchModels();
      }
    }, 2000);
    
    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, []);

  const getStatusBadge = (model: Model) => {
    if (model.downloadProgress) {
      return (
        <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">
          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
          Wird heruntergeladen
        </Badge>
      );
    }
    
    if (model.isActive) {
      return (
        <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
          <CheckCircle className="w-3 h-3 mr-1" />
          AKTIV
        </Badge>
      );
    }
    
    if (model.isDownloaded) {
      return (
        <Badge className="bg-primary/20 text-primary border-primary/50">
          <CheckCircle className="w-3 h-3 mr-1" />
          Heruntergeladen
        </Badge>
      );
    }
    
    return (
      <Badge className="bg-muted text-muted-foreground border-border">
        <XCircle className="w-3 h-3 mr-1" />
        Nicht heruntergeladen
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
    <div className="space-y-6">
      {/* Actions Bar */}
      <div className="flex flex-wrap gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={fetchModels}
          className="border-primary/30 hover:bg-primary/10"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Aktualisieren
        </Button>
        
        {activeModel && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleUnload}
            className="border-destructive/30 hover:bg-destructive/10 text-destructive"
          >
            <Power className="w-4 h-4 mr-2" />
            Modell entladen
          </Button>
        )}
      </div>

      {/* Active Model Info */}
      {activeModel && (
        <Card className="bg-green-500/5 border-green-500/30">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              Aktives Modell: {activeModel.name}
            </CardTitle>
          </CardHeader>
        </Card>
      )}

      {/* Models Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {models.map((model) => (
          <Card
            key={model.id}
            className={`bg-card/50 border-border/50 backdrop-blur-sm transition-all hover:border-primary/30 ${
              model.isActive ? 'border-green-500/30 bg-green-500/5' : ''
            }`}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-display flex items-center gap-2">
                  <Brain className="w-5 h-5 text-primary" />
                  {model.name}
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
                    Provider
                  </span>
                  <span className="text-foreground">{model.provider}</span>
                </div>

                {/* Size */}
                <div className="flex items-center justify-between text-muted-foreground">
                  <span className="flex items-center gap-2">
                    <HardDrive className="w-4 h-4" />
                    Größe
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

                {/* Download Progress */}
                {model.downloadProgress && (
                  <div className="space-y-2 pt-2 border-t border-border/50">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">{model.downloadProgress.message}</span>
                      <span className="text-primary font-medium">{model.downloadProgress.progress}%</span>
                    </div>
                    <Progress value={model.downloadProgress.progress} className="h-2" />
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2">
                  {!model.isDownloaded && !model.downloadProgress && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 border-primary/30"
                      onClick={() => handleDownload(model.id)}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Herunterladen
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
                      Laden
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
                      Aktiv
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ModelsTab;
