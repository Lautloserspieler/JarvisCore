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

// ===== Knowledge Base APIs =====

// GetKnowledgeStats holt Knowledge Base Statistiken
func (a *App) GetKnowledgeStats() (map[string]interface{}, error) {
	return a.bridge.Get("/api/knowledge/stats")
}

// ===== Memory System APIs =====

// GetMemory holt Memory Snapshot mit optionaler Suche
func (a *App) GetMemory(query string) (map[string]interface{}, error) {
	url := "/api/memory"
	if query != "" {
		url += "?q=" + query
	}
	return a.bridge.Get(url)
}

// ===== Logs APIs =====

// GetLogs holt System-Logs
func (a *App) GetLogs(queryParams string) (map[string]interface{}, error) {
	url := "/api/logs"
	if queryParams != "" {
		url += "?" + queryParams
	}
	return a.bridge.Get(url)
}

// ClearLogs löscht alle Logs
func (a *App) ClearLogs() error {
	_, err := a.bridge.Post("/api/logs/clear", nil)
	return err
}

// ===== Training APIs =====

// GetTraining holt Training Status und Daten
func (a *App) GetTraining() (map[string]interface{}, error) {
	return a.bridge.Get("/api/training")
}

// RunTrainingCycle startet einen Training-Zyklus
func (a *App) RunTrainingCycle() error {
	_, err := a.bridge.Get("/api/training/run")
	if err == nil {
		a.BroadcastMessage("training_started", map[string]interface{}{
			"status": "running",
		})
	}
	return err
}

// ===== Custom Commands APIs =====

// GetCommands holt benutzerdefinierte Befehle
func (a *App) GetCommands() (map[string]interface{}, error) {
	return a.bridge.Get("/api/commands")
}

// AddCustomCommand fügt benutzerdefinierten Befehl hinzu
func (a *App) AddCustomCommand(pattern, response string) error {
	payload := map[string]string{
		"pattern":  pattern,
		"response": response,
	}
	_, err := a.bridge.Post("/api/commands", payload)
	if err == nil {
		a.BroadcastMessage("command_added", map[string]interface{}{
			"pattern": pattern,
		})
	}
	return err
}

// DeleteCustomCommand löscht benutzerdefinierten Befehl
func (a *App) DeleteCustomCommand(pattern string) error {
	payload := map[string]string{
		"pattern": pattern,
		"action":  "delete",
	}
	_, err := a.bridge.Post("/api/commands", payload)
	if err == nil {
		a.BroadcastMessage("command_deleted", map[string]interface{}{
			"pattern": pattern,
		})
	}
	return err
}

// ===== Audio Device APIs =====

// GetAudioDevices holt verfügbare Audio-Geräte
func (a *App) GetAudioDevices() (map[string]interface{}, error) {
	return a.bridge.Get("/api/audio/devices")
}

// SetAudioDevice setzt aktives Audio-Gerät
func (a *App) SetAudioDevice(index int) error {
	payload := map[string]int{"index": index}
	_, err := a.bridge.Post("/api/audio/devices", payload)
	return err
}

// MeasureAudioLevel misst Audio-Pegel
func (a *App) MeasureAudioLevel(duration float64) (map[string]interface{}, error) {
	payload := map[string]float64{"duration": duration}
	return a.bridge.Post("/api/audio/measure", payload)
}

// ===== Speech Control APIs =====

// GetSpeechStatus holt Speech Recognition Status
func (a *App) GetSpeechStatus() (map[string]interface{}, error) {
	return a.bridge.Get("/api/speech/status")
}

// ToggleListening startet/stoppt Speech Recognition
func (a *App) ToggleListening(action string) (map[string]interface{}, error) {
	payload := map[string]string{"action": action}
	return a.bridge.Post("/api/speech/control", payload)
}

// ToggleWakeWord aktiviert/deaktiviert Wake-Word Detection
func (a *App) ToggleWakeWord(enabled bool) (map[string]interface{}, error) {
	payload := map[string]interface{}{
		"action":  "wake_word",
		"enabled": enabled,
	}
	return a.bridge.Post("/api/speech/control", payload)
}
