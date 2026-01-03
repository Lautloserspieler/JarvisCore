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

	"jarviscore/go/internal/gateway"
)

func main() {
	cfg := gateway.LoadConfig()
	logger := log.New(os.Stdout, "[gatewayd] ", log.LstdFlags|log.LUTC)

	srv := gateway.NewServer(cfg, logger)
	mux := http.NewServeMux()
	srv.Routes(mux)

	httpServer := &http.Server{
		Addr:         cfg.ListenAddr,
		Handler:      withLogging(logger, mux),
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 15 * time.Second,
	}

	stop := make(chan struct{})
	go srv.Hub().Run(stop)

	go func() {
		logger.Printf("gatewayd lauscht auf %s", sanitizeForLog(cfg.ListenAddr))
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatalf("HTTP-Server-Fehler: %v", err)
		}
	}()

	waitForSignal(logger)
	close(stop)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := httpServer.Shutdown(ctx); err != nil {
		logger.Printf("Graceful Shutdown fehlgeschlagen: %v", err)
	}
	logger.Println("gatewayd gestoppt")
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
	return strings.Map(func(r rune) rune {
		if r < 32 || r == 127 {
			return -1
		}
		return r
	}, value)
}
