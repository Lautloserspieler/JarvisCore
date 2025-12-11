import { WS_URL } from './api';

type MessageHandler = (data: any) => void;
type ErrorHandler = (error: Event) => void;
type ConnectionHandler = () => void;

class WebSocketManager {
  private ws: WebSocket | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private errorHandlers: Set<ErrorHandler> = new Set();
  private connectHandlers: Set<ConnectionHandler> = new Set();
  private disconnectHandlers: Set<ConnectionHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isConnecting = false;

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket(WS_URL + '/ws');

      this.ws.onopen = () => {
        console.log('✓ WebSocket verbunden');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.connectHandlers.forEach(handler => handler());
      };

      this.ws.onerror = (error) => {
        this.isConnecting = false;
        this.errorHandlers.forEach(handler => handler(error));
      };

      this.ws.onclose = () => {
        this.isConnecting = false;
        this.disconnectHandlers.forEach(handler => handler());
        this.scheduleReconnect();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.messageHandlers.forEach(handler => handler(data));
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };
    } catch (error) {
      this.isConnecting = false;
      console.error('WebSocket connection error:', error);
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('✗ Max WebSocket reconnect attempts reached');
      return;
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
    
    this.reconnectTimeout = setTimeout(() => {
      console.log(`↻ Reconnecting WebSocket (attempt ${this.reconnectAttempts})...`);
      this.connect();
    }, delay);
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  onMessage(handler: MessageHandler) {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onError(handler: ErrorHandler) {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  onConnect(handler: ConnectionHandler) {
    this.connectHandlers.add(handler);
    return () => this.connectHandlers.delete(handler);
  }

  onDisconnect(handler: ConnectionHandler) {
    this.disconnectHandlers.add(handler);
    return () => this.disconnectHandlers.delete(handler);
  }
}

// Singleton instance
export const wsManager = new WebSocketManager();

// Auto-connect on load
if (typeof window !== 'undefined') {
  wsManager.connect();
}
