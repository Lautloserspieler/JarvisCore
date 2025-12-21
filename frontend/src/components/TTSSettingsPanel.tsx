import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Volume2, Mic2, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface TTSSettings {
  enabled: boolean;
  language: string;
  autoplay: boolean;
  volume: number;
  speed: number;
  use_voice_samples: boolean;
}

interface TTSStatus {
  available: boolean;
  engine: string;
  device: string;
  gpu_enabled: boolean;
  languages: string[];
}

interface Voice {
  language: string;
  name: string;
  description: string;
  path: string;
  available: boolean;
}

const TTSSettingsPanel: React.FC = () => {
  const { t } = useTranslation();
  const { toast } = useToast();

  const [ttsStatus, setTTSStatus] = useState<TTSStatus | null>(null);
  const [settings, setSettings] = useState<TTSSettings>({
    enabled: true,
    language: 'de',
    autoplay: false,
    volume: 1.0,
    speed: 1.0,
    use_voice_samples: true,
  });
  const [voices, setVoices] = useState<Voice[]>([]);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadTTSStatus();
    loadSettings();
    loadVoices();
  }, []);

  const loadTTSStatus = async () => {
    try {
      const response = await fetch('http://localhost:5050/api/tts/status');
      if (response.ok) {
        const data = await response.json();
        setTTSStatus(data);
      }
    } catch (error) {
      console.error('Failed to load TTS status:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const response = await fetch('http://localhost:5050/api/tts/settings');
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Failed to load TTS settings:', error);
    }
  };

  const loadVoices = async () => {
    try {
      const response = await fetch('http://localhost:5050/api/tts/voices');
      if (response.ok) {
        const data = await response.json();
        setVoices(data.voices || []);
      }
    } catch (error) {
      console.error('Failed to load voices:', error);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const response = await fetch('http://localhost:5050/api/tts/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        toast({
          title: 'Einstellungen gespeichert',
          description: 'TTS-Einstellungen wurden erfolgreich gespeichert',
        });
      } else {
        throw new Error('Speichern fehlgeschlagen');
      }
    } catch (error) {
      toast({
        title: 'Fehler',
        description: 'Einstellungen konnten nicht gespeichert werden',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const testVoice = async () => {
    setTesting(true);
    try {
      const response = await fetch('http://localhost:5050/api/tts/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: settings.language }),
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.volume = settings.volume;
        audio.playbackRate = settings.speed;
        audio.onended = () => URL.revokeObjectURL(audioUrl);
        await audio.play();

        toast({
          title: 'Test erfolgreich',
          description: 'Die Sprachausgabe funktioniert',
        });
      } else {
        throw new Error('Test fehlgeschlagen');
      }
    } catch (error) {
      toast({
        title: 'Fehler',
        description: 'Sprachausgabe-Test fehlgeschlagen',
        variant: 'destructive',
      });
    } finally {
      setTesting(false);
    }
  };

  const getLanguageName = (code: string) => {
    const names: { [key: string]: string } = {
      de: '🇩🇪 Deutsch',
      en: '🇬🇧 English',
    };
    return names[code] || code.toUpperCase();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Volume2 className="w-5 h-5" />
          Sprachausgabe (Text-to-Speech)
        </CardTitle>
        <CardDescription>
          Konfiguriere die Text-zu-Sprache Funktion von JARVIS
          {ttsStatus && (
            <div className="mt-2 flex items-center gap-2">
              {ttsStatus.available ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span className="text-sm">
                    TTS verfügbar ({ttsStatus.engine} auf {ttsStatus.device})
                    {ttsStatus.gpu_enabled && ' 💡 GPU'}
                  </span>
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4 text-red-500" />
                  <span className="text-sm">TTS nicht verfügbar</span>
                </>
              )}
            </div>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Enable TTS Toggle */}
        <div className="flex items-center justify-between p-4 bg-accent/50 rounded-lg">
          <div className="space-y-0.5">
            <Label className="text-base">Sprachausgabe aktivieren</Label>
            <p className="text-sm text-muted-foreground">
              Text-zu-Sprache Ausgabe für AI-Antworten
            </p>
          </div>
          <Switch
            checked={settings.enabled}
            onCheckedChange={(val) => setSettings({ ...settings, enabled: val })}
            disabled={!ttsStatus?.available}
          />
        </div>

        <Separator />

        {/* Language Selection */}
        <div className="space-y-2">
          <Label>Sprache</Label>
          <Select
            value={settings.language}
            onValueChange={(val) => setSettings({ ...settings, language: val })}
            disabled={!settings.enabled}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="de">🇩🇪 Deutsch</SelectItem>
              <SelectItem value="en">🇬🇧 English</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Welche Sprache soll JARVIS verwenden?
          </p>
        </div>

        {/* Auto-play Toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Automatische Wiedergabe</Label>
            <p className="text-sm text-muted-foreground">
              Antworten automatisch vorlesen
            </p>
          </div>
          <Switch
            checked={settings.autoplay}
            onCheckedChange={(val) => setSettings({ ...settings, autoplay: val })}
            disabled={!settings.enabled}
          />
        </div>

        <Separator />

        {/* Volume Control */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label>Lautstärke</Label>
            <span className="text-sm text-muted-foreground">
              {Math.round(settings.volume * 100)}%
            </span>
          </div>
          <Slider
            value={[settings.volume]}
            onValueChange={(val) => setSettings({ ...settings, volume: val[0] })}
            min={0}
            max={1}
            step={0.05}
            disabled={!settings.enabled}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Speed Control */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label>Sprechgeschwindigkeit</Label>
            <span className="text-sm text-muted-foreground">
              {settings.speed.toFixed(1)}x
            </span>
          </div>
          <Slider
            value={[settings.speed]}
            onValueChange={(val) => setSettings({ ...settings, speed: val[0] })}
            min={0.5}
            max={2}
            step={0.1}
            disabled={!settings.enabled}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0.5x (Langsam)</span>
            <span>2.0x (Schnell)</span>
          </div>
        </div>

        {/* Voice Samples */}
        {voices.length > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Mic2 className="w-4 h-4" />
                Stimmen-Samples
              </Label>
              <div className="grid gap-2">
                {voices.map((voice) => (
                  <div
                    key={voice.language}
                    className={`flex items-center justify-between p-3 border rounded-lg ${
                      voice.language === settings.language ? 'border-primary bg-accent/30' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {voice.available ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <div>
                        <div className="font-medium">{voice.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {voice.description}
                        </div>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {voice.available ? '✅ Ready' : '❌ Missing'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-4">
          <Button
            onClick={saveSettings}
            disabled={!settings.enabled || saving}
            className="flex-1"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Volume2 className="w-4 h-4 mr-2" />
            )}
            {saving ? 'Speichern...' : 'Einstellungen speichern'}
          </Button>
          <Button
            onClick={testVoice}
            disabled={!settings.enabled || testing}
            variant="outline"
          >
            {testing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Mic2 className="w-4 h-4 mr-2" />
            )}
            {testing ? 'Teste...' : 'Test Voice'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default TTSSettingsPanel;
