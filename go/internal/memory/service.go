package memory

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"time"
)

// Config beschreibt Laufzeitparameter.
type Config struct {
	ListenAddr string
	StoreFile  string
}

// LoadConfig liest Umgebungsvariablen.
func LoadConfig() Config {
	addr := os.Getenv("MEMORYD_LISTEN")
	if addr == "" {
		addr = ":7072"
	}
	store := os.Getenv("MEMORYD_STORE")
	if store == "" {
		store = "data/memoryd/store.json"
	}
	return Config{
		ListenAddr: addr,
		StoreFile:  store,
	}
}

// Service enthält Store und Logger.
type Service struct {
	store  *Store
	logger *log.Logger
}

// NewService erzeugt einen neuen Memory-Service.
func NewService(cfg Config, logger *log.Logger) (*Service, error) {
	if logger == nil {
		logger = log.New(os.Stdout, "[memoryd] ", log.LstdFlags|log.LUTC)
	}
	store, err := NewStore(cfg.StoreFile)
	if err != nil {
		return nil, err
	}
	return &Service{store: store, logger: logger}, nil
}

// Routes registriert HTTP-Handler.
func (s *Service) Routes(mux *http.ServeMux) {
	mux.HandleFunc("POST /memory/save", s.handleSave)
	mux.HandleFunc("GET /memory/get", s.handleGet)
	mux.HandleFunc("POST /memory/search", s.handleSearch)
	mux.HandleFunc("DELETE /memory/delete", s.handleDelete)
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{"status": "ok", "timestamp": time.Now().UTC()})
	})
}

type saveRequest struct {
	Key        string     `json:"key"`
	Value      any        `json:"value"`
	Category   string     `json:"category,omitempty"`
	Tags       []string   `json:"tags,omitempty"`
	Importance float64    `json:"importance,omitempty"`
	ExpiresAt  *time.Time `json:"expires_at,omitempty"`
	TTLSeconds int64      `json:"ttl_seconds,omitempty"`
}

func (s *Service) handleSave(w http.ResponseWriter, r *http.Request) {
	var req saveRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err)
		return
	}
	if req.Key == "" {
		writeError(w, http.StatusBadRequest, "missing_key", errMissingKey)
		return
	}
	if req.TTLSeconds > 0 {
		exp := time.Now().UTC().Add(time.Duration(req.TTLSeconds) * time.Second)
		req.ExpiresAt = &exp
	}
	entry := Entry{
		Key:        req.Key,
		Value:      req.Value,
		Category:   req.Category,
		Tags:       req.Tags,
		Importance: req.Importance,
		ExpiresAt:  req.ExpiresAt,
		UpdatedAt:  time.Now().UTC(),
	}
	if err := s.store.Save(entry); err != nil {
		writeError(w, http.StatusInternalServerError, "persist_failed", err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true})
}

func (s *Service) handleGet(w http.ResponseWriter, r *http.Request) {
	key := r.URL.Query().Get("key")
	if key == "" {
		writeError(w, http.StatusBadRequest, "missing_key", errMissingKey)
		return
	}
	entry, ok := s.store.Get(key)
	if !ok {
		writeError(w, http.StatusNotFound, "not_found", errNotFound)
		return
	}
	writeJSON(w, http.StatusOK, entry)
}

type searchRequest struct {
	Query    string `json:"query,omitempty"`
	Category string `json:"category,omitempty"`
	Limit    int    `json:"limit,omitempty"`
}

func (s *Service) handleSearch(w http.ResponseWriter, r *http.Request) {
	var req searchRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err)
		return
	}
	results := s.store.Search(req.Query, req.Category, req.Limit)
	writeJSON(w, http.StatusOK, map[string]any{"results": results})
}

type deleteRequest struct {
	Key string `json:"key"`
}

func (s *Service) handleDelete(w http.ResponseWriter, r *http.Request) {
	var req deleteRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err)
		return
	}
	if req.Key == "" {
		writeError(w, http.StatusBadRequest, "missing_key", errMissingKey)
		return
	}
	ok := s.store.Delete(req.Key)
	if !ok {
		writeError(w, http.StatusNotFound, "not_found", errNotFound)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"deleted": true})
}

var (
	errMissingKey = errors.New("key required")
	errNotFound   = errors.New("not found")
)

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
