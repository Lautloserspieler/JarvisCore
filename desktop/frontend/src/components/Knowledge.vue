<template>
  <div class="knowledge-container">
    <header class="view-header">
      <h1>📚 Wissensdatenbank</h1>
      <button @click="refreshKnowledge" class="btn-refresh" :disabled="isLoading">
        <span :class="{ spinning: isLoading }">🔄</span> Aktualisieren
      </button>
    </header>

    <div class="knowledge-content">
      <!-- Statistics Card -->
      <div class="knowledge-stats card">
        <h2>📊 Statistiken</h2>
        <div v-if="knowledgeStats" class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">Dokumente</div>
            <div class="stat-value">{{ formatNumber(knowledgeStats.total_documents) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Vektoren</div>
            <div class="stat-value">{{ formatNumber(knowledgeStats.total_vectors) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Kategorien</div>
            <div class="stat-value">{{ formatNumber(knowledgeStats.categories) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Letzte Abfrage</div>
            <div class="stat-value">{{ knowledgeStats.last_query || '–' }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Datenbank-Größe</div>
            <div class="stat-value">{{ formatBytes(knowledgeStats.db_size) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Index-Größe</div>
            <div class="stat-value">{{ formatBytes(knowledgeStats.index_size) }}</div>
          </div>
        </div>
        <div v-else class="loading">
          <span class="spinner"></span> Lade Statistiken...
        </div>
      </div>

      <!-- Live Feed Card -->
      <div class="knowledge-feed card">
        <div class="feed-header">
          <h2>📡 Live-Feed</h2>
          <span v-if="knowledgeFeed.length > 0" class="feed-count">
            {{ knowledgeFeed.length }} Einträge
          </span>
        </div>
        
        <div class="feed-list">
          <div 
            v-for="(entry, index) in knowledgeFeed" 
            :key="index"
            class="feed-item"
            :class="{ 'feed-item-new': index === 0 }"
          >
            <span class="feed-time">{{ entry.ts }}</span>
            <span class="feed-text">{{ entry.text }}</span>
          </div>
          
          <div v-if="knowledgeFeed.length === 0" class="feed-empty">
            💭 Keine aktuellen Aktivitäten
          </div>
        </div>
      </div>

      <!-- Knowledge Sources Card -->
      <div class="knowledge-sources card">
        <h2>📚 Quellen</h2>
        <div v-if="knowledgeSources.length > 0" class="sources-list">
          <div 
            v-for="source in knowledgeSources" 
            :key="source.name"
            class="source-item"
          >
            <div class="source-header">
              <span class="source-name">{{ source.name }}</span>
              <span class="source-count">{{ source.documents }} Dokumente</span>
            </div>
            <div class="source-meta">
              <span>Typ: {{ source.type }}</span>
              <span v-if="source.last_update">
                Aktualisiert: {{ formatRelativeTime(source.last_update) }}
              </span>
            </div>
          </div>
        </div>
        <div v-else class="sources-empty">
          Keine Quellen konfiguriert
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useWails } from '../composables/useWails'
import { useWebSocket } from '../composables/useWebSocket'

const { api } = useWails()
const { knowledgeFeed } = useWebSocket()

const knowledgeStats = ref(null)
const knowledgeSources = ref([])
const isLoading = ref(false)

const formatNumber = (value) => {
  if (value === null || value === undefined) return '–'
  return new Intl.NumberFormat('de-DE').format(value)
}

const formatBytes = (bytes) => {
  if (!bytes) return '–'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = bytes
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex++
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`
}

const formatRelativeTime = (timestamp) => {
  if (!timestamp) return '–'
  try {
    const date = new Date(timestamp)
    const diff = Date.now() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return 'gerade eben'
    if (minutes === 1) return 'vor einer Minute'
    if (minutes < 60) return `vor ${minutes} Minuten`
    
    const hours = Math.floor(minutes / 60)
    if (hours === 1) return 'vor einer Stunde'
    if (hours < 24) return `vor ${hours} Stunden`
    
    const days = Math.floor(hours / 24)
    if (days === 1) return 'gestern'
    return `vor ${days} Tagen`
  } catch {
    return '–'
  }
}

const loadKnowledgeStats = async () => {
  try {
    const data = await api.GetKnowledgeStats()
    knowledgeStats.value = data.stats || data
    
    // Extract sources if available
    if (data.sources) {
      knowledgeSources.value = data.sources
    }
  } catch (error) {
    console.error('Failed to load knowledge stats:', error)
    knowledgeStats.value = {}
  }
}

const refreshKnowledge = async () => {
  isLoading.value = true
  try {
    await loadKnowledgeStats()
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadKnowledgeStats()
})
</script>

<style scoped>
.knowledge-container {
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

.knowledge-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  flex: 1;
}

.card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-color);
}

.card h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-item {
  padding: 16px;
  background: var(--bg-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
}

/* Feed List */
.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.feed-count {
  font-size: 14px;
  color: var(--text-secondary);
  background: var(--bg-primary);
  padding: 4px 12px;
  border-radius: 12px;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 500px;
  overflow-y: auto;
}

.feed-item {
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  border-left: 3px solid var(--accent);
  display: flex;
  gap: 12px;
  transition: all 0.2s;
}

.feed-item-new {
  animation: slideInFade 0.3s ease-out;
}

@keyframes slideInFade {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.feed-time {
  color: var(--text-secondary);
  font-size: 12px;
  font-family: 'Courier New', monospace;
  flex-shrink: 0;
  min-width: 70px;
}

.feed-text {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
}

.feed-empty {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px;
  font-size: 14px;
}

/* Sources List */
.sources-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-item {
  padding: 16px;
  background: var(--bg-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  transition: border-color 0.2s;
}

.source-item:hover {
  border-color: var(--accent);
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.source-name {
  font-weight: 600;
  color: var(--text-primary);
}

.source-count {
  font-size: 14px;
  color: var(--accent);
}

.source-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

.sources-empty {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px;
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
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
