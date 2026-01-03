<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur">
      <div class="w-full max-w-md rounded-xl border border-border/60 bg-card p-6 shadow-lg">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="text-lg font-semibold">Hugging Face Token erforderlich</h3>
            <p class="text-sm text-muted-foreground">
              {{ modelName ? `Für ${modelName} wird ein Token benötigt.` : 'Für den Download wird ein Token benötigt.' }}
            </p>
          </div>
          <button
            class="rounded-md border border-border/60 px-2 py-1 text-xs text-muted-foreground transition hover:text-foreground"
            @click="emit('close')"
          >
            Schließen
          </button>
        </div>

        <div class="mt-5 space-y-3">
          <label class="text-xs text-muted-foreground" for="hf-token-input">Token</label>
          <input
            id="hf-token-input"
            v-model="tokenInput"
            type="password"
            placeholder="hf_..."
            class="w-full rounded-md border border-border/60 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-400 focus:border-cyan-400/80 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
          />
          <p class="text-xs text-muted-foreground">
            Der Token wird lokal gespeichert und für weitere Downloads wiederverwendet.
          </p>
          <p v-if="errorMessage" class="text-xs text-destructive">
            {{ errorMessage }}
          </p>
        </div>

        <div class="mt-5 flex items-center justify-end gap-2">
          <button
            class="rounded-md border border-border/60 px-3 py-2 text-xs text-muted-foreground transition hover:text-foreground"
            @click="emit('close')"
            :disabled="saving"
          >
            Abbrechen
          </button>
          <button
            class="rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
            @click="submitToken"
            :disabled="saving"
          >
            {{ saving ? 'Speichern…' : 'Token speichern' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  open: boolean;
  modelName: string;
  saving: boolean;
  errorMessage: string | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', token: string): void;
}>();

const tokenInput = ref('');

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      tokenInput.value = '';
    }
  }
);

const submitToken = () => {
  emit('submit', tokenInput.value.trim());
};
</script>
