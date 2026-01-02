<template>
  <div class="rounded-xl border border-border/60 bg-card/50 p-4 shadow-sm transition hover:border-primary/40">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h3 class="text-base font-semibold text-foreground">{{ model.name }}</h3>
        <p class="text-xs text-muted-foreground">{{ model.parameters }} · {{ model.quantization }}</p>
      </div>
      <span class="rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
        {{ model.rating.toFixed(1) }} ★
      </span>
    </div>

    <p class="mt-2 text-sm text-muted-foreground line-clamp-3">
      {{ model.description }}
    </p>

    <div class="mt-3 flex flex-wrap gap-2">
      <span
        v-for="category in model.categories"
        :key="category"
        class="rounded-full border border-border/60 px-2 py-0.5 text-xs text-muted-foreground"
      >
        {{ category }}
      </span>
    </div>

    <div class="mt-3 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
      <div>Größe: <span class="text-foreground">{{ model.sizeGb.toFixed(1) }} GB</span></div>
      <div>Kontext: <span class="text-foreground">{{ model.contextLength }} Tokens</span></div>
      <div>Sprachen: <span class="text-foreground">{{ model.languages.join(', ') }}</span></div>
      <div>Lizenz: <span class="text-foreground">{{ model.license }}</span></div>
    </div>

    <div class="mt-4 space-y-2">
      <div v-if="progressState" class="space-y-2">
        <div class="flex items-center justify-between text-xs">
          <span class="text-muted-foreground">{{ progressLabel }}</span>
          <span class="text-primary font-medium">{{ progressPercent }}%</span>
        </div>
        <div class="h-2 w-full rounded-full bg-muted/40">
          <div
            class="h-2 rounded-full bg-primary transition-all"
            :style="{ width: progressPercent + '%' }"
          />
        </div>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          class="flex-1 rounded-md border border-primary/40 bg-primary/10 px-3 py-2 text-xs font-semibold text-primary transition hover:bg-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="installing || installed"
          @click="emit('install', model.id)"
        >
          {{ installLabel }}
        </button>
        <button
          v-if="installed"
          class="rounded-md border border-destructive/50 px-3 py-2 text-xs font-semibold text-destructive transition hover:bg-destructive/10 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="deleting"
          @click="emit('delete', model.id)"
        >
          {{ deleting ? 'Lösche…' : 'Löschen' }}
        </button>
        <button
          class="rounded-md border border-border/70 px-3 py-2 text-xs text-muted-foreground transition hover:text-foreground"
          @click="emit('details', model)"
        >
          Details
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface HardwareSpec {
  cpu: string;
  gpu: string;
  ramGb: number;
  vramGb: number;
}

interface ModelMetadata {
  id: string;
  name: string;
  categories: string[];
  checksum: string;
  downloadUrl: string;
  languages: string[];
  recommendedHardware: HardwareSpec;
  parameters: string;
  sizeGb: number;
  rating: number;
  license: string;
  description: string;
  tags: string[];
  quantization: string;
  contextLength: number;
  updatedAt: string;
}

interface ProgressState {
  progress: number | null;
  downloaded: number;
  total: number | null;
  status: 'idle' | 'downloading' | 'completed' | 'error';
}

const props = defineProps<{
  model: ModelMetadata;
  progressState?: ProgressState | null;
  installing?: boolean;
  installed?: boolean;
  deleting?: boolean;
}>();

const emit = defineEmits<{
  (e: 'install', id: string): void;
  (e: 'delete', id: string): void;
  (e: 'details', model: ModelMetadata): void;
}>();

const progressPercent = computed(() => {
  if (!props.progressState) return 0;
  const { progress, downloaded, total } = props.progressState;
  if (progress !== null) return Math.min(100, Math.max(0, progress));
  if (total && total > 0) {
    return Math.min(100, Math.max(0, (downloaded / total) * 100));
  }
  return 0;
});

const progressLabel = computed(() => {
  if (!props.progressState) return '';
  if (props.progressState.status === 'completed') return 'Abgeschlossen';
  if (props.progressState.status === 'error') return 'Fehler beim Download';
  return 'Download läuft';
});

const installLabel = computed(() => {
  if (props.installed) return 'Installiert';
  if (props.installing) return 'Installiere…';
  return 'Installieren';
});
</script>
