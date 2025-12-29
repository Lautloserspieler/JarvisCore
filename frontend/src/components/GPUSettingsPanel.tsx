import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, CheckCircle, Zap, Loader } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Label } from '@/components/ui/label';

interface GPUInfo {
  current_device: string;
  available_gpus: string[];
  cuda_available: boolean;
  rocm_available: boolean;
  metal_available: boolean;
}

const GPUSettingsPanel: React.FC = () => {
  const { t } = useTranslation();
  const { toast } = useToast();
  
  const [gpuInfo, setGpuInfo] = useState<GPUInfo | null>(null);
  const [selectedGPU, setSelectedGPU] = useState<string>('cpu');
  const [loading, setLoading] = useState(false);
  const [installing, setInstalling] = useState(false);
  const [installProgress, setInstallProgress] = useState<string>('');

  // Load GPU info on mount
  useEffect(() => {
    loadGPUInfo();
  }, []);

  const loadGPUInfo = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5050/api/settings/gpu');
      if (response.ok) {
        const data = await response.json();
        setGpuInfo(data);
        setSelectedGPU(data.current_device || 'cpu');
      }
    } catch (error) {
      console.error('Failed to load GPU info:', error);
      toast({
        title: t('common.error'),
        description: 'GPU-Info konnte nicht geladen werden',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const installGPUSupport = async () => {
    if (selectedGPU === 'cpu') {
      toast({
        title: 'Hinweis',
        description: 'CPU ist bereits aktiv. Bitte einen GPU-Typ auswählen.'
      });
      return;
    }

    try {
      setInstalling(true);
      setInstallProgress('Installation wird gestartet...');
      
      const response = await fetch('http://localhost:5050/api/settings/gpu/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gpu_type: selectedGPU })
      });

      if (response.ok) {
        const data = await response.json();
        setInstallProgress(data.message || 'Installation erfolgreich!');
        
        // Reload GPU info
        await new Promise(resolve => setTimeout(resolve, 2000));
        await loadGPUInfo();
        
        toast({
          title: 'Erfolg!',
          description: `${selectedGPU.toUpperCase()}-Support erfolgreich installiert`
        });
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Installation fehlgeschlagen');
      }
    } catch (error) {
      console.error('GPU installation error:', error);
      toast({
        title: t('common.error'),
        description: error instanceof Error ? error.message : 'GPU-Installation fehlgeschlagen',
        variant: 'destructive'
      });
    } finally {
      setInstalling(false);
      setInstallProgress('');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Loader className="w-6 h-6 animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5" />
          GPU-Beschleunigung
        </CardTitle>
        <CardDescription>
          Wähle deine GPU-Art für optimale Performance
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Device Status */}
        <div className="p-4 bg-accent/50 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            {gpuInfo?.current_device === 'cpu' ? (
              <AlertCircle className="w-5 h-5 text-yellow-500" />
            ) : (
              <CheckCircle className="w-5 h-5 text-green-500" />
            )}
            <span className="font-semibold">Aktives System:</span>
          </div>
          <p className="text-lg font-bold uppercase tracking-wide">
            {gpuInfo?.current_device || 'cpu'}
          </p>
          {gpuInfo?.current_device !== 'cpu' && (
            <p className="text-sm text-green-600 mt-2">✓ GPU-Beschleunigung aktiv</p>
          )}
        </div>

        <Separator />

        {/* GPU Selection */}
        <div className="space-y-4">
          <div>
            <Label className="text-base">GPU-Typ wählen</Label>
            <p className="text-sm text-muted-foreground mb-3">
              Wähle deinen GPU-Typ aus und klicke dann auf "Installieren"
            </p>
          </div>

          <Select value={selectedGPU} onValueChange={setSelectedGPU} disabled={installing}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="cpu">🔵 CPU (Standard - immer verfügbar)</SelectItem>
              <SelectItem value="cuda">
                🟢 NVIDIA CUDA (RTX/GTX)
                {gpuInfo?.cuda_available && ' ✓'}
              </SelectItem>
              <SelectItem value="rocm">
                🔴 AMD ROCm (RDNA/CDNA)
                {gpuInfo?.rocm_available && ' ✓'}
              </SelectItem>
              <SelectItem value="metal">
                🍎 Apple Metal (macOS)
                {gpuInfo?.metal_available && ' ✓'}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Availability Info */}
        {gpuInfo && (
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className={`p-3 rounded-lg ${
              gpuInfo.cuda_available ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
            }`}>
              <p className="font-semibold">NVIDIA CUDA</p>
              <p className={gpuInfo.cuda_available ? 'text-green-700' : 'text-gray-500'}>
                {gpuInfo.cuda_available ? '✓ Verfügbar' : '✗ Nicht verfügbar'}
              </p>
            </div>
            <div className={`p-3 rounded-lg ${
              gpuInfo.rocm_available ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
            }`}>
              <p className="font-semibold">AMD ROCm</p>
              <p className={gpuInfo.rocm_available ? 'text-green-700' : 'text-gray-500'}>
                {gpuInfo.rocm_available ? '✓ Verfügbar' : '✗ Nicht verfügbar'}
              </p>
            </div>
            <div className={`p-3 rounded-lg ${
              gpuInfo.metal_available ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
            }`}>
              <p className="font-semibold">Apple Metal</p>
              <p className={gpuInfo.metal_available ? 'text-green-700' : 'text-gray-500'}>
                {gpuInfo.metal_available ? '✓ Verfügbar' : '✗ Nicht verfügbar'}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
              <p className="font-semibold">CPU</p>
              <p className="text-blue-700">✓ Immer verfügbar</p>
            </div>
          </div>
        )}

        <Separator />

        {/* Installation Progress */}
        {installing && installProgress && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Loader className="w-4 h-4 animate-spin" />
              <span className="font-semibold text-blue-900">Installation läuft...</span>
            </div>
            <p className="text-sm text-blue-800">{installProgress}</p>
            <p className="text-xs text-blue-700 mt-2">
              Dies kann einige Minuten dauern. Fenster bitte nicht schließen.
            </p>
          </div>
        )}

        {/* Install Button */}
        <Button
          onClick={installGPUSupport}
          disabled={installing || selectedGPU === gpuInfo?.current_device}
          className="w-full"
          size="lg"
        >
          {installing ? (
            <>
              <Loader className="w-4 h-4 mr-2 animate-spin" />
              Installation läuft...
            </>
          ) : selectedGPU === gpuInfo?.current_device ? (
            <>
              <CheckCircle className="w-4 h-4 mr-2" />
              {selectedGPU.toUpperCase()} ist bereits aktiv
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 mr-2" />
              {selectedGPU.toUpperCase()}-Support installieren
            </>
          )}
        </Button>

        {/* Help Text */}
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900">
          <p className="font-semibold mb-1">💡 Hinweis:</p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>CUDA benötigt NVIDIA GPU + CUDA Toolkit</li>
            <li>ROCm benötigt AMD GPU + ROCm Runtime (Linux)</li>
            <li>Metal funktioniert nur auf macOS</li>
            <li>CPU ist der Fallback und funktioniert überall</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default GPUSettingsPanel;