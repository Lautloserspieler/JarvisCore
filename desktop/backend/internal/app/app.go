package app

import (
	"context"
	"jarviscore/desktop/internal/bridge"
	"log"
)

// App struct
type App struct {
	ctx    context.Context
	bridge *bridge.JarvisCoreBridge
}

// NewApp erstellt neue App-Instanz
func NewApp() *App {
	return &App{}
}

// Startup wird beim App-Start aufgerufen
func (a *App) Startup(ctx context.Context) {
	a.ctx = ctx
	log.Println("🚀 J.A.R.V.I.S. Desktop startet...")
	
	// Bridge zu JarvisCore Python Backend
	a.bridge = bridge.NewJarvisCoreBridge("http://127.0.0.1:5050")
	
	log.Println("✅ J.A.R.V.I.S. Desktop bereit!")
}

// Shutdown wird beim Beenden aufgerufen
func (a *App) Shutdown(ctx context.Context) {
	log.Println("🛑 J.A.R.V.I.S. Desktop wird beendet...")
}

// ===== Frontend API Methods =====

// ProcessCommand sendet Befehl an JarvisCore
func (a *App) ProcessCommand(text string) (string, error) {
	return a.bridge.SendMessage(text)
}

// GetSystemStatus holt System-Metriken von JarvisCore
func (a *App) GetSystemStatus() (map[string]interface{}, error) {
	return a.bridge.GetSystemMetrics()
}

// GetConversationHistory holt Chat-Verlauf
func (a *App) GetConversationHistory(limit int) ([]map[string]interface{}, error) {
	return a.bridge.GetHistory(limit)
}

// ListModels holt verfügbare Modelle
func (a *App) ListModels() ([]map[string]interface{}, error) {
	return a.bridge.GetModels()
}

// LoadModel lädt ein Modell
func (a *App) LoadModel(modelKey string) error {
	return a.bridge.LoadModel(modelKey)
}

// GetPlugins holt Plugin-Liste
func (a *App) GetPlugins() ([]map[string]interface{}, error) {
	return a.bridge.GetPlugins()
}

// TogglePlugin aktiviert/deaktiviert Plugin
func (a *App) TogglePlugin(pluginName string, enabled bool) error {
	return a.bridge.TogglePlugin(pluginName, enabled)
}
