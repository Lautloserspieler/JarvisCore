<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur">
      <div class="w-full max-w-md rounded-xl border border-border/60 bg-card p-6 shadow-lg">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="text-lg font-semibold">Installation läuft</h3>
            <p class="text-sm text-muted-foreground">{{ modelName }}</p>
          </div>
          <button
            class="rounded-md border border-border/60 px-2 py-1 text-xs text-muted-foreground transition hover:text-foreground"
            @click="emit('close')"
          >
            Schließen
          </button>
        </div>

        <div class="mt-5 space-y-3">
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">{{ statusLabel }}</span>
            <span class="text-primary font-medium">{{ displayPercent }}%</span>
          </div>
          <div class="h-2 w-full rounded-full bg-muted/40">
            <div
              class="h-2 rounded-full bg-primary transition-all"
              :style="{ width: displayPercent + '%' }"
            />
          </div>
          <div class="flex items-center justify-between text-xs text-muted-foreground">
            <span>Geladen: {{ formattedDownloaded }}</span>
            <span v-if="total">Gesamt: {{ formattedTotal }}</span>
          </div>
          <p v-if="errorMessage" class="text-xs text-destructive">
            {{ errorMessage }}
          </p>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  open: boolean;
  modelName: string;
  progress: number | null;
  downloaded: number;
  total: number | null;
  status: 'idle' | 'downloading' | 'completed' | 'error';
  errorMessage?: string | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const displayPercent = computed(() => {
  if (props.progress !== null) return Math.round(props.progress);
  if (props.total && props.total > 0) {
    return Math.round((props.downloaded / props.total) * 100);
  }
  return 0;
});

const statusLabel = computed(() => {
  switch (props.status) {
    case 'completed':
      return 'Abgeschlossen';
    case 'error':
      return 'Fehler beim Download';
    case 'downloading':
      return 'Download läuft';
    default:
      return 'Bereit';
  }
});

const formatBytes = (bytes: number) => {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let index = 0;
  let value = bytes;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(1)} ${units[index]}`;
};

const formattedDownloaded = computed(() => formatBytes(props.downloaded));
const formattedTotal = computed(() => (props.total ? formatBytes(props.total) : '–'));
</script>
