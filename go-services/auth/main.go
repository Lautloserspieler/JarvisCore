package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/dgrijalva/jwt-go"
	"github.com/gorilla/mux"
	"golang.org/x/time/rate"
)

// Configuration
const PORT = ":8080"

var (
	secretKey   string
	apiKeysFile string
	lastPersist time.Time
)

// API Key Store (in-memory, TODO: move to database)
type APIKeyInfo struct {
	Key        string
	RateLimit  int // requests per minute
	Burst      int
	Enabled    bool
	CreatedAt  time.Time
	LastUsed   time.Time
}

var apiKeys = map[string]*APIKeyInfo{}

var apiKeysMutex sync.RWMutex

// Rate Limiter Store
type RateLimiterStore struct {
	limiters map[string]*rate.Limiter
	mu       sync.RWMutex
}

func NewRateLimiterStore() *RateLimiterStore {
	return &RateLimiterStore{
		limiters: make(map[string]*rate.Limiter),
	}
}

func (s *RateLimiterStore) GetLimiter(key string, rateLimit int, burst int) *rate.Limiter {
	s.mu.RLock()
	limiter, exists := s.limiters[key]
	s.mu.RUnlock()

	if !exists {
		s.mu.Lock()
		limiter = rate.NewLimiter(rate.Limit(rateLimit)/60, burst) // per second conversion
		s.limiters[key] = limiter
		s.mu.Unlock()
	}

	return limiter
}

var rateLimiterStore = NewRateLimiterStore()

type apiKeyEntry struct {
	Key       string `json:"key"`
	RateLimit int    `json:"rate_limit"`
	Burst     int    `json:"burst"`
	Enabled   bool   `json:"enabled"`
	CreatedAt string `json:"created_at"`
	LastUsed  string `json:"last_used,omitempty"`
}

func loadSecretKey() string {
	key := strings.TrimSpace(os.Getenv("JARVIS_AUTH_SECRET"))
	if key == "" {
		log.Fatal("[ERROR] JARVIS_AUTH_SECRET ist nicht gesetzt")
	}
	return key
}

func parseTime(value string, fallback time.Time) time.Time {
	if value == "" {
		return fallback
	}
	parsed, err := time.Parse(time.RFC3339, value)
	if err != nil {
		return fallback
	}
	return parsed
}

func loadAPIKeysFromFile(path string) ([]apiKeyEntry, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var entries []apiKeyEntry
	if err := json.Unmarshal(raw, &entries); err != nil {
		return nil, err
	}
	return entries, nil
}

func parseAPIKeysFromEnv(raw string) ([]apiKeyEntry, error) {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return nil, nil
	}
	var entries []apiKeyEntry
	if err := json.Unmarshal([]byte(raw), &entries); err == nil {
		return entries, nil
	}
	keys := strings.Split(raw, ",")
	entries = make([]apiKeyEntry, 0, len(keys))
	for _, key := range keys {
		trimmed := strings.TrimSpace(key)
		if trimmed == "" {
			continue
		}
		entries = append(entries, apiKeyEntry{
			Key:       trimmed,
			RateLimit: 60,
			Burst:     10,
			Enabled:   true,
			CreatedAt: time.Now().UTC().Format(time.RFC3339),
		})
	}
	return entries, nil
}

func persistAPIKeys(path string, entries []apiKeyEntry) error {
	if path == "" {
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	payload, err := json.MarshalIndent(entries, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, payload, 0o600)
}

func hydrateAPIKeys(entries []apiKeyEntry) {
	apiKeysMutex.Lock()
	defer apiKeysMutex.Unlock()
	apiKeys = map[string]*APIKeyInfo{}
	now := time.Now().UTC()
	for _, entry := range entries {
		if strings.TrimSpace(entry.Key) == "" {
			continue
		}
		rateLimit := entry.RateLimit
		if rateLimit <= 0 {
			rateLimit = 60
		}
		burst := entry.Burst
		if burst <= 0 {
			burst = 10
		}
		createdAt := parseTime(entry.CreatedAt, now)
		lastUsed := parseTime(entry.LastUsed, time.Time{})
		apiKeys[entry.Key] = &APIKeyInfo{
			Key:        entry.Key,
			RateLimit:  rateLimit,
			Burst:      burst,
			Enabled:    entry.Enabled,
			CreatedAt:  createdAt,
			LastUsed:   lastUsed,
		}
	}
}

func snapshotAPIKeys() []apiKeyEntry {
	apiKeysMutex.RLock()
	defer apiKeysMutex.RUnlock()
	entries := make([]apiKeyEntry, 0, len(apiKeys))
	for _, info := range apiKeys {
		entry := apiKeyEntry{
			Key:       info.Key,
			RateLimit: info.RateLimit,
			Burst:     info.Burst,
			Enabled:   info.Enabled,
			CreatedAt: info.CreatedAt.UTC().Format(time.RFC3339),
		}
		if !info.LastUsed.IsZero() {
			entry.LastUsed = info.LastUsed.UTC().Format(time.RFC3339)
		}
		entries = append(entries, entry)
	}
	return entries
}

func maybePersistAPIKeys() {
	if apiKeysFile == "" {
		return
	}
	if time.Since(lastPersist) < 30*time.Second {
		return
	}
	lastPersist = time.Now().UTC()
	if err := persistAPIKeys(apiKeysFile, snapshotAPIKeys()); err != nil {
		log.Printf("[WARN] API-Key-Datei konnte nicht gespeichert werden: %v", err)
	}
}

func loadAPIKeys() {
	apiKeysFile = strings.TrimSpace(os.Getenv("JARVIS_AUTH_KEYS_FILE"))
	if apiKeysFile == "" {
		apiKeysFile = filepath.Join("config", "auth_keys.json")
	}

	envKeys := strings.TrimSpace(os.Getenv("JARVIS_AUTH_KEYS"))
	entries, err := parseAPIKeysFromEnv(envKeys)
	if err != nil {
		log.Fatalf("[ERROR] Ungültiges JARVIS_AUTH_KEYS Format: %v", err)
	}

	if len(entries) == 0 {
		fileEntries, fileErr := loadAPIKeysFromFile(apiKeysFile)
		if fileErr == nil {
			entries = fileEntries
		} else if !os.IsNotExist(fileErr) {
			log.Fatalf("[ERROR] API-Key-Datei konnte nicht gelesen werden: %v", fileErr)
		}
	}

	if len(entries) == 0 {
		log.Fatal("[ERROR] Keine API-Keys konfiguriert. Setze JARVIS_AUTH_KEYS oder eine config/auth_keys.json.")
	}

	hydrateAPIKeys(entries)
}

// JWT Claims
type Claims struct {
	APIKey string `json:"api_key"`
	jwt.StandardClaims
}

// Middleware: Verify API Key
func VerifyAPIKey(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		apiKey := r.Header.Get("X-API-Key")

		if apiKey == "" {
			http.Error(w, `{"error":"API key required"}`, http.StatusUnauthorized)
			return
		}

		apiKeysMutex.RLock()
		keyInfo, exists := apiKeys[apiKey]
		apiKeysMutex.RUnlock()

		if !exists || !keyInfo.Enabled {
			http.Error(w, `{"error":"Invalid API key"}`, http.StatusUnauthorized)
			return
		}

		// Update last used
		apiKeysMutex.Lock()
		keyInfo.LastUsed = time.Now()
		apiKeysMutex.Unlock()
		maybePersistAPIKeys()

		// Add key info to context
		ctx := context.WithValue(r.Context(), "api_key_info", keyInfo)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// Middleware: Rate Limiting
func RateLimitMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		keyInfo := r.Context().Value("api_key_info").(*APIKeyInfo)

		limiter := rateLimiterStore.GetLimiter(keyInfo.Key, keyInfo.RateLimit, keyInfo.Burst)

		if !limiter.Allow() {
			w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", keyInfo.RateLimit))
			w.Header().Set("X-RateLimit-Remaining", "0")
			w.Header().Set("Retry-After", "60")
			http.Error(w, `{"error":"Rate limit exceeded. Try again later."}`, http.StatusTooManyRequests)
			return
		}

		w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", keyInfo.RateLimit))
		next.ServeHTTP(w, r)
	})
}

// JWT Token Generation
func GenerateToken(apiKey string) (string, error) {
	expirationTime := time.Now().Add(24 * time.Hour)
	claims := &Claims{
		APIKey: apiKey,
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: expirationTime.Unix(),
			IssuedAt:  time.Now().Unix(),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString([]byte(secretKey))

	return tokenString, err
}

// JWT Token Verification
func VerifyToken(tokenString string) (*Claims, error) {
	claims := &Claims{}

	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		return []byte(secretKey), nil
	})

	if err != nil {
		return nil, err
	}

	if !token.Valid {
		return nil, fmt.Errorf("invalid token")
	}

	return claims, nil
}

// Handlers

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "jarvis-auth-service",
		"version": "1.0.0",
		"time":    time.Now().Unix(),
	})
}

func generateTokenHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		APIKey string `json:"api_key"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	apiKeysMutex.RLock()
	keyInfo, exists := apiKeys[req.APIKey]
	apiKeysMutex.RUnlock()

	if !exists || !keyInfo.Enabled {
		http.Error(w, `{"error":"Invalid API key"}`, http.StatusUnauthorized)
		return
	}

	token, err := GenerateToken(req.APIKey)
	if err != nil {
		http.Error(w, `{"error":"Failed to generate token"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"token":      token,
		"expires_in": 86400, // 24 hours
	})
}

func verifyTokenHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Token string `json:"token"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	claims, err := VerifyToken(req.Token)
	if err != nil {
		http.Error(w, `{"error":"Invalid token"}`, http.StatusUnauthorized)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"valid":   true,
		"api_key": claims.APIKey,
	})
}

func createAPIKeyHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Key       string `json:"key"`
		RateLimit int    `json:"rate_limit"`
		Burst     int    `json:"burst"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	apiKeysMutex.Lock()
	apiKeys[req.Key] = &APIKeyInfo{
		Key:       req.Key,
		RateLimit: req.RateLimit,
		Burst:     req.Burst,
		Enabled:   true,
		CreatedAt: time.Now(),
	}
	apiKeysMutex.Unlock()

	if err := persistAPIKeys(apiKeysFile, snapshotAPIKeys()); err != nil {
		log.Printf("[WARN] API-Key-Datei konnte nicht gespeichert werden: %v", err)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "API key created",
		"key":     req.Key,
	})
}

func listAPIKeysHandler(w http.ResponseWriter, r *http.Request) {
	apiKeysMutex.RLock()
	defer apiKeysMutex.RUnlock()

	keys := make([]map[string]interface{}, 0, len(apiKeys))
	for _, info := range apiKeys {
		keys = append(keys, map[string]interface{}{
			"key":        info.Key,
			"rate_limit": info.RateLimit,
			"burst":      info.Burst,
			"enabled":    info.Enabled,
			"created_at": info.CreatedAt.Unix(),
			"last_used":  info.LastUsed.Unix(),
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(keys)
}

func protectedHandler(w http.ResponseWriter, r *http.Request) {
	keyInfo := r.Context().Value("api_key_info").(*APIKeyInfo)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message":    "Protected resource accessed successfully",
		"api_key":    keyInfo.Key,
		"rate_limit": keyInfo.RateLimit,
	})
}

func main() {
	secretKey = loadSecretKey()
	loadAPIKeys()

	r := mux.NewRouter()

	// Public endpoints
	r.HandleFunc("/health", healthHandler).Methods("GET")
	r.HandleFunc("/api/auth/token", generateTokenHandler).Methods("POST")
	r.HandleFunc("/api/auth/verify", verifyTokenHandler).Methods("POST")
	r.HandleFunc("/api/auth/keys/create", createAPIKeyHandler).Methods("POST")
	r.HandleFunc("/api/auth/keys", listAPIKeysHandler).Methods("GET")

	// Protected endpoints (with auth + rate limiting)
	protected := r.PathPrefix("/api/protected").Subrouter()
	protected.Use(VerifyAPIKey)
	protected.Use(RateLimitMiddleware)
	protected.HandleFunc("/test", protectedHandler).Methods("GET")

	// CORS middleware
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-API-Key, Authorization")

			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}

			next.ServeHTTP(w, r)
		})
	})

	log.Printf("[INFO] JARVIS Auth Service starting on %s", PORT)
	log.Printf("[INFO] Rate limiting enabled")
	log.Printf("[INFO] Available API keys: %d", len(apiKeys))

	if err := http.ListenAndServe(PORT, r); err != nil {
		log.Fatal(err)
	}
}
