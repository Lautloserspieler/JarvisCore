<template>
  <div class="commands-container">
    <header class="view-header">
      <h1>🎮 Benutzerdefinierte Befehle</h1>
      <button @click="refreshCommands" class="btn-refresh" :disabled="isLoading">
        <span :class="{ spinning: isLoading }">🔄</span> Aktualisieren
      </button>
    </header>

    <!-- Add Command Form -->
    <div class="add-command card">
      <h2>➕ Neuen Befehl hinzufügen</h2>
      <form @submit.prevent="addCommand" class="command-form">
        <div class="form-group">
          <label for="pattern">Muster (RegEx oder Text):</label>
          <input
            id="pattern"
            v-model="newPattern"
            type="text"
            placeholder="z.B. 'starte spotify' oder 'zeig.*desktop'"
            class="form-input"
            required
          />
          <small class="help-text">
            💡 Verwende einfachen Text oder RegEx-Muster
          </small>
        </div>
        
        <div class="form-group">
          <label for="response">Antwort:</label>
          <textarea
            id="response"
            v-model="newResponse"
            placeholder="z.B. 'Spotify wird gestartet...'"
            class="form-textarea"
            rows="3"
            required
          ></textarea>
        </div>
        
        <button type="submit" class="btn-add" :disabled="isAdding">
          {{ isAdding ? '⏳ Speichere...' : '✔️ Befehl speichern' }}
        </button>
      </form>
    </div>

    <!-- Commands List -->
    <div class="commands-list card">
      <h2>📋 Vorhandene Befehle</h2>
      
      <div v-if="commands.length > 0" class="table-wrapper">
        <table class="commands-table">
          <thead>
            <tr>
              <th>Kategorie</th>
              <th>Muster</th>
              <th>Antwort</th>
              <th>Aktionen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cmd in commands" :key="cmd.pattern" class="command-row">
              <td class="category">
                <span class="badge">{{ cmd.category || 'custom' }}</span>
              </td>
              <td class="pattern">
                <code>{{ cmd.pattern }}</code>
              </td>
              <td class="response">
                {{ truncate(cmd.response, 60) }}
              </td>
              <td class="actions">
                <button 
                  @click="confirmDelete(cmd.pattern)" 
                  class="btn-delete"
                  title="Befehl löschen"
                >
                  🗑️
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <p v-else class="empty-state">
        Noch keine benutzerdefinierten Befehle vorhanden.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWails } from '../composables/useWails'

const { api } = useWails()

const commands = ref([])
const newPattern = ref('')
const newResponse = ref('')
const isLoading = ref(false)
const isAdding = ref(false)

const truncate = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const loadCommands = async () => {
  isLoading.value = true
  try {
    const data = await api.GetCommands()
    commands.value = data.commands || []
  } catch (error) {
    console.error('Failed to load commands:', error)
    commands.value = []
  } finally {
    isLoading.value = false
  }
}

const addCommand = async () => {
  const pattern = newPattern.value.trim()
  const response = newResponse.value.trim()
  
  if (!pattern || !response) {
    alert('Bitte sowohl Muster als auch Antwort angeben.')
    return
  }
  
  isAdding.value = true
  try {
    await api.AddCustomCommand(pattern, response)
    
    // Reset form
    newPattern.value = ''
    newResponse.value = ''
    
    // Reload commands
    await loadCommands()
    
    alert(`✅ Befehl "${pattern}" wurde gespeichert.`)
  } catch (error) {
    console.error('Failed to add command:', error)
    alert(`❌ Fehler: ${error.message}`)
  } finally {
    isAdding.value = false
  }
}

const confirmDelete = async (pattern) => {
  if (!confirm(`Befehl "${pattern}" wirklich löschen?`)) {
    return
  }
  
  try {
    await api.DeleteCustomCommand(pattern)
    await loadCommands()
    alert(`✅ Befehl wurde gelöscht.`)
  } catch (error) {
    console.error('Failed to delete command:', error)
    alert(`❌ Fehler beim Löschen: ${error.message}`)
  }
}

const refreshCommands = async () => {
  await loadCommands()
}

onMounted(() => {
  loadCommands()
})
</script>

<style scoped>
.commands-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  gap: 20px;
  overflow-y: auto;
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

.btn-refresh {
  padding: 10px 20px;
  background: var(--accent);
  color: var(--bg-primary);
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

.btn-refresh:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.btn-refresh:disabled {
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
  padding: 24px;
  border: 1px solid var(--border-color);
}

.card h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Form */
.command-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.form-input,
.form-textarea {
  padding: 12px 16px;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.help-text {
  font-size: 12px;
  color: var(--text-secondary);
  font-style: italic;
}

.btn-add {
  padding: 12px 24px;
  background: var(--accent);
  color: var(--bg-primary);
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  align-self: flex-start;
}

.btn-add:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.btn-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Table */
.table-wrapper {
  overflow-x: auto;
}

.commands-table {
  width: 100%;
  border-collapse: collapse;
}

.commands-table thead th {
  background: var(--bg-primary);
  padding: 12px 16px;
  text-align: left;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-color);
}

.commands-table tbody td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  font-size: 14px;
  color: var(--text-primary);
}

.command-row:hover {
  background: var(--bg-primary);
}

.category .badge {
  background: var(--accent);
  color: var(--bg-primary);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.pattern code {
  background: var(--bg-primary);
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--accent);
}

.actions {
  text-align: center;
}

.btn-delete {
  padding: 6px 12px;
  background: transparent;
  border: 2px solid #ff4d4d;
  border-radius: 6px;
  color: #ff4d4d;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: #ff4d4d;
  color: white;
  transform: scale(1.1);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}
</style>
