package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"jarviscore/go/internal/speech"
)

func main() {
	cfg := speech.LoadConfig()
	logger := log.New(os.Stdout, "[speechtaskd] ", log.LstdFlags|log.LUTC)

	svc := speech.NewService(cfg, logger)
	mux := http.NewServeMux()
	svc.Routes(mux)

	server := &http.Server{
		Addr:         cfg.ListenAddr,
		Handler:      withLogging(logger, mux),
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 20 * time.Second,
	}

	go func() {
		logger.Printf("speechtaskd lauscht auf %s", sanitizeForLog(cfg.ListenAddr))
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatalf("HTTP-Server-Fehler: %v", err)
		}
	}()

	waitForSignal(logger)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		logger.Printf("Graceful Shutdown fehlgeschlagen: %v", err)
	}
	logger.Println("speechtaskd gestoppt")
}

func waitForSignal(logger *log.Logger) {
	sigC := make(chan os.Signal, 1)
	signal.Notify(sigC, syscall.SIGINT, syscall.SIGTERM)
	sig := <-sigC
	logger.Printf("Signal empfangen: %s", sig)
}

func withLogging(logger *log.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		method := strconv.QuoteToASCII(r.Method)
		path := strconv.QuoteToASCII(r.URL.EscapedPath())
		logger.Printf("request method=%s path=%s duration=%s", method, path, time.Since(start))
	})
}

func sanitizeForLog(value string) string {
	// Explicitly strip newline and carriage return to prevent log forging via line breaks.
	value = strings.ReplaceAll(value, "\n", "")
	value = strings.ReplaceAll(value, "\r", "")
	return strings.Map(func(r rune) rune {
		// Allow a conservative set of visible ASCII characters commonly used in URLs;
		// replace anything else (including control chars) with '?' to avoid log forging.
		if (r >= 'a' && r <= 'z') ||
			(r >= 'A' && r <= 'Z') ||
			(r >= '0' && r <= '9') ||
			strings.ContainsRune("-._~!$&'()*+,;=:@/?", r) {
			return r
		}
		return '?'
	}, value)
}
