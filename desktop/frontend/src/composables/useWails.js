/**
 * Wails Helper Composable
 * Stellt Wails-Funktionen bereit mit Fallback für Development
 */

import { ref, onMounted } from 'vue'

// Check if Wails is available
const isWailsAvailable = () => {
  return typeof window !== 'undefined' && window.go && window.go.app && window.go.app.App
}

export function useWails() {
  const wailsReady = ref(false)
  const isDevelopment = ref(!isWailsAvailable())
  
  onMounted(() => {
    wailsReady.value = isWailsAvailable()
    
    if (wailsReady.value) {
      console.log('✅ Wails Bindings verfügbar')
    } else {
      console.warn('⚠️  Wails Bindings nicht verfügbar - Dev-Modus mit simulierten Daten')
    }
  })
  
  // API Wrapper mit Fallback
  const api = {
    async ProcessCommand(text) {
      if (wailsReady.value) {
        return await window.go.app.App.ProcessCommand(text)
      }
      // Fallback für Development
      await new Promise(resolve => setTimeout(resolve, 1000))
      return `Simulierte Antwort auf: "${text}"`
    },
    
    async GetSystemStatus() {
      if (wailsReady.value) {
        return await window.go.app.App.GetSystemStatus()
      }
      // Fallback
      return {
        cpu: Math.floor(Math.random() * 30) + 30,
        memory: Math.floor(Math.random() * 20) + 50,
        disk: Math.floor(Math.random() * 10) + 35,
        gpu: Math.floor(Math.random() * 40) + 20
      }
    },
    
    async GetConversationHistory(limit) {
      if (wailsReady.value) {
        return await window.go.app.App.GetConversationHistory(limit)
      }
      return []
    },
    
    async ListModels() {
      if (wailsReady.value) {
        return await window.go.app.App.ListModels()
      }
      return [
        { key: 'mistral', name: 'Mistral 7B', size: '4.1 GB', loaded: true },
        { key: 'llama3', name: 'LLaMA 3 8B', size: '4.7 GB', loaded: false },
        { key: 'deepseek', name: 'DeepSeek Coder', size: '6.8 GB', loaded: false }
      ]
    },
    
    async LoadModel(modelKey) {
      if (wailsReady.value) {
        return await window.go.app.App.LoadModel(modelKey)
      }
      await new Promise(resolve => setTimeout(resolve, 2000))
    },
    
    async GetPlugins() {
      if (wailsReady.value) {
        return await window.go.app.App.GetPlugins()
      }
      return [
        { name: 'Wikipedia', description: 'Suche in Wikipedia-Artikeln', enabled: true },
        { name: 'Weather', description: 'Wetterdaten abrufen', enabled: false },
        { name: 'Calculator', description: 'Mathematische Berechnungen', enabled: true },
        { name: 'News', description: 'Aktuelle Nachrichten', enabled: false }
      ]
    },
    
    async TogglePlugin(pluginName, enabled) {
      if (wailsReady.value) {
        return await window.go.app.App.TogglePlugin(pluginName, enabled)
      }
    }
  }
  
  return {
    wailsReady,
    isDevelopment,
    api
  }
}
