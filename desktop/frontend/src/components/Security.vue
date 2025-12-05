<template>
  <div v-if="securityChallenge.active" class="security-overlay">
    <div class="security-modal">
      <div class="security-header">
        <h2>🔒 Sicherheitsabfrage</h2>
      </div>
      
      <div class="security-body">
        <p class="security-command">
          Befehl: <strong>{{ securityChallenge.command }}</strong>
        </p>
        
        <p class="security-message">
          {{ securityChallenge.message }}
        </p>
        
        <div v-if="securityChallenge.hint" class="security-hint">
          💡 Hinweis: {{ securityChallenge.hint }}
        </div>
        
        <form @submit.prevent="submitPassphrase" class="security-form">
          <input
            ref="passphraseInput"
            v-model="passphraseInput"
            type="password"
            placeholder="Passphrase eingeben..."
            class="security-input"
            autocomplete="off"
            :disabled="isSubmitting"
          />
          
          <div v-if="errorMessage" class="security-error">
            ⚠️ {{ errorMessage }}
          </div>
          
          <div class="security-actions">
            <button 
              type="submit" 
              class="btn-primary"
              :disabled="!passphraseInput.trim() || isSubmitting"
            >
              {{ isSubmitting ? '⏳ Prüfe...' : '✓ Bestätigen' }}
            </button>
            <button 
              type="button" 
              class="btn-secondary"
              @click="cancelSecurity"
              :disabled="isSubmitting"
            >
              ✗ Abbrechen
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useWails } from '../composables/useWails'
import { useWebSocket } from '../composables/useWebSocket'

const { api } = useWails()
const { securityChallenge } = useWebSocket()

const passphraseInput = ref('')
const passphraseInputRef = ref(null)
const errorMessage = ref('')
const isSubmitting = ref(false)

// Auto-focus input when overlay appears
watch(() => securityChallenge.value.active, async (active) => {
  if (active) {
    passphraseInput.value = ''
    errorMessage.value = ''
    isSubmitting.value = false
    await nextTick()
    passphraseInputRef.value?.focus()
  }
})

const submitPassphrase = async () => {
  const passphrase = passphraseInput.value.trim()
  if (!passphrase) {
    errorMessage.value = 'Bitte Passphrase eingeben'
    return
  }
  
  isSubmitting.value = true
  errorMessage.value = ''
  
  try {
    // Submit passphrase as special command
    await api.ProcessCommand(passphrase, {
      source: 'desktop-ui',
      passphrase_only: true
    })
    
    // Success - overlay will be closed by WebSocket event
    passphraseInput.value = ''
  } catch (error) {
    console.error('Security passphrase error:', error)
    errorMessage.value = error.message || 'Passphrase ungültig'
  } finally {
    isSubmitting.value = false
  }
}

const cancelSecurity = () => {
  securityChallenge.value = { active: false }
  passphraseInput.value = ''
  errorMessage.value = ''
  isSubmitting.value = false
}

// ESC key to cancel
const handleKeyDown = (event) => {
  if (event.key === 'Escape' && securityChallenge.value.active) {
    cancelSecurity()
  }
}

// Bind ESC key globally
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', handleKeyDown)
}
</script>

<style scoped>
.security-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.security-modal {
  background: var(--bg-secondary);
  border: 2px solid var(--accent);
  border-radius: 12px;
  padding: 0;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 8px 32px rgba(0, 180, 216, 0.3);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.security-header {
  background: var(--accent);
  color: var(--bg-primary);
  padding: 16px 24px;
  border-radius: 10px 10px 0 0;
}

.security-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.security-body {
  padding: 24px;
}

.security-command {
  color: var(--text-secondary);
  margin-bottom: 16px;
  font-size: 14px;
}

.security-command strong {
  color: var(--accent);
  font-family: 'Courier New', monospace;
}

.security-message {
  color: var(--text-primary);
  margin-bottom: 16px;
  font-size: 15px;
  line-height: 1.5;
}

.security-hint {
  background: rgba(0, 180, 216, 0.1);
  border-left: 3px solid var(--accent);
  padding: 12px;
  margin-bottom: 20px;
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 14px;
}

.security-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.security-input {
  width: 100%;
  padding: 12px 16px;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 15px;
  font-family: 'Courier New', monospace;
  transition: border-color 0.2s;
}

.security-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(0, 180, 216, 0.1);
}

.security-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.security-error {
  background: rgba(255, 77, 77, 0.1);
  border-left: 3px solid #ff4d4d;
  padding: 12px;
  border-radius: 4px;
  color: #ff4d4d;
  font-size: 14px;
}

.security-actions {
  display: flex;
  gap: 12px;
}

.security-actions button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--accent);
  color: var(--bg-primary);
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 180, 216, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 2px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-primary);
  border-color: var(--text-secondary);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
