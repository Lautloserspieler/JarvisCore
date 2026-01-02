<template>
  <Teleport to="body">
    <div v-if="model" class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur">
      <div class="w-full max-w-2xl rounded-xl border border-border/60 bg-card p-6 shadow-lg">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold">{{ model.name }}</h2>
            <p class="text-sm text-muted-foreground">{{ model.parameters }} · {{ model.quantization }}</p>
          </div>
          <button
            class="rounded-md border border-border/60 px-2 py-1 text-xs text-muted-foreground transition hover:text-foreground"
            @click="emit('close')"
          >
            Schließen
          </button>
        </div>

        <p class="mt-4 text-sm text-muted-foreground">{{ model.description }}</p>

        <div class="mt-4 grid gap-3 text-sm text-muted-foreground md:grid-cols-2">
          <div>
            <span class="text-foreground font-semibold">Kategorien:</span>
            {{ model.categories.join(', ') }}
          </div>
          <div>
            <span class="text-foreground font-semibold">Sprachen:</span>
            {{ model.languages.join(', ') }}
          </div>
          <div>
            <span class="text-foreground font-semibold">Größe:</span>
            {{ model.sizeGb.toFixed(1) }} GB
          </div>
          <div>
            <span class="text-foreground font-semibold">Bewertung:</span>
            {{ model.rating.toFixed(1) }} ★
          </div>
          <div>
            <span class="text-foreground font-semibold">Kontext:</span>
            {{ model.contextLength }} Tokens
          </div>
          <div>
            <span class="text-foreground font-semibold">Lizenz:</span>
            {{ model.license }}
          </div>
        </div>

        <div class="mt-4 rounded-lg border border-border/60 bg-background/40 p-4">
          <h3 class="text-sm font-semibold text-foreground">Empfohlene Hardware</h3>
          <div class="mt-2 grid gap-2 text-xs text-muted-foreground md:grid-cols-2">
            <div>CPU: <span class="text-foreground">{{ model.recommendedHardware.cpu }}</span></div>
            <div>GPU: <span class="text-foreground">{{ model.recommendedHardware.gpu }}</span></div>
            <div>RAM: <span class="text-foreground">{{ model.recommendedHardware.ramGb }} GB</span></div>
            <div>VRAM: <span class="text-foreground">{{ model.recommendedHardware.vramGb }} GB</span></div>
          </div>
        </div>

        <div v-if="model.tags.length" class="mt-4 flex flex-wrap gap-2">
          <span
            v-for="tag in model.tags"
            :key="tag"
            class="rounded-full border border-border/60 px-2 py-0.5 text-xs text-muted-foreground"
          >
            {{ tag }}
          </span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
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

const props = defineProps<{
  model: ModelMetadata | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();
</script>
