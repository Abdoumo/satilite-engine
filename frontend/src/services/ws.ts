import { useEffect, useState } from 'react';

export function useMonitoringSocket() {
    const [socket, setSocket] = useState<WebSocket | null>(null);
    const [lastEvent, setLastEvent] = useState<any>(null);

    useEffect(() => {
        const isProd = import.meta.env.PROD;
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = isProd 
            ? `${wsProtocol}//${window.location.hostname}:8899/ws/monitoring`
            : 'ws://localhost:8000/ws/monitoring';
            
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setLastEvent(data);
            } catch (err) {
                console.error("Failed to parse websocket message", err);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
        };

        setSocket(ws);

        return () => {
            ws.close();
        };
    }, []);

    return { socket, lastEvent };
}
