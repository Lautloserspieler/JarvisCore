<template>
  <div class="tts-settings">
    <!-- Header -->
    <div class="settings-header">
      <h3>🎙️ Voice Settings (Text-to-Speech)</h3>
      <div class="status-badge" :class="{ active: ttsStatus.available }">
        {{ ttsStatus.available ? '✅ Active' : '❌ Inactive' }}
      </div>
    </div>

    <!-- TTS Status -->
    <div class="status-info" v-if="ttsStatus.available">
      <p><strong>Engine:</strong> {{ ttsStatus.engine }} on {{ ttsStatus.device }}</p>
      <p><strong>GPU:</strong> {{ ttsStatus.gpu_enabled ? '✅ Enabled' : '❌ Disabled' }}</p>
      <p><strong>Languages:</strong> {{ ttsStatus.languages?.join(', ') || 'N/A' }}</p>
    </div>
    <div class="error-message" v-else>
      TTS service is not available. Install the 'tts' package to enable voice synthesis.
    </div>

    <!-- Settings Form -->
    <div class="settings-form" v-if="ttsStatus.available">
      <!-- Enable/Disable TTS -->
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="localSettings.enabled" />
          <span>Enable Voice Output</span>
        </label>
      </div>

      <!-- Language Selection -->
      <div class="form-group">
        <label for="language">Language</label>
        <select id="language" v-model="localSettings.language" :disabled="!localSettings.enabled">
          <option value="de">🇩🇳 German (Deutsch)</option>
          <option value="en">🇬🇺 English</option>
        </select>
        <small>Which language should JARVIS use for voice output?</small>
      </div>

      <!-- Auto-play Toggle -->
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="localSettings.autoplay" :disabled="!localSettings.enabled" />
          <span>Auto-play Response</span>
        </label>
        <small>Automatically speak responses after receiving them</small>
      </div>

      <!-- Volume Control -->
      <div class="form-group">
        <label for="volume">Volume: {{ Math.round(localSettings.volume * 100) }}%</label>
        <input
          type="range"
          id="volume"
          v-model="localSettings.volume"
          min="0"
          max="1"
          step="0.05"
          :disabled="!localSettings.enabled"
          class="slider"
        />
        <small>Adjust playback volume</small>
      </div>

      <!-- Speed Control -->
      <div class="form-group">
        <label for="speed">Speed: {{ localSettings.speed.toFixed(1) }}x</label>
        <input
          type="range"
          id="speed"
          v-model="localSettings.speed"
          min="0.5"
          max="2"
          step="0.1"
          :disabled="!localSettings.enabled"
          class="slider"
        />
        <small>Speech playback speed (0.5x - 2x)</small>
      </div>

      <!-- Available Voices -->
      <div class="form-group" v-if="voices.length > 0">
        <label>Available Voice Samples</label>
        <div class="voices-list">
          <div
            v-for="voice in voices"
            :key="voice.language"
            class="voice-item"
            :class="{ active: voice.language === localSettings.language }"
          >
            <div class="voice-info">
              <strong>{{ voice.name }}</strong>
              <p>{{ voice.description }}</p>
            </div>
            <div class="voice-status">
              <span v-if="voice.available" class="badge success">✅ Ready</span>
              <span v-else class="badge error">❌ Missing</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Test Button -->
      <div class="form-group">
        <button
          @click="testTTS"
          :disabled="!localSettings.enabled || testing"
          class="btn-test"
        >
          {{ testing ? '🆗 Testing...' : '🔊 Test Voice' }}
        </button>
        <small>Click to hear a test of the JARVIS voice</small>
      </div>

      <!-- Save Button -->
      <div class="form-actions">
        <button @click="saveSettings" class="btn-primary">Save Settings</button>
        <button @click="resetSettings" class="btn-secondary">Reset</button>
      </div>

      <div class="success-message" v-if="saved">
        ✅ Settings saved successfully!
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

interface TTSSettings {
  enabled: boolean
  language: string
  autoplay: boolean
  volume: number
  speed: number
  use_voice_samples: boolean
}

interface Voice {
  language: string
  name: string
  description: string
  available: boolean
}

const localSettings = reactive<TTSSettings>({
  enabled: true,
  language: 'de',
  autoplay: false,
  volume: 1.0,
  speed: 1.0,
  use_voice_samples: true,
})

const ttsStatus = ref<any>({
  available: false,
  engine: 'xtts',
  device: 'cpu',
  gpu_enabled: false,
  languages: ['de', 'en'],
})

const voices = ref<Voice[]>([])
const testing = ref(false)
const saved = ref(false)

// Fetch TTS status on mount
onMounted(async () => {
  try {
    // Get TTS status
    const statusResponse = await fetch('/api/tts/status')
    ttsStatus.value = await statusResponse.json()

    // Get settings
    const settingsResponse = await fetch('/api/tts/settings')
    const settings = await settingsResponse.json()
    Object.assign(localSettings, settings)

    // Get available voices
    const voicesResponse = await fetch('/api/tts/voices')
    const voicesData = await voicesResponse.json()
    voices.value = voicesData.voices
  } catch (error) {
    console.error('Failed to fetch TTS data:', error)
  }
})

const saveSettings = async () => {
  try {
    const response = await fetch('/api/tts/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(localSettings),
    })

    if (response.ok) {
      saved.value = true
      setTimeout(() => {
        saved.value = false
      }, 3000)
    }
  } catch (error) {
    console.error('Failed to save settings:', error)
  }
}

const resetSettings = async () => {
  try {
    const response = await fetch('/api/tts/settings')
    const settings = await response.json()
    Object.assign(localSettings, settings)
  } catch (error) {
    console.error('Failed to reset settings:', error)
  }
}

const testTTS = async () => {
  testing.value = true
  try {
    const response = await fetch('/api/tts/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: localSettings.language }),
    })

    if (response.ok) {
      const audioBlob = await response.blob()
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      audio.volume = localSettings.volume
      audio.playbackRate = localSettings.speed
      audio.play()
    }
  } catch (error) {
    console.error('Test TTS failed:', error)
  } finally {
    testing.value = false
  }
}
</script>

<style scoped lang="css">
.tts-settings {
  background: var(--color-surface);
  border: 1px solid var(--color-card-border);
  border-radius: var(--radius-lg);
  padding: var(--space-16);
  margin-bottom: var(--space-16);
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-16);
  padding-bottom: var(--space-16);
  border-bottom: 2px solid var(--color-border);
}

.settings-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text);
}

.status-badge {
  display: inline-block;
  padding: var(--space-6) var(--space-12);
  border-radius: var(--radius-full);
  background-color: rgba(192, 21, 47, 0.15);
  color: var(--color-error);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.status-badge.active {
  background-color: rgba(33, 128, 141, 0.15);
  color: var(--color-success);
}

.status-info {
  background-color: rgba(33, 128, 141, 0.1);
  border: 1px solid rgba(33, 128, 141, 0.3);
  border-radius: var(--radius-md);
  padding: var(--space-12);
  margin-bottom: var(--space-16);
  font-size: var(--font-size-sm);
}

.status-info p {
  margin: var(--space-4) 0;
}

.error-message {
  background-color: rgba(192, 21, 47, 0.1);
  border: 1px solid rgba(192, 21, 47, 0.3);
  border-radius: var(--radius-md);
  padding: var(--space-12);
  color: var(--color-error);
  font-size: var(--font-size-sm);
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-16);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.form-group label {
  font-weight: 500;
  font-size: var(--font-size-sm);
  color: var(--color-text);
}

.form-group small {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  cursor: pointer;
  font-weight: normal;
}

.checkbox-label input[type='checkbox'] {
  cursor: pointer;
  width: 18px;
  height: 18px;
}

select,
input[type='range'] {
  padding: var(--space-8);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-background);
  color: var(--color-text);
  font-family: inherit;
  font-size: var(--font-size-sm);
}

select:disabled,
input[type='range']:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.slider {
  padding: var(--space-4);
}

.voices-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
  margin-top: var(--space-8);
}

.voice-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-12);
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.voice-item.active {
  border-color: var(--color-primary);
  background-color: rgba(33, 128, 141, 0.1);
}

.voice-info strong {
  display: block;
  margin-bottom: var(--space-4);
  color: var(--color-text);
}

.voice-info p {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.voice-status {
  display: flex;
  gap: var(--space-8);
}

.badge {
  display: inline-block;
  padding: var(--space-4) var(--space-8);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.badge.success {
  background-color: rgba(33, 128, 141, 0.2);
  color: var(--color-success);
}

.badge.error {
  background-color: rgba(192, 21, 47, 0.2);
  color: var(--color-error);
}

.btn-test {
  padding: var(--space-10) var(--space-16);
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.btn-test:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  gap: var(--space-8);
  margin-top: var(--space-16);
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: var(--space-10) var(--space-16);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background-color: var(--color-primary-hover);
}

.btn-secondary {
  background-color: var(--color-secondary);
  color: var(--color-text);
}

.btn-secondary:hover {
  background-color: var(--color-secondary-hover);
}

.success-message {
  padding: var(--space-12);
  background-color: rgba(33, 128, 141, 0.1);
  border: 1px solid var(--color-success);
  border-radius: var(--radius-md);
  color: var(--color-success);
  font-size: var(--font-size-sm);
  text-align: center;
}
</style>
