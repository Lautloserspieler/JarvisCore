package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
)

const PORT = ":8083"

var db *sql.DB

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
	Role      string    `json:"role"` // "user" or "assistant"
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
	ID           string    `json:"id"`
	Name         string    `json:"name"`
	Path         string    `json:"path"`
	Size         int64     `json:"size"`
	Quantization string    `json:"quantization"`
	IsLoaded     bool      `json:"is_loaded"`
	LoadedAt     *time.Time `json:"loaded_at,omitempty"`
	CreatedAt    time.Time `json:"created_at"`
}

// Database initialization
func initDB() error {
	// Get database URL from environment or use default SQLite
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		// Default to PostgreSQL on localhost
		dbURL = "postgres://jarvis:jarvis@localhost:5432/jarviscore?sslmode=disable"
		log.Println("[INFO] DATABASE_URL not set, using default PostgreSQL")
	}

	var err error
	db, err = sql.Open("postgres", dbURL)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}

	// Test connection
	if err := db.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	// Set connection pool settings
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	log.Println("[INFO] Database connected successfully")
	return nil
}

func createTables() error {
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
		tags TEXT[], -- PostgreSQL array
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

	_, err := db.Exec(schema)
	if err != nil {
		return fmt.Errorf("failed to create tables: %w", err)
	}

	log.Println("[INFO] Database schema created/verified")
	return nil
}

// Chat Session Handlers

func createChatSessionHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Title string `json:"title"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	id := uuid.New().String()
	now := time.Now()

	_, err := db.Exec(
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

func getChatSessionsHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(
		"SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC LIMIT 50",
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Query failed: %s"}`, err), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	sessions := []ChatSession{}
	for rows.Next() {
		var s ChatSession
		if err := rows.Scan(&s.ID, &s.Title, &s.CreatedAt, &s.UpdatedAt); err != nil {
			continue
		}
		sessions = append(sessions, s)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(sessions)
}

func addChatMessageHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		SessionID string `json:"session_id"`
		Role      string `json:"role"`
		Content   string `json:"content"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	id := uuid.New().String()

	_, err := db.Exec(
		"INSERT INTO chat_messages (id, session_id, role, content, created_at) VALUES ($1, $2, $3, $4, $5)",
		id, req.SessionID, req.Role, req.Content, time.Now(),
	)

	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to add message: %s"}`, err), http.StatusInternalServerError)
		return
	}

	// Update session updated_at
	db.Exec("UPDATE chat_sessions SET updated_at = $1 WHERE id = $2", time.Now(), req.SessionID)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"id":      id,
	})
}

func getChatHistoryHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["session_id"]

	rows, err := db.Query(
		"SELECT id, session_id, role, content, created_at FROM chat_messages WHERE session_id = $1 ORDER BY created_at ASC",
		sessionID,
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Query failed: %s"}`, err), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	messages := []ChatMessage{}
	for rows.Next() {
		var m ChatMessage
		if err := rows.Scan(&m.ID, &m.SessionID, &m.Role, &m.Content, &m.CreatedAt); err != nil {
			continue
		}
		messages = append(messages, m)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(messages)
}

// Memory Handlers

func addMemoryHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Content    string   `json:"content"`
		Type       string   `json:"type"`
		Tags       []string `json:"tags"`
		Importance int      `json:"importance"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	id := uuid.New().String()
	now := time.Now()

	if req.Importance == 0 {
		req.Importance = 5
	}

	_, err := db.Exec(
		"INSERT INTO memories (id, content, type, tags, importance, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
		id, req.Content, req.Type, req.Tags, req.Importance, now, now,
	)

	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to add memory: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"id":      id,
	})
}

func getMemoriesHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(
		"SELECT id, content, type, tags, importance, created_at, updated_at FROM memories ORDER BY importance DESC, updated_at DESC LIMIT 100",
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Query failed: %s"}`, err), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	memories := []MemoryEntry{}
	for rows.Next() {
		var m MemoryEntry
		var tagsJSON []byte
		if err := rows.Scan(&m.ID, &m.Content, &m.Type, &tagsJSON, &m.Importance, &m.CreatedAt, &m.UpdatedAt); err != nil {
			continue
		}
		json.Unmarshal(tagsJSON, &m.Tags)
		memories = append(memories, m)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(memories)
}

// Model Handlers

func registerModelHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name         string `json:"name"`
		Path         string `json:"path"`
		Size         int64  `json:"size"`
		Quantization string `json:"quantization"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}

	id := uuid.New().String()

	_, err := db.Exec(
		"INSERT INTO models (id, name, path, size, quantization, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
		id, req.Name, req.Path, req.Size, req.Quantization, time.Now(),
	)

	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to register model: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"id":      id,
	})
}

func getModelsHandler(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(
		"SELECT id, name, path, size, quantization, is_loaded, loaded_at, created_at FROM models ORDER BY created_at DESC",
	)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Query failed: %s"}`, err), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	models := []ModelInfo{}
	for rows.Next() {
		var m ModelInfo
		if err := rows.Scan(&m.ID, &m.Name, &m.Path, &m.Size, &m.Quantization, &m.IsLoaded, &m.LoadedAt, &m.CreatedAt); err != nil {
			continue
		}
		models = append(models, m)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models)
}

// Stats Handler

func getStatsHandler(w http.ResponseWriter, r *http.Request) {
	var sessionCount, messageCount, memoryCount, modelCount int

	db.QueryRow("SELECT COUNT(*) FROM chat_sessions").Scan(&sessionCount)
	db.QueryRow("SELECT COUNT(*) FROM chat_messages").Scan(&messageCount)
	db.QueryRow("SELECT COUNT(*) FROM memories").Scan(&memoryCount)
	db.QueryRow("SELECT COUNT(*) FROM models").Scan(&modelCount)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"sessions": sessionCount,
		"messages": messageCount,
		"memories": memoryCount,
		"models":   modelCount,
	})
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// Test DB connection
	err := db.Ping()
	dbStatus := "healthy"
	if err != nil {
		dbStatus = "unhealthy: " + err.Error()
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"service":   "jarvis-database-service",
		"version":   "1.0.0",
		"time":      time.Now().Unix(),
		"db_status": dbStatus,
	})
}

func main() {
	// Initialize database
	if err := initDB(); err != nil {
		log.Fatalf("[ERROR] Failed to initialize database: %s", err)
	}
	defer db.Close()

	// Create tables
	if err := createTables(); err != nil {
		log.Fatalf("[ERROR] Failed to create tables: %s", err)
	}

	r := mux.NewRouter()

	// Health
	r.HandleFunc("/health", healthHandler).Methods("GET")

	// Chat endpoints
	r.HandleFunc("/api/chat/sessions", createChatSessionHandler).Methods("POST")
	r.HandleFunc("/api/chat/sessions", getChatSessionsHandler).Methods("GET")
	r.HandleFunc("/api/chat/messages", addChatMessageHandler).Methods("POST")
	r.HandleFunc("/api/chat/history/{session_id}", getChatHistoryHandler).Methods("GET")

	// Memory endpoints
	r.HandleFunc("/api/memory", addMemoryHandler).Methods("POST")
	r.HandleFunc("/api/memory", getMemoriesHandler).Methods("GET")

	// Model endpoints
	r.HandleFunc("/api/models/register", registerModelHandler).Methods("POST")
	r.HandleFunc("/api/models", getModelsHandler).Methods("GET")

	// Stats
	r.HandleFunc("/api/stats", getStatsHandler).Methods("GET")

	// CORS
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}

			next.ServeHTTP(w, r)
		})
	})

	log.Printf("[INFO] JARVIS Database Service starting on %s", PORT)
	log.Println("[INFO] Connected to PostgreSQL")

	if err := http.ListenAndServe(PORT, r); err != nil {
		log.Fatal(err)
	}
}
