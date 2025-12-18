<template>
  <div class="models-page p-6">
    <div class="header mb-6">
      <h1 class="text-3xl font-bold mb-2">{{ t.title }}</h1>
      <p class="text-gray-600 dark:text-gray-400">{{ t.subtitle }}</p>
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
    <div v-else class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-600 dark:text-gray-400">{{ t.loading }}</p>
    </div>

    <!-- Token Dialog -->
    <TokenDialog
      v-if="showTokenDialog"
      :model-name="currentModel?.name || ''"
      :language="language"
      @close="showTokenDialog = false"
      @submit="handleTokenSubmit"
    />

    <!-- Download Queue (Sticky Bottom) -->
    <DownloadQueue
      v-if="hasActiveDownloads"
      :downloads="activeDownloads"
      :language="language"
      @cancel="cancelDownload"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ModelCard from '@/components/models/ModelCard.vue'
import TokenDialog from '@/components/models/TokenDialog.vue'
import DownloadQueue from '@/components/models/DownloadQueue.vue'

const API_BASE = 'http://localhost:5050'

// Language detection
const language = ref<'de' | 'en'>('en')
if (navigator.language.startsWith('de')) {
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
    const data = await res.json()
    hasToken.value = data.has_token
  } catch (err) {
    console.error('Failed to check token status:', err)
  }
}

// Load models from API
const loadModels = async () => {
  try {
    const res = await fetch(`${API_BASE}/api/models`)
    const data = await res.json()
    models.value = data
  } catch (err) {
    console.error('Failed to load models:', err)
  }
}

// Handle download click
const handleDownload = async (modelId: string) => {
  const model = models.value.find(m => m.id === modelId)
  if (!model) return
  
  // Check if model requires token and we don't have one stored
  if (model.requires_token && !hasToken.value) {
    currentModel.value = model
    showTokenDialog.value = true
    return
  }
  
  // Start download
  await startDownload(modelId)
}

// Handle token dialog submit
const handleTokenSubmit = async ({ token, remember }: { token: string, remember: boolean }) => {
  try {
    // Save token if remember is checked
    if (remember) {
      await fetch(`${API_BASE}/api/hf-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      })
      hasToken.value = true
    }
    
    // Close dialog
    showTokenDialog.value = false
    
    // Start download with token
    if (currentModel.value) {
      await startDownload(currentModel.value.id, remember ? null : token)
    }
  } catch (err) {
    console.error('Failed to save token:', err)
    alert(language.value === 'de' 
      ? 'Fehler beim Speichern des Tokens'
      : 'Failed to save token'
    )
  }
}

// Start download
const startDownload = async (modelId: string, token?: string | null) => {
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
    
    if (result.requires_token) {
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
    console.error('Failed to start download:', err)
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
      console.error('Failed to poll download status:', err)
      clearInterval(interval)
      delete activeDownloads.value[modelId]
    }
  }, 1000)
}

// Load model
const loadModel = async (modelId: string) => {
  try {
    const res = await fetch(`${API_BASE}/api/models/${modelId}/load`, {
      method: 'POST'
    })
    
    const result = await res.json()
    
    if (!result.success) {
      alert(result.message || (language.value === 'de' ? 'Laden fehlgeschlagen' : 'Failed to load'))
      return
    }
    
    // Reload models to update active status
    await loadModels()
  } catch (err) {
    console.error('Failed to load model:', err)
    alert(language.value === 'de' 
      ? 'Fehler beim Laden des Modells'
      : 'Failed to load model'
    )
  }
}

// Cancel download
const cancelDownload = (modelId: string) => {
  // Remove from active downloads
  delete activeDownloads.value[modelId]
  // API doesn't support cancel yet, but we stop polling
}

// Delete model
const deleteModel = async (modelId: string) => {
  try {
    // API doesn't have delete endpoint yet
    console.log('Delete model:', modelId)
    alert(language.value === 'de' 
      ? 'Löschen noch nicht implementiert'
      : 'Delete not implemented yet'
    )
  } catch (err) {
    console.error('Failed to delete model:', err)
  }
}

onMounted(async () => {
  await checkTokenStatus()
  await loadModels()
})
</script>

<style scoped>
/* Add any page-specific styles here */
</style>
