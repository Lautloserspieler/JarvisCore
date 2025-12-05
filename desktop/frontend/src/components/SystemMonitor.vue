<template>
  <div class="system-monitor">
    <h2>System-Monitor</h2>
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
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'SystemMonitor',
  setup() {
    const metrics = ref({ cpu: 0, memory: 0, disk: 0, gpu: 0 })
    let intervalId = null
    
    const updateMetrics = async () => {
      // TODO: Wails Backend-Call
      metrics.value = {
        cpu: Math.floor(Math.random() * 30) + 30,
        memory: Math.floor(Math.random() * 20) + 50,
        disk: Math.floor(Math.random() * 10) + 35,
        gpu: Math.floor(Math.random() * 40) + 20
      }
    }
    
    const getColor = (value) => {
      if (value < 50) return '#00b4d8'
      if (value < 75) return '#ffd166'
      return '#ef476f'
    }
    
    onMounted(() => {
      updateMetrics()
      intervalId = setInterval(updateMetrics, 2000)
    })
    
    onUnmounted(() => {
      if (intervalId) clearInterval(intervalId)
    })
    
    return { metrics, getColor }
  }
}
</script>

<style scoped>
.system-monitor { padding: 20px; }
h2 { margin: 0 0 24px 0; color: var(--text-primary); }
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
.metric-card { background: var(--bg-secondary); padding: 24px; border-radius: 12px; border: 1px solid var(--border-color); }
.metric-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.icon { font-size: 32px; }
h3 { margin: 0; font-size: 18px; color: var(--text-primary); }
.metric-value { font-size: 36px; font-weight: bold; color: var(--accent); margin-bottom: 12px; }
.progress-bar { width: 100%; height: 8px; background: var(--bg-primary); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease, background 0.5s ease; }
</style>
