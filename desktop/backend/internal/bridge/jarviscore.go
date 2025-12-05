package bridge

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// JarvisCoreBridge verbindet zu JarvisCore Python Backend
type JarvisCoreBridge struct {
	baseURL string
	client  *http.Client
	token   string
}

// NewJarvisCoreBridge erstellt neue Bridge-Instanz
func NewJarvisCoreBridge(baseURL string) *JarvisCoreBridge {
	return &JarvisCoreBridge{
		baseURL: baseURL,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
		token: "12345678", // Default Token, TODO: aus Config laden
	}
}

// SendMessage sendet Nachricht an JarvisCore Chat
func (b *JarvisCoreBridge) SendMessage(text string) (string, error) {
	payload := map[string]interface{}{
		"message": text,
		"token":   b.token,
	}
	
	resp, err := b.post("/api/chat", payload)
	if err != nil {
		return "", err
	}
	
	if response, ok := resp["response"].(string); ok {
		return response, nil
	}
	
	return "", fmt.Errorf("Ungültige Antwort")
}

// GetSystemMetrics holt System-Metriken
func (b *JarvisCoreBridge) GetSystemMetrics() (map[string]interface{}, error) {
	resp, err := b.get("/api/system/metrics")
	if err != nil {
		return nil, err
	}
	return resp, nil
}

// GetHistory holt Chat-Verlauf
func (b *JarvisCoreBridge) GetHistory(limit int) ([]map[string]interface{}, error) {
	url := fmt.Sprintf("/api/chat/history?limit=%d", limit)
	resp, err := b.get(url)
	if err != nil {
		return nil, err
	}
	
	if history, ok := resp["history"].([]interface{}); ok {
		result := make([]map[string]interface{}, 0)
		for _, item := range history {
			if entry, ok := item.(map[string]interface{}); ok {
				result = append(result, entry)
			}
		}
		return result, nil
	}
	
	return []map[string]interface{}{}, nil
}

// GetModels holt verfügbare Modelle
func (b *JarvisCoreBridge) GetModels() ([]map[string]interface{}, error) {
	resp, err := b.get("/api/models")
	if err != nil {
		return nil, err
	}
	
	if models, ok := resp["models"].([]interface{}); ok {
		result := make([]map[string]interface{}, 0)
		for _, item := range models {
			if model, ok := item.(map[string]interface{}); ok {
				result = append(result, model)
			}
		}
		return result, nil
	}
	
	return []map[string]interface{}{}, nil
}

// LoadModel lädt Modell
func (b *JarvisCoreBridge) LoadModel(modelKey string) error {
	payload := map[string]interface{}{
		"model": modelKey,
		"token": b.token,
	}
	
	_, err := b.post("/api/models/load", payload)
	return err
}

// GetPlugins holt Plugin-Liste
func (b *JarvisCoreBridge) GetPlugins() ([]map[string]interface{}, error) {
	resp, err := b.get("/api/plugins")
	if err != nil {
		return nil, err
	}
	
	if plugins, ok := resp["plugins"].([]interface{}); ok {
		result := make([]map[string]interface{}, 0)
		for _, item := range plugins {
			if plugin, ok := item.(map[string]interface{}); ok {
				result = append(result, plugin)
			}
		}
		return result, nil
	}
	
	return []map[string]interface{}{}, nil
}

// TogglePlugin aktiviert/deaktiviert Plugin
func (b *JarvisCoreBridge) TogglePlugin(pluginName string, enabled bool) error {
	payload := map[string]interface{}{
		"plugin":  pluginName,
		"enabled": enabled,
		"token":   b.token,
	}
	
	_, err := b.post("/api/plugins/toggle", payload)
	return err
}

// ===== HTTP Helper Methods =====

func (b *JarvisCoreBridge) get(endpoint string) (map[string]interface{}, error) {
	req, err := http.NewRequest("GET", b.baseURL+endpoint, nil)
	if err != nil {
		return nil, err
	}
	
	req.Header.Set("Authorization", "Bearer "+b.token)
	
	resp, err := b.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("Verbindung fehlgeschlagen: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, err
	}
	
	return result, nil
}

func (b *JarvisCoreBridge) post(endpoint string, payload map[string]interface{}) (map[string]interface{}, error) {
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}
	
	req, err := http.NewRequest("POST", b.baseURL+endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}
	
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+b.token)
	
	resp, err := b.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("Verbindung fehlgeschlagen: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, err
	}
	
	return result, nil
}
