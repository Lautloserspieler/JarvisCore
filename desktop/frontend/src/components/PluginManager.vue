<template>
  <div class="plugin-manager">
    <h2>Plugins</h2>
    
    <div class="plugins-list">
      <div v-for="plugin in plugins" :key="plugin.name" class="plugin-card">
        <div class="plugin-info">
          <h3>{{ plugin.name }}</h3>
          <p>{{ plugin.description }}</p>
        </div>
        
        <div class="plugin-toggle">
          <label class="switch">
            <input 
              type="checkbox" 
              :checked="plugin.enabled" 
              @change="togglePlugin(plugin.name, !plugin.enabled)"
            >
            <span class="slider"></span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useWails } from '../composables/useWails'

export default {
  name: 'PluginManager',
  setup() {
    const { api } = useWails()
    
    const plugins = ref([])
    
    const fetchPlugins = async () => {
      try {
        plugins.value = await api.GetPlugins()
      } catch (error) {
        console.error('Fehler beim Laden der Plugins:', error)
      }
    }
    
    const togglePlugin = async (pluginName, enabled) => {
      try {
        await api.TogglePlugin(pluginName, enabled)
        
        // Update local state
        const plugin = plugins.value.find(p => p.name === pluginName)
        if (plugin) {
          plugin.enabled = enabled
        }
      } catch (error) {
        console.error('Fehler beim Toggle:', error)
      }
    }
    
    onMounted(fetchPlugins)
    
    return {
      plugins,
      togglePlugin
    }
  }
}
</script>

<style scoped>
.plugin-manager { padding: 20px; }
h2 { margin: 0 0 24px 0; }
.plugins-list { display: flex; flex-direction: column; gap: 16px; }
.plugin-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-secondary);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}
.plugin-info h3 { margin: 0 0 8px 0; color: var(--text-primary); }
.plugin-info p { margin: 0; color: var(--text-secondary); font-size: 14px; }
.switch { position: relative; display: inline-block; width: 50px; height: 24px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  transition: .4s;
  border-radius: 24px;
}
.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}
input:checked + .slider { background-color: var(--accent); }
input:checked + .slider:before { transform: translateX(26px); }
</style>
