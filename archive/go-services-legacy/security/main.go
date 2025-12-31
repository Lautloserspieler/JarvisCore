package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/gorilla/mux"
)

const (
	PORT       = ":8081"
	MAX_LENGTH = 50000 // Max 50K characters
)

// Dangerous patterns that indicate injection attempts
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

// Suspicious strings
var suspiciousStrings = []string{
	"<!--", "-->",        // HTML comments
	"{{", "}}",          // Template injection
	"${", "}",           // Expression injection
	"\\x", "\\u",       // Encoding escape attempts
	"\x00",              // Null byte
	"<script>", "</script>", // XSS
	"javascript:",       // XSS
	"data:text/html",    // Data URI XSS
	"onerror=", "onload=", // Event handlers
}

// Request/Response Models
type ValidateRequest struct {
	Input string `json:"input"`
	Strict bool  `json:"strict"` // If true, reject on any warning
}

type ValidateResponse struct {
	IsSafe        bool     `json:"is_safe"`
	CleanedInput  string   `json:"cleaned_input"`
	Warnings      []string `json:"warnings"`
	Severity      string   `json:"severity"` // "low", "medium", "high", "critical"
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

var stats = Stats{
	Warnings: make(map[string]int),
}

// PromptValidator
type PromptValidator struct{}

func NewPromptValidator() *PromptValidator {
	return &PromptValidator{}
}

func (v *PromptValidator) Validate(input string, strict bool) ValidateResponse {
	warnings := []string{}
	cleanedInput := input
	severity := "low"

	// Check length
	if len(input) > MAX_LENGTH {
		warnings = append(warnings, fmt.Sprintf("Input exceeds maximum length (%d chars)", MAX_LENGTH))
		cleanedInput = cleanedInput[:MAX_LENGTH]
		severity = "medium"
	}

	// Check for dangerous patterns
	for _, pattern := range dangerousPatterns {
		if pattern.MatchString(input) {
			warning := fmt.Sprintf("Detected injection pattern: %s", pattern.String())
			warnings = append(warnings, warning)
			stats.Warnings["dangerous_pattern"]++
			severity = "critical"
		}
	}

	// Check for suspicious strings
	for _, suspicious := range suspiciousStrings {
		if strings.Contains(input, suspicious) {
			warnings = append(warnings, fmt.Sprintf("Detected suspicious string: %s", suspicious))
			cleanedInput = strings.ReplaceAll(cleanedInput, suspicious, "")
			stats.Warnings["suspicious_string"]++
			if severity == "low" {
				severity = "medium"
			}
		}
	}

	// Check for excessive character repetition (e.g., "aaaaaaa..." to DoS)
	repeatPattern := regexp.MustCompile(`(.)\1{100,}`)
	if repeatPattern.MatchString(input) {
		warnings = append(warnings, "Detected excessive character repetition")
		stats.Warnings["repetition"]++
		if severity == "low" {
			severity = "medium"
		}
	}

	// Check for base64 encoding attempts (often used to hide payloads)
	base64Pattern := regexp.MustCompile(`(?i)[A-Za-z0-9+/]{40,}={0,2}`)
	if base64Pattern.MatchString(input) {
		warnings = append(warnings, "Detected potential base64 encoded payload")
		stats.Warnings["base64"]++
	}

	// Check for unicode/encoding tricks
	if strings.Contains(input, "\u") || strings.Contains(input, "\x") {
		warnings = append(warnings, "Detected unicode/hex encoding")
		stats.Warnings["encoding"]++
	}

	// Determine if safe
	isSafe := len(warnings) == 0 || (!strict && severity != "critical")
	rejected := !isSafe

	if rejected {
		stats.Rejected++
	}

	return ValidateResponse{
		IsSafe:        isSafe,
		CleanedInput:  cleanedInput,
		Warnings:      warnings,
		Severity:      severity,
		Rejected:      rejected,
		RejectedCount: stats.Rejected,
	}
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

// HTTP Handlers

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "jarvis-security-service",
		"version": "1.0.0",
		"time":    time.Now().Unix(),
	})
}

func validateHandler(w http.ResponseWriter, r *http.Request) {
	var req ValidateRequest

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	validator := NewPromptValidator()
	result := validator.Validate(req.Input, req.Strict)

	stats.TotalValidations++

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func sanitizeHandler(w http.ResponseWriter, r *http.Request) {
	var req SanitizeRequest

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
		return
	}

	validator := NewPromptValidator()
	result := validator.SanitizeOutput(req.Output)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func statsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func main() {
	r := mux.NewRouter()

	// Endpoints
	r.HandleFunc("/health", healthHandler).Methods("GET")
	r.HandleFunc("/api/security/validate", validateHandler).Methods("POST")
	r.HandleFunc("/api/security/sanitize", sanitizeHandler).Methods("POST")
	r.HandleFunc("/api/security/stats", statsHandler).Methods("GET")

	// CORS
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}

			next.ServeHTTP(w, r)
		})
	})

	log.Printf("[INFO] JARVIS Security Service starting on %s", PORT)
	log.Printf("[INFO] Prompt injection protection enabled")
	log.Printf("[INFO] Monitoring %d dangerous patterns", len(dangerousPatterns))

	if err := http.ListenAndServe(PORT, r); err != nil {
		log.Fatal(err)
	}
}
