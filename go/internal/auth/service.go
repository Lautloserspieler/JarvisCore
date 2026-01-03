package auth

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

	"github.com/golang-jwt/jwt/v4"
	"github.com/gorilla/mux"
	"golang.org/x/time/rate"
)

const defaultListenAddr = ":8080"

// Configuration

type Config struct {
	ListenAddr  string
	SecretKey   string
	KeysFile    string
	KeysEnv     string
	AdminKey    string
	CORSOrigins string
}

func LoadConfig() (Config, error) {
	cfg := Config{
		ListenAddr:  defaultListenAddr,
		KeysFile:    filepath.Join("config", "auth_keys.json"),
		KeysEnv:     strings.TrimSpace(os.Getenv("JARVIS_AUTH_KEYS")),
		SecretKey:   strings.TrimSpace(os.Getenv("JARVIS_AUTH_SECRET")),
		AdminKey:    strings.TrimSpace(os.Getenv("JARVIS_AUTH_ADMIN_KEY")),
		CORSOrigins: strings.TrimSpace(os.Getenv("JARVIS_AUTH_CORS_ORIGINS")),
	}

	if value := strings.TrimSpace(os.Getenv("JARVIS_AUTH_ADDR")); value != "" {
		cfg.ListenAddr = value
	}
	if value := strings.TrimSpace(os.Getenv("JARVIS_AUTH_KEYS_FILE")); value != "" {
		cfg.KeysFile = value
	}

	if cfg.SecretKey == "" {
		return cfg, fmt.Errorf("JARVIS_AUTH_SECRET ist nicht gesetzt")
	}

	return cfg, nil
}

// API Key Store (in-memory, TODO: move to database)
type APIKeyInfo struct {
	Key       string
	RateLimit int // requests per minute
	Burst     int
	Enabled   bool
	CreatedAt time.Time
	LastUsed  time.Time
}

type contextKey string

const apiKeyInfoKey contextKey = "api_key_info"

var (
	secretKey    string
	apiKeysFile  string
	adminKey     string
	lastPersist  time.Time
	apiKeys      = map[string]*APIKeyInfo{}
	apiKeysMu    sync.RWMutex
	persistMu    sync.Mutex
	corsOrigins  map[string]struct{}
	allowAllCORS bool
)

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

func loadCORSOrigins(raw string) {
	corsOrigins = map[string]struct{}{}
	allowAllCORS = false
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return
	}
	for _, entry := range strings.Split(raw, ",") {
		origin := strings.TrimSpace(entry)
		if origin == "" {
			continue
		}
		if origin == "*" {
			allowAllCORS = true
		} else {
			corsOrigins[origin] = struct{}{}
		}
	}
}

func isAllowedOrigin(origin string) bool {
	if origin == "" {
		return false
	}
	if allowAllCORS {
		return true
	}
	_, ok := corsOrigins[origin]
	return ok
}

func isAdminRequest(r *http.Request) bool {
	if adminKey == "" {
		return false
	}
	headerKey := strings.TrimSpace(r.Header.Get("X-Admin-Key"))
	if headerKey == "" {
		authHeader := strings.TrimSpace(r.Header.Get("Authorization"))
		if strings.HasPrefix(strings.ToLower(authHeader), "bearer ") {
			headerKey = strings.TrimSpace(authHeader[7:])
		}
	}
	return headerKey != "" && headerKey == adminKey
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
	apiKeysMu.Lock()
	defer apiKeysMu.Unlock()
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
			Key:       entry.Key,
			RateLimit: rateLimit,
			Burst:     burst,
			Enabled:   entry.Enabled,
			CreatedAt: createdAt,
			LastUsed:  lastUsed,
		}
	}
}

func snapshotAPIKeys() []apiKeyEntry {
	apiKeysMu.RLock()
	defer apiKeysMu.RUnlock()
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

func maybePersistAPIKeys(logger *log.Logger) {
	if apiKeysFile == "" {
		return
	}
	persistMu.Lock()
	if time.Since(lastPersist) < 30*time.Second {
		persistMu.Unlock()
		return
	}
	lastPersist = time.Now().UTC()
	persistMu.Unlock()
	if err := persistAPIKeys(apiKeysFile, snapshotAPIKeys()); err != nil {
		logger.Printf("[WARN] API-Key-Datei konnte nicht gespeichert werden: %v", err)
	}
}

func loadAPIKeys(logger *log.Logger, cfg Config) error {
	apiKeysFile = cfg.KeysFile

	entries, err := parseAPIKeysFromEnv(cfg.KeysEnv)
	if err != nil {
		return fmt.Errorf("ungültiges JARVIS_AUTH_KEYS Format: %w", err)
	}

	if len(entries) == 0 {
		fileEntries, fileErr := loadAPIKeysFromFile(apiKeysFile)
		if fileErr == nil {
			entries = fileEntries
		} else if !os.IsNotExist(fileErr) {
			return fmt.Errorf("API-Key-Datei konnte nicht gelesen werden: %w", fileErr)
		}
	}

	if len(entries) == 0 {
		return fmt.Errorf("keine API-Keys konfiguriert. Setze JARVIS_AUTH_KEYS oder eine config/auth_keys.json")
	}

	hydrateAPIKeys(entries)
	return nil
}

// JWT Claims

type Claims struct {
	APIKey string `json:"api_key"`
	jwt.RegisteredClaims
}

// Middleware: Verify API Key
func VerifyAPIKey(logger *log.Logger) mux.MiddlewareFunc {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			apiKey := r.Header.Get("X-API-Key")

			if apiKey == "" {
				http.Error(w, `{"error":"API key required"}`, http.StatusUnauthorized)
				return
			}

			apiKeysMu.RLock()
			keyInfo, exists := apiKeys[apiKey]
			apiKeysMu.RUnlock()

			if !exists || !keyInfo.Enabled {
				http.Error(w, `{"error":"Invalid API key"}`, http.StatusUnauthorized)
				return
			}

			// Update last used
			apiKeysMu.Lock()
			keyInfo.LastUsed = time.Now()
			apiKeysMu.Unlock()
			maybePersistAPIKeys(logger)

			// Add key info to context
			ctx := context.WithValue(r.Context(), apiKeyInfoKey, keyInfo)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func apiKeyInfoFromContext(ctx context.Context) (*APIKeyInfo, bool) {
	info, ok := ctx.Value(apiKeyInfoKey).(*APIKeyInfo)
	if !ok || info == nil {
		return nil, false
	}
	return info, true
}

// Middleware: Rate Limiting
func RateLimitMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		keyInfo, ok := apiKeyInfoFromContext(r.Context())
		if !ok {
			http.Error(w, `{"error":"API key required"}`, http.StatusUnauthorized)
			return
		}

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
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(secretKey))
}

// JWT Token Verification
func VerifyToken(tokenString string) (*Claims, error) {
	claims := &Claims{}

	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		if token.Method.Alg() != jwt.SigningMethodHS256.Alg() {
			return nil, fmt.Errorf("unexpected signing method: %s", token.Method.Alg())
		}
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

type Service struct {
	cfg    Config
	logger *log.Logger
}

func NewService(cfg Config, logger *log.Logger) (*Service, error) {
	if logger == nil {
		logger = log.New(os.Stdout, "[auth] ", log.LstdFlags|log.LUTC)
	}

	secretKey = cfg.SecretKey
	adminKey = cfg.AdminKey
	loadCORSOrigins(cfg.CORSOrigins)
	if err := loadAPIKeys(logger, cfg); err != nil {
		return nil, err
	}

	logger.Printf("[INFO] Rate limiting enabled")
	logger.Printf("[INFO] Available API keys: %d", len(apiKeys))

	return &Service{cfg: cfg, logger: logger}, nil
}

func (s *Service) Routes(mux *http.ServeMux) {
	router := mux.NewRouter()

	// Public endpoints
	router.HandleFunc("/health", s.healthHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/auth/token", s.generateTokenHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/auth/verify", s.verifyTokenHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/auth/keys/create", s.createAPIKeyHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/auth/keys", s.listAPIKeysHandler).Methods(http.MethodGet)

	// Protected endpoints (with auth + rate limiting)
	protected := router.PathPrefix("/api/protected").Subrouter()
	protected.Use(VerifyAPIKey(s.logger))
	protected.Use(RateLimitMiddleware)
	protected.HandleFunc("/test", s.protectedHandler).Methods(http.MethodGet)

	// CORS middleware
	router.Use(corsMiddleware)

	mux.Handle("/", router)
}

// Handlers

func (s *Service) healthHandler(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "jarvis-auth-service",
		"version": "1.0.0",
		"time":    time.Now().Unix(),
	})
}

func (s *Service) generateTokenHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		APIKey string `json:"api_key"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	apiKeysMu.RLock()
	keyInfo, exists := apiKeys[req.APIKey]
	apiKeysMu.RUnlock()

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
		"expires_in": 86400,
	})
}

func (s *Service) verifyTokenHandler(w http.ResponseWriter, r *http.Request) {
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

func (s *Service) createAPIKeyHandler(w http.ResponseWriter, r *http.Request) {
	if !isAdminRequest(r) {
		http.Error(w, `{"error":"Admin access required"}`, http.StatusForbidden)
		return
	}
	var req struct {
		Key       string `json:"key"`
		RateLimit int    `json:"rate_limit"`
		Burst     int    `json:"burst"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	key := strings.TrimSpace(req.Key)
	if len(key) < 16 {
		http.Error(w, `{"error":"API key must be at least 16 characters"}`, http.StatusBadRequest)
		return
	}
	if req.RateLimit <= 0 {
		req.RateLimit = 60
	}
	if req.Burst <= 0 {
		req.Burst = 10
	}

	apiKeysMu.Lock()
	if _, exists := apiKeys[key]; exists {
		apiKeysMu.Unlock()
		http.Error(w, `{"error":"API key already exists"}`, http.StatusConflict)
		return
	}
	apiKeys[key] = &APIKeyInfo{
		Key:       key,
		RateLimit: req.RateLimit,
		Burst:     req.Burst,
		Enabled:   true,
		CreatedAt: time.Now(),
	}
	apiKeysMu.Unlock()

	if err := persistAPIKeys(apiKeysFile, snapshotAPIKeys()); err != nil {
		s.logger.Printf("[WARN] API-Key-Datei konnte nicht gespeichert werden: %v", err)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "API key created",
		"key":     key,
	})
}

func (s *Service) listAPIKeysHandler(w http.ResponseWriter, r *http.Request) {
	if !isAdminRequest(r) {
		http.Error(w, `{"error":"Admin access required"}`, http.StatusForbidden)
		return
	}
	apiKeysMu.RLock()
	defer apiKeysMu.RUnlock()

	keys := make([]map[string]interface{}, 0, len(apiKeys))
	for _, info := range apiKeys {
		maskedKey := info.Key
		if len(maskedKey) > 4 {
			maskedKey = fmt.Sprintf("****%s", maskedKey[len(maskedKey)-4:])
		}
		entry := map[string]interface{}{
			"key":        maskedKey,
			"rate_limit": info.RateLimit,
			"burst":      info.Burst,
			"enabled":    info.Enabled,
			"created_at": info.CreatedAt.Unix(),
		}
		if !info.LastUsed.IsZero() {
			entry["last_used"] = info.LastUsed.Unix()
		}
		keys = append(keys, entry)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(keys)
}

func (s *Service) protectedHandler(w http.ResponseWriter, r *http.Request) {
	keyInfo, ok := apiKeyInfoFromContext(r.Context())
	if !ok {
		http.Error(w, `{"error":"API key required"}`, http.StatusUnauthorized)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message":    "Protected resource accessed successfully",
		"api_key":    keyInfo.Key,
		"rate_limit": keyInfo.RateLimit,
	})
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if isAllowedOrigin(origin) {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Add("Vary", "Origin")
		} else if allowAllCORS {
			w.Header().Set("Access-Control-Allow-Origin", "*")
		}
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-API-Key, Authorization, X-Admin-Key")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}
