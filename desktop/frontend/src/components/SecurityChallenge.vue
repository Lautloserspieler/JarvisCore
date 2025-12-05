<template>
  <div v-if="showChallenge" class="security-overlay">
    <div class="security-modal">
      <div class="modal-header">
        <h2>🔒 Sicherheitsüberprüfung</h2>
        <p>Authentifizierung erforderlich</p>
      </div>

      <div class="modal-body">
        <!-- Passphrase Input -->
        <div class="input-group">
          <label for="passphrase">Passphrase:</label>
          <input
            id="passphrase"
            v-model="passphrase"
            type="password"
            placeholder="Gib deine Passphrase ein"
            @keyup.enter="submitChallenge"
            autocomplete="current-password"
          />
        </div>

        <!-- TOTP Input (optional) -->
        <div v-if="totpRequired" class="input-group">
          <label for="totp">2FA Code:</label>
          <input
            id="totp"
            v-model="totpCode"
            type="text"
            placeholder="6-stelliger Code"
            maxlength="6"
            @keyup.enter="submitChallenge"
            autocomplete="one-time-code"
          />
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </div>

      <div class="modal-footer">
        <button @click="submitChallenge" class="btn-primary" :disabled="loading">
          <span v-if="loading">Überprüfe...</span>
          <span v-else>Entsperren</span>
        </button>
        <button @click="cancel" class="btn-secondary">
          Abbrechen
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SecurityChallenge',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    requireTotp: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      showChallenge: this.show,
      passphrase: '',
      totpCode: '',
      totpRequired: this.requireTotp,
      errorMessage: '',
      loading: false
    }
  },
  watch: {
    show(newVal) {
      this.showChallenge = newVal
      if (newVal) {
        this.reset()
      }
    }
  },
  methods: {
    async submitChallenge() {
      if (!this.passphrase.trim()) {
        this.errorMessage = 'Bitte Passphrase eingeben'
        return
      }

      if (this.totpRequired && !this.totpCode.trim()) {
        this.errorMessage = 'Bitte 2FA Code eingeben'
        return
      }

      this.loading = true
      this.errorMessage = ''

      try {
        // API-Call zur Verifizierung
        const response = await fetch('http://127.0.0.1:5050/api/security/verify', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            passphrase: this.passphrase,
            totp_code: this.totpCode || null
          })
        })

        const data = await response.json()

        if (response.ok && data.verified) {
          this.$emit('verified', {
            token: data.token,
            passphrase: this.passphrase
          })
          this.showChallenge = false
          this.reset()
        } else {
          this.errorMessage = data.error || 'Authentifizierung fehlgeschlagen'
        }
      } catch (error) {
        console.error('Security verification error:', error)
        this.errorMessage = 'Verbindungsfehler zum Backend'
      } finally {
        this.loading = false
      }
    },

    cancel() {
      this.$emit('cancelled')
      this.showChallenge = false
      this.reset()
    },

    reset() {
      this.passphrase = ''
      this.totpCode = ''
      this.errorMessage = ''
      this.loading = false
    }
  }
}
</script>

<style scoped>
.security-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.security-modal {
  background: #1e1e1e;
  border: 1px solid #3a3a3a;
  border-radius: 12px;
  padding: 32px;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal-header {
  margin-bottom: 24px;
  text-align: center;
}

.modal-header h2 {
  margin: 0 0 8px 0;
  color: #ffffff;
  font-size: 24px;
}

.modal-header p {
  margin: 0;
  color: #888;
  font-size: 14px;
}

.modal-body {
  margin-bottom: 24px;
}

.input-group {
  margin-bottom: 16px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  color: #cccccc;
  font-size: 14px;
  font-weight: 500;
}

.input-group input {
  width: 100%;
  padding: 12px;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  transition: all 0.2s;
}

.input-group input:focus {
  outline: none;
  border-color: #4a9eff;
  box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.1);
}

.error-message {
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #ef4444;
  font-size: 14px;
  margin-top: 16px;
}

.modal-footer {
  display: flex;
  gap: 12px;
}

.modal-footer button {
  flex: 1;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4a9eff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #3a8eef;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(74, 158, 255, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #3a3a3a;
  color: #cccccc;
}

.btn-secondary:hover {
  background: #4a4a4a;
}
</style>
