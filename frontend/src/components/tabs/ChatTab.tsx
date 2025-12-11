import { useState, useRef, useEffect } from "react";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CoreState } from "@/components/JarvisCore";
import { useChat } from "@/hooks/useChat";
import { WifiOff } from "lucide-react";

interface ChatTabProps {
  onStateChange: (state: CoreState) => void;
}

const ChatTab = ({ onStateChange }: ChatTabProps) => {
  const { messages, sendMessage, isTyping, isConnected, isLoading } = useChat();
  const [isListening, setIsListening] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Update Core state based on activity
  useEffect(() => {
    if (isListening) {
      onStateChange("listening");
    } else if (isTyping) {
      onStateChange("processing");
    } else if (messages.length > 0 && messages[messages.length - 1]?.isUser === false) {
      onStateChange("speaking");
      // Return to idle after "speaking"
      const timer = setTimeout(() => onStateChange("idle"), 2000);
      return () => clearTimeout(timer);
    } else {
      onStateChange("idle");
    }
  }, [isListening, isTyping, messages, onStateChange]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;
    
    try {
      await sendMessage(text);
    } catch (error) {
      console.error("Failed to send message:", error);
      // Could show error toast here
    }
  };

  const handleToggleListening = () => {
    setIsListening(!isListening);
  };

  return (
    <div className="flex flex-col h-[600px]">
      {/* Connection Status Warning */}
      {!isConnected && (
        <Alert variant="destructive" className="mb-4">
          <WifiOff className="h-4 w-4" />
          <AlertDescription>
            WebSocket disconnected. Messages will be sent via REST API. Reconnecting...
          </AlertDescription>
        </Alert>
      )}

      {/* Chat Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-muted-foreground">Loading messages...</div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-muted-foreground">
              <p className="text-lg mb-2">Welcome to JARVIS</p>
              <p className="text-sm">Start a conversation to begin</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))
        )}
        
        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex items-center gap-2 p-4">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm text-muted-foreground">JARVIS is thinking...</span>
          </div>
        )}
      </ScrollArea>

      {/* Chat Input */}
      <ChatInput 
        onSend={handleSendMessage} 
        onToggleListening={handleToggleListening}
        isListening={isListening}
        disabled={isTyping}
      />
    </div>
  );
};

export default ChatTab;
