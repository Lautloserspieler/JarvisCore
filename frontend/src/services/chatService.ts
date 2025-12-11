import { apiService } from './api';

export interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

export interface SendMessageRequest {
  message: string;
  sessionId?: string;
}

export interface SendMessageResponse {
  messageId: string;
  response: string;
  sessionId: string;
}

class ChatService {
  async getSessions(): Promise<ChatSession[]> {
    return apiService.get<ChatSession[]>('/chat/sessions');
  }

  async getSession(sessionId: string): Promise<ChatSession> {
    return apiService.get<ChatSession>(`/chat/sessions/${sessionId}`);
  }

  async createSession(title?: string): Promise<ChatSession> {
    return apiService.post<ChatSession>('/chat/sessions', { title });
  }

  async deleteSession(sessionId: string): Promise<void> {
    return apiService.delete(`/chat/sessions/${sessionId}`);
  }

  async sendMessage(data: SendMessageRequest): Promise<SendMessageResponse> {
    return apiService.post<SendMessageResponse>('/chat/messages', data);
  }

  async getMessages(sessionId: string): Promise<Message[]> {
    return apiService.get<Message[]>(`/chat/sessions/${sessionId}/messages`);
  }

  async clearHistory(sessionId: string): Promise<void> {
    return apiService.delete(`/chat/sessions/${sessionId}/messages`);
  }
}

export const chatService = new ChatService();
export default chatService;
