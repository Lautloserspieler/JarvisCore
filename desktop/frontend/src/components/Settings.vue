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
      <div class="settings-section">
        <h3>Über</h3>
        <p>J.A.R.V.I.S. Desktop v1.0.0</p>
        <p>Built with Wails + Vue.js + Go</p>
        <p>© 2025 Lautloserspieler</p>
      </div>
    </div>
    <div class="settings-actions">
      <button class="save-btn" @click="saveSettings">Speichern</button>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'Settings',
  setup() {
    const jarviscoreUrl = ref('http://127.0.0.1:5050')
    const apiToken = ref('12345678')
    const theme = ref('dark')
    
    const saveSettings = () => {
      alert('Einstellungen gespeichert!')
    }
    
    return { jarviscoreUrl, apiToken, theme, saveSettings }
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
.setting-item input, .setting-item select { width: 100%; padding: 8px 12px; background: var(--bg-primary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 8px; font-size: 14px; }
.save-btn { padding: 12px 24px; border: none; border-radius: 8px; background: var(--accent); color: white; font-weight: 600; cursor: pointer; transition: all 0.3s; }
.save-btn:hover { background: var(--accent-hover); }
</style>
