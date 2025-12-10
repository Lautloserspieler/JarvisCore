import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, Download, CheckCircle, AlertTriangle, Loader } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Model {
  key: string;
  displayName: string;
  description: string;
  sizegb: string;
  downloaded: boolean;
  ready: boolean;
  localPath?: string;
  loaded: boolean;
  active: boolean;
}

interface DownloadStatus {
  model: string;
  status: 'inprogress' | 'completed' | 'failed' | 'alreadyexists';
  downloaded: number;
  total: number;
  percent?: number;
  speed?: number;
  eta?: number;
  message?: string;
}

export function ModelsTab() {
  const [models, setModels] = useState<Model[]>([]);
  const [downloadStatus, setDownloadStatus] = useState<DownloadStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // 🔴 CRITICAL: Track active polling intervals
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const downloadingModelRef = useRef<string | null>(null);

  // 📊 Fetch model list
  const fetchModels = useCallback(async () => {
    try {
      console.log('[ModelsTab] Fetching model overview...');
      const response = await apiClient.get('/api/llm/model_overview');
      console.log('[ModelsTab] Model overview:', response.data);
      
      const modelList: Model[] = Object.entries(response.data).map(([key, info]: any) => ({
        key,
        displayName: info.displayName || key,
        description: info.description || '',
        sizegb: info.sizegb || '0',
        downloaded: info.downloaded || false,
        ready: info.ready || false,
        localPath: info.localPath,
        loaded: info.loaded || false,
        active: info.active || false,
      }));
      
      setModels(modelList);
      setError(null);
    } catch (err) {
      console.error('[ModelsTab] Error fetching models:', err);
      setError('Failed to load models');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 🔄 Poll download status (MUST BE AGGRESSIVE)
  const pollDownloadStatus = useCallback(async (modelKey: string) => {
    try {
      console.log(`[ModelsTab] Polling status for ${modelKey}...`);
      
      const response = await apiClient.get('/api/llm/download_status', {
        params: { model: modelKey }
      });
      
      const status: DownloadStatus = response.data;
      console.log(`[ModelsTab] Status response for ${modelKey}:`, status);
      
      // ✅ Update UI
      setDownloadStatus(status);

      // 🏁 If download is complete, stop polling
      if (status.status === 'completed' || status.status === 'alreadyexists' || status.status === 'failed') {
        console.log(`[ModelsTab] Download ${status.status}, stopping poll for ${modelKey}`);
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        downloadingModelRef.current = null;
        
        // Refresh model list to show updated status
        setTimeout(() => fetchModels(), 500);
      }
    } catch (err) {
      console.error(`[ModelsTab] Poll error for ${modelKey}:`, err);
      // Don't stop polling on error, backend might be processing
    }
  }, [fetchModels]);

  // 🚀 Start download
  const handleDownload = useCallback(async (modelKey: string) => {
    try {
      console.log(`[ModelsTab] Starting download for ${modelKey}...`);
      setError(null);
      downloadingModelRef.current = modelKey;

      // ⚡ Start download request
      const response = await apiClient.post('/api/llm/download', {
        model: modelKey
      });

      console.log(`[ModelsTab] Download initiated:`, response.data);

      // 🔄 Start aggressive polling immediately
      // Clear any existing interval first
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }

      // Poll every 500ms (AGGRESSIVE)
      pollingIntervalRef.current = setInterval(() => {
        if (downloadingModelRef.current === modelKey) {
          pollDownloadStatus(modelKey);
        }
      }, 500);

      // Initial status check immediately
      await pollDownloadStatus(modelKey);

    } catch (err) {
      console.error(`[ModelsTab] Download failed for ${modelKey}:`, err);
      setError(`Failed to start download: ${err instanceof Error ? err.message : 'Unknown error'}`);
      downloadingModelRef.current = null;
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
  }, [pollDownloadStatus]);

  // 🛑 Stop polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Initial load
  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4 flex gap-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-destructive">Error</p>
            <p className="text-sm text-destructive/90">{error}</p>
          </div>
        </div>
      )}

      {/* Download Status */}
      {downloadStatus && (
        <Card className="border-primary/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {downloadStatus.status === 'completed' || downloadStatus.status === 'alreadyexists' ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : downloadStatus.status === 'failed' ? (
                <AlertTriangle className="w-5 h-5 text-destructive" />
              ) : (
                <Download className="w-5 h-5 text-primary animate-pulse" />
              )}
              {downloadStatus.model} Download
            </CardTitle>
            <CardDescription>
              {downloadStatus.status === 'completed' ? 'Download Complete!' : 
               downloadStatus.status === 'alreadyexists' ? 'Already Downloaded' :
               downloadStatus.status === 'failed' ? 'Download Failed' :
               'Downloading...'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Progress Bar */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-foreground">Progress</span>
                <span className="text-muted-foreground">
                  {Math.round(downloadStatus.percent || 0)}%
                </span>
              </div>
              <Progress value={downloadStatus.percent || 0} className="h-3" />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Downloaded</p>
                <p className="font-mono text-foreground">
                  {(downloadStatus.downloaded / (1024 * 1024)).toFixed(1)} MB
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Total</p>
                <p className="font-mono text-foreground">
                  {(downloadStatus.total / (1024 * 1024)).toFixed(1)} MB
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Speed</p>
                <p className="font-mono text-foreground">
                  {downloadStatus.speed ? 
                    `${(downloadStatus.speed / (1024 * 1024)).toFixed(1)} MB/s` : 
                    '—'}
                </p>
              </div>
            </div>

            {/* ETA */}
            {downloadStatus.eta && (
              <div>
                <p className="text-sm text-muted-foreground">Estimated Time</p>
                <p className="font-mono text-sm text-foreground">
                  {Math.floor(downloadStatus.eta / 60)}m {Math.floor(downloadStatus.eta % 60)}s
                </p>
              </div>
            )}

            {/* Message */}
            {downloadStatus.message && (
              <p className="text-sm text-muted-foreground italic">{downloadStatus.message}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {models.map((model) => (
          <Card key={model.key} className={model.active ? 'border-primary/50 bg-primary/5' : ''}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{model.displayName}</CardTitle>
                  <CardDescription className="mt-1">{model.description}</CardDescription>
                </div>
                <div className="flex gap-2">
                  {model.active && (
                    <span className="px-2 py-1 text-xs bg-primary text-primary-foreground rounded">
                      Active
                    </span>
                  )}
                  {model.loaded && (
                    <span className="px-2 py-1 text-xs bg-green-500/20 text-green-700 rounded">
                      Loaded
                    </span>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Size */}
              <div className="text-sm">
                <p className="text-muted-foreground">Size</p>
                <p className="font-mono text-foreground">{model.sizegb} GB</p>
              </div>

              {/* Status */}
              <div className="text-sm">
                <p className="text-muted-foreground">Status</p>
                <div className="flex gap-2 mt-1">
                  {model.ready ? (
                    <span className="flex items-center gap-2 text-sm text-green-600">
                      <CheckCircle className="w-4 h-4" />
                      Ready to use
                    </span>
                  ) : model.downloaded ? (
                    <span className="flex items-center gap-2 text-sm text-yellow-600">
                      <AlertTriangle className="w-4 h-4" />
                      Downloaded but not ready
                    </span>
                  ) : (
                    <span className="text-sm text-muted-foreground">Not downloaded</span>
                  )}
                </div>
              </div>

              {/* Download Button */}
              <div className="pt-2">
                <Button
                  onClick={() => handleDownload(model.key)}
                  disabled={model.downloaded || downloadingModelRef.current?.valueOf() === model.key}
                  className="w-full"
                  variant={model.downloaded ? 'outline' : 'default'}
                >
                  {downloadingModelRef.current?.valueOf() === model.key ? (
                    <>
                      <Loader className="w-4 h-4 mr-2 animate-spin" />
                      Downloading...
                    </>
                  ) : model.downloaded ? (
                    'Already Downloaded'
                  ) : (
                    <>
                      <Download className="w-4 h-4 mr-2" />
                      Download Model
                    </>
                  )}
                </Button>
              </div>

              {/* Local Path */}
              {model.localPath && (
                <div className="text-xs text-muted-foreground p-2 bg-muted rounded">
                  <p className="font-mono truncate">{model.localPath}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}