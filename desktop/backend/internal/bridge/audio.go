package bridge

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
)

// SendAudio sendet Audio-Daten zur Transkription
func (b *JarvisCoreBridge) SendAudio(audioData []byte) (string, error) {
	body := new(bytes.Buffer)
	writer := multipart.NewWriter(body)

	// Audio-Datei als Form-Field
	part, err := writer.CreateFormFile("audio", "recording.wav")
	if err != nil {
		return "", err
	}

	if _, err := part.Write(audioData); err != nil {
		return "", err
	}

	writer.Close()

	// HTTP POST Request
	req, err := http.NewRequest("POST", b.baseURL+"/api/stt", body)
	if err != nil {
		return "", err
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("STT Request fehlgeschlagen: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("STT Fehler: %s - %s", resp.Status, string(bodyBytes))
	}

	// Response parsen
	var result struct {
		Text string `json:"text"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}

	return result.Text, nil
}
