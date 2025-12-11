import { useMemo } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage = ({ message }: ChatMessageProps) => {
  // Format timestamp
  const formattedTime = useMemo(() => {
    if (!message.timestamp) return '';
    
    try {
      const date = new Date(message.timestamp);
      return date.toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return message.timestamp;
    }
  }, [message.timestamp]);

  return (
    <div
      className={cn(
        "flex gap-3 mb-4 animate-in slide-in-from-bottom-2",
        message.isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <Avatar className={cn(
        "h-8 w-8",
        message.isUser ? "bg-primary" : "bg-primary/20"
      )}>
        <AvatarFallback>
          {message.isUser ? (
            <User className="h-4 w-4" />
          ) : (
            <Bot className="h-4 w-4" />
          )}
        </AvatarFallback>
      </Avatar>
      <div
        className={cn(
          "flex flex-col max-w-[80%]",
          message.isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-lg px-4 py-2 break-words whitespace-pre-wrap",
            message.isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted"
          )}
        >
          {message.text}
        </div>
        {formattedTime && (
          <span className="text-xs text-muted-foreground mt-1">
            {formattedTime}
          </span>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
