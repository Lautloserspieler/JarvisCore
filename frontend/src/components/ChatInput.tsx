import { useState, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Mic, Send } from "lucide-react";
import VoiceVisualizer from "./VoiceVisualizer";

interface ChatInputProps {
  onSend: (message: string) => void;
  onToggleListening: () => void;
  isListening: boolean;
  disabled?: boolean;
}

const ChatInput = ({ onSend, onToggleListening, isListening, disabled = false }: ChatInputProps) => {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input);
      setInput("");
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border/40 bg-card/50 backdrop-blur-sm p-4">
      {isListening && (
        <div className="mb-4">
          <VoiceVisualizer isActive={isListening} />
        </div>
      )}
      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={disabled ? "JARVIS verarbeitet..." : "Nachricht eingeben... (Enter zum Senden, Shift+Enter für neue Zeile)"}
          className="min-h-[80px] resize-none"
          disabled={disabled}
        />
        <div className="flex flex-col gap-2">
          <Button
            onClick={onToggleListening}
            variant={isListening ? "default" : "outline"}
            size="icon"
            className={isListening ? "bg-red-500 hover:bg-red-600" : ""}
            disabled={disabled}
            title="Spracheingabe"
          >
            <Mic className="h-4 w-4" />
          </Button>
          <Button 
            onClick={handleSend} 
            size="icon"
            disabled={!input.trim() || disabled}
            title="Senden"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
