package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"jarviscore/go/internal/security"
)

func main() {
	cfg := security.LoadConfig()
	logger := log.New(os.Stdout, "[securityd] ", log.LstdFlags|log.LUTC)

	svc := security.NewService(cfg, logger)
	mux := http.NewServeMux()
	svc.Routes(mux)

	server := &http.Server{
		Addr:         cfg.ListenAddr,
		Handler:      withLogging(logger, mux),
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 15 * time.Second,
	}

	listener, err := security.Listen(cfg.ListenAddr)
	if err != nil {
		logger.Fatalf("failed to listen on %s: %v", cfg.ListenAddr, err)
	}
	logger.Printf("securityd listening on %s", listener.Addr())

	go func() {
		if err := server.Serve(listener); err != nil && err != http.ErrServerClosed {
			logger.Fatalf("server error: %v", err)
		}
	}()

	waitForSignal(logger)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		logger.Printf("graceful shutdown failed: %v", err)
	}
	logger.Println("securityd stopped")
}

func waitForSignal(logger *log.Logger) {
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)
	sig := <-sigs
	logger.Printf("received signal: %s", sig)
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
