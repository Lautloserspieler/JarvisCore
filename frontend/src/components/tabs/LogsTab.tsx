import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RefreshCw, Trash2, Download } from "lucide-react";

interface LogEntry {
  timestamp: string;
  level: "INFO" | "DEBUG" | "WARN" | "ERROR";
  source: string;
  message: string;
}

const LogsTab = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sampleLogs: LogEntry[] = [
      { timestamp: "2025-12-10 20:15:32", level: "INFO", source: "core.jarvis", message: "System initialization complete" },
      { timestamp: "2025-12-10 20:15:33", level: "INFO", source: "llm.manager", message: "Loading model: llama-3-8b-instruct.gguf" },
      { timestamp: "2025-12-10 20:15:35", level: "DEBUG", source: "llm.manager", message: "Allocated 8192MB VRAM for model context" },
      { timestamp: "2025-12-10 20:15:36", level: "INFO", source: "llm.manager", message: "Model loaded successfully in 3.2s" },
      { timestamp: "2025-12-10 20:15:36", level: "INFO", source: "plugins.loader", message: "Loading enabled plugins..." },
      { timestamp: "2025-12-10 20:15:37", level: "INFO", source: "plugins.wikipedia", message: "Wikipedia plugin initialized" },
      { timestamp: "2025-12-10 20:15:37", level: "INFO", source: "plugins.wikidata", message: "Wikidata plugin initialized" },
      { timestamp: "2025-12-10 20:15:38", level: "INFO", source: "plugins.pubmed", message: "PubMed plugin initialized" },
      { timestamp: "2025-12-10 20:15:38", level: "WARN", source: "plugins.osm", message: "Rate limit configured: 1 req/s" },
      { timestamp: "2025-12-10 20:15:39", level: "INFO", source: "memory.manager", message: "Memory system initialized" },
      { timestamp: "2025-12-10 20:15:40", level: "INFO", source: "core.jarvis", message: "JARVIS ready - awaiting commands" },
    ];
    setLogs(sampleLogs);
  }, []);

  useEffect(() => {
    if (!autoScroll) return;
    const interval = setInterval(() => {
      const newLog: LogEntry = {
        timestamp: new Date().toISOString().replace("T", " ").split(".")[0],
        level: Math.random() > 0.9 ? "WARN" : Math.random() > 0.95 ? "ERROR" : "INFO",
        source: ["core.jarvis", "llm.manager", "plugins.loader", "memory.manager"][Math.floor(Math.random() * 4)],
        message: [
          "Processing user request...",
          "Memory cache updated",
          "Plugin response received",
          "Context window optimized",
          "Background task completed",
        ][Math.floor(Math.random() * 5)],
      };
      setLogs(prev => [...prev.slice(-100), newLog]);
    }, 3000);
    return () => clearInterval(interval);
  }, [autoScroll]);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const handleClear = () => {
    setLogs([]);
  };

  const getLevelColor = (level: LogEntry["level"]) => {
    switch (level) {
      case "INFO": return "text-primary";
      case "DEBUG": return "text-muted-foreground";
      case "WARN": return "text-yellow-400";
      case "ERROR": return "text-destructive";
    }
  };

  return (
    <div className="flex flex-col h-full p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleClear}>
            <Trash2 className="h-4 w-4" />
            Clear
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4" />
            Export
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox 
            id="auto-scroll" 
            checked={autoScroll}
            onCheckedChange={(checked) => setAutoScroll(checked as boolean)}
          />
          <label htmlFor="auto-scroll" className="text-sm cursor-pointer">
            Auto-Scroll (3s refresh)
          </label>
        </div>
      </div>

      <Card className="flex-1">
        <CardHeader>
          <CardTitle className="text-sm">Source: logs/jarvis.log • Last 100KB</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] font-mono text-xs" ref={scrollRef}>
            {logs.map((log, i) => (
              <div key={i} className="py-1 border-b border-border/50 last:border-0">
                <span className="text-muted-foreground mr-2">{log.timestamp}</span>
                <span className={`font-bold mr-2 ${getLevelColor(log.level)}`}>[{log.level}]</span>
                <span className="text-primary mr-2">{log.source}</span>
                <span>-</span>
                <span className="ml-2">{log.message}</span>
              </div>
            ))}
            {logs.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                No logs to display
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default LogsTab;
