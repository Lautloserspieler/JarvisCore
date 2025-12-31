package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/mux"
)

const (
	PORT        = ":8082"
	STORAGE_DIR = "data/memories"
)

// Memory represents a single memory entry
type Memory struct {
	ID         string    `json:"id"`
	Content    string    `json:"content"`
	Type       string    `json:"type"` // "fact", "conversation", "note", "code"
	Tags       []string  `json:"tags"`
	Importance int       `json:"importance"` // 1-10
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
	References []string  `json:"references"` // IDs of related memories
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// MemoryStore manages all memories
type MemoryStore struct {
	memories map[string]*Memory
	mu       sync.RWMutex
}

func NewMemoryStore() *MemoryStore {
	return &MemoryStore{
		memories: make(map[string]*Memory),
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
	os.MkdirAll(STORAGE_DIR, 0755)

	filepath := fmt.Sprintf("%s/%s", STORAGE_DIR, filename)
	return os.WriteFile(filepath, data, 0644)
}

func (s *MemoryStore) LoadFromFile(filename string) error {
	filepath := fmt.Sprintf("%s/%s", STORAGE_DIR, filename)

	data, err := os.ReadFile(filepath)
	if err != nil {
		return err
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	return json.Unmarshal(data, &s.memories)
}

var store = NewMemoryStore()

// HTTP Handlers

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "jarvis-memory-service",
		"version": "1.0.0",
		"time":    time.Now().Unix(),
	})
}

func addMemoryHandler(w http.ResponseWriter, r *http.Request) {
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

	id := store.Add(&memory)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"id":      id,
		"message": "Memory added successfully",
	})
}

func getMemoryHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	memory, exists := store.Get(id)
	if !exists {
		http.Error(w, `{"error":"Memory not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(memory)
}

func updateMemoryHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	if !store.Update(id, updates) {
		http.Error(w, `{"error":"Memory not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Memory updated successfully",
	})
}

func deleteMemoryHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	if !store.Delete(id) {
		http.Error(w, `{"error":"Memory not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Memory deleted successfully",
	})
}

func searchMemoriesHandler(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("query")
	memoryType := r.URL.Query().Get("type")
	tagsParam := r.URL.Query().Get("tags")

	var tags []string
	if tagsParam != "" {
		tags = strings.Split(tagsParam, ",")
	}

	results := store.Search(query, memoryType, tags)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

func getAllMemoriesHandler(w http.ResponseWriter, r *http.Request) {
	memories := store.GetAll()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(memories)
}

func getStatsHandler(w http.ResponseWriter, r *http.Request) {
	stats := store.GetStats()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func saveMemoriesHandler(w http.ResponseWriter, r *http.Request) {
	if err := store.SaveToFile("memories.json"); err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to save: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Memories saved to disk",
	})
}

func loadMemoriesHandler(w http.ResponseWriter, r *http.Request) {
	if err := store.LoadFromFile("memories.json"); err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"Failed to load: %s"}`, err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Memories loaded from disk",
		"count":   len(store.memories),
	})
}

func main() {
	// Try to load existing memories
	if err := store.LoadFromFile("memories.json"); err != nil {
		log.Printf("[INFO] No existing memories found, starting fresh")
	} else {
		log.Printf("[INFO] Loaded %d memories from disk", len(store.memories))
	}

	// Auto-save every 5 minutes
	go func() {
		ticker := time.NewTicker(5 * time.Minute)
		defer ticker.Stop()

		for range ticker.C {
			if err := store.SaveToFile("memories.json"); err != nil {
				log.Printf("[ERROR] Auto-save failed: %s", err)
			} else {
				log.Printf("[INFO] Auto-saved %d memories", len(store.memories))
			}
		}
	}()

	r := mux.NewRouter()

	// Endpoints
	r.HandleFunc("/health", healthHandler).Methods("GET")
	r.HandleFunc("/api/memory", addMemoryHandler).Methods("POST")
	r.HandleFunc("/api/memory/{id}", getMemoryHandler).Methods("GET")
	r.HandleFunc("/api/memory/{id}", updateMemoryHandler).Methods("PUT")
	r.HandleFunc("/api/memory/{id}", deleteMemoryHandler).Methods("DELETE")
	r.HandleFunc("/api/memory/search", searchMemoriesHandler).Methods("GET")
	r.HandleFunc("/api/memory/all", getAllMemoriesHandler).Methods("GET")
	r.HandleFunc("/api/memory/stats", getStatsHandler).Methods("GET")
	r.HandleFunc("/api/memory/save", saveMemoriesHandler).Methods("POST")
	r.HandleFunc("/api/memory/load", loadMemoriesHandler).Methods("POST")

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

	log.Printf("[INFO] JARVIS Memory Service starting on %s", PORT)
	log.Printf("[INFO] Storage directory: %s", STORAGE_DIR)
	log.Printf("[INFO] Auto-save interval: 5 minutes")

	if err := http.ListenAndServe(PORT, r); err != nil {
		log.Fatal(err)
	}
}
