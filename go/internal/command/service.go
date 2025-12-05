package command

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
	"time"
)

// Config haelt Laufzeitparameter.
type Config struct {
	ListenAddr string
}

// LoadConfig liest Umgebungsvariablen.
func LoadConfig() Config {
	addr := os.Getenv("COMMANDD_LISTEN")
	if addr == "" {
		addr = ":7075"
	}
	return Config{ListenAddr: addr}
}

// Service ist ein Minimal-Stub fuer Command-Routing.
type Service struct {
	cfg    Config
	logger *log.Logger
	queue  *Queue
}

// NewService erstellt den Service.
func NewService(cfg Config, logger *log.Logger) *Service {
	if logger == nil {
		logger = log.New(os.Stdout, "[commandd] ", log.LstdFlags|log.LUTC)
	}
	return &Service{
		cfg:    cfg,
		logger: logger,
		queue:  NewQueue(),
	}
}

// Routes registriert HTTP-Endpunkte.
func (s *Service) Routes(mux *http.ServeMux) {
	mux.HandleFunc("/command/execute", s.handleExecute)
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{"status": "ok", "timestamp": time.Now().UTC()})
	})
}

type executeRequest struct {
	Text     string         `json:"text"`
	Metadata map[string]any `json:"metadata,omitempty"`
	Context  map[string]any `json:"context,omitempty"`
	Priority int            `json:"priority,omitempty"`
}

type executeResponse struct {
	Response string         `json:"response"`
	Meta     map[string]any `json:"meta,omitempty"`
}

func (s *Service) handleExecute(w http.ResponseWriter, r *http.Request) {
	var req executeRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err)
		return
	}
	job := Job{
		ID:        time.Now().UTC().Format("20060102T150405.000000000"),
		Text:      strings.TrimSpace(req.Text),
		Metadata:  req.Metadata,
		Context:   req.Context,
		Priority:  req.Priority,
		CreatedAt: time.Now().UTC(),
	}
	s.queue.Enqueue(job)
	writeJSON(w, http.StatusOK, executeResponse{
		Response: "",
		Meta: map[string]any{
			"job_id":   job.ID,
			"queued":   true,
			"priority": job.Priority,
		},
	})
}

func decodeJSON(r *http.Request, target any) error {
	defer r.Body.Close()
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	return dec.Decode(target)
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func writeError(w http.ResponseWriter, status int, code string, err error) {
	writeJSON(w, status, map[string]any{
		"error":   code,
		"message": err.Error(),
	})
}
