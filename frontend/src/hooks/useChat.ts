import { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import chatService, { Message, ChatSession } from '@/services/chatService';
import useWebSocket from './useWebSocket';

export const useChat = (sessionId?: string) => {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  // WebSocket for real-time messages
  const { send, isConnected } = useWebSocket({
    onMessage: (data) => {
      if (data.type === 'chat_response') {
        setMessages(prev => [...prev, {
          id: data.messageId,
          text: data.response,
          isUser: false,
          timestamp: new Date().toISOString(),
        }]);
        setIsTyping(false);
      } else if (data.type === 'typing') {
        setIsTyping(data.isTyping);
      }
    },
  });

  // Get chat sessions
  const { data: sessions, isLoading: loadingSessions } = useQuery({
    queryKey: ['chatSessions'],
    queryFn: () => chatService.getSessions(),
  });

  // Get messages for current session
  const { data: sessionMessages, isLoading: loadingMessages } = useQuery({
    queryKey: ['chatMessages', sessionId],
    queryFn: () => sessionId ? chatService.getMessages(sessionId) : Promise.resolve([]),
    enabled: !!sessionId,
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) => {
      // Optimistically add user message
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        text: message,
        isUser: true,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, userMessage]);
      setIsTyping(true);

      // Send via WebSocket if connected, otherwise use API
      if (isConnected()) {
        send('chat_message', { message, sessionId });
        return Promise.resolve({ messageId: userMessage.id, response: '', sessionId: sessionId || '' });
      } else {
        return chatService.sendMessage({ message, sessionId });
      }
    },
    onSuccess: (data) => {
      if (!isConnected()) {
        // Add response if not using WebSocket
        setMessages(prev => [...prev, {
          id: data.messageId,
          text: data.response,
          isUser: false,
          timestamp: new Date().toISOString(),
        }]);
        setIsTyping(false);
      }
      queryClient.invalidateQueries({ queryKey: ['chatMessages', sessionId] });
    },
    onError: () => {
      setIsTyping(false);
    },
  });

  const sendMessage = useCallback((message: string) => {
    sendMessageMutation.mutate(message);
  }, [sendMessageMutation]);

  return {
    messages: sessionMessages || messages,
    sessions,
    isTyping,
    isLoading: loadingSessions || loadingMessages,
    sendMessage,
    isConnected: isConnected(),
  };
};

export default useChat;
