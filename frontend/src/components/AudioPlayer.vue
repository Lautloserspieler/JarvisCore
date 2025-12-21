<template>
  <div class="audio-player" :class="{ playing: isPlaying, loading: isLoading }">
    <!-- Play Button -->
    <button
      v-if="!isPlaying"
      @click="playAudio"
      :disabled="isLoading"
      class="audio-btn play-btn"
      :title="isLoading ? 'Generiere Audio...' : 'Audio abspielen'"
    >
      <i v-if="!isLoading" class="fas fa-volume-up"></i>
      <i v-else class="fas fa-spinner fa-spin"></i>
    </button>

    <!-- Stop Button -->
    <button
      v-else
      @click="stopAudio"
      class="audio-btn stop-btn"
      title="Audio stoppen"
    >
      <i class="fas fa-stop"></i>
    </button>

    <!-- Error Message -->
    <span v-if="error" class="audio-error" :title="error">
      <i class="fas fa-exclamation-circle"></i>
    </span>

    <!-- Language Indicator -->
    <span v-if="detectedLanguage && !error" class="language-badge" :title="languageTitle">
      {{ detectedLanguage.toUpperCase() }}
    </span>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  text: {
    type: String,
    required: true
  },
  language: {
    type: String,
    default: null // Auto-detect if null
  },
  messageId: {
    type: String,
    required: true
  }
});

const isPlaying = ref(false);
const isLoading = ref(false);
const error = ref(null);
const detectedLanguage = ref(props.language);
const audioElement = ref(null);

const languageTitle = computed(() => {
  const langMap = {
    'de': 'Deutsch',
    'en': 'English'
  };
  return langMap[detectedLanguage.value] || detectedLanguage.value;
});

const playAudio = async () => {
  error.value = null;
  isLoading.value = true;

  try {
    // Call TTS API
    const response = await fetch('/api/tts/synthesize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: props.text,
        language: props.language // null = auto-detect
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    // Get detected language from headers
    const responseLanguage = response.headers.get('X-Language');
    if (responseLanguage) {
      detectedLanguage.value = responseLanguage;
    }

    // Create audio blob
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);

    // Create and play audio element
    audioElement.value = new Audio(audioUrl);
    
    audioElement.value.onended = () => {
      isPlaying.value = false;
      URL.revokeObjectURL(audioUrl);
    };

    audioElement.value.onerror = () => {
      error.value = 'Audio-Wiedergabe fehlgeschlagen';
      isPlaying.value = false;
      URL.revokeObjectURL(audioUrl);
    };

    await audioElement.value.play();
    isPlaying.value = true;

  } catch (err) {
    console.error('TTS Error:', err);
    error.value = err.message || 'TTS nicht verfügbar';
  } finally {
    isLoading.value = false;
  }
};

const stopAudio = () => {
  if (audioElement.value) {
    audioElement.value.pause();
    audioElement.value.currentTime = 0;
    isPlaying.value = false;
  }
};
</script>

<style scoped>
.audio-player {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: 0.5rem;
}

.audio-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid var(--color-accent, #00d4ff);
  background: transparent;
  color: var(--color-accent, #00d4ff);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  position: relative;
}

.audio-btn:hover:not(:disabled) {
  background: var(--color-accent, #00d4ff);
  color: var(--color-bg, #0a0e27);
  box-shadow: 0 0 15px var(--color-accent, #00d4ff);
  transform: scale(1.1);
}

.audio-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.audio-btn i {
  font-size: 14px;
}

.play-btn {
  animation: pulse 2s infinite;
}

.stop-btn {
  border-color: #ff4444;
  color: #ff4444;
}

.stop-btn:hover {
  background: #ff4444;
  color: #fff;
  box-shadow: 0 0 15px #ff4444;
}

.audio-error {
  color: #ff4444;
  font-size: 14px;
  animation: shake 0.5s;
}

.language-badge {
  font-size: 10px;
  font-weight: bold;
  color: var(--color-accent, #00d4ff);
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid var(--color-accent, #00d4ff);
  border-radius: 4px;
  padding: 2px 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 5px var(--color-accent, #00d4ff);
  }
  50% {
    box-shadow: 0 0 20px var(--color-accent, #00d4ff);
  }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* Loading state */
.audio-player.loading .audio-btn {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
