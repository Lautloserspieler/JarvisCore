<template>
  <div class="model-manager">
    <h2>LLM-Modelle</h2>
    <div class="models-list">
      <div v-for="model in models" :key="model.key" class="model-card" :class="{ loaded: model.loaded }">
        <div class="model-info">
          <h3>{{ model.name }}</h3>
          <p>Größe: {{ model.size }}</p>
        </div>
        <div class="model-actions">
          <span v-if="model.loaded" class="status-badge">Geladen</span>
          <button v-else @click="loadModel(model.key)" :disabled="loading" class="load-btn">
            {{ loading ? 'Lade...' : 'Laden' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ModelManager',
  setup() {
    const models = ref([
      { key: 'mistral', name: 'Mistral 7B', size: '4.1 GB', loaded: true },
      { key: 'llama3', name: 'LLaMA 3 8B', size: '4.7 GB', loaded: false },
      { key: 'deepseek', name: 'DeepSeek Coder', size: '6.8 GB', loaded: false }
    ])
    const loading = ref(false)
    
    const loadModel = async (modelKey) => {
      loading.value = true
      await new Promise(resolve => setTimeout(resolve, 2000))
      models.value = models.value.map(m => ({ ...m, loaded: m.key === modelKey }))
      loading.value = false
    }
    
    return { models, loading, loadModel }
  }
}
</script>

<style scoped>
.model-manager { padding: 20px; }
h2 { margin: 0 0 24px 0; }
.models-list { display: flex; flex-direction: column; gap: 16px; }
.model-card { display: flex; justify-content: space-between; align-items: center; background: var(--bg-secondary); padding: 20px; border-radius: 12px; border: 2px solid var(--border-color); transition: all 0.3s; }
.model-card.loaded { border-color: var(--accent); }
.model-info h3 { margin: 0 0 8px 0; color: var(--text-primary); }
.model-info p { margin: 0; color: var(--text-secondary); font-size: 14px; }
.status-badge { padding: 8px 16px; background: var(--accent); color: white; border-radius: 20px; font-size: 14px; font-weight: 600; }
.load-btn { padding: 8px 20px; background: var(--accent); color: white; border: none; border-radius: 20px; cursor: pointer; transition: all 0.3s; }
.load-btn:hover:not(:disabled) { background: var(--accent-hover); transform: translateY(-2px); }
.load-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
