package memory

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/mux"
)

const (
	defaultListenAddr       = ":8082"
	defaultStorageDir       = "data/memories"
	defaultAutoSaveInterval = 5 * time.Minute
)

type Config struct {
	ListenAddr       string
	StorageDir       string
	AutoSaveInterval time.Duration
}

func LoadConfig() Config {
	cfg := Config{
		ListenAddr:       defaultListenAddr,
		StorageDir:       defaultStorageDir,
		AutoSaveInterval: defaultAutoSaveInterval,
	}

	if value := strings.TrimSpace(os.Getenv("JARVIS_MEMORY_ADDR")); value != "" {
		cfg.ListenAddr = value
	}
	if value := strings.TrimSpace(os.Getenv("JARVIS_MEMORY_STORAGE_DIR")); value != "" {
		cfg.StorageDir = value
	}
	if value := strings.TrimSpace(os.Getenv("JARVIS_MEMORY_AUTOSAVE_INTERVAL")); value != "" {
		if parsed, err := time.ParseDuration(value); err == nil {
			cfg.AutoSaveInterval = parsed
		}
	}

	return cfg
}

// Memory represents a single memory entry.
type Memory struct {
	ID         string                 `json:"id"`
	Content    string                 `json:"content"`
	Type       string                 `json:"type"`
	Tags       []string               `json:"tags"`
	Importance int                    `json:"importance"`
	CreatedAt  time.Time              `json:"created_at"`
	UpdatedAt  time.Time              `json:"updated_at"`
	References []string               `json:"references"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// MemoryStore manages all memories.
type MemoryStore struct {
	memories   map[string]*Memory
	storageDir string
	mu         sync.RWMutex
}

func NewMemoryStore(storageDir string) *MemoryStore {
	return &MemoryStore{
		memories:   make(map[string]*Memory),
		storageDir: storageDir,
	}
}

func (s *MemoryStore) Add(memory *Memory) string {
	s.mu.Lock()
	defer s.mu.Unlock()

	if memory.ID == "" {
		memory.ID = uuid.New().String()
	}
	if memory.CreatedAt.IsZero() {
		memory.CreatedAt = time.Now()
	}
	memory.UpdatedAt = time.Now()

	s.memories[memory.ID] = memory
	return memory.ID
}

func (s *MemoryStore) Get(id string) (*Memory, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	memory, exists := s.memories[id]
	return memory, exists
}

func (s *MemoryStore) Update(id string, updates map[string]interface{}) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	memory, exists := s.memories[id]
	if !exists {
		return false
	}

	// Apply updates
	if content, ok := updates["content"].(string); ok {
		memory.Content = content
	}
	if tags, ok := updates["tags"].([]string); ok {
		memory.Tags = tags
	}
	if importance, ok := updates["importance"].(float64); ok {
		memory.Importance = int(importance)
	}

	memory.UpdatedAt = time.Now()
	return true
}

func (s *MemoryStore) Delete(id string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.memories[id]; exists {
		delete(s.memories, id)
		return true
	}
	return false
}

func (s *MemoryStore) Search(query string, memoryType string, tags []string) []*Memory {
	s.mu.RLock()
	defer s.mu.RUnlock()

	results := []*Memory{}
	queryLower := strings.ToLower(query)

	for _, memory := range s.memories {
		// Filter by type
		if memoryType != "" && memory.Type != memoryType {
			continue
		}

		// Filter by tags
		if len(tags) > 0 {
			hasTag := false
			for _, tag := range tags {
				for _, memTag := range memory.Tags {
					if tag == memTag {
						hasTag = true
						break
					}
				}
				if hasTag {
					break
				}
			}
			if !hasTag {
				continue
			}
		}

		// Search in content
		if query == "" || strings.Contains(strings.ToLower(memory.Content), queryLower) {
			results = append(results, memory)
		}
	}

	// Sort by importance then updated_at
	sort.Slice(results, func(i, j int) bool {
		if results[i].Importance != results[j].Importance {
			return results[i].Importance > results[j].Importance
		}
		return results[i].UpdatedAt.After(results[j].UpdatedAt)
	})

	return results
}

func (s *MemoryStore) GetAll() []*Memory {
	s.mu.RLock()
	defer s.mu.RUnlock()

	results := make([]*Memory, 0, len(s.memories))
	for _, memory := range s.memories {
		results = append(results, memory)
	}

	// Sort by updated_at descending
	sort.Slice(results, func(i, j int) bool {
		return results[i].UpdatedAt.After(results[j].UpdatedAt)
	})

	return results
}

func (s *MemoryStore) GetStats() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	typeCounts := make(map[string]int)
	totalImportance := 0

	for _, memory := range s.memories {
		typeCounts[memory.Type]++
		totalImportance += memory.Importance
	}

	avgImportance := 0.0
	if len(s.memories) > 0 {
		avgImportance = float64(totalImportance) / float64(len(s.memories))
	}

	return map[string]interface{}{
		"total":           len(s.memories),
		"by_type":         typeCounts,
		"avg_importance":  avgImportance,
		"storage_size_kb": s.estimateSize() / 1024,
	}
}

func (s *MemoryStore) estimateSize() int {
	s.mu.RLock()
	defer s.mu.RUnlock()

	totalSize := 0
	for _, memory := range s.memories {
		totalSize += len(memory.Content)
		totalSize += len(memory.ID) * 2 // ID stored twice
		totalSize += len(memory.Type)
		for _, tag := range memory.Tags {
			totalSize += len(tag)
		}
	}
	return totalSize
}

// Persistence
func (s *MemoryStore) SaveToFile(filename string) error {
	s.mu.RLock()
	defer s.mu.RUnlock()

	data, err := json.MarshalIndent(s.memories, "", "  ")
	if err != nil {
		return err
	}

	// Ensure directory exists
	if err := os.MkdirAll(s.storageDir, 0o755); err != nil {
		return err
	}

	path := filepath.Join(s.storageDir, filename)
	return os.WriteFile(path, data, 0o644)
}

func (s *MemoryStore) LoadFromFile(filename string) error {
	path := filepath.Join(s.storageDir, filename)

	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	return json.Unmarshal(data, &s.memories)
}

type Service struct {
	cfg    Config
	store  *MemoryStore
	logger *log.Logger
}

func NewService(cfg Config, logger *log.Logger) (*Service, error) {
	store := NewMemoryStore(cfg.StorageDir)
	if logger == nil {
		logger = log.New(os.Stdout, "[memory] ", log.LstdFlags|log.LUTC)
	}

	svc := &Service{cfg: cfg, store: store, logger: logger}

	if err := store.LoadFromFile("memories.json"); err != nil {
		logger.Printf("[INFO] No existing memories found, starting fresh")
	} else {
		logger.Printf("[INFO] Loaded %d memories from disk", len(store.memories))
	}

	svc.startAutoSave()

	return svc, nil
}

func (s *Service) Routes(mux *http.ServeMux) {
	router := mux.NewRouter()

	router.HandleFunc("/health", s.healthHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/memory", s.addMemoryHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/memory/{id}", s.getMemoryHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/memory/{id}", s.updateMemoryHandler).Methods(http.MethodPut)
	router.HandleFunc("/api/memory/{id}", s.deleteMemoryHandler).Methods(http.MethodDelete)
	router.HandleFunc("/api/memory/search", s.searchMemoriesHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/memory/all", s.getAllMemoriesHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/memory/stats", s.getStatsHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/memory/save", s.saveMemoriesHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/memory/load", s.loadMemoriesHandler).Methods(http.MethodPost)

	router.Use(corsMiddleware)

	mux.Handle("/", router)
}

func (s *Service) startAutoSave() {
	if s.cfg.AutoSaveInterval <= 0 {
		return
	}

	go func() {
		ticker := time.NewTicker(s.cfg.AutoSaveInterval)
		defer ticker.Stop()

		for range ticker.C {
			if err := s.store.SaveToFile("memories.json"); err != nil {
				s.logger.Printf("[ERROR] Auto-save failed: %s", err)
			} else {
				s.logger.Printf("[INFO] Auto-saved %d memories", len(s.store.memories))
			}
		}
	}()
}

// HTTP Handlers

func (s *Service) healthHandler(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "jarvis-memory-service",
		"version": "1.0.0",
		"time":    time.Now().Unix(),
	})
}

func (s *Service) addMemoryHandler(w http.ResponseWriter, r *http.Request) {
	var memory Memory

	if err := json.NewDecoder(r.Body).Decode(&memory); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	// Validate
	if memory.Content == "" {
		http.Error(w, `{"error":"Content is required"}`, http.StatusBadRequest)
		return
	}
	if memory.Type == "" {
		memory.Type = "note"
	}
	if memory.Importance == 0 {
		memory.Importance = 5
	}

	id := s.store.Add(&memory)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"id":      id,
		"message": "Memory added successfully",
	})
}

func (s *Service) getMemoryHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	memory, exists := s.store.Get(id)
	if !exists {
		http.Error(w, `{"error":"Memory not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(memory)
}

func (s *Service) updateMemoryHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	if !s.store.Update(id, updates) {
		http.Error(w, `{"error":"Memory not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Memory updated successfully",
	})
}

func (s *Service) deleteMemoryHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	if !s.store.Delete(id) {
		http.Error(w, `{"error":"Memory not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Memory deleted successfully",
	})
}

func (s *Service) searchMemoriesHandler(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("query")
	memoryType := r.URL.Query().Get("type")
	tagsParam := r.URL.Query().Get("tags")

	var tags []string
	if tagsParam != "" {
		tags = strings.Split(tagsParam, ",")
	}

	results := s.store.Search(query, memoryType, tags)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

func (s *Service) getAllMemoriesHandler(w http.ResponseWriter, _ *http.Request) {
	memories := s.store.GetAll()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(memories)
}

func (s *Service) getStatsHandler(w http.ResponseWriter, _ *http.Request) {
	stats := s.store.GetStats()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func (s *Service) saveMemoriesHandler(w http.ResponseWriter, _ *http.Request) {
	if err := s.store.SaveToFile("memories.json"); err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to save: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Memories saved to disk",
	})
}

func (s *Service) loadMemoriesHandler(w http.ResponseWriter, _ *http.Request) {
	if err := s.store.LoadFromFile("memories.json"); err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to load: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Memories loaded from disk",
		"count":   len(s.store.memories),
	})
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
