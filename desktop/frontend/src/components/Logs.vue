<template>
  <div class="logs-container">
    <header class="view-header">
      <h1>📋 System-Logs</h1>
      <div class="header-actions">
        <button @click="refreshLogs" class="btn-refresh" :disabled="isLoading">
          <span :class="{ spinning: isLoading }">🔄</span> Aktualisieren
        </button>
        <button @click="confirmClearLogs" class="btn-danger" :disabled="isLoading">
          🗑️ Löschen
        </button>
      </div>
    </header>

    <!-- Search & Filter Controls -->
    <div class="logs-controls card">
      <div class="control-group">
        <label for="log-search">🔍 Suche:</label>
        <input
          id="log-search"
          v-model="searchQuery"
          type="text"
          placeholder="Logs durchsuchen..."
          class="search-input"
          @keyup.enter="refreshLogs"
        />
      </div>
      
      <div class="control-group">
        <label for="log-lines">📊 Zeilen:</label>
        <select id="log-lines" v-model="lineLimit" @change="refreshLogs" class="select-input">
          <option :value="50">50 Zeilen</option>
          <option :value="100">100 Zeilen</option>
          <option :value="200">200 Zeilen</option>
          <option :value="500">500 Zeilen</option>
          <option :value="1000">1000 Zeilen</option>
        </select>
      </div>
      
      <div class="control-group">
        <label>🎯 Filter:</label>
        <div class="filter-buttons">
          <button 
            v-for="level in logLevels" 
            :key="level"
            @click="toggleLevel(level)"
            :class="['filter-btn', { active: selectedLevels.includes(level) }]"
          >
            {{ level }}
          </button>
        </div>
      </div>
    </div>

    <!-- Log Output -->
    <div class="logs-output card">
      <div v-if="isLoading" class="loading">
        <span class="spinner"></span> Lade Logs...
      </div>
      
      <pre v-else-if="filteredLogs" class="log-content">{{ filteredLogs }}</pre>
      
      <div v-else class="logs-empty">
        Keine Logs verfügbar
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useWails } from '../composables/useWails'

const { api } = useWails()

const searchQuery = ref('')
const lineLimit = ref(200)
const logOutput = ref('')
const isLoading = ref(false)

const logLevels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
const selectedLevels = ref([...logLevels])

const filteredLogs = computed(() => {
  if (!logOutput.value) return ''
  
  const lines = logOutput.value.split('\n')
  return lines
    .filter(line => {
      // Filter by log level
      const hasLevel = selectedLevels.value.some(level => line.includes(level))
      if (!hasLevel && selectedLevels.value.length < logLevels.length) return false
      
      // Filter by search query
      if (searchQuery.value) {
        return line.toLowerCase().includes(searchQuery.value.toLowerCase())
      }
      
      return true
    })
    .join('\n')
})

const toggleLevel = (level) => {
  const index = selectedLevels.value.indexOf(level)
  if (index > -1) {
    selectedLevels.value.splice(index, 1)
  } else {
    selectedLevels.value.push(level)
  }
}

const refreshLogs = async () => {
  isLoading.value = true
  try {
    const params = new URLSearchParams({
      lines: lineLimit.value.toString()
    })
    
    if (searchQuery.value) {
      params.set('q', searchQuery.value)
    }
    
    const data = await api.GetLogs(params.toString())
    logOutput.value = Array.isArray(data.logs) ? data.logs.join('\n') : data.logs || ''
  } catch (error) {
    console.error('Failed to load logs:', error)
    logOutput.value = `Fehler beim Laden der Logs: ${error.message}`
  } finally {
    isLoading.value = false
  }
}

const confirmClearLogs = async () => {
  if (!confirm('Logs wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.')) {
    return
  }
  
  isLoading.value = true
  try {
    await api.ClearLogs()
    logOutput.value = ''
    alert('Logs wurden gelöscht.')
  } catch (error) {
    console.error('Failed to clear logs:', error)
    alert(`Fehler beim Löschen: ${error.message}`)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  refreshLogs()
})
</script>

<style scoped>
.logs-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  gap: 20px;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.view-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn-refresh,
.btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-refresh {
  background: var(--accent);
  color: var(--bg-primary);
}

.btn-refresh:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.btn-danger {
  background: #ff4d4d;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #ff3333;
  transform: translateY(-1px);
}

.btn-refresh:disabled,
.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-color);
}

/* Controls */
.logs-controls {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 20px;
  align-items: end;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-group label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.search-input,
.select-input {
  padding: 10px 14px;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.2s;
}

.search-input:focus,
.select-input:focus {
  outline: none;
  border-color: var(--accent);
}

.filter-buttons {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 8px 16px;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
}

.filter-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--bg-primary);
}

.filter-btn:hover {
  border-color: var(--accent);
}

/* Log Output */
.logs-output {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.log-content {
  flex: 1;
  margin: 0;
  padding: 16px;
  background: var(--bg-primary);
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  overflow: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.loading,
.logs-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 14px;
  gap: 12px;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style>
