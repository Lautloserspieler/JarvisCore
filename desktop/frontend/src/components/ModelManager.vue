<template>
  <div class="model-manager">
    <h2>LLM-Modelle</h2>
    
    <div class="models-list">
      <div 
        v-for="model in models"
        :key="model.key"
        class="model-card"
        :class="{ loaded: model.loaded }"
      >
        <div class="model-info">
          <h3>{{ model.name }}</h3>
          <p>Größe: {{ model.size }}</p>
        </div>
        
        <div class="model-actions">
          <span v-if="model.loaded" class="status-badge">Geladen</span>
          <button 
            v-else
            @click="loadModel(model.key)"
            :disabled="loading"
            class="load-btn"
          >
            {{ loading ? 'Lade...' : 'Laden' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useWails } from '../composables/useWails'

export default {
  name: 'ModelManager',
  setup() {
    const { api } = useWails()
    
    const models = ref([])
    const loading = ref(false)
    
    const fetchModels = async () => {
      try {
        models.value = await api.ListModels()
      } catch (error) {
        console.error('Fehler beim Laden der Modelle:', error)
      }
    }
    
    const loadModel = async (modelKey) => {
      loading.value = true
      try {
        await api.LoadModel(modelKey)
        await fetchModels() // Refresh
        alert(`Modell ${modelKey} erfolgreich geladen!`)
      } catch (error) {
        alert(`Fehler: ${error.message}`)
      } finally {
        loading.value = false
      }
    }
    
    onMounted(fetchModels)
    
    return {
      models,
      loading,
      loadModel
    }
  }
}
</script>

<style scoped>
.model-manager { padding: 20px; }
h2 { margin: 0 0 24px 0; }
.models-list { display: flex; flex-direction: column; gap: 16px; }
.model-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-secondary);
  padding: 20px;
  border-radius: 12px;
  border: 2px solid var(--border-color);
  transition: all 0.3s;
}
.model-card.loaded { border-color: var(--accent); }
.model-info h3 { margin: 0 0 8px 0; color: var(--text-primary); }
.model-info p { margin: 0; color: var(--text-secondary); font-size: 14px; }
.status-badge {
  padding: 8px 16px;
  background: var(--accent);
  color: white;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}
.load-btn {
  padding: 8px 20px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
}
.load-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-2px);
}
.load-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
