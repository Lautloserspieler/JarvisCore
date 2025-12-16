<template>
  <div class="download-queue fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 shadow-2xl border-t border-gray-200 dark:border-gray-700 p-4 z-50">
    <div class="max-w-7xl mx-auto">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-semibold">Active Downloads ({{ downloadCount }})</h3>
      </div>

      <div class="space-y-2">
        <div
          v-for="(progress, key) in downloads"
          :key="key"
          class="download-item flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
        >
          <!-- Model Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <span class="font-medium truncate">{{ key }}</span>
              <span class="text-sm text-gray-500">{{ progress.percent?.toFixed(1) || 0 }}%</span>
            </div>
            
            <!-- Progress Bar -->
            <div class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div 
                class="h-full bg-blue-500 transition-all duration-300"
                :style="{ width: `${progress.percent || 0}%` }"
              ></div>
            </div>
            
            <!-- Stats -->
            <div class="flex gap-4 text-xs text-gray-500 mt-1">
              <span>{{ progress.speed_mbps?.toFixed(2) || 0 }} MB/s</span>
              <span>{{ formatBytes(progress.downloaded) }} / {{ formatBytes(progress.total) }}</span>
              <span>ETA: {{ progress.eta || 'calculating...' }}</span>
            </div>
          </div>

          <!-- Cancel Button -->
          <button
            @click="$emit('cancel', key)"
            class="px-3 py-1.5 text-sm bg-red-100 text-red-600 rounded hover:bg-red-200 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  downloads: Record<string, any>
}>()

const emit = defineEmits(['cancel'])

const downloadCount = computed(() => {
  return Object.keys(props.downloads).length
})

const formatBytes = (bytes: number) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>
