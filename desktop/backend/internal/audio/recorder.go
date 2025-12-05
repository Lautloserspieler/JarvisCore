package audio

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"io"
	"sync"
	"time"

	"github.com/gordonklaus/portaudio"
)

// Recorder verwaltet Audio-Aufnahme
type Recorder struct {
	stream      *portaudio.Stream
	isRecording bool
	mu          sync.RWMutex
	audioBuffer *bytes.Buffer
	sampleRate  float64
	channels    int
}

// NewRecorder erstellt neuen Audio-Recorder
func NewRecorder() *Recorder {
	return &Recorder{
		sampleRate:  16000, // 16kHz für Whisper
		channels:    1,     // Mono
		audioBuffer: new(bytes.Buffer),
	}
}

// Start startet Audio-Aufnahme
func (r *Recorder) Start() error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.isRecording {
		return fmt.Errorf("Aufnahme läuft bereits")
	}

	// PortAudio initialisieren
	if err := portaudio.Initialize(); err != nil {
		return fmt.Errorf("PortAudio Init fehlgeschlagen: %w", err)
	}

	// Buffer zurücksetzen
	r.audioBuffer.Reset()

	// Input-Stream öffnen
	inputChannels := r.channels
	outputChannels := 0
	framesPerBuffer := 1024

	// Audio-Buffer für PortAudio
	audioData := make([]int16, framesPerBuffer)

	stream, err := portaudio.OpenDefaultStream(
		inputChannels,
		outputChannels,
		r.sampleRate,
		framesPerBuffer,
		audioData,
	)

	if err != nil {
		portaudio.Terminate()
		return fmt.Errorf("Stream öffnen fehlgeschlagen: %w", err)
	}

	r.stream = stream

	// Stream starten
	if err := stream.Start(); err != nil {
		stream.Close()
		portaudio.Terminate()
		return fmt.Errorf("Stream starten fehlgeschlagen: %w", err)
	}

	r.isRecording = true

	// Audio-Aufnahme in Goroutine
	go r.recordLoop(audioData)

	return nil
}

// recordLoop nimmt Audio auf
func (r *Recorder) recordLoop(buffer []int16) {
	for r.IsRecording() {
		// Audio-Frame lesen
		if err := r.stream.Read(); err != nil {
			if err != io.EOF {
				fmt.Printf("Fehler beim Lesen: %v\n", err)
			}
			break
		}

		// In Buffer schreiben
		r.mu.Lock()
		for _, sample := range buffer {
			binary.Write(r.audioBuffer, binary.LittleEndian, sample)
		}
		r.mu.Unlock()

		time.Sleep(10 * time.Millisecond)
	}
}

// Stop stoppt Audio-Aufnahme
func (r *Recorder) Stop() ([]byte, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	if !r.isRecording {
		return nil, fmt.Errorf("Keine Aufnahme aktiv")
	}

	r.isRecording = false

	// Stream stoppen
	if r.stream != nil {
		r.stream.Stop()
		r.stream.Close()
		r.stream = nil
	}

	// PortAudio terminieren
	portaudio.Terminate()

	// Audio-Daten zurückgeben
	audioData := r.audioBuffer.Bytes()
	return audioData, nil
}

// IsRecording gibt zurück ob aktuell aufgenommen wird
func (r *Recorder) IsRecording() bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.isRecording
}

// GetDuration gibt Aufnahme-Dauer zurück
func (r *Recorder) GetDuration() time.Duration {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Bytes / (SampleRate * Channels * BytesPerSample)
	bytesPerSample := 2 // int16
	totalSamples := r.audioBuffer.Len() / bytesPerSample
	seconds := float64(totalSamples) / r.sampleRate

	return time.Duration(seconds * float64(time.Second))
}
