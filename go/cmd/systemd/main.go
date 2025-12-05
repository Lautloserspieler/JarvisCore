package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"jarviscore/go/internal/system"
)

func main() {
	cfg := system.LoadConfig()
	logger := log.New(os.Stdout, "[systemd] ", log.LstdFlags|log.LUTC)

	svc := system.NewService(cfg, logger)
	mux := http.NewServeMux()
	svc.Routes(mux)

	server := &http.Server{
		Addr:         cfg.ListenAddr,
		Handler:      withLogging(logger, mux),
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 15 * time.Second,
	}

	go func() {
		logger.Printf("systemd lauscht auf %s", cfg.ListenAddr)
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
	logger.Println("systemd gestoppt")
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
		logger.Printf("%s %s %s", r.Method, r.URL.Path, time.Since(start))
	})
}
