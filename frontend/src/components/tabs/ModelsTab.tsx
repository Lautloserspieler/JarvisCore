import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, Download, Power, Brain, HardDrive, Cpu } from "lucide-react";

interface Model {
  id: string;
  name: string;
  filename: string;
  size: number;
  contextLength: number;
  status: "active" | "loaded" | "downloaded" | "available";
}

const ModelsTab = () => {
  const [models, setModels] = useState<Model[]>([
    {
      id: "1",
      name: "LLaMA 3 8B",
      filename: "llama-3-8b-instruct.gguf",
      size: 4500,
      contextLength: 8192,
      status: "active",
    },
    {
      id: "2",
      name: "Mistral 7B",
      filename: "mistral-7b-instruct-v0.2.gguf",
      size: 4100,
      contextLength: 32768,
      status: "loaded",
    },
    {
      id: "3",
      name: "Phi-3 Mini",
      filename: "phi-3-mini-4k-instruct.gguf",
      size: 2300,
      contextLength: 4096,
      status: "downloaded",
    },
    {
      id: "4",
      name: "Gemma 7B",
      filename: "gemma-7b-it.gguf",
      size: 5200,
      contextLength: 8192,
      status: "available",
    },
    {
      id: "5",
      name: "CodeLlama 13B",
      filename: "codellama-13b-instruct.gguf",
      size: 7400,
      contextLength: 16384,
      status: "available",
    },
  ]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const handleUnloadAll = () => {
    setModels(models.map(m => ({
      ...m,
      status: m.status === "active" || m.status === "loaded" ? "downloaded" : m.status
    })));
  };

  const getStatusBadge = (status: Model["status"]) => {
    switch (status) {
      case "active":
        return <Badge className="bg-green-500">🟢 ACTIVE</Badge>;
      case "loaded":
        return <Badge className="bg-blue-500">🔵 LOADED</Badge>;
      case "downloaded":
        return <Badge variant="outline">✅ Downloaded</Badge>;
      case "available":
        return <Badge variant="destructive">❌ Not Downloaded</Badge>;
    }
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4" />
            Download Model
          </Button>
        </div>
        <Button variant="destructive" size="sm" onClick={handleUnloadAll}>
          <Power className="h-4 w-4" />
          Unload All
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {models.map((model) => (
          <Card key={model.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  {model.name}
                </span>
                {getStatusBadge(model.status)}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Filename</span>
                  <span className="font-mono text-xs">{model.filename}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground flex items-center gap-1">
                    <HardDrive className="h-3 w-3" /> Size
                  </span>
                  <span>{(model.size / 1000).toFixed(1)} GB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground flex items-center gap-1">
                    <Cpu className="h-3 w-3" /> Context Length
                  </span>
                  <span>{model.contextLength.toLocaleString()} tokens</span>
                </div>
              </div>

              <div className="flex gap-2">
                {model.status === "available" && (
                  <Button size="sm" className="w-full">
                    <Download className="h-4 w-4" />
                    Download
                  </Button>
                )}
                {model.status === "downloaded" && (
                  <Button size="sm" className="w-full">
                    <Power className="h-4 w-4" />
                    Load
                  </Button>
                )}
                {(model.status === "loaded" || model.status === "active") && (
                  <>
                    {model.status !== "active" && (
                      <Button size="sm" className="flex-1">
                        Activate
                      </Button>
                    )}
                    <Button size="sm" variant="outline" className="flex-1">
                      Unload
                    </Button>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ModelsTab;
