<template>
  <div class="models-page p-6">
    <div class="header mb-6">
      <h1 class="text-3xl font-bold mb-2">{{ t.title }}</h1>
      <p class="text-gray-600 dark:text-gray-400">{{ t.subtitle }}</p>
    </div>

    <!-- Debug Info -->
    <div v-if="debugMode" class="mb-4 p-4 bg-yellow-100 rounded">
      <p>Models loaded: {{ models.length }}</p>
      <p>Has token: {{ hasToken }}</p>
      <p>Language: {{ language }}</p>
    </div>

    <!-- Model Grid -->
    <div v-if="models.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <ModelCard
        v-for="model in models"
        :key="model.id"
        :model-key="model.id"
        :model="model"
        :is-downloading="isDownloading(model.id)"
        :download-progress="getProgress(model.id)"
        :language="language"
        @download="handleDownload"
        @load="loadModel"
        @cancel="cancelDownload"
        @delete="deleteModel"
      />
    </div>

    <!-- Loading State -->
    <div v-else-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-600 dark:text-gray-400">{{ t.loading }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-12">
      <p class="text-red-600 mb-4">{{ error }}</p>
      <button @click="loadModels" class="px-4 py-2 bg-blue-600 text-white rounded">
        {{ language === 'de' ? 'Erneut versuchen' : 'Retry' }}
      </button>
    </div>

    <!-- Token Dialog -->
    <TokenDialog
      v-if="showTokenDialog"
      :model-name="currentModel?.name || ''"
      :language="language"
      @close="showTokenDialog = false"
      @submit="handleTokenSubmit"
    />

    <!-- Download Queue -->
    <DownloadQueue
      v-if="hasActiveDownloads"
      :downloads="activeDownloads"
      @cancel="cancelDownload"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ModelCard from '../components/models/ModelCard.vue'
import TokenDialog from '../components/models/TokenDialog.vue'
import DownloadQueue from '../components/models/DownloadQueue.vue'

const API_BASE = 'http://localhost:5050'

// Debug mode (enable with Ctrl+D)
const debugMode = ref(false)
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'd') {
      e.preventDefault()
      debugMode.value = !debugMode.value
    }
  })
}

// Language detection
const language = ref<'de' | 'en'>('en')
if (typeof navigator !== 'undefined' && navigator.language.startsWith('de')) {
  language.value = 'de'
}

const translations = {
  de: {
    title: 'LLM Modelle',
    subtitle: 'Modelle herunterladen und verwalten',
    loading: 'Modelle werden geladen...'
  },
  en: {
    title: 'LLM Models',
    subtitle: 'Download and manage language models',
    loading: 'Loading models...'
  }
}

const t = computed(() => translations[language.value])

// State
const models = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const activeDownloads = ref<Record<string, any>>({})
const showTokenDialog = ref(false)
const currentModel = ref<any>(null)
const hasToken = ref(false)

const hasActiveDownloads = computed(() => {
  return Object.keys(activeDownloads.value).length > 0
})

const isDownloading = (modelId: string) => {
  return modelId in activeDownloads.value
}

const getProgress = (modelId: string) => {
  return activeDownloads.value[modelId]
}

// Check if token is stored
const checkTokenStatus = async () => {
  try {
    const res = await fetch(`${API_BASE}/api/hf-token/status`)
    if (!res.ok) throw new Error('Failed to check token status')
    const data = await res.json()
    hasToken.value = data.has_token
    console.log('[ModelsPage] Token status:', data)
  } catch (err) {
    console.error('[ModelsPage] Failed to check token status:', err)
  }
}

// Load models from API
const loadModels = async () => {
  loading.value = true
  error.value = ''
  
  try {
    console.log('[ModelsPage] Loading models from:', `${API_BASE}/api/models`)
    const res = await fetch(`${API_BASE}/api/models`)
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    }
    
    const data = await res.json()
    console.log('[ModelsPage] Loaded models:', data)
    
    models.value = data
    loading.value = false
  } catch (err) {
    console.error('[ModelsPage] Failed to load models:', err)
    error.value = language.value === 'de' 
      ? `Fehler beim Laden: ${err}`
      : `Failed to load: ${err}`
    loading.value = false
  }
}

// Handle download click
const handleDownload = async (modelId: string) => {
  console.log('[ModelsPage] Download clicked:', modelId)
  const model = models.value.find(m => m.id === modelId)
  if (!model) {
    console.error('[ModelsPage] Model not found:', modelId)
    return
  }
  
  console.log('[ModelsPage] Model info:', model)
  
  // Check if model requires token and we don't have one stored
  if (model.requires_token && !hasToken.value) {
    console.log('[ModelsPage] Token required, showing dialog')
    currentModel.value = model
    showTokenDialog.value = true
    return
  }
  
  // Start download
  await startDownload(modelId)
}

// Handle token dialog submit
const handleTokenSubmit = async ({ token, remember }: { token: string, remember: boolean }) => {
  console.log('[ModelsPage] Token submitted, remember:', remember)
  
  try {
    // Save token if remember is checked
    if (remember) {
      console.log('[ModelsPage] Saving token...')
      const res = await fetch(`${API_BASE}/api/hf-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      })
      
      const result = await res.json()
      console.log('[ModelsPage] Token save result:', result)
      
      if (result.success) {
        hasToken.value = true
      }
    }
    
    // Close dialog
    showTokenDialog.value = false
    
    // Start download with token
    if (currentModel.value) {
      await startDownload(currentModel.value.id, remember ? null : token)
    }
  } catch (err) {
    console.error('[ModelsPage] Failed to save token:', err)
    alert(language.value === 'de' 
      ? 'Fehler beim Speichern des Tokens'
      : 'Failed to save token'
    )
  }
}

// Start download
const startDownload = async (modelId: string, token?: string | null) => {
  console.log('[ModelsPage] Starting download:', modelId, 'with token:', !!token)
  
  try {
    const body: any = {}
    if (token) {
      body.token = token
    }
    
    const res = await fetch(`${API_BASE}/api/models/${modelId}/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    
    const result = await res.json()
    console.log('[ModelsPage] Download result:', result)
    
    if (result.requires_token) {
      console.log('[ModelsPage] Token required, showing dialog')
      // Show token dialog
      const model = models.value.find(m => m.id === modelId)
      if (model) {
        currentModel.value = model
        showTokenDialog.value = true
      }
      return
    }
    
    if (!result.success) {
      alert(result.message || (language.value === 'de' ? 'Download fehlgeschlagen' : 'Download failed'))
      return
    }
    
    // Mark as downloading
    activeDownloads.value[modelId] = {
      percent: 0,
      status: language.value === 'de' ? 'Download startet' : 'Starting download',
      speed_mbps: 0,
      eta: ''
    }
    
    // Poll download status
    pollDownloadStatus(modelId)
  } catch (err) {
    console.error('[ModelsPage] Failed to start download:', err)
    alert(language.value === 'de' 
      ? 'Fehler beim Starten des Downloads'
      : 'Failed to start download'
    )
  }
}

// Poll download status
const pollDownloadStatus = async (modelId: string) => {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/models/download/status`)
      const status = await res.json()
      
      if (status.current_model === modelId && status.is_downloading) {
        activeDownloads.value[modelId] = {
          percent: status.progress || 0,
          status: language.value === 'de' ? 'Download läuft' : 'Downloading',
          speed_mbps: 0,
          eta: ''
        }
      } else {
        // Download finished or cancelled
        delete activeDownloads.value[modelId]
        clearInterval(interval)
        
        // Reload models to update status
        await loadModels()
      }
    } catch (err) {
      console.error('[ModelsPage] Failed to poll download status:', err)
      clearInterval(interval)
      delete activeDownloads.value[modelId]
    }
  }, 1000)
}

// Load model
const loadModel = async (modelId: string) => {
  console.log('[ModelsPage] Loading model:', modelId)
  
  try {
    const res = await fetch(`${API_BASE}/api/models/${modelId}/load`, {
      method: 'POST'
    })
    
    const result = await res.json()
    console.log('[ModelsPage] Load result:', result)
    
    if (!result.success) {
      alert(result.message || (language.value === 'de' ? 'Laden fehlgeschlagen' : 'Failed to load'))
      return
    }
    
    // Reload models to update active status
    await loadModels()
  } catch (err) {
    console.error('[ModelsPage] Failed to load model:', err)
    alert(language.value === 'de' 
      ? 'Fehler beim Laden des Modells'
      : 'Failed to load model'
    )
  }
}

// Cancel download
const cancelDownload = (modelId: string) => {
  console.log('[ModelsPage] Cancelling download:', modelId)
  // Remove from active downloads
  delete activeDownloads.value[modelId]
  // API doesn't support cancel yet, but we stop polling
}

// Delete model
const deleteModel = async (modelId: string) => {
  console.log('[ModelsPage] Delete model:', modelId)
  try {
    // API doesn't have delete endpoint yet
    alert(language.value === 'de' 
      ? 'Löschen noch nicht implementiert'
      : 'Delete not implemented yet'
    )
  } catch (err) {
    console.error('[ModelsPage] Failed to delete model:', err)
  }
}

onMounted(async () => {
  console.log('[ModelsPage] Component mounted')
  await checkTokenStatus()
  await loadModels()
})
</script>

<style scoped>
/* Add any page-specific styles here */
</style>
