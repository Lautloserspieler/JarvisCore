<template>
  <div class="status-bar">
    <div class="status-left">
      <span class="status-indicator" :class="{ online: isOnline }"></span>
      <span class="status-text">{{ statusText }}</span>
    </div>
    <div class="status-right">
      <span class="time">{{ currentTime }}</span>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'StatusBar',
  setup() {
    const isOnline = ref(true)
    const statusText = ref('Verbunden mit JarvisCore')
    const currentTime = ref('')
    let timeInterval = null
    
    const updateTime = () => {
      const now = new Date()
      currentTime.value = now.toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    onMounted(() => {
      updateTime()
      timeInterval = setInterval(updateTime, 1000)
    })
    
    onUnmounted(() => {
      if (timeInterval) clearInterval(timeInterval)
    })
    
    return { isOnline, statusText, currentTime }
  }
}
</script>

<style scoped>
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}
.status-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--text-secondary);
  transition: all 0.3s;
}
.status-indicator.online {
  background: var(--success);
  box-shadow: 0 0 10px var(--success);
}
.status-text {
  font-size: 14px;
  color: var(--text-primary);
}
.status-right {
  font-size: 14px;
  color: var(--text-secondary);
  font-family: monospace;
}
</style>
