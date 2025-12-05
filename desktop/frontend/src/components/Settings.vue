<template>
  <div class="settings">
    <h2>Einstellungen</h2>
    <div class="settings-sections">
      <div class="settings-section">
        <h3>Verbindung</h3>
        <div class="setting-item">
          <label>JarvisCore URL</label>
          <input type="text" v-model="jarviscoreUrl" placeholder="http://127.0.0.1:5050">
        </div>
        <div class="setting-item">
          <label>API Token</label>
          <input type="password" v-model="apiToken" placeholder="12345678">
        </div>
      </div>
      
      <div class="settings-section">
        <h3>Oberfläche</h3>
        <div class="setting-item">
          <label>Theme</label>
          <select v-model="theme">
            <option value="dark">Dunkel</option>
            <option value="light">Hell</option>
          </select>
        </div>
      </div>
      
      <!-- ✨ NEW: Update Settings -->
      <div class="settings-section">
        <h3>🔄 Updates</h3>
        
        <div class="setting-item checkbox">
          <label>
            <input type="checkbox" v-model="updateSettings.auto_check" />
            Automatisch nach Updates suchen
          </label>
        </div>
        
        <div class="setting-item" v-if="updateSettings.auto_check">
          <label>Prüfintervall</label>
          <select v-model="updateSettings.check_interval">
            <option value="startup">Bei jedem Start</option>
            <option value="daily">Täglich</option>
            <option value="weekly">Wöchentlich</option>
            <option value="never">Nie</option>
          </select>
        </div>
        
        <div class="setting-item checkbox">
          <label>
            <input type="checkbox" v-model="updateSettings.auto_download" />
            Updates automatisch herunterladen
          </label>
        </div>
        
        <div class="setting-item checkbox">
          <label>
            <input type="checkbox" v-model="updateSettings.notify_updates" />
            Benachrichtigung bei verfügbaren Updates
          </label>
        </div>
        
        <div class="setting-item">
          <button @click="checkForUpdatesNow" class="check-update-btn" :disabled="checking">
            {{ checking ? '🔄 Prüfe...' : '🔍 Jetzt nach Updates suchen' }}
          </button>
        </div>
        
        <div v-if="lastCheckTime" class="last-check-info">
          🕒 Letzte Prüfung: {{ lastCheckTime }}
        </div>
      </div>
      
      <div class="settings-section">
        <h3>Über</h3>
        <p><strong>J.A.R.V.I.S. Desktop</strong> {{ currentVersion }}</p>
        <p>Built with Wails + Vue.js + Go</p>
        <p>© 2025 Lautloserspieler</p>
      </div>
    </div>
    
    <div class="settings-actions">
      <button class="save-btn" @click="saveSettings">Speichern</button>
    </div>
    
    <!-- Update Notification -->
    <UpdateNotification
      v-if="showUpdateModal"
      :update-info="updateInfo"
      @close="showUpdateModal = false"
    />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import UpdateNotification from './UpdateNotification.vue'

export default {
  name: 'Settings',
  components: {
    UpdateNotification
  },
  setup() {
    const jarviscoreUrl = ref('http://127.0.0.1:5050')
    const apiToken = ref('12345678')
    const theme = ref('dark')
    const currentVersion = ref('v1.0.0')
    const lastCheckTime = ref('')
    const checking = ref(false)
    const showUpdateModal = ref(false)
    const updateInfo = ref(null)
    
    const updateSettings = ref({
      auto_check: true,
      auto_download: false,
      check_interval: 'daily',
      notify_updates: true
    })
    
    // Load settings on mount
    onMounted(async () => {
      try {
        // Get current version
        if (window.go && window.go.app && window.go.app.App) {
          currentVersion.value = await window.go.app.App.GetCurrentVersion()
          
          // Load update settings
          const settings = await window.go.app.App.GetUpdateSettings()
          updateSettings.value = settings
          
          if (settings.last_check_time) {
            lastCheckTime.value = new Date(settings.last_check_time).toLocaleString('de-DE')
          }
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
      }
    })
    
    const checkForUpdatesNow = async () => {
      if (checking.value) return
      
      checking.value = true
      
      try {
        if (!window.go || !window.go.app || !window.go.app.App) {
          throw new Error('Wails runtime not available')
        }
        
        const info = await window.go.app.App.CheckForUpdates()
        lastCheckTime.value = new Date().toLocaleString('de-DE')
        
        // Check if version is skipped
        const skippedVersion = localStorage.getItem('skip_version')
        
        if (info.available && info.latest_version !== skippedVersion) {
          updateInfo.value = info
          showUpdateModal.value = true
        } else if (info.available && info.latest_version === skippedVersion) {
          alert('ℹ️ Update verfügbar, aber von dir übersprungen: ' + info.latest_version)
        } else {
          alert('✅ Du nutzt bereits die neueste Version!')
        }
      } catch (error) {
        console.error('Update check failed:', error)
        alert('❌ Update-Prüfung fehlgeschlagen: ' + error.message)
      } finally {
        checking.value = false
      }
    }
    
    const saveSettings = async () => {
      try {
        if (window.go && window.go.app && window.go.app.App) {
          await window.go.app.App.SaveUpdateSettings(updateSettings.value)
        }
        alert('✅ Einstellungen gespeichert!')
      } catch (error) {
        console.error('Failed to save settings:', error)
        alert('❌ Fehler beim Speichern: ' + error.message)
      }
    }
    
    return {
      jarviscoreUrl,
      apiToken,
      theme,
      currentVersion,
      updateSettings,
      lastCheckTime,
      checking,
      showUpdateModal,
      updateInfo,
      checkForUpdatesNow,
      saveSettings
    }
  }
}
</script>

<style scoped>
.settings { padding: 20px; max-width: 800px; }
h2 { margin: 0 0 24px 0; }
.settings-sections { display: flex; flex-direction: column; gap: 24px; margin-bottom: 32px; }
.settings-section { background: var(--bg-secondary); padding: 24px; border-radius: 12px; border: 1px solid var(--border-color); }
.settings-section h3 { margin: 0 0 16px 0; color: var(--text-primary); }
.setting-item { margin-bottom: 16px; }
.setting-item:last-child { margin-bottom: 0; }
.setting-item label { display: block; margin-bottom: 8px; color: var(--text-primary); font-size: 14px; }
.setting-item input[type="text"],
.setting-item input[type="password"],
.setting-item select {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
}

/* Checkbox styling */
.setting-item.checkbox label {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.setting-item.checkbox input[type="checkbox"] {
  width: auto;
  margin-right: 10px;
  cursor: pointer;
}

/* Check update button */
.check-update-btn {
  width: 100%;
  padding: 12px;
  background: var(--accent, #2196F3);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.check-update-btn:hover:not(:disabled) {
  background: var(--accent-hover, #1976D2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

.check-update-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.last-check-info {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--bg-primary);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
}

.save-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.save-btn:hover {
  background: var(--accent-hover);
}
</style>
