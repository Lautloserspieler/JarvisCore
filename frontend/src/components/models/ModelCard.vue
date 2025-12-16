<template>
  <div class="model-card bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
    <!-- Header -->
    <div class="flex items-start justify-between mb-4">
      <div>
        <h3 class="text-xl font-bold">{{ model.display_name }}</h3>
        <p class="text-sm text-gray-500">{{ model.parameters }}</p>
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
        <div class="text-xs text-gray-500">Size</div>
        <div class="text-sm font-semibold">{{ model.size_gb }} GB</div>
      </div>
      <div>
        <div class="text-xs text-gray-500">Context</div>
        <div class="text-sm font-semibold">{{ formatNumber(model.context_length) }}</div>
      </div>
    </div>

    <!-- Download Progress -->
    <div v-if="isDownloading" class="progress-section mb-4">
      <div class="flex justify-between text-sm mb-2">
        <span>{{ downloadProgress?.status || 'Downloading' }}...</span>
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
        <span>ETA: {{ downloadProgress?.eta || 'calculating...' }}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="actions flex gap-2">
      <button
        v-if="!model.downloaded && !isDownloading"
        @click="$emit('download', modelKey)"
        class="btn-primary flex-1"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Download
      </button>

      <button
        v-if="isDownloading"
        @click="$emit('cancel', modelKey)"
        class="btn-secondary flex-1"
      >
        Cancel
      </button>

      <button
        v-if="model.downloaded && !isDownloading"
        @click="$emit('select-variant', modelKey)"
        class="btn-secondary"
        title="Download different variant"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>

      <button
        v-if="model.downloaded && !isDownloading"
        @click="confirmDelete"
        class="btn-danger"
        title="Delete model"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>

    <!-- Strengths -->
    <div v-if="model.strengths" class="strengths mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
      <div class="text-xs text-gray-500 mb-2">Best for:</div>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="strength in model.strengths.slice(0, 3)"
          :key="strength"
          class="tag px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs"
        >
          {{ strength }}
        </span>
      </div>
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
}>()

const emit = defineEmits(['download', 'cancel', 'delete', 'select-variant'])

const statusClass = computed(() => {
  if (props.isDownloading) return 'bg-blue-100 text-blue-800'
  if (props.model.downloaded) return 'bg-green-100 text-green-800'
  return 'bg-gray-100 text-gray-800'
})

const statusText = computed(() => {
  if (props.isDownloading) return 'Downloading'
  if (props.model.downloaded) return 'Ready'
  return 'Not Downloaded'
})

const formatNumber = (num: number) => {
  return num?.toLocaleString() || 0
}

const confirmDelete = () => {
  if (confirm(`Delete ${props.model.display_name}?`)) {
    emit('delete', props.modelKey)
  }
}
</script>

<style scoped>
.btn-primary {
  @apply px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center font-medium;
}

.btn-secondary {
  @apply px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors flex items-center justify-center;
}

.btn-danger {
  @apply px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors flex items-center justify-center;
}
</style>
