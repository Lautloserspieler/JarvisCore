<template>
  <div class="voice-recording">
    <button 
      class="voice-btn"
      :class="{ 
        active: isRecording, 
        processing: isProcessing,
        disabled: isProcessing 
      }"
      @click="toggleRecording"
      :disabled="isProcessing"
      :title="getTooltip()"
    >
      <span v-if="!isRecording && !isProcessing">🎤</span>
      <span v-else-if="isRecording" class="recording-icon">⏸️</span>
      <span v-else class="processing-icon">⏳</span>
    </button>
    
    <div v-if="isRecording" class="recording-indicator">
      <span class="pulse"></span>
      <span class="duration">{{ formattedDuration }}</span>
    </div>
    
    <div v-if="error" class="error-message">
      ⚠️ {{ error }}
    </div>
  </div>
</template>

<script>
import { useVoiceRecording } from '../composables/useVoiceRecording'

export default {
  name: 'VoiceRecordingButton',
  emits: ['transcription'],
  setup(props, { emit }) {
    const {
      isRecording,
      isProcessing,
      formattedDuration,
      error,
      startRecording,
      stopRecording,
      cancelRecording
    } = useVoiceRecording()
    
    const toggleRecording = async () => {
      if (isProcessing.value) return
      
      if (isRecording.value) {
        // Stop Recording
        try {
          const transcription = await stopRecording()
          emit('transcription', transcription)
        } catch (err) {
          console.error('Recording Error:', err)
        }
      } else {
        // Start Recording
        try {
          await startRecording()
        } catch (err) {
          console.error('Recording Error:', err)
        }
      }
    }
    
    const getTooltip = () => {
      if (isProcessing.value) return 'Wird verarbeitet...'
      if (isRecording.value) return 'Aufnahme stoppen'
      return 'Sprachaufnahme starten'
    }
    
    return {
      isRecording,
      isProcessing,
      formattedDuration,
      error,
      toggleRecording,
      getTooltip
    }
  }
}
</script>

<style scoped>
.voice-recording {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
}

.voice-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--accent);
  background: transparent;
  color: var(--accent);
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voice-btn:hover:not(.disabled) {
  background: var(--accent);
  color: white;
  transform: scale(1.05);
}

.voice-btn.active {
  background: var(--accent);
  color: white;
  animation: pulse 1.5s infinite;
  border-color: #ef476f;
  background: #ef476f;
}

.voice-btn.processing {
  background: var(--accent);
  color: white;
  opacity: 0.7;
  cursor: wait;
}

.voice-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 71, 111, 0.7);
  }
  50% {
    box-shadow: 0 0 0 15px rgba(239, 71, 111, 0);
  }
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(239, 71, 111, 0.1);
  border-radius: 20px;
  color: #ef476f;
  font-size: 12px;
  font-weight: 600;
}

.pulse {
  width: 8px;
  height: 8px;
  background: #ef476f;
  border-radius: 50%;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.duration {
  font-family: monospace;
}

.error-message {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(239, 71, 111, 0.1);
  border: 1px solid #ef476f;
  border-radius: 8px;
  color: #ef476f;
  font-size: 12px;
  white-space: nowrap;
  z-index: 10;
}

.recording-icon,
.processing-icon {
  display: inline-block;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
