<template>
  <div class="model-card bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
    <!-- Header -->
    <div class="flex items-start justify-between mb-4">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <h3 class="text-xl font-bold">{{ model.name }}</h3>
          <!-- Token Required Badge -->
          <span 
            v-if="model.requires_token"
            class="token-badge"
            :title="language === 'de' ? 'Token erforderlich' : 'Token required'"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </span>
        </div>
        <p class="text-sm text-gray-500">{{ model.provider || model.parameters }}</p>
      </div>
      <div 
        class="status-badge px-3 py-1 rounded-full text-xs font-semibold"
        :class="statusClass"
      >
        {{ statusText }}
      </div>
    </div>

    <!-- Description -->
    <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
      {{ model.description }}
    </p>

    <!-- Stats -->
    <div class="stats grid grid-cols-2 gap-4 mb-4">
      <div>
        <div class="text-xs text-gray-500">{{ language === 'de' ? 'Größe' : 'Size' }}</div>
        <div class="text-sm font-semibold">{{ model.size }}</div>
      </div>
      <div v-if="model.context_length">
        <div class="text-xs text-gray-500">Context</div>
        <div class="text-sm font-semibold">{{ formatNumber(model.context_length) }}</div>
      </div>
    </div>

    <!-- Capabilities -->
    <div v-if="model.capabilities && model.capabilities.length > 0" class="capabilities mb-4">
      <div class="flex flex-wrap gap-2">
        <span
          v-for="capability in model.capabilities.slice(0, 3)"
          :key="capability"
          class="capability-tag px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs"
        >
          {{ capability }}
        </span>
      </div>
    </div>

    <!-- Download Progress -->
    <div v-if="isDownloading" class="progress-section mb-4">
      <div class="flex justify-between text-sm mb-2">
        <span>{{ downloadProgress?.status || (language === 'de' ? 'Download läuft' : 'Downloading') }}...</span>
        <span>{{ downloadProgress?.percent?.toFixed(1) || 0 }}%</span>
      </div>
      <div class="progress-bar w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          class="progress-fill h-full bg-blue-500 transition-all duration-300"
          :style="{ width: `${downloadProgress?.percent || 0}%` }"
        ></div>
      </div>
      <div class="flex justify-between text-xs text-gray-500 mt-1">
        <span>{{ downloadProgress?.speed_mbps?.toFixed(2) || 0 }} MB/s</span>
        <span>ETA: {{ downloadProgress?.eta || (language === 'de' ? 'berechnen...' : 'calculating...') }}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="actions flex gap-2">
      <button
        v-if="!model.isDownloaded && !isDownloading"
        @click="$emit('download', modelKey)"
        class="btn-primary flex-1"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        {{ language === 'de' ? 'Herunterladen' : 'Download' }}
      </button>

      <button
        v-if="isDownloading"
        @click="$emit('cancel', modelKey)"
        class="btn-secondary flex-1"
      >
        {{ language === 'de' ? 'Abbrechen' : 'Cancel' }}
      </button>

      <button
        v-if="model.isDownloaded && !isDownloading && !model.isActive"
        @click="$emit('load', modelKey)"
        class="btn-primary flex-1"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        {{ language === 'de' ? 'Laden' : 'Load' }}
      </button>

      <button
        v-if="model.isActive"
        class="btn-success flex-1"
        disabled
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        {{ language === 'de' ? 'Aktiv' : 'Active' }}
      </button>

      <button
        v-if="model.isDownloaded && !isDownloading"
        @click="confirmDelete"
        class="btn-danger"
        :title="language === 'de' ? 'Modell löschen' : 'Delete model'"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelKey: string
  model: any
  isDownloading: boolean
  downloadProgress?: any
  language?: 'de' | 'en'
}>()

const emit = defineEmits(['download', 'load', 'cancel', 'delete'])

const statusClass = computed(() => {
  if (props.isDownloading) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  if (props.model.isActive) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
  if (props.model.isDownloaded) return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
  return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
})

const statusText = computed(() => {
  const lang = props.language || 'en'
  if (props.isDownloading) return lang === 'de' ? 'Download...' : 'Downloading'
  if (props.model.isActive) return lang === 'de' ? 'Aktiv' : 'Active'
  if (props.model.isDownloaded) return lang === 'de' ? 'Bereit' : 'Ready'
  return lang === 'de' ? 'Nicht heruntergeladen' : 'Not Downloaded'
})

const formatNumber = (num: number) => {
  return num?.toLocaleString() || 0
}

const confirmDelete = () => {
  const lang = props.language || 'en'
  const message = lang === 'de' 
    ? `${props.model.name} löschen?`
    : `Delete ${props.model.name}?`
  
  if (confirm(message)) {
    emit('delete', props.modelKey)
  }
}
</script>

<style scoped>
.token-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 6px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

@media (prefers-color-scheme: dark) {
  .token-badge {
    background: #78350f;
    color: #fde68a;
  }
}

.btn-primary {
  @apply px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center font-medium;
}

.btn-secondary {
  @apply px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors flex items-center justify-center;
}

.btn-success {
  @apply px-4 py-2 bg-green-600 text-white rounded-lg cursor-default flex items-center justify-center font-medium;
}

.btn-danger {
  @apply px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors flex items-center justify-center;
}

@media (prefers-color-scheme: dark) {
  .btn-danger {
    @apply bg-red-900 text-red-200 hover:bg-red-800;
  }
}

.capability-tag {
  text-transform: capitalize;
}
</style>
