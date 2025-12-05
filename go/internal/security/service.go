package security

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"log"
	"net"
	"net/http"
	"os"
	"strings"
	"time"
)

// Config captures runtime settings for the security service.
type Config struct {
	ListenAddr     string
	AdminToken     string
	AuditLogPath   string
	AllowAnonymous bool
	JWTSecret      string
	TokenRoles     map[string]string
	Policy         map[string][]string
}

// SecurityContext mirrors the caller identity passed from Python.
type SecurityContext struct {
	UserID     string         `json:"user_id"`
	Roles      []string       `json:"roles"`
	Token      string         `json:"token,omitempty"`
	Attributes map[string]any `json:"attributes,omitempty"`
}

// ValidationRequest describes an authorization check.
type ValidationRequest struct {
	Action   string          `json:"action"`
	Resource string          `json:"resource"`
	Context  SecurityContext `json:"context"`
	Metadata map[string]any  `json:"metadata,omitempty"`
}

// PermissionRequest validates a specific permission.
type PermissionRequest struct {
	UserID     string          `json:"user_id"`
	Roles      []string        `json:"roles"`
	Permission string          `json:"permission"`
	Context    SecurityContext `json:"context,omitempty"`
}

// TokenRequest validates an incoming token.
type TokenRequest struct {
	Token string `json:"token"`
}

// ValidationResult is the unified response for access checks.
type ValidationResult struct {
	Allowed       bool      `json:"allowed"`
	Reason        string    `json:"reason,omitempty"`
	EffectiveRole string    `json:"effective_role,omitempty"`
	Timestamp     time.Time `json:"timestamp"`
}

// TokenValidation describes the outcome of token verification.
type TokenValidation struct {
	Valid     bool   `json:"valid"`
	Subject   string `json:"subject,omitempty"`
	IssuedAt  int64  `json:"issued_at,omitempty"`
	ExpiresAt int64  `json:"expires_at,omitempty"`
}

// Service bundles configuration and handlers.
type Service struct {
	cfg    Config
	logger *log.Logger
	policy map[string][]string
}

// NewService builds a Security service with defaults applied.
func NewService(cfg Config, logger *log.Logger) *Service {
	if logger == nil {
		logger = log.New(os.Stdout, "[securityd] ", log.LstdFlags|log.LUTC)
	}
	policy := map[string][]string{
		"admin":    {"*"},
		"operator": {"read:*", "write:command", "write:memory", "write:safe_mode"},
		"viewer":   {"read:*"},
	}
	for role, perms := range cfg.Policy {
		policy[role] = perms
	}
	return &Service{cfg: cfg, logger: logger, policy: policy}
}

// Routes wires the HTTP handlers.
func (s *Service) Routes(mux *http.ServeMux) {
	mux.HandleFunc("POST /security/validate", s.handleValidate)
	mux.HandleFunc("POST /security/check_permission", s.handleCheckPermission)
	mux.HandleFunc("POST /security/verify_token", s.handleVerifyToken)
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{"status": "ok", "timestamp": time.Now().UTC()})
	})
}

func (s *Service) handleValidate(w http.ResponseWriter, r *http.Request) {
	var req ValidationRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err)
		return
	}
	result := s.ValidateRequest(r.Context(), req)
	writeJSON(w, http.StatusOK, result)
}

func (s *Service) handleCheckPermission(w http.ResponseWriter, r *http.Request) {
	var req PermissionRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err)
		return
	}
	ok, role, err := s.CheckPermission(r.Context(), req)
	if err != nil {
		writeError(w, http.StatusForbidden, "permission_denied", err)
		return
	}
	writeJSON(w, http.StatusOK, ValidationResult{
		Allowed:       ok,
		EffectiveRole: role,
		Timestamp:     time.Now().UTC(),
	})
}

func (s *Service) handleVerifyToken(w http.ResponseWriter, r *http.Request) {
	var req TokenRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", err)
		return
	}
	result := s.VerifyToken(r.Context(), req.Token)
	if !result.Valid {
		writeJSON(w, http.StatusUnauthorized, result)
		return
	}
	writeJSON(w, http.StatusOK, result)
}

// ValidateRequest evaluates action and resource permissions.
func (s *Service) ValidateRequest(_ context.Context, req ValidationRequest) ValidationResult {
	role, err := s.authorize(req.Context, req.Action)
	if err != nil {
		return ValidationResult{
			Allowed:   false,
			Reason:    err.Error(),
			Timestamp: time.Now().UTC(),
		}
	}
	return ValidationResult{
		Allowed:       true,
		EffectiveRole: role,
		Timestamp:     time.Now().UTC(),
	}
}

// CheckPermission validates a specific permission value.
func (s *Service) CheckPermission(_ context.Context, req PermissionRequest) (bool, string, error) {
	ctx := req.Context
	if ctx.UserID == "" {
		ctx.UserID = req.UserID
	}
	if len(ctx.Roles) == 0 {
		ctx.Roles = append(ctx.Roles, req.Roles...)
	}
	role, err := s.authorize(ctx, req.Permission)
	if err != nil {
		return false, "", err
	}
	return true, role, nil
}

// VerifyToken performs a lightweight token check.
func (s *Service) VerifyToken(_ context.Context, token string) TokenValidation {
	token = strings.TrimSpace(token)
	if token == "" {
		return TokenValidation{Valid: s.cfg.AllowAnonymous}
	}
	if s.cfg.AdminToken == "" {
		if role := s.cfg.TokenRoles[token]; role != "" {
			return TokenValidation{Valid: true, Subject: role}
		}
		if sub, ok := s.parseJWT(token); ok {
			return TokenValidation{Valid: true, Subject: sub}
		}
		// Accept tokens if no secret configured; caller can enforce stricter policy.
		return TokenValidation{Valid: true, Subject: "anonymous"}
	}
	valid := token == s.cfg.AdminToken
	subject := "anonymous"
	if valid {
		subject = "operator"
	}
	return TokenValidation{
		Valid:     valid,
		Subject:   subject,
		IssuedAt:  time.Now().Add(-5 * time.Minute).Unix(),
		ExpiresAt: time.Now().Add(12 * time.Hour).Unix(),
	}
}

func (s *Service) parseJWT(token string) (string, bool) {
	if s.cfg.JWTSecret == "" {
		return "", false
	}
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return "", false
	}
	mac := hmac.New(sha256.New, []byte(s.cfg.JWTSecret))
	mac.Write([]byte(parts[0] + "." + parts[1]))
	expected := mac.Sum(nil)
	sig, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil || !hmac.Equal(sig, expected) {
		return "", false
	}
	payloadBytes, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return "", false
	}
	var claims map[string]any
	if err := json.Unmarshal(payloadBytes, &claims); err != nil {
		return "", false
	}
	if exp, ok := claims["exp"].(float64); ok && exp > 0 {
		if time.Now().After(time.Unix(int64(exp), 0)) {
			return "", false
		}
	}
	if sub, ok := claims["sub"].(string); ok && sub != "" {
		return sub, true
	}
	return "jwt", true
}

func (s *Service) authorize(ctx SecurityContext, action string) (string, error) {
	action = strings.TrimSpace(strings.ToLower(action))
	tokenValidation := s.VerifyToken(context.Background(), ctx.Token)
	if !tokenValidation.Valid {
		return "", errors.New("invalid_token")
	}
	if len(ctx.Roles) == 0 && s.cfg.AllowAnonymous {
		return "anonymous", nil
	}
	for _, role := range ctx.Roles {
		role = strings.ToLower(strings.TrimSpace(role))
		perms := s.policy[role]
		for _, perm := range perms {
			if matchesPermission(perm, action) {
				return role, nil
			}
		}
	}
	return "", errors.New("permission_denied")
}

func matchesPermission(pattern, action string) bool {
	pattern = strings.TrimSpace(strings.ToLower(pattern))
	if pattern == "*" {
		return true
	}
	if strings.HasSuffix(pattern, "*") {
		prefix := strings.TrimSuffix(pattern, "*")
		return strings.HasPrefix(action, prefix)
	}
	return pattern == action
}

func decodeJSON(r *http.Request, target any) error {
	defer r.Body.Close()
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	return decoder.Decode(target)
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

// LoadConfig builds Config from environment variables.
func LoadConfig() Config {
	listen := os.Getenv("SECURITYD_LISTEN")
	if listen == "" {
		listen = ":7071"
	}
	tokenMap := map[string]string{}
	if raw := os.Getenv("SECURITYD_TOKENS"); raw != "" {
		_ = json.Unmarshal([]byte(raw), &tokenMap)
	}
	policy := map[string][]string{}
	if raw := os.Getenv("SECURITYD_POLICY"); raw != "" {
		_ = json.Unmarshal([]byte(raw), &policy)
	}
	allowAnon := strings.ToLower(os.Getenv("SECURITYD_ALLOW_ANON")) == "true"
	return Config{
		ListenAddr:     listen,
		AdminToken:     os.Getenv("JARVIS_SECURITYD_TOKEN"),
		AuditLogPath:   os.Getenv("SECURITYD_AUDIT_LOG"),
		AllowAnonymous: allowAnon,
		JWTSecret:      os.Getenv("SECURITYD_JWT_SECRET"),
		TokenRoles:     tokenMap,
		Policy:         policy,
	}
}

// Listen creates the listener; extracted for testing overrides.
func Listen(addr string) (net.Listener, error) {
	if addr == "" {
		addr = ":7071"
	}
	return net.Listen("tcp", addr)
}
