<template>
  <div class="training-container">
    <header class="view-header">
      <h1>🎯 Training & Learning</h1>
      <button @click="runTraining" class="btn-train" :disabled="isTraining">
        {{ isTraining ? '⏳ Training läuft...' : '▶️ Training starten' }}
      </button>
    </header>

    <div class="training-content">
      <!-- Top Commands Card -->
      <div class="top-commands card">
        <h2>🔝 Häufigste Befehle</h2>
        <div v-if="topCommands.length > 0" class="commands-list">
          <div 
            v-for="(cmd, index) in topCommands" 
            :key="cmd.command"
            class="command-item"
          >
            <span class="rank">#{{ index + 1 }}</span>
            <span class="command-text">{{ cmd.command }}</span>
            <span class="command-count">{{ cmd.count }}x</span>
          </div>
        </div>
        <p v-else class="empty-state">Keine Befehlsdaten verfügbar</p>
      </div>

      <!-- Reinforcement Learning Card -->
      <div class="reinforcement card">
        <h2>🛡️ Reinforcement Learning</h2>
        <div v-if="reinforcement" class="reinforcement-stats">
          <div class="stat-item positive">
            <span class="stat-icon">👍</span>
            <span class="stat-label">Positives Feedback</span>
            <span class="stat-value">{{ reinforcement.positive_feedback || 0 }}</span>
          </div>
          <div class="stat-item negative">
            <span class="stat-icon">👎</span>
            <span class="stat-label">Negatives Feedback</span>
            <span class="stat-value">{{ reinforcement.negative_feedback || 0 }}</span>
          </div>
          <div class="stat-item ratio">
            <span class="stat-icon">📊</span>
            <span class="stat-label">Erfolgsrate</span>
            <span class="stat-value">{{ calculateSuccessRate() }}%</span>
          </div>
        </div>
        <pre v-else class="reinforcement-data">{{ JSON.stringify(reinforcement, null, 2) }}</pre>
      </div>

      <!-- Long-term Learning Card -->
      <div class="long-term card">
        <h2>🧠 Langzeitgedächtnis</h2>
        <div v-if="longTerm" class="long-term-data">
          <pre>{{ JSON.stringify(longTerm, null, 2) }}</pre>
        </div>
        <p v-else class="empty-state">Noch keine Trainingsdaten</p>
      </div>

      <!-- Training Log Card -->
      <div class="training-log card">
        <h2>📜 Trainingsprotokoll</h2>
        <div v-if="trainingLog.length > 0" class="log-list">
          <div 
            v-for="(entry, index) in trainingLog" 
            :key="index"
            class="log-entry"
          >
            <span class="log-time">{{ entry.timestamp }}</span>
            <span class="log-message">{{ entry.message }}</span>
          </div>
        </div>
        <p v-else class="empty-state">Noch keine Trainingseinträge</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWails } from '../composables/useWails'
import { useWebSocket } from '../composables/useWebSocket'

const { api } = useWails()
const { trainingStatus } = useWebSocket()

const topCommands = ref([])
const reinforcement = ref(null)
const longTerm = ref(null)
const trainingLog = ref([])
const isTraining = ref(false)

const calculateSuccessRate = () => {
  if (!reinforcement.value) return 0
  const positive = reinforcement.value.positive_feedback || 0
  const negative = reinforcement.value.negative_feedback || 0
  const total = positive + negative
  if (total === 0) return 0
  return Math.round((positive / total) * 100)
}

const loadTrainingData = async () => {
  try {
    const data = await api.GetTraining()
    
    if (data.training) {
      topCommands.value = data.training.learning?.top_commands || []
      reinforcement.value = data.training.reinforcement || null
      longTerm.value = data.training.long_term || null
    }
  } catch (error) {
    console.error('Failed to load training data:', error)
  }
}

const runTraining = async () => {
  if (isTraining.value) return
  
  isTraining.value = true
  try {
    const now = new Date().toLocaleTimeString()
    trainingLog.value.unshift({
      timestamp: now,
      message: 'Training-Zyklus gestartet...'
    })
    
    await api.RunTrainingCycle()
    
    trainingLog.value.unshift({
      timestamp: new Date().toLocaleTimeString(),
      message: '✅ Training erfolgreich abgeschlossen'
    })
    
    // Reload data
    await loadTrainingData()
  } catch (error) {
    console.error('Training failed:', error)
    trainingLog.value.unshift({
      timestamp: new Date().toLocaleTimeString(),
      message: `❌ Training fehlgeschlagen: ${error.message}`
    })
  } finally {
    isTraining.value = false
  }
}

onMounted(() => {
  loadTrainingData()
})
</script>

<style scoped>
.training-container {
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

.btn-train {
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

.btn-train:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.btn-train:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.training-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
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

/* Top Commands */
.commands-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.command-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  border-left: 3px solid var(--accent);
}

.rank {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
  min-width: 40px;
}

.command-text {
  flex: 1;
  color: var(--text-primary);
  font-size: 15px;
}

.command-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 4px 12px;
  border-radius: 12px;
}

/* Reinforcement Learning */
.reinforcement-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-item {
  padding: 16px;
  background: var(--bg-primary);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  border: 2px solid var(--border-color);
}

.stat-item.positive {
  border-color: #4caf50;
}

.stat-item.negative {
  border-color: #f44336;
}

.stat-item.ratio {
  border-color: var(--accent);
}

.stat-icon {
  font-size: 32px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.reinforcement-data {
  background: var(--bg-primary);
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  overflow-x: auto;
  margin: 0;
}

/* Long-term Learning */
.long-term-data pre {
  background: var(--bg-primary);
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  font-family: 'Courier New', monospace;
  color: var(--text-secondary);
  overflow-x: auto;
  margin: 0;
}

/* Training Log */
.log-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.log-entry {
  display: flex;
  gap: 12px;
  padding: 10px;
  background: var(--bg-primary);
  border-radius: 6px;
  font-size: 14px;
}

.log-time {
  color: var(--text-secondary);
  font-family: 'Courier New', monospace;
  font-size: 12px;
  flex-shrink: 0;
}

.log-message {
  color: var(--text-primary);
  line-height: 1.5;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}
</style>
