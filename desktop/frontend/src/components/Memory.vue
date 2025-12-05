<template>
  <div class="memory-container">
    <header class="view-header">
      <h1>🧠 Gedächtnis-System</h1>
      <button @click="refreshMemory" class="btn-refresh" :disabled="isLoading">
        <span :class="{ spinning: isLoading }">🔄</span> Aktualisieren
      </button>
    </header>

    <div class="memory-content">
      <!-- Memory Search -->
      <div class="memory-search card">
        <h2>🔍 Erinnerungen durchsuchen</h2>
        <form @submit.prevent="searchMemory" class="search-form">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Suche nach Themen, Ereignissen, Kontext..."
            class="search-input"
          />
          <button type="submit" class="btn-search" :disabled="isSearching">
            {{ isSearching ? 'Suche...' : '🔍 Suchen' }}
          </button>
        </form>
        
        <div v-if="searchResults.length > 0" class="search-results">
          <h3>Suchergebnisse ({{ searchResults.length }})</h3>
          <div class="results-list">
            <div 
              v-for="(result, index) in searchResults" 
              :key="index"
              class="result-item"
            >
              <div class="result-header">
                <span class="result-score">🎯 Score: {{ result.score?.toFixed(2) || '–' }}</span>
                <span class="result-time">{{ formatTime(result.timestamp) }}</span>
              </div>
              <div class="result-content">{{ result.text || JSON.stringify(result.metadata) }}</div>
            </div>
          </div>
        </div>
        
        <div v-else-if="searchQuery && !isSearching" class="search-empty">
          Keine Ergebnisse für "{{ searchQuery }}"
        </div>
      </div>

      <!-- Short-term Summary -->
      <div class="memory-summary card">
        <h2>📋 Kurzzeitgedächtnis</h2>
        <p class="summary-text">
          {{ memorySnapshot.short_term_summary || 'Keine Daten verfügbar.' }}
        </p>
        
        <div v-if="memorySnapshot.conversation_context" class="context-box">
          <h3>💬 Konversations-Kontext</h3>
          <p>{{ memorySnapshot.conversation_context }}</p>
        </div>
      </div>

      <!-- Active Topics -->
      <div class="memory-topics card">
        <h2>🏷️ Aktive Themen</h2>
        <ul v-if="memorySnapshot.active_topics?.length" class="topics-list">
          <li v-for="topic in memorySnapshot.active_topics" :key="topic" class="topic-item">
            📌 {{ topic }}
          </li>
        </ul>
        <p v-else class="empty-state">Keine aktiven Themen</p>
      </div>

      <!-- Recent Messages -->
      <div class="memory-messages card">
        <h2>💬 Letzte Nachrichten</h2>
        <div v-if="memorySnapshot.recent_messages?.length" class="messages-list">
          <div 
            v-for="(message, index) in memorySnapshot.recent_messages.slice().reverse()" 
            :key="index"
            class="message-item"
            :class="`message-${message.role}`"
          >
            <div class="message-header">
              <span class="message-role">{{ getRoleLabel(message.role) }}</span>
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            </div>
            <div class="message-content">{{ message.content }}</div>
          </div>
        </div>
        <p v-else class="empty-state">Noch keine Konversation gespeichert.</p>
      </div>

      <!-- Timeline -->
      <div class="memory-timeline card">
        <h2>⏱️ Ereignis-Timeline</h2>
        <div v-if="memorySnapshot.timeline?.length" class="timeline-list">
          <div 
            v-for="(event, index) in memorySnapshot.timeline" 
            :key="index"
            class="timeline-item"
          >
            <div class="timeline-marker"></div>
            <div class="timeline-content">
              <div class="timeline-header">
                <span class="event-type">📦 {{ event.event_type }}</span>
                <span class="event-time">{{ formatTime(event.timestamp) }}</span>
              </div>
              <pre class="event-payload">{{ JSON.stringify(event.payload, null, 2) }}</pre>
            </div>
          </div>
        </div>
        <p v-else class="empty-state">Keine Timeline-Einträge.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWails } from '../composables/useWails'

const { api } = useWails()

const memorySnapshot = ref({})
const searchQuery = ref('')
const searchResults = ref([])
const isLoading = ref(false)
const isSearching = ref(false)

const formatTime = (timestamp) => {
  if (!timestamp) return '–'
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return '–'
  }
}

const getRoleLabel = (role) => {
  const labels = {
    user: '👤 Benutzer',
    assistant: '🤖 J.A.R.V.I.S.',
    system: '⚙️ System'
  }
  return labels[role] || role
}

const loadMemory = async (query = '') => {
  try {
    const data = await api.GetMemory(query)
    memorySnapshot.value = data.memory || data
    
    if (query && data.memory?.search_results) {
      searchResults.value = data.memory.search_results
    }
  } catch (error) {
    console.error('Failed to load memory:', error)
    memorySnapshot.value = {}
  }
}

const searchMemory = async () => {
  const query = searchQuery.value.trim()
  if (!query) {
    searchResults.value = []
    await loadMemory()
    return
  }
  
  isSearching.value = true
  try {
    await loadMemory(query)
  } finally {
    isSearching.value = false
  }
}

const refreshMemory = async () => {
  isLoading.value = true
  try {
    await loadMemory(searchQuery.value)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadMemory()
})
</script>

<style scoped>
.memory-container {
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
  margin-bottom: 10px;
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

.memory-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 20px;
}

.card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-color);
}

.card h2 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.card h3 {
  margin: 16px 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Search Form */
.search-form {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 12px 16px;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
}

.btn-search {
  padding: 12px 24px;
  background: var(--accent);
  color: var(--bg-primary);
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-search:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-search:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Search Results */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.result-item {
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  border-left: 3px solid var(--accent);
}

.result-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
}

.result-score {
  color: var(--accent);
  font-weight: 600;
}

.result-time {
  color: var(--text-secondary);
}

.result-content {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
}

.search-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* Memory Summary */
.summary-text {
  color: var(--text-primary);
  line-height: 1.6;
  margin: 0;
}

.context-box {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-primary);
  border-radius: 8px;
  border-left: 3px solid var(--accent);
}

.context-box h3 {
  margin: 0 0 12px 0;
}

.context-box p {
  margin: 0;
  color: var(--text-primary);
  line-height: 1.5;
}

/* Topics List */
.topics-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-item {
  padding: 8px 16px;
  background: var(--bg-primary);
  border-radius: 20px;
  font-size: 14px;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

/* Messages List */
.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 500px;
  overflow-y: auto;
}

.message-item {
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  border-left: 3px solid var(--border-color);
}

.message-user {
  border-left-color: #4a9eff;
}

.message-assistant {
  border-left-color: var(--accent);
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
}

.message-role {
  font-weight: 600;
  color: var(--text-primary);
}

.message-time {
  color: var(--text-secondary);
}

.message-content {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
}

/* Timeline */
.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 600px;
  overflow-y: auto;
}

.timeline-item {
  display: flex;
  gap: 16px;
}

.timeline-marker {
  width: 12px;
  height: 12px;
  background: var(--accent);
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
  box-shadow: 0 0 0 4px rgba(0, 180, 216, 0.2);
}

.timeline-content {
  flex: 1;
  padding-bottom: 16px;
  border-left: 2px solid var(--border-color);
  padding-left: 16px;
  margin-left: -8px;
}

.timeline-item:last-child .timeline-content {
  border-left: none;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.event-type {
  font-weight: 600;
  color: var(--text-primary);
}

.event-time {
  color: var(--text-secondary);
  font-size: 12px;
}

.event-payload {
  background: var(--bg-primary);
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  color: var(--text-secondary);
  overflow-x: auto;
  margin: 0;
}

/* Empty States */
.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}
</style>
