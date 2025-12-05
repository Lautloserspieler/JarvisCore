package app

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"time"

	"jarviscore/desktop/internal/audio"
)

// Audio-Recorder Instanz
var globalRecorder *audio.Recorder

// StartRecording startet Audio-Aufnahme
func (a *App) StartRecording() error {
	if globalRecorder != nil && globalRecorder.IsRecording() {
		return fmt.Errorf("Aufnahme läuft bereits")
	}

	globalRecorder = audio.NewRecorder()

	if err := globalRecorder.Start(); err != nil {
		return fmt.Errorf("Aufnahme starten fehlgeschlagen: %w", err)
	}

	// Broadcast Recording-Start
	a.BroadcastMessage("recording_started", map[string]interface{}{
		"timestamp": time.Now().Unix(),
	})

	return nil
}

// StopRecording stoppt Audio-Aufnahme und sendet an JarvisCore
func (a *App) StopRecording() (string, error) {
	if globalRecorder == nil || !globalRecorder.IsRecording() {
		return "", fmt.Errorf("Keine aktive Aufnahme")
	}

	// Aufnahme stoppen
	audioData, err := globalRecorder.Stop()
	if err != nil {
		return "", fmt.Errorf("Aufnahme stoppen fehlgeschlagen: %w", err)
	}

	if len(audioData) == 0 {
		return "", fmt.Errorf("Keine Audio-Daten aufgenommen")
	}

	// Broadcast Recording-Stop
	a.BroadcastMessage("recording_stopped", map[string]interface{}{
		"timestamp": time.Now().Unix(),
		"size":      len(audioData),
	})

	// Audio zu WAV konvertieren
	wavData, err := convertToWAV(audioData, 16000, 1)
	if err != nil {
		return "", fmt.Errorf("WAV-Konvertierung fehlgeschlagen: %w", err)
	}

	// An JarvisCore senden
	response, err := a.bridge.SendAudio(wavData)
	if err != nil {
		return "", fmt.Errorf("Audio-Verarbeitung fehlgeschlagen: %w", err)
	}

	// Broadcast Transcription
	a.BroadcastMessage("transcription_received", map[string]interface{}{
		"text":      response,
		"timestamp": time.Now().Unix(),
	})

	return response, nil
}

// IsRecording gibt Status zurück
func (a *App) IsRecording() bool {
	if globalRecorder == nil {
		return false
	}
	return globalRecorder.IsRecording()
}

// GetRecordingDuration gibt Aufnahme-Dauer zurück
func (a *App) GetRecordingDuration() float64 {
	if globalRecorder == nil {
		return 0
	}
	duration := globalRecorder.GetDuration()
	return duration.Seconds()
}

// convertToWAV konvertiert PCM zu WAV
func convertToWAV(pcmData []byte, sampleRate, channels int) ([]byte, error) {
	buf := new(bytes.Buffer)

	// WAV Header
	buf.WriteString("RIFF")

	// File size - 8
	fileSize := uint32(36 + len(pcmData))
	if err := binary.Write(buf, binary.LittleEndian, fileSize); err != nil {
		return nil, err
	}

	buf.WriteString("WAVE")
	buf.WriteString("fmt ")

	// fmt chunk size
	fmtSize := uint32(16)
	if err := binary.Write(buf, binary.LittleEndian, fmtSize); err != nil {
		return nil, err
	}

	// Audio format (1 = PCM)
	audioFormat := uint16(1)
	if err := binary.Write(buf, binary.LittleEndian, audioFormat); err != nil {
		return nil, err
	}

	// Channels
	if err := binary.Write(buf, binary.LittleEndian, uint16(channels)); err != nil {
		return nil, err
	}

	// Sample rate
	if err := binary.Write(buf, binary.LittleEndian, uint32(sampleRate)); err != nil {
		return nil, err
	}

	// Byte rate
	byteRate := uint32(sampleRate * channels * 2) // 2 = 16-bit
	if err := binary.Write(buf, binary.LittleEndian, byteRate); err != nil {
		return nil, err
	}

	// Block align
	blockAlign := uint16(channels * 2)
	if err := binary.Write(buf, binary.LittleEndian, blockAlign); err != nil {
		return nil, err
	}

	// Bits per sample
	bitsPerSample := uint16(16)
	if err := binary.Write(buf, binary.LittleEndian, bitsPerSample); err != nil {
		return nil, err
	}

	// Data chunk
	buf.WriteString("data")

	// Data size
	if err := binary.Write(buf, binary.LittleEndian, uint32(len(pcmData))); err != nil {
		return nil, err
	}

	// PCM data
	buf.Write(pcmData)

	return buf.Bytes(), nil
}
