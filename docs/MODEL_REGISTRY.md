# Model Registry - Ollama-Level Download System

## Übersicht

Das Model Registry System bietet Ollama-level Funktionalität für das Herunterladen und Verwalten von LLM-Modellen in JarvisCore.

### Features

✅ **Multi-Registry Support**
- Hugging Face (`hf.co`, `huggingface.co`)
- Ollama Registry (`ollama.ai`)
- Custom Registries

✅ **Robuster Download**
- Resume-Support (unterbrochene Downloads fortsetzen)
- SHA256-Verifizierung
- Chunked Download (4MB chunks)
- Progress-Tracking mit ETA

✅ **Manifest-System**
- Metadaten für jedes Modell
- Layer-basierte Architektur (Ollama-kompatibel)
- Versionierung mit Tags

✅ **Flexible Model-Pfade**
- Einfach: `mistral`
- Mit Namespace: `bartowski/mistral`
- Full Path: `hf.co/bartowski/mistral:v1`
- Custom Registry: `myregistry.com/namespace/model:tag`

---

## Architektur

```
core/model_registry/
├── modelpath.py       # Model-Pfad Parser (Ollama-kompatibel)
├── manifest.py        # Manifest-Handler für Metadaten
├── downloader.py      # Download mit Resume + SHA256
├── registry.py        # Zentrale Registry-Verwaltung
└── __init__.py        # Package exports
```

---

## Verwendung

### 1. Basis-Download

```python
from core.model_registry import ModelRegistry
from pathlib import Path

# Registry initialisieren
registry = ModelRegistry(models_dir=Path("models/llm"))

# Bekanntes Modell herunterladen
path = registry.download_model("mistral-nemo-instruct-2407-q4")
print(f"Modell heruntergeladen: {path}")
```

### 2. Custom Model-Pfad

```python
# Mit vollem Pfad
path = registry.download_model(
    model_identifier="hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF",
    filename="Qwen2.5-7B-Instruct-Q4_K_M.gguf"
)

# Mit Namespace/Repo
path = registry.download_model(
    model_identifier="bartowski/mistral-7b",
    filename="mistral-7b-instruct.Q4_K_M.gguf"
)
```

### 3. Mit Progress-Tracking

```python
def on_progress(progress):
    print(f"Status: {progress['status']}")
    print(f"Progress: {progress['percent']:.1f}%")
    print(f"Speed: {progress['speed'] / 1024 / 1024:.2f} MB/s")
    if progress['eta']:
        print(f"ETA: {progress['eta']:.0f} seconds")

path = registry.download_model(
    model_identifier="mistral-nemo-instruct-2407-q4",
    progress_callback=on_progress
)
```

### 4. Mit SHA256-Verifizierung

```python
path = registry.download_model(
    model_identifier="hf.co/bartowski/model",
    filename="model.Q4_K_M.gguf",
    expected_sha256="abc123..."
)
# Automatische Verifizierung nach Download
```

### 5. Mit HuggingFace Token

```python
# Token wird automatisch aus settings geholt
# Oder manuell:
path = registry.download_model(
    model_identifier="hf.co/private/model",
    filename="model.gguf",
    hf_token="hf_..."
)
```

---

## Integration in LLM Manager

```python
from core.llm_manager import LLMManager

llm = LLMManager()

# Neuer Ollama-level Download
success = llm.download_model_advanced(
    model_identifier="hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF",
    filename="Qwen2.5-7B-Instruct-Q4_K_M.gguf"
)

# Model-Pfad parsen
info = llm.parse_model_path("hf.co/bartowski/model:v1")
print(info)
# {
#   'registry': 'huggingface.co',
#   'namespace': 'bartowski',
#   'repository': 'model',
#   'tag': 'v1',
#   'full_path': 'huggingface.co/bartowski/model:v1',
#   ...
# }

# Bekannte Modelle auflisten
known = llm.list_known_models()
for key, info in known.items():
    print(f"{key}: {info['description']}")
```

---

## Model-Pfad Format

### Syntax

```
[registry/]namespace/repository[:tag]
```

### Beispiele

| Input | Parsed |
|-------|--------|
| `mistral` | `huggingface.co/bartowski/mistral:latest` |
| `bartowski/qwen` | `huggingface.co/bartowski/qwen:latest` |
| `hf.co/meta/llama:v2` | `huggingface.co/meta/llama:v2` |
| `ollama.ai/library/mistral` | `registry.ollama.ai/library/mistral:latest` |
| `myhost.com/ns/model:v1` | `myhost.com/ns/model:v1` |

---

## Bekannte Modelle

Die Registry kennt folgende Modelle out-of-the-box:

```python
KNOWN_MODELS = {
    "mistral-nemo-instruct-2407-q4": {
        "path": "hf.co/second-state/Mistral-Nemo-Instruct-2407-GGUF",
        "filename": "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "size_gb": 7.48
    },
    "deepseek-r1-distill-llama-8b-q4": {...},
    "qwen2.5-7b-instruct-q4": {...},
    "llama-2-7b-chat-q4": {...}
}
```

Eigene Modelle können einfach hinzugefügt werden.

---

## Manifest-System

Jedes heruntergeladene Modell erhält ein Manifest:

```json
{
  "schemaVersion": 2,
  "name": "mistral",
  "tag": "latest",
  "digest": "sha256:abc123...",
  "size": 7480000000,
  "createdAt": "2025-12-16T09:20:00Z",
  "layers": [
    {
      "digest": "sha256:def456...",
      "size": 7480000000,
      "filename": "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf"
    }
  ],
  "config": {}
}
```

Manifeste werden in `models/llm/.manifests/` gespeichert.

---

## Resume-Support

Unterbrochene Downloads werden automatisch fortgesetzt:

```python
# Download starten
registry.download_model("mistral-nemo-instruct-2407-q4")
# ... Verbindung bricht ab ...

# Erneut starten - wird fortgesetzt!
registry.download_model("mistral-nemo-instruct-2407-q4")
# → Startet ab bereits heruntergeladenen Bytes
```

---

## API-Referenz

### ModelRegistry

#### `download_model(model_identifier, filename=None, expected_sha256=None, progress_callback=None, hf_token=None)`

Lädt ein Modell herunter.

**Args:**
- `model_identifier`: Model-Key oder Pfad
- `filename`: Dateiname (optional für bekannte Modelle)
- `expected_sha256`: SHA256-Checksum (optional)
- `progress_callback`: Callback für Progress-Updates
- `hf_token`: HuggingFace Token (optional)

**Returns:** `Path` zur Datei

#### `parse_model_path(path)`

Parst einen Model-Pfad.

**Returns:** `ModelPath` Objekt

#### `model_exists(filename)`

Prüft ob ein Modell lokal existiert.

**Returns:** `bool`

#### `list_local_models()`

Listet alle lokalen GGUF-Modelle.

**Returns:** `List[str]`

---

## Vergleich zu Ollama

| Feature | Ollama | JarvisCore (neu) |
|---------|--------|------------------|
| Multi-Registry | ✅ | ✅ |
| Resume-Support | ✅ | ✅ |
| SHA256-Verify | ✅ | ✅ |
| Manifest-System | ✅ | ✅ |
| Blob-Dedup | ✅ | ❌ (future) |
| Model Pull | ✅ | ✅ |
| Custom Registry | ✅ | ✅ |

---

## Nächste Schritte

- [ ] SHA256-Checksums für alle bekannten Modelle hinzufügen
- [ ] Blob-Deduplication implementieren
- [ ] Model-Push zu Custom Registry
- [ ] Kompression-Support (gzip, zstd)
- [ ] Delta-Updates für Modell-Versionen

---

## Lizenz

Apache 2.0 - Siehe LICENSE
