package database

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
)

const (
	defaultListenAddr  = ":8083"
	defaultDatabaseURL = "postgres://jarvis:jarvis@localhost:5432/jarviscore?sslmode=disable"
)

type Config struct {
	ListenAddr  string
	DatabaseURL string
}

func LoadConfig() Config {
	cfg := Config{
		ListenAddr:  defaultListenAddr,
		DatabaseURL: defaultDatabaseURL,
	}
	if value := strings.TrimSpace(os.Getenv("JARVIS_DATABASE_ADDR")); value != "" {
		cfg.ListenAddr = value
	}
	if value := strings.TrimSpace(os.Getenv("DATABASE_URL")); value != "" {
		cfg.DatabaseURL = value
	}

	return cfg
}

// Models

type ChatSession struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type ChatMessage struct {
	ID        string    `json:"id"`
	SessionID string    `json:"session_id"`
	Role      string    `json:"role"`
	Content   string    `json:"content"`
	CreatedAt time.Time `json:"created_at"`
}

type MemoryEntry struct {
	ID         string    `json:"id"`
	Content    string    `json:"content"`
	Type       string    `json:"type"`
	Tags       []string  `json:"tags"`
	Importance int       `json:"importance"`
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
}

type ModelInfo struct {
	ID           string     `json:"id"`
	Name         string     `json:"name"`
	Path         string     `json:"path"`
	Size         int64      `json:"size"`
	Quantization string     `json:"quantization"`
	IsLoaded     bool       `json:"is_loaded"`
	LoadedAt     *time.Time `json:"loaded_at,omitempty"`
	CreatedAt    time.Time  `json:"created_at"`
}

type Service struct {
	cfg    Config
	logger *log.Logger
	db     *sql.DB
}

func NewService(cfg Config, logger *log.Logger) (*Service, error) {
	if logger == nil {
		logger = log.New(os.Stdout, "[database] ", log.LstdFlags|log.LUTC)
	}

	db, err := initDB(cfg.DatabaseURL, logger)
	if err != nil {
		return nil, err
	}

	svc := &Service{
		cfg:    cfg,
		logger: logger,
		db:     db,
	}

	if err := svc.createTables(); err != nil {
		return nil, err
	}

	return svc, nil
}

func initDB(dbURL string, logger *log.Logger) (*sql.DB, error) {
	if dbURL == "" {
		dbURL = defaultDatabaseURL
		logger.Println("[INFO] DATABASE_URL not set, using default PostgreSQL")
	}

	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	logger.Println("[INFO] Database connected successfully")
	return db, nil
}

func (s *Service) createTables() error {
	schema := `
	-- Chat Sessions
	CREATE TABLE IF NOT EXISTS chat_sessions (
		id VARCHAR(36) PRIMARY KEY,
		title VARCHAR(255) NOT NULL,
		created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
	);

	-- Chat Messages
	CREATE TABLE IF NOT EXISTS chat_messages (
		id VARCHAR(36) PRIMARY KEY,
		session_id VARCHAR(36) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
		role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
		content TEXT NOT NULL,
		created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
	);
	CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);

	-- Memories
	CREATE TABLE IF NOT EXISTS memories (
		id VARCHAR(36) PRIMARY KEY,
		content TEXT NOT NULL,
		type VARCHAR(50) NOT NULL,
		tags TEXT[],
		importance INTEGER DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),
		created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
	);
	CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
	CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);

	-- Models
	CREATE TABLE IF NOT EXISTS models (
		id VARCHAR(36) PRIMARY KEY,
		name VARCHAR(255) NOT NULL UNIQUE,
		path TEXT NOT NULL,
		size BIGINT NOT NULL,
		quantization VARCHAR(20),
		is_loaded BOOLEAN DEFAULT FALSE,
		loaded_at TIMESTAMP,
		created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
	);

	-- Plugin Configs
	CREATE TABLE IF NOT EXISTS plugin_configs (
		id VARCHAR(36) PRIMARY KEY,
		plugin_name VARCHAR(255) NOT NULL UNIQUE,
		config JSONB NOT NULL,
		enabled BOOLEAN DEFAULT TRUE,
		created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
	);

	-- API Keys
	CREATE TABLE IF NOT EXISTS api_keys (
		id VARCHAR(36) PRIMARY KEY,
		key VARCHAR(255) NOT NULL UNIQUE,
		rate_limit INTEGER NOT NULL DEFAULT 60,
		burst INTEGER NOT NULL DEFAULT 10,
		enabled BOOLEAN DEFAULT TRUE,
		created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
		last_used TIMESTAMP
	);
	`

	_, err := s.db.Exec(schema)
	if err != nil {
		return fmt.Errorf("failed to create tables: %w", err)
	}

	s.logger.Println("[INFO] Database schema created/verified")
	return nil
}

func (s *Service) Routes(mux *http.ServeMux) {
	router := mux.NewRouter()

	router.HandleFunc("/health", s.healthHandler).Methods(http.MethodGet)

	router.HandleFunc("/api/database/sessions", s.createChatSessionHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/database/sessions", s.getChatSessionsHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/database/sessions/{id}", s.getChatSessionHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/database/sessions/{id}", s.deleteChatSessionHandler).Methods(http.MethodDelete)
	router.HandleFunc("/api/database/sessions/{id}/messages", s.addMessageHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/database/sessions/{id}/messages", s.getSessionMessagesHandler).Methods(http.MethodGet)

	router.HandleFunc("/api/database/memories", s.addMemoryHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/database/memories", s.searchMemoriesHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/database/memories/{id}", s.getMemoryHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/database/memories/{id}", s.updateMemoryHandler).Methods(http.MethodPut)
	router.HandleFunc("/api/database/memories/{id}", s.deleteMemoryHandler).Methods(http.MethodDelete)

	router.HandleFunc("/api/database/models", s.addModelHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/database/models", s.getModelsHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/database/models/{id}", s.updateModelStatusHandler).Methods(http.MethodPut)
	router.HandleFunc("/api/database/models/{id}", s.deleteModelHandler).Methods(http.MethodDelete)

	router.Use(corsMiddleware)

	mux.Handle("/", router)
}

// Handlers

func (s *Service) healthHandler(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "jarvis-database-service",
		"version": "1.0.0",
		"time":    time.Now().Unix(),
	})
}

func (s *Service) createChatSessionHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Title string `json:"title"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	id := uuid.New().String()
	now := time.Now()

	_, err := s.db.Exec(
		"INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES ($1, $2, $3, $4)",
		id, req.Title, now, now,
	)

	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to create session: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"id":      id,
	})
}

func (s *Service) getChatSessionsHandler(w http.ResponseWriter, _ *http.Request) {
	rows, err := s.db.Query(
		"SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC LIMIT 50",
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Query failed: %s"}`, err), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var sessions []ChatSession
	for rows.Next() {
		var session ChatSession
		if err := rows.Scan(&session.ID, &session.Title, &session.CreatedAt, &session.UpdatedAt); err != nil {
			http.Error(w, fmt.Sprintf(`{"error":"Scan failed: %s"}`, err), http.StatusInternalServerError)
			return
		}
		sessions = append(sessions, session)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(sessions)
}

func (s *Service) getChatSessionHandler(w http.ResponseWriter, r *http.Request) {
	id := mux.Vars(r)["id"]

	var session ChatSession
	row := s.db.QueryRow("SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = $1", id)
	if err := row.Scan(&session.ID, &session.Title, &session.CreatedAt, &session.UpdatedAt); err != nil {
		http.Error(w, `{"error":"Session not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(session)
}

func (s *Service) deleteChatSessionHandler(w http.ResponseWriter, r *http.Request) {
	id := mux.Vars(r)["id"]

	_, err := s.db.Exec("DELETE FROM chat_sessions WHERE id = $1", id)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to delete session: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true})
}

func (s *Service) addMessageHandler(w http.ResponseWriter, r *http.Request) {
	sessionID := mux.Vars(r)["id"]

	var req struct {
		Role    string `json:"role"`
		Content string `json:"content"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	id := uuid.New().String()
	now := time.Now()

	_, err := s.db.Exec(
		"INSERT INTO chat_messages (id, session_id, role, content, created_at) VALUES ($1, $2, $3, $4, $5)",
		id, sessionID, req.Role, req.Content, now,
	)

	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to add message: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true, "id": id})
}

func (s *Service) getSessionMessagesHandler(w http.ResponseWriter, r *http.Request) {
	sessionID := mux.Vars(r)["id"]

	rows, err := s.db.Query(
		"SELECT id, session_id, role, content, created_at FROM chat_messages WHERE session_id = $1 ORDER BY created_at ASC",
		sessionID,
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Query failed: %s"}`, err), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var messages []ChatMessage
	for rows.Next() {
		var msg ChatMessage
		if err := rows.Scan(&msg.ID, &msg.SessionID, &msg.Role, &msg.Content, &msg.CreatedAt); err != nil {
			http.Error(w, fmt.Sprintf(`{"error":"Scan failed: %s"}`, err), http.StatusInternalServerError)
			return
		}
		messages = append(messages, msg)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(messages)
}

func (s *Service) addMemoryHandler(w http.ResponseWriter, r *http.Request) {
	var memory MemoryEntry

	if err := json.NewDecoder(r.Body).Decode(&memory); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	memory.ID = uuid.New().String()
	now := time.Now()
	memory.CreatedAt = now
	memory.UpdatedAt = now

	_, err := s.db.Exec(
		"INSERT INTO memories (id, content, type, tags, importance, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
		memory.ID, memory.Content, memory.Type, memory.Tags, memory.Importance, memory.CreatedAt, memory.UpdatedAt,
	)

	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to add memory: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true, "id": memory.ID})
}

func (s *Service) searchMemoriesHandler(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("query")
	memoryType := r.URL.Query().Get("type")
	var tags []string

	if tagsParam := r.URL.Query().Get("tags"); tagsParam != "" {
		tags = strings.Split(tagsParam, ",")
	}

	rows, err := s.db.Query(
		"SELECT id, content, type, tags, importance, created_at, updated_at FROM memories WHERE content ILIKE '%' || $1 || '%' AND ($2 = '' OR type = $2) ORDER BY importance DESC, updated_at DESC LIMIT 100",
		query, memoryType,
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Query failed: %s"}`, err), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var memories []MemoryEntry
	for rows.Next() {
		var memory MemoryEntry
		if err := rows.Scan(&memory.ID, &memory.Content, &memory.Type, &memory.Tags, &memory.Importance, &memory.CreatedAt, &memory.UpdatedAt); err != nil {
			http.Error(w, fmt.Sprintf(`{"error":"Scan failed: %s"}`, err), http.StatusInternalServerError)
			return
		}
		memories = append(memories, memory)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(memories)
}

func (s *Service) getMemoryHandler(w http.ResponseWriter, r *http.Request) {
	id := mux.Vars(r)["id"]

	var memory MemoryEntry
	row := s.db.QueryRow("SELECT id, content, type, tags, importance, created_at, updated_at FROM memories WHERE id = $1", id)
	if err := row.Scan(&memory.ID, &memory.Content, &memory.Type, &memory.Tags, &memory.Importance, &memory.CreatedAt, &memory.UpdatedAt); err != nil {
		http.Error(w, `{"error":"Memory not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(memory)
}

func (s *Service) updateMemoryHandler(w http.ResponseWriter, r *http.Request) {
	id := mux.Vars(r)["id"]

	var updates struct {
		Content    string   `json:"content"`
		Tags       []string `json:"tags"`
		Importance int      `json:"importance"`
	}

	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	_, err := s.db.Exec(
		"UPDATE memories SET content = $1, tags = $2, importance = $3, updated_at = $4 WHERE id = $5",
		updates.Content, updates.Tags, updates.Importance, time.Now(), id,
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to update memory: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true})
}

func (s *Service) deleteMemoryHandler(w http.ResponseWriter, r *http.Request) {
	id := mux.Vars(r)["id"]

	_, err := s.db.Exec("DELETE FROM memories WHERE id = $1", id)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to delete memory: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true})
}

func (s *Service) addModelHandler(w http.ResponseWriter, r *http.Request) {
	var model ModelInfo

	if err := json.NewDecoder(r.Body).Decode(&model); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	model.ID = uuid.New().String()
	model.CreatedAt = time.Now()

	_, err := s.db.Exec(
		"INSERT INTO models (id, name, path, size, quantization, is_loaded, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
		model.ID, model.Name, model.Path, model.Size, model.Quantization, model.IsLoaded, model.CreatedAt,
	)

	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to add model: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true, "id": model.ID})
}

func (s *Service) getModelsHandler(w http.ResponseWriter, _ *http.Request) {
	rows, err := s.db.Query(
		"SELECT id, name, path, size, quantization, is_loaded, loaded_at, created_at FROM models ORDER BY created_at DESC",
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Query failed: %s"}`, err), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var models []ModelInfo
	for rows.Next() {
		var model ModelInfo
		if err := rows.Scan(&model.ID, &model.Name, &model.Path, &model.Size, &model.Quantization, &model.IsLoaded, &model.LoadedAt, &model.CreatedAt); err != nil {
			http.Error(w, fmt.Sprintf(`{"error":"Scan failed: %s"}`, err), http.StatusInternalServerError)
			return
		}
		models = append(models, model)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models)
}

func (s *Service) updateModelStatusHandler(w http.ResponseWriter, r *http.Request) {
	id := mux.Vars(r)["id"]

	var update struct {
		IsLoaded bool `json:"is_loaded"`
	}

	if err := json.NewDecoder(r.Body).Decode(&update); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	var loadedAt *time.Time
	if update.IsLoaded {
		now := time.Now()
		loadedAt = &now
	}

	_, err := s.db.Exec(
		"UPDATE models SET is_loaded = $1, loaded_at = $2 WHERE id = $3",
		update.IsLoaded, loadedAt, id,
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to update model: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true})
}

func (s *Service) deleteModelHandler(w http.ResponseWriter, r *http.Request) {
	id := mux.Vars(r)["id"]

	_, err := s.db.Exec("DELETE FROM models WHERE id = $1", id)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to delete model: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{"success": true})
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}
