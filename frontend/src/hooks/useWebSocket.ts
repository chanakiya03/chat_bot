'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

export interface ChatMessage {
    id: string;
    role: 'user' | 'bot';
    text: string;
    intent?: string;
    sources?: string[];
    suggestions?: string[];
    timestamp: Date;
}

interface UseWebSocketReturn {
    messages: ChatMessage[];
    sendMessage: (text: string) => void;
    sendHidden: (text: string) => void;
    isConnected: boolean;
    isTyping: boolean;
    connectionError: string | null;
}

const WS_URL = 'ws://localhost:8000/ws/chat/';
const RECONNECT_DELAY = 3000;
const MAX_RECONNECTS = 5;

export function useWebSocket(): UseWebSocketReturn {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const [connectionError, setConnectionError] = useState<string | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectCount = useRef(0);
    const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
    const mountedRef = useRef(true);
    const hasGreeted = useRef(false);

    const addMessage = useCallback((msg: Omit<ChatMessage, 'id' | 'timestamp'>) => {
        setMessages(prev => [...prev, {
            ...msg,
            id: `${Date.now()}-${Math.random()}`,
            timestamp: new Date(),
        }]);
    }, []);

    const connect = useCallback(() => {
        if (!mountedRef.current) return;
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        try {
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                if (!mountedRef.current) return;
                setIsConnected(true);
                setConnectionError(null);
                reconnectCount.current = 0;
            };

            ws.onmessage = (event) => {
                if (!mountedRef.current) return;
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === 'typing') {
                        setIsTyping(true);
                        return;
                    }

                    if (data.type === 'connected') {
                        setIsTyping(false);
                        // Fire INIT_CHAT silently — backend returns dynamic welcome with college list.
                        // No user bubble is added.
                        if (!hasGreeted.current && wsRef.current?.readyState === WebSocket.OPEN) {
                            wsRef.current.send(JSON.stringify({ message: 'INIT_CHAT' }));
                            hasGreeted.current = true;
                        }
                        return;
                    }

                    if (data.type === 'message') {
                        setIsTyping(false);
                        addMessage({
                            role: 'bot',
                            text: data.text || '',
                            intent: data.intent,
                            sources: data.sources || [],
                            suggestions: data.suggestions || [],
                        });
                    }
                } catch {
                    setIsTyping(false);
                }
            };

            ws.onclose = () => {
                if (!mountedRef.current) return;
                setIsConnected(false);
                setIsTyping(false);

                if (reconnectCount.current < MAX_RECONNECTS) {
                    reconnectCount.current += 1;
                    setConnectionError(`Reconnecting… (attempt ${reconnectCount.current})`);
                    reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY);
                } else {
                    setConnectionError('Connection lost. Please refresh the page.');
                }
            };

            ws.onerror = () => {
                setConnectionError('Unable to connect to server.');
                ws.close();
            };
        } catch (err) {
            setConnectionError('WebSocket not supported or server unavailable.');
        }
    }, [addMessage]);

    const sendMessage = useCallback((text: string) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            setConnectionError('Not connected to server.');
            return;
        }
        addMessage({ role: 'user', text });
        wsRef.current.send(JSON.stringify({ message: text }));
    }, [addMessage]);

    // sendHidden: sends a command to the backend WITHOUT adding a user bubble.
    // Used for INIT_CHAT and other system commands.
    const sendHidden = useCallback((text: string) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        wsRef.current.send(JSON.stringify({ message: text }));
    }, []);

    useEffect(() => {
        mountedRef.current = true;
        connect();
        return () => {
            mountedRef.current = false;
            if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
            wsRef.current?.close();
        };
    }, [connect]);

    return { messages, sendMessage, sendHidden, isConnected, isTyping, connectionError };
}
