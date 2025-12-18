<template>
  <div class="token-dialog-overlay" @click.self="$emit('close')">
    <div class="token-dialog">
      <div class="dialog-header">
        <h2>{{ t.title }}</h2>
        <button @click="$emit('close')" class="close-btn">×</button>
      </div>
      
      <div class="dialog-content">
        <div class="info-box">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <div>
            <p class="info-text">{{ t.message }}</p>
            <a 
              href="https://huggingface.co/settings/tokens" 
              target="_blank"
              class="link"
            >
              {{ t.getToken }}
            </a>
          </div>
        </div>

        <div class="input-group">
          <label>{{ t.tokenLabel }}</label>
          <input 
            v-model="token"
            type="password"
            :placeholder="t.tokenPlaceholder"
            class="token-input"
            @keyup.enter="handleSubmit"
          />
          <p v-if="error" class="error-text">{{ error }}</p>
        </div>

        <div class="remember-check">
          <input 
            v-model="remember" 
            type="checkbox" 
            id="remember-token"
          />
          <label for="remember-token">{{ t.rememberToken }}</label>
        </div>
      </div>

      <div class="dialog-actions">
        <button @click="$emit('close')" class="btn-cancel">
          {{ t.cancel }}
        </button>
        <button @click="handleSubmit" class="btn-submit" :disabled="!token">
          {{ t.submit }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  modelName: string
  language?: 'de' | 'en'
}>()

const emit = defineEmits(['close', 'submit'])

const token = ref('')
const remember = ref(true)
const error = ref('')

const translations = {
  de: {
    title: 'HuggingFace Token benötigt',
    message: 'Dieses Modell benötigt einen HuggingFace Token für den Download.',
    getToken: 'Token erstellen →',
    tokenLabel: 'HuggingFace Token',
    tokenPlaceholder: 'hf_...',
    rememberToken: 'Token für zukünftige Downloads speichern',
    cancel: 'Abbrechen',
    submit: 'Speichern & Download',
    invalidToken: 'Ungültiges Token-Format. Token sollte mit "hf_" beginnen.'
  },
  en: {
    title: 'HuggingFace Token Required',
    message: 'This model requires a HuggingFace token for download.',
    getToken: 'Get Token →',
    tokenLabel: 'HuggingFace Token',
    tokenPlaceholder: 'hf_...',
    rememberToken: 'Remember token for future downloads',
    cancel: 'Cancel',
    submit: 'Save & Download',
    invalidToken: 'Invalid token format. Token should start with "hf_"'
  }
}

const t = computed(() => translations[props.language || 'en'])

const handleSubmit = () => {
  error.value = ''
  
  if (!token.value) {
    return
  }
  
  // Validate token format
  if (!token.value.startsWith('hf_')) {
    error.value = t.value.invalidToken
    return
  }
  
  emit('submit', { token: token.value, remember: remember.value })
}
</script>

<style scoped>
.token-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.token-dialog {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

@media (prefers-color-scheme: dark) {
  .token-dialog {
    background: #1f2937;
    color: #f3f4f6;
  }
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}

@media (prefers-color-scheme: dark) {
  .dialog-header {
    border-bottom-color: #374151;
  }
}

.dialog-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #6b7280;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

@media (prefers-color-scheme: dark) {
  .close-btn:hover {
    background: #374151;
    color: #f3f4f6;
  }
}

.dialog-content {
  padding: 24px;
}

.info-box {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #eff6ff;
  border-left: 4px solid #3b82f6;
  border-radius: 8px;
  margin-bottom: 24px;
}

@media (prefers-color-scheme: dark) {
  .info-box {
    background: #1e3a8a;
    border-left-color: #60a5fa;
  }
}

.info-box .icon {
  width: 24px;
  height: 24px;
  color: #3b82f6;
  flex-shrink: 0;
}

@media (prefers-color-scheme: dark) {
  .info-box .icon {
    color: #60a5fa;
  }
}

.info-text {
  margin: 0 0 8px 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

.link {
  color: #3b82f6;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.link:hover {
  text-decoration: underline;
}

@media (prefers-color-scheme: dark) {
  .link {
    color: #60a5fa;
  }
}

.input-group {
  margin-bottom: 16px;
}

.input-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 8px;
  color: #374151;
}

@media (prefers-color-scheme: dark) {
  .input-group label {
    color: #d1d5db;
  }
}

.token-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.875rem;
  font-family: 'Courier New', monospace;
  transition: all 0.2s;
}

.token-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

@media (prefers-color-scheme: dark) {
  .token-input {
    background: #374151;
    border-color: #4b5563;
    color: #f3f4f6;
  }
  
  .token-input:focus {
    border-color: #60a5fa;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1);
  }
}

.error-text {
  margin-top: 8px;
  font-size: 0.75rem;
  color: #dc2626;
}

.remember-check {
  display: flex;
  align-items: center;
  gap: 8px;
}

.remember-check input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.remember-check label {
  font-size: 0.875rem;
  cursor: pointer;
  user-select: none;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

@media (prefers-color-scheme: dark) {
  .dialog-actions {
    border-top-color: #374151;
  }
}

.btn-cancel,
.btn-submit {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel {
  background: #f3f4f6;
  color: #374151;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

@media (prefers-color-scheme: dark) {
  .btn-cancel {
    background: #374151;
    color: #d1d5db;
  }
  
  .btn-cancel:hover {
    background: #4b5563;
  }
}

.btn-submit {
  background: #3b82f6;
  color: white;
}

.btn-submit:hover:not(:disabled) {
  background: #2563eb;
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
