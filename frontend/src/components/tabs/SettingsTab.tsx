import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Save, Brain, Volume2, Mic } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Settings {
  llm: {
    enabled: boolean;
    contextLength: number;
    temperature: number;
  };
  tts: {
    enabled: boolean;
    speechRate: number;
    volume: number;
  };
  speech: {
    wakeWordEnabled: boolean;
    continuousListening: boolean;
  };
}

const SettingsTab = () => {
  const { toast } = useToast();
  const [settings, setSettings] = useState<Settings>({
    llm: {
      enabled: true,
      contextLength: 2048,
      temperature: 0.7,
    },
    tts: {
      enabled: true,
      speechRate: 150,
      volume: 100,
    },
    speech: {
      wakeWordEnabled: true,
      continuousListening: false,
    },
  });

  const handleSave = () => {
    toast({
      title: "Settings Saved",
      description: "Configuration saved to data/settings.json",
    });
  };

  return (
    <div className="p-4 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            LLM Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Enable LLM</Label>
              <p className="text-sm text-muted-foreground">Use language model for responses</p>
            </div>
            <Switch 
              checked={settings.llm.enabled}
              onCheckedChange={(checked) =>
                setSettings(prev => ({ ...prev, llm: { ...prev.llm, enabled: checked } }))
              }
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Context Length</Label>
              <span className="text-sm text-muted-foreground">{settings.llm.contextLength} tokens</span>
            </div>
            <Slider
              value={[settings.llm.contextLength]}
              onValueChange={(value) =>
                setSettings(prev => ({ ...prev, llm: { ...prev.llm, contextLength: value[0] } }))
              }
              min={512}
              max={8192}
              step={256}
              disabled={!settings.llm.enabled}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>512</span>
              <span>8192</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Temperature</Label>
              <span className="text-sm text-muted-foreground">{settings.llm.temperature.toFixed(1)}</span>
            </div>
            <Slider
              value={[settings.llm.temperature * 10]}
              onValueChange={(value) =>
                setSettings(prev => ({ ...prev, llm: { ...prev.llm, temperature: value[0] / 10 } }))
              }
              min={0}
              max={20}
              step={1}
              disabled={!settings.llm.enabled}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0.0 (Precise)</span>
              <span>2.0 (Creative)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Volume2 className="h-5 w-5" />
            TTS Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Enable TTS</Label>
              <p className="text-sm text-muted-foreground">Text-to-speech voice output</p>
            </div>
            <Switch 
              checked={settings.tts.enabled}
              onCheckedChange={(checked) =>
                setSettings(prev => ({ ...prev, tts: { ...prev.tts, enabled: checked } }))
              }
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Speech Rate</Label>
              <span className="text-sm text-muted-foreground">{settings.tts.speechRate} WPM</span>
            </div>
            <Slider
              value={[settings.tts.speechRate]}
              onValueChange={(value) =>
                setSettings(prev => ({ ...prev, tts: { ...prev.tts, speechRate: value[0] } }))
              }
              min={50}
              max={300}
              step={10}
              disabled={!settings.tts.enabled}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>50 WPM</span>
              <span>300 WPM</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Volume</Label>
              <span className="text-sm text-muted-foreground">{settings.tts.volume}%</span>
            </div>
            <Slider
              value={[settings.tts.volume]}
              onValueChange={(value) =>
                setSettings(prev => ({ ...prev, tts: { ...prev.tts, volume: value[0] } }))
              }
              min={0}
              max={100}
              step={5}
              disabled={!settings.tts.enabled}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5" />
            Speech Recognition
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Enable Wake Word</Label>
              <p className="text-sm text-muted-foreground">Activate with &quot;Hey JARVIS&quot;</p>
            </div>
            <Switch 
              checked={settings.speech.wakeWordEnabled}
              onCheckedChange={(checked) =>
                setSettings(prev => ({ ...prev, speech: { ...prev.speech, wakeWordEnabled: checked } }))
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label>Continuous Listening</Label>
              <p className="text-sm text-muted-foreground">No wake word required</p>
            </div>
            <Switch 
              checked={settings.speech.continuousListening}
              onCheckedChange={(checked) =>
                setSettings(prev => ({ ...prev, speech: { ...prev.speech, continuousListening: checked } }))
              }
            />
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave} className="w-full">
        <Save className="h-4 w-4 mr-2" />
        Save Settings
      </Button>
    </div>
  );
};

export default SettingsTab;
