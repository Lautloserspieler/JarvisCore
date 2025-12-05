<template>
  <div v-if="visible" class="update-modal-overlay" @click="close">
    <div class="update-modal" @click.stop>
      <div class="modal-header">
        <h2>🎉 Update verfügbar!</h2>
        <button class="close-btn" @click="close">✕</button>
      </div>
      
      <div class="modal-body">
        <div class="version-info">
          <span class="version-current">{{ updateInfo.current_version }}</span>
          <span class="arrow">→</span>
          <span class="version-latest">{{ updateInfo.latest_version }}</span>
        </div>
        
        <div class="meta-info">
          <span class="published-date">
            📅 Veröffentlicht: {{ formattedDate }}
          </span>
        </div>
        
        <div class="changelog">
          <h3>🌟 Was ist neu?</h3>
          <div class="changelog-content" v-html="formattedChangelog"></div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="downloadUpdate" class="btn-primary">
          📥 Herunterladen
        </button>
        <button @click="openReleases" class="btn-secondary">
          🔗 Release Notes ansehen
        </button>
        <button @click="skipVersion" class="btn-link">
          Diese Version überspringen
        </button>
        <button @click="close" class="btn-link">
          Später erinnern
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  updateInfo: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])

const visible = ref(true)

const formattedDate = computed(() => {
  if (!props.updateInfo.published_at) return ''
  const date = new Date(props.updateInfo.published_at)
  return date.toLocaleDateString('de-DE', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

const formattedChangelog = computed(() => {
  if (!props.updateInfo.changelog) return '<p>Keine Änderungen verfügbar.</p>'
  
  // Simple Markdown to HTML converter
  let html = props.updateInfo.changelog
  
  // Headers
  html = html.replace(/###\s+(.+)/g, '<h4>$1</h4>')
  html = html.replace(/##\s+(.+)/g, '<h3>$1</h3>')
  
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  
  // Lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
  
  // Line breaks
  html = html.replace(/\n\n/g, '</p><p>')
  html = '<p>' + html + '</p>'
  
  return html
})

const downloadUpdate = () => {
  if (props.updateInfo.download_url) {
    window.open(props.updateInfo.download_url, '_blank')
  } else {
    // Fallback to release page
    window.open(props.updateInfo.release_url, '_blank')
  }
  close()
}

const openReleases = () => {
  window.open(props.updateInfo.release_url, '_blank')
}

const skipVersion = () => {
  // Save skipped version to localStorage
  localStorage.setItem('skip_version', props.updateInfo.latest_version)
  close()
}

const close = () => {
  visible.value = false
  emit('close')
}
</script>

<style scoped>
.update-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.update-modal {
  background: var(--bg-primary, #1e1e1e);
  border-radius: 16px;
  width: 600px;
  max-width: 90vw;
  max-height: 85vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid var(--border-color, #333);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  color: var(--text-primary, #fff);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary, #888);
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--bg-hover, #333);
  color: var(--text-primary, #fff);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.version-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-size: 28px;
  margin-bottom: 12px;
}

.version-current {
  color: var(--text-secondary, #888);
  font-weight: 500;
}

.arrow {
  color: var(--text-secondary, #888);
}

.version-latest {
  color: #4CAF50;
  font-weight: bold;
}

.meta-info {
  text-align: center;
  margin-bottom: 24px;
  color: var(--text-secondary, #888);
  font-size: 14px;
}

.changelog {
  background: var(--bg-secondary, #252525);
  border-radius: 8px;
  padding: 20px;
}

.changelog h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  color: var(--text-primary, #fff);
}

.changelog-content {
  color: var(--text-secondary, #ccc);
  line-height: 1.6;
}

.changelog-content :deep(h3) {
  font-size: 16px;
  margin-top: 16px;
  margin-bottom: 8px;
  color: var(--text-primary, #fff);
}

.changelog-content :deep(h4) {
  font-size: 14px;
  margin-top: 12px;
  margin-bottom: 6px;
  color: var(--text-primary, #fff);
}

.changelog-content :deep(ul) {
  margin: 8px 0;
  padding-left: 24px;
}

.changelog-content :deep(li) {
  margin: 4px 0;
}

.changelog-content :deep(strong) {
  color: var(--text-primary, #fff);
}

.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid var(--border-color, #333);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.btn-primary,
.btn-secondary,
.btn-link {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4CAF50;
  color: white;
}

.btn-primary:hover {
  background: #45a049;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.btn-secondary {
  background: var(--bg-secondary, #333);
  color: var(--text-primary, #fff);
}

.btn-secondary:hover {
  background: var(--bg-hover, #444);
}

.btn-link {
  background: transparent;
  color: var(--text-secondary, #888);
  padding: 8px 16px;
}

.btn-link:hover {
  color: var(--text-primary, #fff);
  background: var(--bg-hover, rgba(255, 255, 255, 0.05));
}

/* Scrollbar styling */
.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: var(--bg-secondary, #252525);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: var(--text-secondary, #555);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: var(--text-primary, #777);
}
</style>
