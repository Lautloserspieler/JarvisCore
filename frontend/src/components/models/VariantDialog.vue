<template>
  <div class="variant-dialog-overlay fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="$emit('close')">
    <div class="variant-dialog bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-6 max-w-2xl w-full mx-4" @click.stop>
      <div class="header mb-4">
        <h2 class="text-2xl font-bold mb-2">Select Model Variant</h2>
        <p class="text-sm text-gray-600 dark:text-gray-400">Choose a quantization for {{ modelKey }}</p>
      </div>

      <div class="variants-list space-y-3">
        <div
          v-for="variant in variants"
          :key="variant.quantization"
          class="variant-item p-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 cursor-pointer transition-colors"
          @click="$emit('select', variant)"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="font-semibold text-lg">{{ variant.quantization }}</div>
              <div class="text-sm text-gray-600 dark:text-gray-400">{{ variant.name }}</div>
            </div>
            <div class="text-right">
              <div class="text-sm font-semibold text-blue-600">{{ variant.size_estimate }}</div>
              <div class="text-xs text-gray-500">{{ getQualityLabel(variant.quantization) }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="actions mt-6 flex justify-end">
        <button
          @click="$emit('close')"
          class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelKey: string
  variants: any[]
}>()

const emit = defineEmits(['select', 'close'])

const getQualityLabel = (quant: string) => {
  const labels: Record<string, string> = {
    'Q4_K_M': 'Balanced',
    'Q4_K_S': 'Fast & Small',
    'Q5_K_M': 'High Quality',
    'Q6_K': 'Very High Quality',
    'Q8_0': 'Maximum Quality'
  }
  return labels[quant] || 'Custom'
}
</script>
