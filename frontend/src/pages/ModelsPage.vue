<template>
  <div class="models-page p-6">
    <div class="header mb-6">
      <h1 class="text-3xl font-bold mb-2">LLM Models</h1>
      <p class="text-gray-600 dark:text-gray-400">Download and manage language models</p>
    </div>

    <!-- Model Grid -->
    <div v-if="Object.keys(models).length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <ModelCard
        v-for="(model, key) in models"
        :key="key"
        :model-key="key"
        :model="model"
        :is-downloading="isDownloading(key)"
        :download-progress="getProgress(key)"
        @download="startDownload"
        @cancel="cancelDownload"
        @delete="deleteModel"
        @select-variant="showVariantDialog"
      />
    </div>

    <!-- Loading State -->
    <div v-else class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-600 dark:text-gray-400">Loading models...</p>
    </div>

    <!-- Variant Selection Dialog -->
    <VariantDialog
      v-if="variantDialogOpen"
      :model-key="selectedModelKey"
      :variants="modelVariants"
      @select="downloadVariant"
      @close="variantDialogOpen = false"
    />

    <!-- Download Queue (Sticky Bottom) -->
    <DownloadQueue
      v-if="hasActiveDownloads"
      :downloads="activeDownloads"
      @cancel="cancelDownload"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ModelCard from '@/components/models/ModelCard.vue'
import VariantDialog from '@/components/models/VariantDialog.vue'
import DownloadQueue from '@/components/models/DownloadQueue.vue'
import { useModels } from '@/hooks/useModels'

const {
  models,
  activeDownloads,
  loadModels,
  startDownload,
  cancelDownload,
  deleteModel,
  getVariants
} = useModels()

const variantDialogOpen = ref(false)
const selectedModelKey = ref('')
const modelVariants = ref([])

const hasActiveDownloads = computed(() => {
  return Object.keys(activeDownloads.value).length > 0
})

const isDownloading = (modelKey: string) => {
  return modelKey in activeDownloads.value
}

const getProgress = (modelKey: string) => {
  return activeDownloads.value[modelKey]
}

const showVariantDialog = async (modelKey: string) => {
  selectedModelKey.value = modelKey
  modelVariants.value = await getVariants(modelKey) as any
  variantDialogOpen.value = true
}

const downloadVariant = (variant: any) => {
  startDownload(selectedModelKey.value, variant.quantization)
  variantDialogOpen.value = false
}

onMounted(() => {
  loadModels()
})
</script>
