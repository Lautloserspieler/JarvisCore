import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Brain, Download, Trash2, Play, Square, Loader2 } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Model {
  id: string;
  name: string;
  provider: string;
  type?: string;
  size?: string;
  isActive: boolean;
  isDownloaded?: boolean;
  capabilities: string[];
}

const ModelsTab = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [activeModel, setActiveModel] = useState<Model | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchModels = async () => {
    try {
      const [modelsData, activeData] = await Promise.all([
        apiRequest<Model[]>('/api/models'),
        apiRequest<Model>('/api/models/active').catch(() => null)
      ]);
      setModels(modelsData || []);
      setActiveModel(activeData);
      setError(null);
    } catch (error) {
      console.error('Fehler beim Laden der Modelle:', error);
      setError('Verbindung zum Backend fehlgeschlagen');
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleDownload = async (modelId: string) => {
    setDownloading(modelId);
    try {
      const result = await apiRequest<{success: boolean, message: string}>(
        `/api/models/${modelId}/download`,
        { method: 'POST' }
      );
      
      if (result.success) {
        toast({
          title: "Download erfolgreich",
          description: result.message,
        });
        await fetchModels();
      } else {
        toast({
          title: "Download fehlgeschlagen",
          description: result.message,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Fehler",
        description: "Download konnte nicht gestartet werden",
        variant: "destructive"
      });
    } finally {
      setDownloading(null);
    }
  };

  const handleLoad = async (modelId: string) => {
    try {
      const result = await apiRequest<{success: boolean, message: string}>(
        `/api/models/${modelId}/load`,
        { method: 'POST' }
      );
      
      if (result.success) {
        toast({
          title: "Modell geladen",
          description: result.message,
        });
        await fetchModels();
      } else {
        toast({
          title: "Fehler",
          description: result.message,
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Fehler",
        description: "Modell konnte nicht geladen werden",
        variant: "destructive"
      });
    }
  };

  const handleUnload = async () => {
    try {
      const result = await apiRequest<{success: boolean, message: string}>(
        '/api/models/unload',
        { method: 'POST' }
      );
      
      if (result.success) {
        toast({
          title: "Modell entladen",
          description: result.message,
        });
        await fetchModels();
      }
    } catch (error) {
      toast({
        title: "Fehler",
        description: "Modell konnte nicht entladen werden",
        variant: "destructive"
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-muted-foreground">Lade Modelle...</div>
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

  return (
    <div className="space-y-6">
      {/* Active Model */}
      {activeModel && (
        <Card className="holo-panel border-primary/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Aktives Modell: {activeModel.name}
                </CardTitle>
                <CardDescription>{activeModel.provider}</CardDescription>
              </div>
              <div className="flex gap-2">
                <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                  Aktiv
                </Badge>
                <Button variant="outline" size="sm" onClick={handleUnload}>
                  <Square className="h-4 w-4 mr-2" />
                  Entladen
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {activeModel.capabilities?.map((cap) => (
                <Badge key={cap} variant="outline">
                  {cap}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Available Models */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Verfügbare Modelle</h3>
        {models.length === 0 ? (
          <Card className="holo-card">
            <CardContent className="pt-6">
              <p className="text-center text-muted-foreground">Keine Modelle verfügbar</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {models.map((model) => (
              <Card key={model.id} className="holo-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base">{model.name}</CardTitle>
                      <CardDescription>
                        {model.provider} {model.size && `• ${model.size}`}
                      </CardDescription>
                    </div>
                    {model.isActive ? (
                      <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                        Aktiv
                      </Badge>
                    ) : model.isDownloaded ? (
                      <Badge variant="outline">Heruntergeladen</Badge>
                    ) : (
                      <Badge variant="secondary">Nicht geladen</Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {model.capabilities?.map((cap) => (
                      <Badge key={cap} variant="outline" className="text-xs">
                        {cap}
                      </Badge>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    {model.isActive ? (
                      <Button variant="outline" size="sm" className="w-full" onClick={handleUnload}>
                        <Square className="h-4 w-4 mr-2" />
                        Entladen
                      </Button>
                    ) : model.isDownloaded ? (
                      <Button size="sm" className="w-full" onClick={() => handleLoad(model.id)}>
                        <Play className="h-4 w-4 mr-2" />
                        Laden
                      </Button>
                    ) : (
                      <Button 
                        size="sm" 
                        className="w-full" 
                        variant="outline"
                        onClick={() => handleDownload(model.id)}
                        disabled={downloading === model.id}
                      >
                        {downloading === model.id ? (
                          <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Downloading...</>
                        ) : (
                          <><Download className="h-4 w-4 mr-2" /> Herunterladen</>
                        )}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Model Management */}
      <Card className="holo-panel">
        <CardHeader>
          <CardTitle>Modell-Verwaltung</CardTitle>
          <CardDescription>
            Verwalten Sie Ihre KI-Modelle und deren Konfiguration
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground">
            <p>• Modelle werden in ./models gespeichert</p>
            <p>• Download-Fortschritt wird im Protokoll angezeigt</p>
            <p>• Nur heruntergeladene Modelle können geladen werden</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModelsTab;
