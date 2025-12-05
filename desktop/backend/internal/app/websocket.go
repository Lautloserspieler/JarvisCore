package app

import (
	"fmt"
	"time"
	
	"jarviscore/desktop/internal/websocket"
)

// StartWebSocketHub startet WebSocket-Hub und Broadcaster
func (a *App) StartWebSocketHub() {
	a.wsHub = websocket.NewHub()
	go a.wsHub.Run()
	
	// System Metrics Broadcaster
	go a.broadcastSystemMetrics()
}

// broadcastSystemMetrics sendet System-Metriken alle 2 Sekunden
func (a *App) broadcastSystemMetrics() {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			if a.wsHub.GetClientCount() == 0 {
				continue // Keine Clients, skip
			}
			
			metrics, err := a.GetSystemStatus()
			if err != nil {
				continue
			}
			
			a.wsHub.BroadcastJSON("system_metrics", metrics)
			
		case <-a.ctx.Done():
			return
		}
	}
}

// SubscribeToWebSocket registriert Client für WebSocket-Updates
func (a *App) SubscribeToWebSocket(clientID string) error {
	if a.wsHub == nil {
		return fmt.Errorf("WebSocket Hub nicht initialisiert")
	}
	
	client := &websocket.Client{
		ID:       clientID,
		Messages: make(chan websocket.Message, 256),
	}
	
	a.wsHub.Register(client)
	
	// Client-Handler in Goroutine
	go func() {
		for msg := range client.Messages {
			// Messages werden vom Frontend via Wails Runtime empfangen
			// TODO: Wails Runtime Events nutzen
			_ = msg
		}
	}()
	
	return nil
}

// UnsubscribeFromWebSocket entfernt Client
func (a *App) UnsubscribeFromWebSocket(clientID string) {
	if a.wsHub == nil {
		return
	}
	
	// TODO: Client aus Hub entfernen
}

// BroadcastMessage sendet Nachricht an alle Clients
func (a *App) BroadcastMessage(msgType string, data map[string]interface{}) {
	if a.wsHub == nil {
		return
	}
	
	a.wsHub.Broadcast(websocket.Message{
		Type: msgType,
		Data: data,
	})
}
