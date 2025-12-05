package gateway

import (
	"log"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

// Event ist das Broadcast-Format.
type Event struct {
	Type      string         `json:"type"`
	Payload   map[string]any `json:"payload,omitempty"`
	Timestamp time.Time      `json:"timestamp"`
	Meta      map[string]any `json:"meta,omitempty"`
}

// Hub verwaltet verbundene Clients und Broadcasts.
type Hub struct {
	clients    map[*Client]struct{}
	register   chan *Client
	unregister chan *Client
	broadcast  chan Event
	logger     *log.Logger
	mu         sync.RWMutex
}

// NewHub erzeugt einen Hub.
func NewHub(logger *log.Logger) *Hub {
	if logger == nil {
		logger = log.Default()
	}
	return &Hub{
		clients:    make(map[*Client]struct{}),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan Event, 128),
		logger:     logger,
	}
}

// Run startet die zentrale Hub-Schleife.
func (h *Hub) Run(stop <-chan struct{}) {
	for {
		select {
		case c := <-h.register:
			h.mu.Lock()
			h.clients[c] = struct{}{}
			h.mu.Unlock()
		case c := <-h.unregister:
			h.remove(c)
		case evt := <-h.broadcast:
			h.dispatch(evt)
		case <-stop:
			h.closeAll()
			return
		}
	}
}

// Broadcast legt ein Event in die Queue.
func (h *Hub) Broadcast(evt Event) {
	select {
	case h.broadcast <- evt:
	default:
		h.logger.Printf("broadcast queue voll, verwerfe Event %s", evt.Type)
	}
}

// Register fügt einen Client hinzu.
func (h *Hub) Register(c *Client) {
	h.register <- c
}

// Unregister entfernt einen Client.
func (h *Hub) Unregister(c *Client) {
	h.unregister <- c
}

func (h *Hub) dispatch(evt Event) {
	h.mu.RLock()
	defer h.mu.RUnlock()
	for client := range h.clients {
		select {
		case client.send <- evt:
		default:
			h.remove(client)
		}
	}
}

func (h *Hub) remove(c *Client) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if _, ok := h.clients[c]; ok {
		delete(h.clients, c)
		close(c.send)
	}
}

func (h *Hub) closeAll() {
	h.mu.Lock()
	defer h.mu.Unlock()
	for c := range h.clients {
		_ = c.conn.Close()
		close(c.send)
		delete(h.clients, c)
	}
}

// Client repräsentiert eine WebSocket-Verbindung.
type Client struct {
	hub  *Hub
	conn *websocket.Conn
	send chan Event
}

// NewClient baut einen Client um eine WebSocket-Conn.
func NewClient(h *Hub, conn *websocket.Conn) *Client {
	return &Client{
		hub:  h,
		conn: conn,
		send: make(chan Event, 32),
	}
}

// Reader verarbeitet eingehende Nachrichten (derzeit nur Ping/Pong keep-alive).
func (c *Client) Reader() {
	defer func() {
		c.hub.Unregister(c)
		_ = c.conn.Close()
	}()
	c.conn.SetReadLimit(1024)
	c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})
	for {
		if _, _, err := c.conn.ReadMessage(); err != nil {
			break
		}
	}
}

// Writer sendet Broadcasts an den Client.
func (c *Client) Writer() {
	ticker := time.NewTicker(30 * time.Second)
	defer func() {
		ticker.Stop()
		_ = c.conn.Close()
	}()
	for {
		select {
		case evt, ok := <-c.send:
			_ = c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				_ = c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}
			if err := c.conn.WriteJSON(evt); err != nil {
				return
			}
		case <-ticker.C:
			_ = c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}
