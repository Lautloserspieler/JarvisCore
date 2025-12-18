import { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Globe } from "lucide-react";
import JarvisCore, { CoreState } from "@/components/JarvisCore";
import ChatTab from "@/components/tabs/ChatTab";
import DashboardTab from "@/components/tabs/DashboardTab";
import LogsTab from "@/components/tabs/LogsTab";
import MemoryTab from "@/components/tabs/MemoryTab";
import ModelsTab from "@/components/tabs/ModelsTab";
import PluginsTab from "@/components/tabs/PluginsTab";
import SettingsTab from "@/components/tabs/SettingsTab";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useLanguage } from "@/hooks/useLanguage";

const Index = () => {
  const { t } = useTranslation();
  const { currentLanguage, switchLanguage } = useLanguage();
  const [coreState, setCoreState] = useState<CoreState>("idle");
  const [activeTab, setActiveTab] = useState("chat");
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');

  // WebSocket connection management
  const { isConnected } = useWebSocket({
    onConnect: () => {
      console.log('WebSocket verbunden');
      setConnectionStatus('connected');
    },
    onDisconnect: () => {
      console.log('WebSocket getrennt');
      setConnectionStatus('disconnected');
    },
    onError: (error) => {
      console.error('WebSocket Fehler:', error);
      setConnectionStatus('error');
    },
  });

  useEffect(() => {
    if (isConnected()) {
      setConnectionStatus('connected');
    }
  }, [isConnected]);

  const stateLabels: Record<CoreState, string> = {
    idle: t('common.ready') || "BEREIT",
    listening: t('common.listening') || "HÖRE ZU",
    processing: t('common.processing') || "VERARBEITE",
    speaking: t('common.speaking') || "ANTWORTE"
  };

  const connectionLabels = {
    connected: t('api.connected') || 'ONLINE',
    error: t('errors.connectionFailed') || 'FEHLER',
    disconnected: t('api.disconnected') || 'VERBINDE'
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header mit JARVIS Core */}
      <header className="border-b border-border/40 bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <JarvisCore state={coreState} isActive={true} size="sm" />
            <div>
              <h1 className="text-2xl font-display font-bold glow-text">JARVIS</h1>
              <p className="text-sm text-muted-foreground">
                {currentLanguage === 'de' ? 'KI-Assistent Kernsystem' : 'AI Assistant Core System'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Language Switcher */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => switchLanguage(currentLanguage === 'de' ? 'en' : 'de')}
              className="gap-2"
            >
              <Globe className="h-4 w-4" />
              {currentLanguage === 'de' ? '🇬🇧 EN' : '🇩🇪 DE'}
            </Button>
            
            {/* Verbindungsstatus */}
            <div className="flex items-center gap-2">
              <div className={`h-2 w-2 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-500 animate-pulse' :
                connectionStatus === 'error' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'
              }`} />
              <span className="text-xs font-mono text-muted-foreground">
                {connectionLabels[connectionStatus]}
              </span>
            </div>
            
            {/* Status Badge */}
            <Badge variant="outline" className="font-mono">
              {stateLabels[coreState]}
            </Badge>
          </div>
        </div>
      </header>

      {/* Hauptinhalt */}
      <main className="flex-1 container mx-auto px-4 py-6">
        <Card className="holo-panel">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-7 lg:w-auto">
              <TabsTrigger value="chat">{t('navigation.chat')}</TabsTrigger>
              <TabsTrigger value="dashboard">{t('navigation.dashboard')}</TabsTrigger>
              <TabsTrigger value="memory">{t('navigation.memory')}</TabsTrigger>
              <TabsTrigger value="models">{t('navigation.models')}</TabsTrigger>
              <TabsTrigger value="plugins">{t('tabs.plugins')}</TabsTrigger>
              <TabsTrigger value="logs">
                {currentLanguage === 'de' ? 'Protokolle' : 'Logs'}
              </TabsTrigger>
              <TabsTrigger value="settings">{t('navigation.settings')}</TabsTrigger>
            </TabsList>

            <TabsContent value="chat" className="mt-4">
              <ChatTab onStateChange={setCoreState} />
            </TabsContent>

            <TabsContent value="dashboard" className="mt-4">
              <DashboardTab />
            </TabsContent>

            <TabsContent value="memory" className="mt-4">
              <MemoryTab />
            </TabsContent>

            <TabsContent value="models" className="mt-4">
              <ModelsTab />
            </TabsContent>

            <TabsContent value="plugins" className="mt-4">
              <PluginsTab />
            </TabsContent>

            <TabsContent value="logs" className="mt-4">
              <LogsTab />
            </TabsContent>

            <TabsContent value="settings" className="mt-4">
              <SettingsTab />
            </TabsContent>
          </Tabs>
        </Card>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 py-4">
        <div className="container mx-auto px-4 text-center text-xs text-muted-foreground">
          <p>
            {currentLanguage === 'de' 
              ? 'JARVIS Kernsystem v1.1.0 | Angetrieben durch fortschrittliche KI-Technologie'
              : 'JARVIS Core System v1.1.0 | Powered by Advanced AI Technology'
            }
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
