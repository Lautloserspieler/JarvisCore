package memory

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// Entry beschreibt einen Memory-Eintrag.
type Entry struct {
	Key        string     `json:"key"`
	Value      any        `json:"value"`
	Category   string     `json:"category,omitempty"`
	Tags       []string   `json:"tags,omitempty"`
	Importance float64    `json:"importance,omitempty"`
	ExpiresAt  *time.Time `json:"expires_at,omitempty"`
	CreatedAt  time.Time  `json:"created_at"`
	UpdatedAt  time.Time  `json:"updated_at"`
}

// Store kapselt die persistente Ablage.
type Store struct {
	mu      sync.RWMutex
	entries map[string]Entry
	path    string
}

// NewStore baut einen Store und lädt ggf. vorhandene Daten.
func NewStore(path string) (*Store, error) {
	entries := make(map[string]Entry)
	if path != "" {
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return nil, err
		}
		if _, err := os.Stat(path); err == nil {
			if err := loadFromFile(path, entries); err != nil {
				return nil, err
			}
		}
	}
	return &Store{entries: entries, path: path}, nil
}

// Save speichert oder aktualisiert einen Eintrag.
func (s *Store) Save(e Entry) error {
	if e.Key == "" {
		return errors.New("key required")
	}
	now := time.Now().UTC()
	s.mu.Lock()
	defer s.mu.Unlock()
	s.removeExpiredLocked(now)
	existing, ok := s.entries[e.Key]
	if !ok {
		if e.CreatedAt.IsZero() {
			e.CreatedAt = now
		}
	} else {
		if e.CreatedAt.IsZero() {
			e.CreatedAt = existing.CreatedAt
		}
	}
	if e.UpdatedAt.IsZero() {
		e.UpdatedAt = now
	}
	s.entries[e.Key] = e
	return s.persist()
}

// Get liefert einen Eintrag, sofern nicht abgelaufen.
func (s *Store) Get(key string) (Entry, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	entry, ok := s.entries[key]
	if !ok {
		return Entry{}, false
	}
	if entry.ExpiresAt != nil && time.Now().UTC().After(*entry.ExpiresAt) {
		return Entry{}, false
	}
	return entry, true
}

// Delete entfernt einen Eintrag.
func (s *Store) Delete(key string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.entries[key]; !ok {
		return false
	}
	delete(s.entries, key)
	_ = s.persist()
	return true
}

// Search sucht nach Query/Category und begrenzt auf limit.
func (s *Store) Search(query, category string, limit int) []Entry {
	s.mu.RLock()
	defer s.mu.RUnlock()
	query = strings.ToLower(strings.TrimSpace(query))
	category = strings.ToLower(strings.TrimSpace(category))
	if limit <= 0 {
		limit = 10
	}
	results := make([]Entry, 0, limit)
	now := time.Now().UTC()
	for _, e := range s.entries {
		if e.ExpiresAt != nil && now.After(*e.ExpiresAt) {
			continue
		}
		if category != "" && strings.ToLower(e.Category) != category {
			continue
		}
		if query == "" || strings.Contains(strings.ToLower(e.Key), query) || strings.Contains(toString(e.Value), query) {
			results = append(results, e)
			if len(results) >= limit {
				break
			}
		}
	}
	return results
}

func toString(v any) string {
	switch t := v.(type) {
	case string:
		return t
	default:
		data, _ := json.Marshal(t)
		return strings.ToLower(string(data))
	}
}

func (s *Store) removeExpiredLocked(now time.Time) {
	for k, v := range s.entries {
		if v.ExpiresAt != nil && now.After(*v.ExpiresAt) {
			delete(s.entries, k)
		}
	}
}

func loadFromFile(path string, target map[string]Entry) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var entries []Entry
	if err := json.Unmarshal(data, &entries); err != nil {
		return err
	}
	for _, e := range entries {
		target[e.Key] = e
	}
	return nil
}

func (s *Store) persist() error {
	if s.path == "" {
		return nil
	}
	list := make([]Entry, 0, len(s.entries))
	for _, e := range s.entries {
		list = append(list, e)
	}
	data, err := json.MarshalIndent(list, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(s.path, data, 0o644)
}
