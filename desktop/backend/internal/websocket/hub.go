package websocket

import (
	"encoding/json"
	"log"
	"sync"
)

// Message repräsentiert eine WebSocket-Nachricht
type Message struct {
	Type string                 `json:"type"`
	Data map[string]interface{} `json:"data"`
}

// Client repräsentiert einen verbundenen Client
type Client struct {
	ID       string
	Messages chan Message
}

// Hub verwaltet alle WebSocket-Clients
type Hub struct {
	clients    map[string]*Client
	mu         sync.RWMutex
	register   chan *Client
	unregister chan *Client
	broadcast  chan Message
}

// NewHub erstellt neue Hub-Instanz
func NewHub() *Hub {
	return &Hub{
		clients:    make(map[string]*Client),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan Message, 256),
	}
}

// Run startet den Hub
func (h *Hub) Run() {
	log.Println("🔌 WebSocket Hub gestartet")
	
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client.ID] = client
			h.mu.Unlock()
			log.Printf("✅ Client verbunden: %s (Total: %d)", client.ID, len(h.clients))
			
		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client.ID]; ok {
				delete(h.clients, client.ID)
				close(client.Messages)
			}
			h.mu.Unlock()
			log.Printf("❌ Client getrennt: %s (Verbleibend: %d)", client.ID, len(h.clients))
			
		case message := <-h.broadcast:
			h.mu.RLock()
			for _, client := range h.clients {
				select {
				case client.Messages <- message:
					// Message gesendet
				default:
					// Client Buffer voll, skip
				}
			}
			h.mu.RUnlock()
		}
	}
}

// Register registriert neuen Client
func (h *Hub) Register(client *Client) {
	h.register <- client
}

// Unregister entfernt Client
func (h *Hub) Unregister(client *Client) {
	h.unregister <- client
}

// Broadcast sendet Nachricht an alle Clients
func (h *Hub) Broadcast(message Message) {
	select {
	case h.broadcast <- message:
		// Message gequeued
	default:
		log.Println("⚠️  Broadcast Buffer voll, Message verworfen")
	}
}

// BroadcastJSON sendet JSON-Nachricht
func (h *Hub) BroadcastJSON(msgType string, data interface{}) error {
	dataMap, ok := data.(map[string]interface{})
	if !ok {
		// Versuche zu konvertieren
		jsonBytes, err := json.Marshal(data)
		if err != nil {
			return err
		}
		
		if err := json.Unmarshal(jsonBytes, &dataMap); err != nil {
			return err
		}
	}
	
	h.Broadcast(Message{
		Type: msgType,
		Data: dataMap,
	})
	
	return nil
}

// GetClientCount gibt Anzahl verbundener Clients zurück
func (h *Hub) GetClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}
