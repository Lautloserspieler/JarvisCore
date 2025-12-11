import { useState, useRef, useEffect } from "react";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CoreState } from "@/components/JarvisCore";

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
}

interface ChatTabProps {
  onStateChange: (state: CoreState) => void;
}

const ChatTab = ({ onStateChange }: ChatTabProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "Guten Tag. Ich bin JARVIS, Ihr persönlicher AI-Assistent. Wie kann ich Ihnen heute behilflich sein?",
      isUser: false,
      timestamp: new Date().toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [isListening, setIsListening] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (isListening) {
      onStateChange("listening");
    } else if (isTyping) {
      onStateChange("processing");
    } else {
      onStateChange("idle");
    }
  }, [isListening, isTyping, onStateChange]);

  const processCommand = (text: string): string => {
    const lowerText = text.toLowerCase();
    
    if (lowerText.includes("load llama") || lowerText.includes("lade llama")) {
      return "Modell llama3 wird geladen... Dies kann einige Sekunden dauern.";
    }
    
    if (lowerText.includes("unload model") || lowerText.includes("modell entladen")) {
      return "Alle Modelle wurden aus dem RAM entladen. Speicher freigegeben.";
    }
    
    if (lowerText.includes("list plugins") || lowerText.includes("plugins anzeigen")) {
      return "Aktive Plugins:\n• Wikipedia Search (enabled)\n• Wikidata Query (enabled)\n• PubMed Search (enabled)\n• Semantic Scholar (enabled)\n• OpenStreetMap (enabled)\n• Memory Manager (enabled)";
    }
    
    if (lowerText.includes("search") || lowerText.includes("suche")) {
      const query = text.replace(/search|suche/gi, "").trim();
      return `Wissenssuche gestartet für: "${query}"\nDurchsuche lokale Datenbank und Online-Quellen...`;
    }
    
    if (lowerText.includes("system status") || lowerText.includes("systemstatus")) {
      return "Systemstatus:\n• CPU: 45% Auslastung\n• RAM: 62% verwendet (40GB/64GB)\n• GPU: 38% Auslastung\n• Alle Systeme operational";
    }
    
    if (lowerText.includes("hilfe") || lowerText.includes("help")) {
      return "Verfügbare Befehle:\n• 'load llama3' - LLM laden\n• 'unload model' - Modell entladen\n• 'list plugins' - Plugin-Übersicht\n• 'search <query>' - Wissenssuche\n• 'system status' - Systemstatus";
    }
    
    const responses = [
      "Ich verstehe Ihre Anfrage. Lassen Sie mich das für Sie analysieren...",
      "Sehr interessant. Ich werde sofort die entsprechenden Daten abrufen.",
      "Natürlich, ich kümmere mich darum. Einen Moment bitte.",
      "Ich habe Ihre Anfrage verarbeitet. Kann ich sonst noch etwas für Sie tun?",
      "Selbstverständlich. Die Informationen werden jetzt zusammengestellt.",
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const handleSendMessage = (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      isUser: true,
      timestamp: new Date().toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    onStateChange("processing");

    setTimeout(() => {
      const responseText = processCommand(text);
      onStateChange("speaking");
      
      setTimeout(() => {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: responseText,
          isUser: false,
          timestamp: new Date().toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" }),
        };
        setIsTyping(false);
        setMessages(prev => [...prev, aiMessage]);
        setTimeout(() => onStateChange("idle"), 1000);
      }, 500);
    }, 1500);
  };

  const handleToggleListening = () => {
    setIsListening(!isListening);
  };

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isTyping && (
          <ChatMessage message={{ id: "typing", text: "...", isUser: false, timestamp: "" }} />
        )}
      </ScrollArea>
      <ChatInput 
        onSend={handleSendMessage} 
        onToggleListening={handleToggleListening}
        isListening={isListening}
      />
    </div>
  );
};

export default ChatTab;
