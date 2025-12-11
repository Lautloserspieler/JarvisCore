import { useEffect, useCallback, useState } from 'react';
import { wsManager } from '@/lib/websocket';

interface UseWebSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (data: any) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { onConnect, onDisconnect, onError, onMessage } = options;
  const [isConnected, setIsConnected] = useState(wsManager.isConnected());

  useEffect(() => {
    // Register handlers
    const unsubscribers: Array<() => void> = [];

    if (onConnect) {
      unsubscribers.push(wsManager.onConnect(() => {
        setIsConnected(true);
        onConnect();
      }));
    }

    if (onDisconnect) {
      unsubscribers.push(wsManager.onDisconnect(() => {
        setIsConnected(false);
        onDisconnect();
      }));
    }

    if (onError) {
      unsubscribers.push(wsManager.onError(onError));
    }

    if (onMessage) {
      unsubscribers.push(wsManager.onMessage(onMessage));
    }

    // Update connection state
    setIsConnected(wsManager.isConnected());

    // Cleanup
    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [onConnect, onDisconnect, onError, onMessage]);

  const send = useCallback((data: any) => {
    return wsManager.send(data);
  }, []);

  const disconnect = useCallback(() => {
    wsManager.disconnect();
  }, []);

  const reconnect = useCallback(() => {
    wsManager.connect();
  }, []);

  return {
    send,
    disconnect,
    reconnect,
    isConnected: () => isConnected,
  };
};
