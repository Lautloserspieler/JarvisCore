package gateway

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/gorilla/websocket"
)

// Config enthält Laufzeit-Einstellungen für gatewayd.
type Config struct {
	ListenAddr string
	Token      string
}

// LoadConfig lädt Env-Variablen.
func LoadConfig() Config {
	addr := os.Getenv("GATEWAYD_LISTEN")
	if addr == "" {
		addr = ":7081"
	}
	token := os.Getenv("JARVIS_GATEWAYD_TOKEN")
	if token == "" {
		token = os.Getenv("GATEWAYD_TOKEN")
	}
	return Config{
		ListenAddr: addr,
		Token:      strings.TrimSpace(token),
	}
}

// Server kapselt Hub und HTTP-Routing.
type Server struct {
	hub      *Hub
	upgrader websocket.Upgrader
	cfg      Config
	logger   *log.Logger
}

// NewServer erzeugt einen neuen Server.
func NewServer(cfg Config, logger *log.Logger) *Server {
	if logger == nil {
		logger = log.New(os.Stdout, "[gatewayd] ", log.LstdFlags|log.LUTC)
	}
	return &Server{
		hub: NewHub(logger),
		upgrader: websocket.Upgrader{
			ReadBufferSize:  4096,
			WriteBufferSize: 4096,
			CheckOrigin: func(r *http.Request) bool {
				return true
			},
		},
		cfg:    cfg,
		logger: logger,
	}
}

// Hub gibt den aktiven Hub zurück (z. B. für die Main-Loop).
func (s *Server) Hub() *Hub {
	return s.hub
}

// Routes registriert die HTTP-Routen.
func (s *Server) Routes(mux *http.ServeMux) {
	mux.HandleFunc("/ws", s.handleWebSocket)
	mux.HandleFunc("/api/events", s.handleBroadcast)
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{"status": "ok", "timestamp": time.Now().UTC()})
	})
}

func (s *Server) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	if !s.authorize(r) {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		s.logger.Printf("upgrade fehlgeschlagen: %v", err)
		return
	}
	client := NewClient(s.hub, conn)
	s.hub.Register(client)
	go client.Writer()
	go client.Reader()
}

func (s *Server) handleBroadcast(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if !s.authorize(r) {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	var evt Event
	if err := decodeJSON(r, &evt); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err)
		return
	}
	if evt.Timestamp.IsZero() {
		evt.Timestamp = time.Now().UTC()
	}
	s.hub.Broadcast(evt)
	writeJSON(w, http.StatusAccepted, map[string]string{"status": "queued"})
}

func (s *Server) authorize(r *http.Request) bool {
	if s.cfg.Token == "" {
		return true
	}
	header := strings.TrimSpace(r.Header.Get("X-API-Key"))
	if header == s.cfg.Token {
		return true
	}
	query := r.URL.Query().Get("token")
	return strings.TrimSpace(query) == s.cfg.Token
}

// Hilfsfunktionen für JSON-Antworten.
func decodeJSON(r *http.Request, target any) error {
	defer r.Body.Close()
	return jsonNewDecoder(r).Decode(target)
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = jsonNewEncoder(w).Encode(payload)
}

func writeError(w http.ResponseWriter, status int, code string, err error) {
	writeJSON(w, status, map[string]any{
		"error":   code,
		"message": err.Error(),
	})
}

// Minimale Wrapper für Encoder/Decoder mit strengerem Verhalten.
type decoder interface {
	Decode(v any) error
}

func jsonNewDecoder(r *http.Request) decoder {
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	return dec
}

type encoder interface {
	Encode(v any) error
}

func jsonNewEncoder(w http.ResponseWriter) encoder {
	return json.NewEncoder(w)
}
