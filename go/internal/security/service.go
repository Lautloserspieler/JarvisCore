package security

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/mux"
)

const defaultListenAddr = ":8081"
const defaultMaxLength = 50000

type Config struct {
	ListenAddr string
	MaxLength  int
}

func LoadConfig() Config {
	cfg := Config{
		ListenAddr: defaultListenAddr,
		MaxLength:  defaultMaxLength,
	}

	if value := strings.TrimSpace(os.Getenv("JARVIS_SECURITY_ADDR")); value != "" {
		cfg.ListenAddr = value
	}
	if value := strings.TrimSpace(os.Getenv("JARVIS_SECURITY_MAX_LENGTH")); value != "" {
		if parsed, err := strconv.Atoi(value); err == nil && parsed > 0 {
			cfg.MaxLength = parsed
		}
	}

	return cfg
}

// Dangerous patterns that indicate injection attempts.
var dangerousPatterns = []*regexp.Regexp{
	// System prompt manipulation
	regexp.MustCompile(`(?i)(system\s*:|ignore\s+previous|forget\s+that|pretend\s+you\s+are)`),
	regexp.MustCompile(`(?i)(new\s+instructions|override\s+instructions|disregard)`),

	// Code execution attempts
	regexp.MustCompile(`(?i)(execute|eval|__import__|subprocess|os\.system)`),
	regexp.MustCompile(`(?i)(exec\s*\(|eval\s*\(|compile\s*\()`),

	// Sensitive data extraction
	regexp.MustCompile(`(?i)(password|secret|token|api[_-]?key|credentials)`),
	regexp.MustCompile(`(?i)(private[_-]?key|access[_-]?token|auth[_-]?token)`),

	// Injection patterns
	regexp.MustCompile(`(?i)(sql\s+injection|command\s+injection|code\s+injection)`),
	regexp.MustCompile(`(?i)(\bUNION\s+SELECT|DROP\s+TABLE|DELETE\s+FROM)`),

	// Path traversal
	regexp.MustCompile(`\.\.[\\/]`),
	regexp.MustCompile(`(?i)(\.\.%2f|\.\.%5c)`),

	// Jailbreak attempts
	regexp.MustCompile(`(?i)(DAN\s+mode|developer\s+mode|god\s+mode)`),
	regexp.MustCompile(`(?i)(unrestricted|uncensored|no\s+filter)`),
}

// Suspicious strings.
var suspiciousStrings = []string{
	"<!--", "-->",
	"{{", "}}",
	"${", "}",
	"\\x", "\\u",
	"\x00",
	"<script>", "</script>",
	"javascript:",
	"data:text/html",
	"onerror=", "onload=",
}

// Request/Response Models.
type ValidateRequest struct {
	Input  string `json:"input"`
	Strict bool   `json:"strict"`
}

type ValidateResponse struct {
	IsSafe        bool     `json:"is_safe"`
	CleanedInput  string   `json:"cleaned_input"`
	Warnings      []string `json:"warnings"`
	Severity      string   `json:"severity"`
	Rejected      bool     `json:"rejected"`
	RejectedCount int      `json:"rejected_count"`
}

type SanitizeRequest struct {
	Output string `json:"output"`
}

type SanitizeResponse struct {
	Sanitized string   `json:"sanitized"`
	Removed   []string `json:"removed"`
}

type Stats struct {
	TotalValidations int            `json:"total_validations"`
	Rejected         int            `json:"rejected"`
	Warnings         map[string]int `json:"warnings"`
}

// PromptValidator.
type PromptValidator struct {
	maxLength int
	stats     *Stats
	mu        *sync.Mutex
}

func NewPromptValidator(maxLength int, stats *Stats, mu *sync.Mutex) *PromptValidator {
	return &PromptValidator{
		maxLength: maxLength,
		stats:     stats,
		mu:        mu,
	}
}

func (v *PromptValidator) Validate(input string, strict bool) ValidateResponse {
	warnings := []string{}
	cleanedInput := input
	severity := "low"

	// Check length
	if len(input) > v.maxLength {
		warnings = append(warnings, fmt.Sprintf("Input exceeds maximum length (%d chars)", v.maxLength))
		cleanedInput = cleanedInput[:v.maxLength]
		severity = "medium"
	}

	// Check for dangerous patterns
	for _, pattern := range dangerousPatterns {
		if pattern.MatchString(input) {
			warning := fmt.Sprintf("Detected injection pattern: %s", pattern.String())
			warnings = append(warnings, warning)
			v.incrementWarning("dangerous_pattern")
			severity = "critical"
		}
	}

	// Check for suspicious strings
	for _, suspicious := range suspiciousStrings {
		if strings.Contains(input, suspicious) {
			warnings = append(warnings, fmt.Sprintf("Detected suspicious string: %s", suspicious))
			cleanedInput = strings.ReplaceAll(cleanedInput, suspicious, "")
			v.incrementWarning("suspicious_string")
			if severity == "low" {
				severity = "medium"
			}
		}
	}

	// Check for excessive character repetition (e.g., "aaaaaaa..." to DoS)
	repeatPattern := regexp.MustCompile(`(.)\1{100,}`)
	if repeatPattern.MatchString(input) {
		warnings = append(warnings, "Detected excessive character repetition")
		v.incrementWarning("repetition")
		if severity == "low" {
			severity = "medium"
		}
	}

	// Check for base64 encoding attempts (often used to hide payloads)
	base64Pattern := regexp.MustCompile(`(?i)[A-Za-z0-9+/]{40,}={0,2}`)
	if base64Pattern.MatchString(input) {
		warnings = append(warnings, "Detected potential base64 encoded payload")
		v.incrementWarning("base64")
	}

	// Check for unicode/encoding tricks
	if strings.Contains(input, "\\u") || strings.Contains(input, "\\x") {
		warnings = append(warnings, "Detected unicode/hex encoding")
		v.incrementWarning("encoding")
	}

	// Determine if safe
	isSafe := len(warnings) == 0 || (!strict && severity != "critical")
	rejected := !isSafe

	if rejected {
		v.mu.Lock()
		v.stats.Rejected++
		v.mu.Unlock()
	}

	return ValidateResponse{
		IsSafe:        isSafe,
		CleanedInput:  cleanedInput,
		Warnings:      warnings,
		Severity:      severity,
		Rejected:      rejected,
		RejectedCount: v.stats.Rejected,
	}
}

func (v *PromptValidator) incrementWarning(key string) {
	v.mu.Lock()
	v.stats.Warnings[key]++
	v.mu.Unlock()
}

func (v *PromptValidator) SanitizeOutput(output string) SanitizeResponse {
	removed := []string{}
	sanitized := output

	// Remove potential code execution attempts in output
	codePatterns := []string{
		"exec(", "eval(", "__import__(",
		"subprocess.", "os.system(",
		"open(", "read(", "write(",
	}

	for _, pattern := range codePatterns {
		if strings.Contains(sanitized, pattern) {
			sanitized = strings.ReplaceAll(sanitized, pattern, "[REDACTED]")
			removed = append(removed, pattern)
		}
	}

	// Remove potential XSS in output
	xssPatterns := []string{
		"<script", "</script>",
		"javascript:",
		"onerror=", "onload=",
	}

	for _, pattern := range xssPatterns {
		if strings.Contains(strings.ToLower(sanitized), strings.ToLower(pattern)) {
			sanitized = strings.ReplaceAll(sanitized, pattern, "")
			removed = append(removed, pattern)
		}
	}

	return SanitizeResponse{
		Sanitized: sanitized,
		Removed:   removed,
	}
}

type Service struct {
	cfg       Config
	logger    *log.Logger
	stats     Stats
	statsLock sync.Mutex
}

func NewService(cfg Config, logger *log.Logger) *Service {
	if logger == nil {
		logger = log.New(os.Stdout, "[security] ", log.LstdFlags|log.LUTC)
	}

	return &Service{
		cfg:    cfg,
		logger: logger,
		stats: Stats{
			Warnings: make(map[string]int),
		},
	}
}

func Listen(addr string) (net.Listener, error) {
	return net.Listen("tcp", addr)
}

func (s *Service) Routes(mux *http.ServeMux) {
	router := mux.NewRouter()

	router.HandleFunc("/health", s.healthHandler).Methods(http.MethodGet)
	router.HandleFunc("/api/security/validate", s.validateHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/security/sanitize", s.sanitizeHandler).Methods(http.MethodPost)
	router.HandleFunc("/api/security/stats", s.statsHandler).Methods(http.MethodGet)

	router.Use(corsMiddleware)

	mux.Handle("/", router)
}

// HTTP Handlers

func (s *Service) healthHandler(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "jarvis-security-service",
		"version": "1.0.0",
		"time":    time.Now().Unix(),
	})
}

func (s *Service) validateHandler(w http.ResponseWriter, r *http.Request) {
	var req ValidateRequest

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	s.statsLock.Lock()
	s.stats.TotalValidations++
	s.statsLock.Unlock()

	validator := NewPromptValidator(s.cfg.MaxLength, &s.stats, &s.statsLock)
	result := validator.Validate(req.Input, req.Strict)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (s *Service) sanitizeHandler(w http.ResponseWriter, r *http.Request) {
	var req SanitizeRequest

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	validator := NewPromptValidator(s.cfg.MaxLength, &s.stats, &s.statsLock)
	result := validator.SanitizeOutput(req.Output)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (s *Service) statsHandler(w http.ResponseWriter, _ *http.Request) {
	s.statsLock.Lock()
	statsCopy := s.stats
	s.statsLock.Unlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(statsCopy)
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}
