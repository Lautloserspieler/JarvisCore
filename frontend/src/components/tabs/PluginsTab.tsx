import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { RefreshCw, Puzzle, Globe, BookOpen, FlaskConical, Map, Library, Brain, MessageSquare } from "lucide-react";

interface Plugin {
  id: string;
  name: string;
  type: string;
  description: string;
  enabled: boolean;
  icon: React.ElementType;
}

const PluginsTab = () => {
  const [plugins, setPlugins] = useState<Plugin[]>([
    {
      id: "wikipedia",
      name: "Wikipedia Search",
      type: "Knowledge",
      description: "Search Wikipedia for general knowledge and encyclopedic information",
      enabled: true,
      icon: Globe,
    },
    {
      id: "wikidata",
      name: "Wikidata Query",
      type: "Knowledge",
      description: "Query Wikidata for structured, linked data and facts",
      enabled: true,
      icon: BookOpen,
    },
    {
      id: "pubmed",
      name: "PubMed Search",
      type: "Research",
      description: "Search biomedical literature and life science journals",
      enabled: true,
      icon: FlaskConical,
    },
    {
      id: "semantic",
      name: "Semantic Scholar",
      type: "Research",
      description: "AI-powered research tool for scientific literature",
      enabled: true,
      icon: Brain,
    },
    {
      id: "osm",
      name: "OpenStreetMap",
      type: "Location",
      description: "Query geographic and location-based information",
      enabled: true,
      icon: Map,
    },
    {
      id: "openlibrary",
      name: "OpenLibrary",
      type: "Knowledge",
      description: "Search for books and literary information",
      enabled: false,
      icon: Library,
    },
    {
      id: "memory",
      name: "Memory Manager",
      type: "System",
      description: "Manage short-term and long-term conversation memory",
      enabled: true,
      icon: Brain,
    },
    {
      id: "clarification",
      name: "Clarification",
      type: "System",
      description: "Ask clarifying questions when input is ambiguous",
      enabled: true,
      icon: MessageSquare,
    },
  ]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const togglePlugin = (id: string) => {
    setPlugins(plugins.map(p =>
      p.id === id ? { ...p, enabled: !p.enabled } : p
    ));
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "Knowledge": return "bg-blue-500/20 text-blue-400 border-blue-500/50";
      case "Research": return "bg-purple-500/20 text-purple-400 border-purple-500/50";
      case "Location": return "bg-green-500/20 text-green-400 border-green-500/50";
      case "System": return "bg-orange-500/20 text-orange-400 border-orange-500/50";
      default: return "bg-muted text-muted-foreground border-border";
    }
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh Status
        </Button>
        <Badge variant="outline">
          <Puzzle className="h-3 w-3 mr-1" />
          {plugins.filter(p => p.enabled).length} / {plugins.length} plugins enabled
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {plugins.map((plugin) => (
          <Card key={plugin.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <plugin.icon className="h-5 w-5" />
                  {plugin.name}
                </span>
                <div className="flex items-center gap-2">
                  <Badge className={getTypeColor(plugin.type)}>
                    {plugin.type}
                  </Badge>
                  <Badge variant={plugin.enabled ? "default" : "destructive"}>
                    {plugin.enabled ? "🟢 ENABLED" : "🔴 DISABLED"}
                  </Badge>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">{plugin.description}</p>
              <div className="flex items-center justify-between">
                <span className="text-sm">Enable Plugin</span>
                <Switch 
                  checked={plugin.enabled}
                  onCheckedChange={() => togglePlugin(plugin.id)}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default PluginsTab;
