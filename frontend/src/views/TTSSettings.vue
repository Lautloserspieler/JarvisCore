<template>
  <div class="tts-settings">
    <div class="settings-header">
      <h2>🎙️ Sprachausgabe (TTS)</h2>
      <p class="subtitle">Konfiguriere die Text-zu-Sprache Funktion von JARVIS</p>
    </div>

    <!-- TTS Status -->
    <div class="status-card" :class="statusClass">
      <div class="status-indicator">
        <i :class="statusIcon"></i>
        <span>{{ statusText }}</span>
      </div>
      <div v-if="ttsStatus" class="status-details">
        <span class="status-badge">{{ ttsStatus.engine }}</span>
        <span v-if="ttsStatus.gpu_enabled" class="status-badge gpu">
          <i class="fas fa-microchip"></i> GPU
        </span>
      </div>
    </div>

    <!-- Settings Form -->
    <div class="settings-form" v-if="config">
      
      <!-- Enable/Disable TTS -->
      <div class="setting-group">
        <div class="setting-row">
          <label class="setting-label">
            <i class="fas fa-power-off"></i>
            Sprachausgabe aktivieren
          </label>
          <label class="switch">
            <input type="checkbox" v-model="config.enabled">
            <span class="slider"></span>
          </label>
        </div>
      </div>

      <!-- Language Settings -->
      <div class="setting-group" v-if="config.enabled">
        <h3><i class="fas fa-language"></i> Sprache</h3>
        
        <!-- Default Language -->
        <div class="setting-row">
          <label class="setting-label">Standardsprache</label>
          <select v-model="config.default_language" class="setting-select">
            <option value="de">🇩🇪 Deutsch</option>
            <option value="en">🇬🇧 English</option>
          </select>
        </div>

        <!-- Auto Language Detection -->
        <div class="setting-row">
          <label class="setting-label">
            Automatische Spracherkennung
            <span class="help-text">Erkennt die Sprache aus dem Text</span>
          </label>
          <label class="switch">
            <input type="checkbox" v-model="config.auto_language_detection">
            <span class="slider"></span>
          </label>
        </div>
      </div>

      <!-- Engine Settings -->
      <div class="setting-group" v-if="config.enabled">
        <h3><i class="fas fa-cogs"></i> TTS-Engine</h3>
        
        <!-- Backend Selection -->
        <div class="setting-row">
          <label class="setting-label">TTS-Backend</label>
          <select v-model="config.backend" class="setting-select">
            <option value="xtts">XTTS v2 (Neural, höchste Qualität)</option>
            <option value="pyttsx3">pyttsx3 (Fallback, schnell)</option>
          </select>
        </div>

        <!-- GPU Acceleration -->
        <div class="setting-row" v-if="config.backend === 'xtts'">
          <label class="setting-label">
            GPU-Beschleunigung
            <span class="help-text">Nutzt NVIDIA CUDA (falls verfügbar)</span>
          </label>
          <label class="switch">
            <input type="checkbox" v-model="config.use_gpu">
            <span class="slider"></span>
          </label>
        </div>

        <!-- Fallback -->
        <div class="setting-row">
          <label class="setting-label">
            Fallback zu pyttsx3
            <span class="help-text">Falls XTTS nicht verfügbar</span>
          </label>
          <label class="switch">
            <input type="checkbox" v-model="config.fallback_to_pyttsx3">
            <span class="slider"></span>
          </label>
        </div>
      </div>

      <!-- Voice Quality Settings -->
      <div class="setting-group" v-if="config.enabled && config.backend === 'xtts'">
        <h3><i class="fas fa-sliders-h"></i> Stimmqualität</h3>
        
        <!-- Temperature -->
        <div class="setting-row">
          <label class="setting-label">
            Kreativität (Temperature)
            <span class="help-text">{{ config.temperature.toFixed(2) }} - Höher = natürlicher, Niedriger = stabiler</span>
          </label>
          <input 
            type="range" 
            v-model.number="config.temperature" 
            min="0.1" 
            max="1.0" 
            step="0.05"
            class="setting-slider"
          >
        </div>

        <!-- Speed -->
        <div class="setting-row">
          <label class="setting-label">
            Sprechgeschwindigkeit
            <span class="help-text">{{ config.speed.toFixed(2) }}x - Normal = 1.0</span>
          </label>
          <input 
            type="range" 
            v-model.number="config.speed" 
            min="0.5" 
            max="2.0" 
            step="0.1"
            class="setting-slider"
          >
        </div>
      </div>

      <!-- Voice Samples Info -->
      <div class="setting-group" v-if="ttsStatus && ttsStatus.voice_samples">
        <h3><i class="fas fa-microphone-alt"></i> Stimmen-Samples</h3>
        <div class="voice-samples">
          <div 
            v-for="(path, lang) in ttsStatus.voice_samples" 
            :key="lang"
            class="voice-sample-item"
            :class="{ available: path !== 'missing' }"
          >
            <div class="voice-icon">
              <i :class="path !== 'missing' ? 'fas fa-check-circle' : 'fas fa-times-circle'"></i>
            </div>
            <div class="voice-info">
              <strong>{{ getLanguageName(lang) }}</strong>
              <span class="voice-path">{{ getVoiceStatus(path) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="setting-actions">
        <button @click="saveSettings" class="btn btn-primary" :disabled="saving">
          <i :class="saving ? 'fas fa-spinner fa-spin' : 'fas fa-save'"></i>
          {{ saving ? 'Speichern...' : 'Einstellungen speichern' }}
        </button>
        <button @click="resetSettings" class="btn btn-secondary">
          <i class="fas fa-undo"></i>
          Zurücksetzen
        </button>
        <button @click="testTTS" class="btn btn-test" :disabled="testing">
          <i :class="testing ? 'fas fa-spinner fa-spin' : 'fas fa-volume-up'"></i>
          {{ testing ? 'Teste...' : 'Test-Audio' }}
        </button>
      </div>

      <!-- Success/Error Messages -->
      <div v-if="message" class="message" :class="messageType">
        <i :class="messageType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const ttsStatus = ref(null);
const config = ref(null);
const saving = ref(false);
const testing = ref(false);
const message = ref('');
const messageType = ref('success');

const statusClass = computed(() => {
  if (!ttsStatus.value) return 'loading';
  return ttsStatus.value.available ? 'online' : 'offline';
});

const statusIcon = computed(() => {
  if (!ttsStatus.value) return 'fas fa-spinner fa-spin';
  return ttsStatus.value.available ? 'fas fa-check-circle' : 'fas fa-times-circle';
});

const statusText = computed(() => {
  if (!ttsStatus.value) return 'Lade TTS-Status...';
  if (ttsStatus.value.available) {
    return `TTS verfügbar (${ttsStatus.value.engine})`;
  }
  return ttsStatus.value.error || 'TTS nicht verfügbar';
});

const getLanguageName = (code) => {
  const names = { 'de': '🇩🇪 Deutsch', 'en': '🇬🇧 English' };
  return names[code] || code.toUpperCase();
};

const getVoiceStatus = (path) => {
  if (path === 'missing') return '❌ Nicht gefunden';
  return `✅ Jarvis_${path.includes('DE') ? 'DE' : 'EN'}.wav (v2.2)`;
};

const loadSettings = async () => {
  try {
    // Load TTS status
    const statusRes = await fetch('/api/tts/status');
    ttsStatus.value = await statusRes.json();

    // Initialize config from status or defaults
    config.value = {
      enabled: ttsStatus.value.enabled || false,
      backend: ttsStatus.value.backend || 'xtts',
      default_language: ttsStatus.value.current_language || 'de',
      auto_language_detection: true,
      use_gpu: ttsStatus.value.gpu_enabled || false,
      fallback_to_pyttsx3: true,
      temperature: 0.75,
      speed: 1.0
    };
  } catch (error) {
    console.error('Failed to load TTS settings:', error);
    showMessage('Fehler beim Laden der Einstellungen', 'error');
  }
};

const saveSettings = async () => {
  saving.value = true;
  try {
    const response = await fetch('/api/tts/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.value)
    });

    if (!response.ok) throw new Error('Speichern fehlgeschlagen');

    showMessage('✅ Einstellungen gespeichert', 'success');
    await loadSettings(); // Reload status
  } catch (error) {
    console.error('Failed to save settings:', error);
    showMessage('❌ Fehler beim Speichern', 'error');
  } finally {
    saving.value = false;
  }
};

const resetSettings = () => {
  config.value = {
    enabled: true,
    backend: 'xtts',
    default_language: 'de',
    auto_language_detection: true,
    use_gpu: true,
    fallback_to_pyttsx3: true,
    temperature: 0.75,
    speed: 1.0
  };
  showMessage('Einstellungen zurückgesetzt', 'success');
};

const testTTS = async () => {
  testing.value = true;
  try {
    const testText = config.value.default_language === 'de' 
      ? 'Guten Tag, ich bin JARVIS. Ihr persönlicher KI-Assistent.'
      : 'Hello, I am JARVIS. Your personal AI assistant.';

    const response = await fetch('/api/tts/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: testText,
        language: config.value.default_language
      })
    });

    if (!response.ok) throw new Error('TTS-Test fehlgeschlagen');

    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    
    audio.onended = () => URL.revokeObjectURL(audioUrl);
    await audio.play();

    showMessage('✅ Test erfolgreich', 'success');
  } catch (error) {
    console.error('TTS test failed:', error);
    showMessage('❌ Test fehlgeschlagen: ' + error.message, 'error');
  } finally {
    testing.value = false;
  }
};

const showMessage = (text, type = 'success') => {
  message.value = text;
  messageType.value = type;
  setTimeout(() => { message.value = ''; }, 5000);
};

onMounted(() => {
  loadSettings();
});
</script>

<style scoped>
.tts-settings {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
}

.settings-header h2 {
  color: var(--color-accent, #00d4ff);
  font-size: 2rem;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 10px var(--color-accent, #00d4ff);
}

.subtitle {
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 2rem;
}

.status-card {
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-card.online {
  border-color: #00ff88;
  background: rgba(0, 255, 136, 0.1);
}

.status-card.offline {
  border-color: #ff4444;
  background: rgba(255, 68, 68, 0.1);
}

.status-card.loading {
  border-color: var(--color-accent, #00d4ff);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 1.1rem;
}

.status-details {
  display: flex;
  gap: 0.5rem;
}

.status-badge {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--color-accent, #00d4ff);
  border-radius: 20px;
  padding: 0.3rem 0.8rem;
  font-size: 0.85rem;
  text-transform: uppercase;
}

.status-badge.gpu {
  border-color: #00ff88;
  color: #00ff88;
}

.setting-group {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.setting-group h3 {
  color: var(--color-accent, #00d4ff);
  font-size: 1.2rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.setting-row:last-child {
  border-bottom: none;
}

.setting-label {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.help-text {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.setting-select,
.setting-slider {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--color-accent, #00d4ff);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  color: #fff;
  min-width: 250px;
}

.setting-slider {
  width: 250px;
}

/* Switch Toggle */
.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 30px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  transition: 0.3s;
  border-radius: 30px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--color-accent, #00d4ff);
  border-color: var(--color-accent, #00d4ff);
  box-shadow: 0 0 10px var(--color-accent, #00d4ff);
}

input:checked + .slider:before {
  transform: translateX(30px);
}

/* Voice Samples */
.voice-samples {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.voice-sample-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.voice-sample-item.available {
  border-color: #00ff88;
}

.voice-icon i {
  font-size: 1.5rem;
}

.voice-sample-item.available .voice-icon i {
  color: #00ff88;
}

.voice-info {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.voice-path {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

/* Actions */
.setting-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.btn {
  padding: 0.8rem 1.5rem;
  border: 2px solid;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: var(--color-accent, #00d4ff);
  border-color: var(--color-accent, #00d4ff);
  color: #0a0e27;
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 0 20px var(--color-accent, #00d4ff);
  transform: translateY(-2px);
}

.btn-secondary {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.5);
  color: #fff;
}

.btn-test {
  background: transparent;
  border-color: #00ff88;
  color: #00ff88;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Messages */
.message {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  animation: slideIn 0.3s ease;
}

.message.success {
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid #00ff88;
  color: #00ff88;
}

.message.error {
  background: rgba(255, 68, 68, 0.1);
  border: 1px solid #ff4444;
  color: #ff4444;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
