<template>
  <div class="system-monitor">
    <div class="header">
      <h2>System-Monitor</h2>
      <span class="live-indicator" v-if="wsConnected">
        <span class="pulse"></span>
        Live
      </span>
    </div>
    
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-header">
          <span class="icon">💻</span>
          <h3>CPU</h3>
        </div>
        <div class="metric-value">{{ metrics.cpu }}%</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: metrics.cpu + '%', background: getColor(metrics.cpu) }"></div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="icon">🧠</span>
          <h3>RAM</h3>
        </div>
        <div class="metric-value">{{ metrics.memory }}%</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: metrics.memory + '%', background: getColor(metrics.memory) }"></div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="icon">💾</span>
          <h3>Festplatte</h3>
        </div>
        <div class="metric-value">{{ metrics.disk }}%</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: metrics.disk + '%', background: getColor(metrics.disk) }"></div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="icon">🎮</span>
          <h3>GPU</h3>
        </div>
        <div class="metric-value">{{ metrics.gpu }}%</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: metrics.gpu + '%', background: getColor(metrics.gpu) }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useWails } from '../composables/useWails'
import { useWebSocket } from '../composables/useWebSocket'

export default {
  name: 'SystemMonitor',
  setup() {
    const { api } = useWails()
    const { connected: wsConnected, systemMetrics } = useWebSocket()
    
    const metrics = ref({ cpu: 0, memory: 0, disk: 0, gpu: 0 })
    let intervalId = null
    
    const updateMetrics = async () => {
      try {
        const status = await api.GetSystemStatus()
        metrics.value = {
          cpu: Math.round(status.cpu || 0),
          memory: Math.round(status.memory || 0),
          disk: Math.round(status.disk || 0),
          gpu: Math.round(status.gpu || 0)
        }
      } catch (error) {
        console.error('Fehler beim Abrufen der System-Metriken:', error)
      }
    }
    
    const getColor = (value) => {
      if (value < 50) return '#00b4d8'
      if (value < 75) return '#ffd166'
      return '#ef476f'
    }
    
    // Watch for WebSocket updates
    watch(systemMetrics, (newMetrics) => {
      if (newMetrics) {
        metrics.value = {
          cpu: Math.round(newMetrics.cpu || 0),
          memory: Math.round(newMetrics.memory || 0),
          disk: Math.round(newMetrics.disk || 0),
          gpu: Math.round(newMetrics.gpu || 0)
        }
      }
    })
    
    onMounted(() => {
      updateMetrics()
      // Fallback polling if WebSocket not available
      if (!wsConnected.value) {
        intervalId = setInterval(updateMetrics, 2000)
      }
    })
    
    onUnmounted(() => {
      if (intervalId) clearInterval(intervalId)
    })
    
    return {
      metrics,
      wsConnected,
      getColor
    }
  }
}
</script>

<style scoped>
.system-monitor { padding: 20px; }

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

h2 { margin: 0; color: var(--text-primary); }

.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(6, 214, 160, 0.1);
  color: #06d6a0;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.pulse {
  width: 8px;
  height: 8px;
  background: #06d6a0;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.metric-card {
  background: var(--bg-secondary);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.icon { font-size: 32px; }

h3 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.metric-value {
  font-size: 36px;
  font-weight: bold;
  color: var(--accent);
  margin-bottom: 12px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--bg-primary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease, background 0.5s ease;
}
</style>
