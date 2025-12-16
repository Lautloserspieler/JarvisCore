# JarvisCore LLM Download System

## Überblick

Das JarvisCore LLM Download System ist eine **Ollama-inspirierte** Implementierung für das Herunterladen, Verwalten und Verifizieren von Large Language Models. Es bietet Enterprise-Level Features wie Resume-Support, SHA256-Verifizierung und Multi-Registry-Unterstützung.

## Features

### ✅ Ollama-Level Features

- **Multi-Registry-Support**: Hugging Face, Ollama Registry, Custom URLs
- **Flexible Model Paths**: `mistral`, `hf.co/user/repo`, `custom.ai/org/model:v1.0`
- **Resume-Support**: Unterbrochene Downloads werden automatisch fortgesetzt
- **SHA256-Verifizierung**: Automatische Integritätsprüfung aller Downloads
- **Progress-Tracking**: Detaillierte Download-Statistiken (Speed, ETA, Percent)
- **Manifest-System**: Metadaten und Versions-Tracking wie bei Ollama
- **HuggingFace Token**: Unterstützung für private Repositories

## Architektur

```
core/
├── model_registry.py      # Multi-Registry Path Parsing (Ollama-Style)
├── model_downloader.py    # Advanced Download Engine (Resume + SHA256)
├── model_manifest.py      # Metadata & Version Management
└── llm_manager.py         # High-Level LLM Management
```

### Vergleich mit Ollama

| Feature | Ollama | JarvisCore | Status |
|---------|--------|------------|--------|
| **Multi-Registry** | ✅ | ✅ | Implementiert |
| **Model Path Parsing** | ✅ | ✅ | Ollama-kompatibel |
| **Resume-Support** | ✅ | ✅ | HTTP Range |
| **SHA256-Verifizierung** | ✅ | ✅ | Vollständig |
| **Progress-Callbacks** | ✅ | ✅ | + ETA + Speed |
| **Manifest-System** | ✅ | ✅ | JSON-basiert |
| **Blob-Deduplication** | ✅ | ⚠️ | Geplant v2.0 |
| **HuggingFace Token** | ❌ | ✅ | Bonus! |

## Usage

### 1. Basic Download

```python
from core.model_registry import ModelRegistry, get_download_url
from core.model_downloader import ModelDownloader
from pathlib import Path

# Parse model path (Ollama-Style)
model_path = ModelRegistry.parse("hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF")
print(model_path)  # ModelPath(registry='huggingface.co', namespace='bartowski', ...)

# Get download URL
url = get_download_url("mistral", quantization="Q4_K_M")

# Download with resume & verification
downloader = ModelDownloader(download_dir=Path("models/llm"))
file_path = downloader.download(
    model_key="mistral",
    url=url,
    filename="Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
    expected_sha256="abc123..."  # Optional
)
```

### 2. Progress Tracking

```python
def progress_callback(progress):
    print(f"Download: {progress.percent:.1f}% | "
          f"Speed: {progress.speed_mbps:.2f} MB/s | "
          f"ETA: {progress.eta_formatted}")

downloader.download(
    model_key="qwen",
    url=download_url,
    filename="qwen2.5-7b.gguf",
    progress_callback=progress_callback
)
```

### 3. Multi-Registry Support

```python
from core.model_registry import ModelRegistry

# Hugging Face (Standard)
url1 = get_download_url("hf.co/second-state/Mistral-Nemo-Instruct-2407-GGUF")
# → https://huggingface.co/second-state/Mistral-Nemo-Instruct-2407-GGUF/resolve/main/...

# Custom Registry
url2 = get_download_url("models.jarviscore.ai/community/my-model:v1.0")
# → https://models.jarviscore.ai/community/my-model/...

# Shortcut (vordefiniert)
url3 = get_download_url("mistral")
# → https://huggingface.co/second-state/Mistral-Nemo-Instruct-2407-GGUF/resolve/main/...
```

### 4. Eigene Modelle hinzufügen

```python
from core.model_registry import ModelRegistry

# Eigenes Modell als Shortcut registrieren
ModelRegistry.add_known_model(
    shortcut="my-model",
    namespace="myuser",
    repository="awesome-model-GGUF",
    filename="model-q4_k_m.gguf",
    tag="v1.0"
)

# Jetzt verwendbar:
url = get_download_url("my-model")
```

### 5. Manifest-Management

```python
from core.model_manifest import ManifestManager
from pathlib import Path

manager = ManifestManager(manifest_dir=Path("models/manifests"))

# Manifest erstellen
manifest = manager.create_manifest(
    model_key="mistral",
    registry="huggingface.co",
    namespace="second-state",
    repository="Mistral-Nemo-Instruct-2407-GGUF",
    display_name="Mistral 7B Nemo Instruct",
    parameters="7B",
    context_length=8192
)

# Layer hinzufügen
manifest.add_layer(
    filename="Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
    sha256="abc123...",
    size_bytes=7_500_000_000
)

# Status aktualisieren
manifest.mark_downloaded()
manifest.mark_verified()
manager.update_manifest("mistral", manifest)

# Statistiken
stats = manager.get_model_stats()
print(f"Downloaded: {stats['downloaded']}/{stats['total_models']}")
print(f"Total size: {stats['total_size_gb']} GB")
```

### 6. HuggingFace Token für Private Repos

```python
downloader = ModelDownloader(download_dir=Path("models/llm"))

# Token setzen
downloader.set_hf_token("hf_YourTokenHere")

# Oder via Environment Variable
import os
os.environ["HUGGINGFACE_TOKEN"] = "hf_YourTokenHere"
```

## Integration in llm_manager.py

Der `LLMManager` wurde erweitert um die neuen Features:

```python
from core.llm_manager import LLMManager

llm = LLMManager()

# Automatisches Parsen und Download
llm.download_model_from_path("hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF")

# Mit Quantization-Auswahl
llm.download_model_from_path("mistral", quantization="Q5_K_M")

# Mit Progress-Callback
def my_progress(progress):
    print(f"{progress.model}: {progress.percent:.1f}%")

llm.download_model_from_path("deepseek", progress_callback=my_progress)
```

## Model Path Format

### Unterstützte Formate

```
# 1. Shortcut (vordefinierte Modelle)
mistral
deepseek
qwen
llama

# 2. Registry + Path
hf.co/namespace/repo
huggingface.co/user/model-GGUF
ollama.ai/library/llama2
custom.ai/org/model

# 3. Vollständiger Pfad mit Tag
hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF:main
custom.ai/myorg/model:v1.0

# 4. Mit Protokoll
https://hf.co/user/repo
https://models.jarviscore.ai/community/model
```

### Registry-Aliase

```python
"hf.co"        → "huggingface.co"
"hf"           → "huggingface.co"
"huggingface"  → "huggingface.co"
"ollama"       → "registry.ollama.ai"
```

## Quantization Variants

Jedes Modell unterstützt mehrere Quantization-Varianten:

| Variant | Qualität | Geschwindigkeit | Speicher | Use Case |
|---------|---------|----------------|----------|----------|
| **Q4_K_M** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ~4GB | **Standard** (balanced) |
| **Q4_K_S** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ~3.5GB | Schnell, weniger RAM |
| **Q5_K_M** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ~5GB | Höhere Qualität |
| **Q6_K** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ~6GB | Sehr hohe Qualität |
| **Q8_0** | ⭐⭐⭐⭐⭐⭐ | ⭐ | ~8GB | Maximum Qualität |

```python
# Alle Varianten abrufen
from core.model_registry import ModelRegistry

variants = ModelRegistry.get_variants("mistral")
for url in variants:
    print(url)
```

## Error Handling

```python
try:
    file_path = downloader.download(
        model_key="test",
        url="https://...",
        filename="model.gguf",
        expected_sha256="abc123..."
    )
except RuntimeError as e:
    if "SHA256" in str(e):
        print("Integritätsprüfung fehlgeschlagen!")
    elif "404" in str(e):
        print("Modell nicht gefunden!")
    else:
        print(f"Download-Fehler: {e}")
```

## Performance

### Download-Geschwindigkeit

- **Chunk-Size**: 4 MB (optimiert für Balance zwischen RAM und Speed)
- **Retry-Mechanismus**: 3 Versuche mit exponential backoff
- **Resume-Support**: Spart Bandbreite bei unterbrochenen Downloads
- **Progress-Updates**: Alle 500ms (konfigurierbar)

### Speicherverbrauch

- **Streaming**: Modelle werden nicht vollständig in RAM geladen
- **SHA256 in Chunks**: Nur 4 MB RAM für Verifizierung
- **Manifest-Cache**: Wenige KB pro Modell

## Migration von altem System

Wenn Du bereits Modelle mit dem alten System heruntergeladen hast:

```python
from core.model_manifest import ManifestManager
from pathlib import Path

manager = ManifestManager(manifest_dir=Path("models/manifests"))
downloader = ModelDownloader(download_dir=Path("models/llm"))

# Existierende Modelle erfassen
for model_file in Path("models/llm").glob("*.gguf"):
    # SHA256 berechnen
    sha256 = downloader.calculate_file_hash(model_file)
    
    # Manifest erstellen
    model_key = model_file.stem.lower()
    manifest = manager.create_manifest(
        model_key=model_key,
        registry="huggingface.co",
        namespace="unknown",
        repository="unknown"
    )
    
    # Layer hinzufügen
    manifest.add_layer(
        filename=model_file.name,
        sha256=sha256,
        size_bytes=model_file.stat().st_size
    )
    
    manifest.mark_downloaded()
    manifest.mark_verified()
    manager.update_manifest(model_key, manifest)
    
    print(f"✅ {model_key}: {sha256[:8]}...")
```

## Roadmap

### v1.0 (Current) ✅
- Multi-Registry-Support
- Resume-Downloads
- SHA256-Verifizierung
- Progress-Tracking
- Manifest-System

### v2.0 (Geplant)
- Blob-Deduplication (wie Ollama)
- Parallel-Downloads (mehrere Chunks gleichzeitig)
- Delta-Updates (nur geänderte Teile laden)
- Model-Server (eigene Registry hosten)
- WebUI für Download-Management

## Troubleshooting

### Download schlägt fehl

```python
# Debug-Modus aktivieren
import logging
logging.basicConfig(level=logging.DEBUG)

# Retry-Parameter erhöhen
downloader.max_retries = 5
downloader.retry_delay = 5.0
```

### SHA256-Mismatch

```python
# Datei neu herunterladen
downloader.download(
    model_key="mistral",
    url=url,
    filename="model.gguf",
    force=True  # Ignoriert existierende Datei
)
```

### HuggingFace 403 Forbidden

```python
# Token setzen für private Repos
downloader.set_hf_token("hf_YourTokenHere")

# Oder Environment Variable
import os
os.environ["HUGGINGFACE_TOKEN"] = "hf_..."
```

## Beispiele

### Beispiel 1: Batch-Download mehrerer Modelle

```python
models = ["mistral", "qwen", "deepseek"]

for model in models:
    try:
        url = get_download_url(model)
        downloader.download(
            model_key=model,
            url=url,
            filename=f"{model}.gguf"
        )
        print(f"✅ {model} downloaded")
    except Exception as e:
        print(f"❌ {model} failed: {e}")
```

### Beispiel 2: Custom Model von eigenem Server

```python
ModelRegistry.add_known_model(
    shortcut="jarvis-custom",
    namespace="jarviscore",
    repository="custom-model-GGUF",
    filename="jarvis-7b-q4.gguf"
)

# Custom Registry URL
model_path = ModelRegistry.parse("models.jarviscore.ai/jarviscore/custom-model-GGUF")
url = model_path.full_url("jarvis-7b-q4.gguf")

downloader.download(
    model_key="jarvis-custom",
    url=url,
    filename="jarvis-7b-q4.gguf"
)
```

## Credits

Inspiriert von:
- **Ollama**: Model Registry & Manifest System
- **HuggingFace**: Repository Structure
- **Docker**: Layer-basiertes Download-Konzept

## License

Apache 2.0 (wie JarvisCore)
