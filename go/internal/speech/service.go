package speech

import (
	"encoding/base64"
	"encoding/json"
	"errors"
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
	addr := os.Getenv("SPEECHD_LISTEN")
	if addr == "" {
		addr = ":7074"
	}
	return Config{ListenAddr: addr}
}

// Service kapselt Logger.
type Service struct {
	cfg    Config
	logger *log.Logger
	queue  *Queue
}

// NewService erzeugt einen Service.
func NewService(cfg Config, logger *log.Logger) *Service {
	if logger == nil {
		logger = log.New(os.Stdout, "[speechtaskd] ", log.LstdFlags|log.LUTC)
	}
	return &Service{cfg: cfg, logger: logger, queue: NewQueue()}
}

// Routes registriert Endpunkte.
func (s *Service) Routes(mux *http.ServeMux) {
	mux.HandleFunc("/speech/recognize", s.handleRecognize)
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{"status": "ok", "timestamp": time.Now().UTC()})
	})
}

type recognizeRequest struct {
	Audio      string `json:"audio"` // base64 PCM16
	SampleRate int    `json:"sample_rate,omitempty"`
	Channels   int    `json:"channels,omitempty"`
}

type recognizeResponse struct {
	Transcript string `json:"transcript"`
	JobID      string `json:"job_id,omitempty"`
}

func (s *Service) handleRecognize(w http.ResponseWriter, r *http.Request) {
	var req recognizeRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err)
		return
	}
	if req.Audio == "" {
		writeError(w, http.StatusBadRequest, "missing_audio", errors.New("audio required"))
		return
	}
	// Hinweis: Dies ist ein Stub. Die eigentliche STT bleibt in Python.
	_, err := base64.StdEncoding.DecodeString(req.Audio)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid_audio", err)
		return
	}
	job := Job{
		ID:         time.Now().UTC().Format("20060102T150405.000000000"),
		AudioB64:   strings.TrimSpace(req.Audio),
		SampleRate: req.SampleRate,
		Channels:   req.Channels,
		CreatedAt:  time.Now().UTC(),
	}
	s.queue.Enqueue(job)
	// Hier koennte spaeter eine Callback/RPC-Integration zum Python-STT stattfinden.
	writeJSON(w, http.StatusOK, recognizeResponse{Transcript: "", JobID: job.ID})
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
