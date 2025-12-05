package app

import (
	"context"
	"jarviscore/desktop/internal/bridge"
	"jarviscore/desktop/internal/websocket"
	"log"
)

// App struct
type App struct {
	ctx    context.Context
	bridge *bridge.JarvisCoreBridge
	wsHub  *websocket.Hub
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
	
	// WebSocket Hub starten
	a.StartWebSocketHub()
	
	log.Println("✅ J.A.R.V.I.S. Desktop bereit!")
}

// Shutdown wird beim Beenden aufgerufen
func (a *App) Shutdown(ctx context.Context) {
	log.Println("🛑 J.A.R.V.I.S. Desktop wird beendet...")
}

// ===== Frontend API Methods =====

// ProcessCommand sendet Befehl an JarvisCore
func (a *App) ProcessCommand(text string) (string, error) {
	response, err := a.bridge.SendMessage(text)
	
	// Broadcast zu allen Clients
	if err == nil {
		a.BroadcastMessage("chat_message", map[string]interface{}{
			"role": "assistant",
			"text": response,
		})
	}
	
	return response, err
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
	err := a.bridge.LoadModel(modelKey)
	
	// Broadcast Model-Change
	if err == nil {
		a.BroadcastMessage("model_loaded", map[string]interface{}{
			"model": modelKey,
		})
	}
	
	return err
}

// GetPlugins holt Plugin-Liste
func (a *App) GetPlugins() ([]map[string]interface{}, error) {
	return a.bridge.GetPlugins()
}

// TogglePlugin aktiviert/deaktiviert Plugin
func (a *App) TogglePlugin(pluginName string, enabled bool) error {
	err := a.bridge.TogglePlugin(pluginName, enabled)
	
	// Broadcast Plugin-Change
	if err == nil {
		a.BroadcastMessage("plugin_toggled", map[string]interface{}{
			"plugin":  pluginName,
			"enabled": enabled,
		})
	}
	
	return err
}
