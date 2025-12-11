import { useEffect, useCallback, useRef } from 'react';
import wsService from '@/services/websocket';

interface UseWebSocketOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoConnect?: boolean;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    autoConnect = true,
  } = options;

  const messageHandlerRef = useRef(onMessage);
  const errorHandlerRef = useRef(onError);
  const connectHandlerRef = useRef(onConnect);
  const disconnectHandlerRef = useRef(onDisconnect);

  useEffect(() => {
    messageHandlerRef.current = onMessage;
    errorHandlerRef.current = onError;
    connectHandlerRef.current = onConnect;
    disconnectHandlerRef.current = onDisconnect;
  }, [onMessage, onError, onConnect, onDisconnect]);

  useEffect(() => {
    if (autoConnect && !wsService.isConnected()) {
      wsService.connect().catch(console.error);
    }

    const handleMessage = (data: any) => {
      messageHandlerRef.current?.(data);
    };

    const handleError = (error: Event) => {
      errorHandlerRef.current?.(error);
    };

    const handleConnect = () => {
      connectHandlerRef.current?.();
    };

    const handleDisconnect = () => {
      disconnectHandlerRef.current?.();
    };

    wsService.on('message', handleMessage);
    wsService.onError(handleError);
    wsService.onConnect(handleConnect);
    wsService.onDisconnect(handleDisconnect);

    return () => {
      wsService.off('message', handleMessage);
    };
  }, [autoConnect]);

  const send = useCallback((type: string, data: any) => {
    wsService.send(type, data);
  }, []);

  const connect = useCallback(() => {
    return wsService.connect();
  }, []);

  const disconnect = useCallback(() => {
    wsService.disconnect();
  }, []);

  const isConnected = useCallback(() => {
    return wsService.isConnected();
  }, []);

  return {
    send,
    connect,
    disconnect,
    isConnected,
  };
};

export default useWebSocket;
