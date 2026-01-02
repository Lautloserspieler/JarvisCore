<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 rounded-xl border border-border/60 bg-card/50 p-4">
      <div class="flex flex-wrap gap-3">
        <input
          v-model="searchInput"
          type="text"
          placeholder="Suche nach Modell, Tag oder Beschreibung"
          class="flex-1 rounded-md border border-border/60 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-400 focus:border-cyan-400/80 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
        />
        <button
          class="inline-flex items-center gap-2 rounded-md border border-border/60 bg-slate-900/40 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-cyan-400/60 hover:text-white"
          @click="resetFilters"
        >
          <span class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-300">
            <svg viewBox="0 0 24 24" aria-hidden="true" class="h-4 w-4">
              <path
                d="M3 6h18M6 6v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V6M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </span>
          Filter zurücksetzen
        </button>
      </div>

      <div class="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        <select
          v-model="selectedCategory"
          class="rounded-md border border-border/60 bg-slate-900/70 px-3 py-2 text-xs text-slate-200 focus:border-cyan-400/80 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
        >
          <option value="">Kategorie</option>
          <option v-for="category in categoryOptions" :key="category" :value="category">
            {{ category }}
          </option>
        </select>

        <select
          v-model="selectedLanguage"
          class="rounded-md border border-border/60 bg-slate-900/70 px-3 py-2 text-xs text-slate-200 focus:border-cyan-400/80 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
        >
          <option value="">Sprache</option>
          <option v-for="language in languageOptions" :key="language" :value="language">
            {{ language }}
          </option>
        </select>

        <input
          v-model.number="minRating"
          type="number"
          min="0"
          max="5"
          step="0.1"
          placeholder="Min. Rating"
          class="rounded-md border border-border/60 bg-slate-900/70 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-400 focus:border-cyan-400/80 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
        />

        <div class="flex gap-2">
          <input
            v-model.number="minSize"
            type="number"
            min="0"
            step="0.1"
            placeholder="Min. GB"
            class="w-full rounded-md border border-border/60 bg-slate-900/70 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-400 focus:border-cyan-400/80 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
          />
          <input
            v-model.number="maxSize"
            type="number"
            min="0"
            step="0.1"
            placeholder="Max. GB"
            class="w-full rounded-md border border-border/60 bg-slate-900/70 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-400 focus:border-cyan-400/80 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
          />
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-10 text-sm text-muted-foreground">
      Lade Model-Gallery…
    </div>
    <div
      v-else-if="errorMessage"
      class="rounded-lg border border-destructive/40 bg-destructive/10 p-8 text-sm text-destructive"
    >
      <div class="flex flex-col items-center gap-3 text-center">
        <span class="inline-flex h-12 w-12 items-center justify-center rounded-full bg-destructive/20 text-destructive">
          <svg viewBox="0 0 24 24" aria-hidden="true" class="h-6 w-6">
            <path
              d="M12 9v4m0 4h.01M10.29 3.86l-8 14A2 2 0 0 0 4 20h16a2 2 0 0 0 1.71-2.14l-8-14a2 2 0 0 0-3.42 0Z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <p class="text-sm font-semibold">Gallery konnte nicht geladen werden</p>
        <p class="text-xs text-destructive/80">Bitte prüfe die Verbindung oder versuche es später erneut.</p>
      </div>
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <ModelCard
        v-for="model in filteredModels"
        :key="model.id"
        :model="model"
        :progress-state="progressById[model.id]"
        :installing="installingIds.has(model.id)"
        :installed="installedIds.has(model.id)"
        :deleting="deletingIds.has(model.id)"
        @install="installModel"
        @delete="deleteModel"
        @details="openDetails"
      />
    </div>

    <div v-if="!loading && !errorMessage && filteredModels.length === 0" class="text-sm text-muted-foreground">
      Keine Modelle gefunden. Passe die Filter an.
    </div>

    <ModelInfo :model="selectedModel" @close="selectedModel = null" />

    <InstallationProgress
      :open="Boolean(activeInstallModel)"
      :model-name="activeInstallModel?.name || ''"
      :progress="activeProgress?.progress ?? null"
      :downloaded="activeProgress?.downloaded ?? 0"
      :total="activeProgress?.total ?? null"
      :status="activeProgress?.status ?? 'idle'"
      :error-message="activeProgress?.status === 'error' ? activeProgress?.errorMessage ?? null : null"
      @close="activeInstallId = null"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { API_BASE_URL } from '@/lib/api';
import ModelCard from '@/components/ModelCard.vue';
import InstallationProgress from '@/components/InstallationProgress.vue';
import ModelInfo from '@/components/ModelInfo.vue';

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
  errorMessage?: string | null;
}

interface InstalledModelEntry {
  id: string;
  path?: string;
  size?: number;
  installedAt?: string;
  backend?: string;
  active?: boolean;
  status?: string;
}

const models = ref<ModelMetadata[]>([]);
const loading = ref(true);
const errorMessage = ref<string | null>(null);

const searchInput = ref('');
const debouncedSearch = ref('');
const selectedCategory = ref('');
const selectedLanguage = ref('');
const minRating = ref<number | null>(null);
const minSize = ref<number | null>(null);
const maxSize = ref<number | null>(null);

const progressById = ref<Record<string, ProgressState>>({});
const installingIds = ref(new Set<string>());
const installedIds = ref(new Set<string>());
const deletingIds = ref(new Set<string>());
const activeInstallId = ref<string | null>(null);
const selectedModel = ref<ModelMetadata | null>(null);

let debounceTimer: ReturnType<typeof setTimeout> | null = null;
let socket: WebSocket | null = null;

const categoryOptions = computed(() => {
  const options = new Set<string>();
  models.value.forEach((model) => model.categories.forEach((category) => options.add(category)));
  return Array.from(options).sort();
});

const languageOptions = computed(() => {
  const options = new Set<string>();
  models.value.forEach((model) => model.languages.forEach((language) => options.add(language)));
  return Array.from(options).sort();
});

const filteredModels = computed(() => {
  const query = debouncedSearch.value.trim().toLowerCase();
  return models.value.filter((model) => {
    if (query) {
      const haystack = [
        model.id,
        model.name,
        model.description,
        model.tags.join(' '),
      ].join(' ').toLowerCase();
      if (!haystack.includes(query)) {
        return false;
      }
    }
    if (selectedCategory.value && !model.categories.includes(selectedCategory.value)) {
      return false;
    }
    if (selectedLanguage.value && !model.languages.includes(selectedLanguage.value)) {
      return false;
    }
    if (minRating.value !== null && model.rating < minRating.value) {
      return false;
    }
    if (minSize.value !== null && model.sizeGb < minSize.value) {
      return false;
    }
    if (maxSize.value !== null && model.sizeGb > maxSize.value) {
      return false;
    }
    return true;
  });
});

const activeProgress = computed(() => {
  if (!activeInstallId.value) return null;
  return progressById.value[activeInstallId.value] || null;
});

const activeInstallModel = computed(() => {
  if (!activeInstallId.value) return null;
  return models.value.find((model) => model.id === activeInstallId.value) || null;
});

watch(searchInput, (value) => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    debouncedSearch.value = value;
  }, 300);
});

const resetFilters = () => {
  searchInput.value = '';
  debouncedSearch.value = '';
  selectedCategory.value = '';
  selectedLanguage.value = '';
  minRating.value = null;
  minSize.value = null;
  maxSize.value = null;
};

const loadGallery = async () => {
  loading.value = true;
  errorMessage.value = null;
  try {
    const response = await fetch(`${API_BASE_URL}/api/models/gallery`);
    if (!response.ok) throw new Error('Fehler beim Laden der Gallery');
    const data = await response.json();
    models.value = data.models ?? [];
  } catch (error) {
    console.error(error);
    errorMessage.value = 'Gallery konnte nicht geladen werden.';
  } finally {
    loading.value = false;
  }
};

const loadInstalled = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/models/installed`);
    if (!response.ok) throw new Error('Fehler beim Laden der installierten Modelle');
    const data = (await response.json()) as InstalledModelEntry[];
    installedIds.value = new Set(
      data
        .filter((entry) => entry.status !== 'missing')
        .map((entry) => entry.id)
    );
  } catch (error) {
    console.error(error);
  }
};

const installModel = async (modelId: string) => {
  if (installingIds.value.has(modelId)) return;
  installingIds.value.add(modelId);
  activeInstallId.value = modelId;
  progressById.value[modelId] = {
    progress: 0,
    downloaded: 0,
    total: null,
    status: 'downloading',
  };

  try {
    const response = await fetch(`${API_BASE_URL}/api/models/gallery/${modelId}/install`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error('Installation konnte nicht gestartet werden');
    }
  } catch (error) {
    console.error(error);
    progressById.value[modelId] = {
      progress: null,
      downloaded: 0,
      total: null,
      status: 'error',
      errorMessage: 'Installation fehlgeschlagen. Bitte erneut versuchen.',
    };
  } finally {
    installingIds.value.delete(modelId);
  }
};

const deleteModel = async (modelId: string) => {
  if (deletingIds.value.has(modelId)) return;
  deletingIds.value.add(modelId);
  try {
    const response = await fetch(`${API_BASE_URL}/api/models/${modelId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Modell konnte nicht gelöscht werden');
    await loadInstalled();
  } catch (error) {
    console.error(error);
  } finally {
    deletingIds.value.delete(modelId);
  }
};

const openDetails = (model: ModelMetadata) => {
  selectedModel.value = model;
};

const connectWebSocket = () => {
  const wsBase = API_BASE_URL.replace(/^http/, 'ws');
  socket = new WebSocket(`${wsBase}/api/models/ws/progress`);

  socket.onmessage = async (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (!payload.model_id) return;
      const current = progressById.value[payload.model_id] || {
        progress: null,
        downloaded: 0,
        total: null,
        status: 'downloading' as const,
      };
      const progressValue = payload.progress !== null ? Number(payload.progress) : null;
      const nextStatus =
        progressValue !== null && progressValue >= 100 ? 'completed' : 'downloading';
      progressById.value[payload.model_id] = {
        ...current,
        progress: progressValue,
        downloaded: payload.downloaded ?? current.downloaded,
        total: payload.total ?? current.total,
        status: nextStatus,
      };
      if (nextStatus === 'completed' && current.status !== 'completed') {
        await loadInstalled();
      }
    } catch (error) {
      console.error('Fehler beim Verarbeiten des Progress-Events', error);
    }
  };

  socket.onerror = (error) => {
    console.error('WebSocket Fehler', error);
  };
};

onMounted(() => {
  loadGallery();
  loadInstalled();
  connectWebSocket();
});

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer);
  if (socket) socket.close();
});
</script>
