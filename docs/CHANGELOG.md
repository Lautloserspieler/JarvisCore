# Changelog

Alle bedeutenden Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

## [1.0.1] - 2025-12-16, 11:10 CET

### ✨ Major Features Added

#### 🧠 llama.cpp Lokale Inferenz - FERTIGGESTELLT!
- **NEU:** `core/llama_inference.py` - Vollständige llama.cpp Inference Engine
- **NEU:** GPU-Acceleration mit CUDA (n_gpu_layers=-1)
- **NEU:** Chat-Modus mit History-Support
- **NEU:** Text-Generation mit vollständiger Parameterkontrolle
- **NEU:** Thread-Safe Model Loading/Unloading
- **NEU:** Status-API für Live-Monitoring

**Features:**
- ✅ GGUF Model Loading (Mistral, Qwen, DeepSeek, Llama 2)
- ✅ Context-Management bis 32K Tokens
- ✅ Automatische CUDA-Erkennung
- ✅ Memory-efficient mit Garbage Collection
- ✅ Performance: ~30-50 tok/s (GPU), ~5-10 tok/s (CPU)

**Backend Integration:**
- 🔄 `backend/main.py` - Integration von llama_inference
- 🔄 WebSocket-Chat nutzt jetzt echte AI-Responses
- 🔄 API-Endpunkte für Model-Management

```python
# Verwendung
from core.llama_inference import llama_runtime

llama_runtime.load_model(
    model_path="models/llm/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
    model_name="mistral",
    n_ctx=8192
)

result = llama_runtime.chat(
    message="Hallo JARVIS!",
    history=[],
    temperature=0.7
)
print(result['text'])  # Echte AI-Antwort!
```

### 📝 Dokumentation
- ✅ `IMPLEMENTATION_STATUS.md` - llama.cpp als "Production Ready" markiert
- ✅ `docs/ARCHITECTURE.md` - llama.cpp Architektur dokumentiert
- ✅ `README.md` - Features aktualisiert (v1.0.1)
- ✅ `README_GB.md` - Englische Version aktualisiert
- ✅ `docs/CHANGELOG.md` - Dieser Changelog erstellt

### 🐛 Bugfixes
- ✅ Backend nutzte `hf_inference.py` (nicht existent) - ersetzt durch `llama_inference.py`
- ✅ Mock-Chat-Responses durch echte LLM-Inferenz ersetzt

### ⚠️ Deprecated
- ❌ `hf_inference.py` wurde nie implementiert (entfernt aus Plänen)
- ❌ HuggingFace Transformers Integration verworfen (llama.cpp ist besser)

---

## [1.0.0] - 2025-12-14

### ✨ Initial Release

#### 📦 LLM Download-System (Ollama-Style)
- `core/model_downloader.py` - Advanced Download-Engine
- `core/model_registry.py` - Multi-Registry Support
- `core/model_manifest.py` - Metadata-Management
- `core/llm_manager.py` - High-Level LLM-Management

**Features:**
- ✅ Multi-Registry (HuggingFace, Ollama, Custom)
- ✅ Resume-Support (HTTP Range Requests)
- ✅ SHA256-Verifizierung
- ✅ Progress-Callbacks (Speed, ETA)
- ✅ Quantization-Varianten

#### 🎨 Models-Page (React Frontend)
- `frontend/src/pages/ModelsPage.tsx` - Model-Grid
- `frontend/src/components/models/ModelCard.tsx` - Model-Karten
- `frontend/src/components/models/DownloadQueue.tsx` - Download-Queue
- `frontend/src/components/models/VariantDialog.tsx` - Varianten-Auswahl

**Features:**
- ✅ Live-Progress-Tracking (SSE)
- ✅ Download-Queue (Sticky Panel)
- ✅ Cancel-Downloads
- ✅ Status-Badges
- ✅ Dark Mode (shadcn/ui)

#### 🚀 Backend API
- `backend/main.py` - FastAPI Server
- `main.py` (Root) - Unified Launcher

**Features:**
- ✅ REST-API für Models, Chat, Plugins, Logs
- ✅ WebSocket-Support
- ✅ SSE für Progress-Tracking
- ✅ Auto-Port-Detection

#### 📚 Dokumentation
- `README.md` - Vollständige deutsche Dokumentation
- `README_GB.md` - Englische Version
- `docs/LLM_DOWNLOAD_SYSTEM.md` - Download-System Details
- `docs/ARCHITECTURE.md` - Architektur-Übersicht
- `IMPLEMENTATION_STATUS.md` - Feature-Status

---

## Kategorien-Legende

- **Added** - Neue Features
- **Changed** - Änderungen an bestehenden Features
- **Deprecated** - Bald entfernte Features
- **Removed** - Entfernte Features
- **Fixed** - Bugfixes
- **Security** - Sicherheits-Updates

---

**Versionierungs-Schema:** [Semantic Versioning 2.0.0](https://semver.org/)

- **MAJOR** (1.x.x) - Inkompatible API-Änderungen
- **MINOR** (x.1.x) - Neue Features, abwärtskompatibel
- **PATCH** (x.x.1) - Bugfixes, abwärtskompatibel
