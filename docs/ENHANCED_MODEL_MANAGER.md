# 🚀 Enhanced Model Manager - Documentation

**Version:** 1.0.0  
**Last Updated:** December 10, 2025

---

## 📋 Overview

Der Enhanced Model Manager erweitert die bestehende LLM-Verwaltung in JarvisCore um:

- ✅ **Download-Progress-Tracking** mit Echtzeit-Fortschrittsanzeige
- ✅ **Automatisches Benchmarking** für Performance-Metriken
- ✅ **Model-Comparison-View** zum Vergleich mehrerer Modelle
- ✅ **Context-Window-Visualisierung** für Token-Nutzung
- ✅ **Persistente Benchmark-Ergebnisse** mit History
- ✅ **Detaillierte Modell-Informationen** (GPU-Layer, Ladezeit, Speicher)

---

## 🎯 Features im Detail

### 1. Download Progress Tracking

**Funktionalität:**
- Echtzeit-Download-Progress mit Geschwindigkeit und ETA
- Visueller Progress-Bar mit Prozentanzeige
- Heruntergeladene/Gesamt-Bytes-Anzeige
- Automatisches Refresh nach erfolgreichem Download
- Error-Handling mit detaillierten Fehlermeldungen

**UI-Elemente:**
```
┌─────────────────────────────────────┐
│ Downloading MISTRAL                 │
├─────────────────────────────────────┤
│ Status: Downloading...              │
│ [████████████░░░░░░░░] 65.3%        │
│                                     │
│ Downloaded: 2.7 GB / 4.1 GB         │
│ Speed: 15.3 MB/s     ETA: 1m 32s    │
│                                     │
│ [Close (disabled)]                  │
└─────────────────────────────────────┘
```

**Implementierung:**
- `ModelDownloadManager` verwaltet Downloads
- Callback-System für UI-Updates
- Thread-sichere Progress-Speicherung
- Automatische Geschwindigkeits- und ETA-Berechnung

---

### 2. Model Benchmarking

**Funktionalität:**
- Automatische Performance-Tests mit standardisiertem Prompt
- Messung von Tokens/Sekunde, Inference-Zeit, Memory-Usage
- Persistente Speicherung in `data/model_benchmarks.json`
- History der letzten 10 Benchmark-Runs pro Modell
- Durchschnitts-Performance-Berechnung

**Gemessene Metriken:**
- **Tokens/Second**: Durchsatz (höher = besser)
- **Inference Time**: Antwortzeit in Millisekunden (niedriger = besser)
- **Memory Usage**: RAM-Verbrauch in MB
- **Context Usage**: Genutzte vs. verfügbare Tokens
- **Prompt/Completion Tokens**: Token-Verteilung

**Benchmark-Prompt:**
```python
test_prompt = (
    "Explain quantum computing in simple terms. "
    "Focus on the key principles and practical applications."
)
```

**Ergebnis-Format:**
```json
{
  "model_key": "mistral",
  "tokens_per_second": 45.32,
  "inference_time": 3250.5,
  "context_used": 158,
  "context_available": 8192,
  "timestamp": "2025-12-10T19:30:45.123456",
  "prompt_tokens": 25,
  "completion_tokens": 133,
  "memory_usage_mb": 4829.3
}
```

---

### 3. Model Comparison

**Funktionalität:**
- Side-by-Side-Vergleich mehrerer Modelle
- Sortierung nach Performance-Metriken
- Automatische Identifikation des schnellsten/effizientesten Modells
- Tabellarische Darstellung mit Highlighting

**Vergleichs-Tabelle:**
```
┌────────────────────────────────────────────────────────────────┐
│ 📊 Performance Comparison                                      │
├─────────┬────────────┬──────────────┬────────────┬─────────────┤
│ Model   │ Tokens/Sec │ Inference(ms)│ Memory(MB) │ Context     │
├─────────┼────────────┼──────────────┼────────────┼─────────────┤
│ MISTRAL │ 45.32      │ 3250.5       │ 4829.3     │ 158/8192    │
│ LLAMA3  │ 38.17      │ 3890.2       │ 5123.7     │ 165/8192    │
│ DEEPSEEK│ 28.44      │ 5210.8       │ 6890.1     │ 172/8192    │
└─────────┴────────────┴──────────────┴────────────┴─────────────┘

🏆 Fastest: MISTRAL (45.32 tokens/sec)
💾 Most Efficient: MISTRAL (4829.3 MB)
```

---

### 4. Context Window Visualization

**Funktionalität:**
- Farbcodierte Progress-Bar für Token-Nutzung
- Grün (< 50%), Orange (50-80%), Rot (> 80%)
- Numerische Anzeige: `Used/Available tokens`
- Integration in Benchmark-Ergebnisse

**Visualisierung:**
```
Context: 158/8192 tokens [█████░░░░░░░░░░░░░░░] 1.9%
```

---

### 5. Enhanced Model List

**Erweiterte Informationen pro Modell:**
- ✅/❌ Ready-Status
- 🟢 Active-Indicator
- 🔵 Loaded-Indicator
- 📝 Display Name und Description
- 📁 Dateiname und Größe
- 📊 Context Window Size
- ⚡ Latest/Average Benchmark Results
- 🎮 GPU-Layer-Info
- ⏱️ Load Time

**Beispiel-Ausgabe:**
```
✅  MISTRAL  🟢 ACTIVE  🔵 LOADED
     📝 Nous Hermes 2 (Mistral 7B DPO)
     💬 Einsatzgebiet: Code, technische Details, Systembefehle
     📁 Nous-Hermes-2-Mistral-7B-DPO.Q4_K_M.gguf (4.1 GB)
     📊 Context Window: 8192 tokens
     ⚡ Latest Benchmark:
        • 45.3 tokens/sec
        • 3251 ms inference time
        • 4829.3 MB memory
     🎮 GPU Acceleration: 35 layers
     ⏱️  Load Time: 8.3s
```

---

## 📦 Installation

### Voraussetzungen

```bash
# Bereits in requirements.txt enthalten:
pip install dearpygui psutil requests
```

### Integration

**Option 1: Vollständige Integration (Empfohlen)**

Ersetze den Model-Manager-Tab in `desktop/jarvis_imgui_app_full.py`:

```python
# Am Anfang der Datei importieren
from desktop.model_manager_ui import ExtendedModelManagerUI

# In der __init__-Methode initialisieren
self.model_manager_ui = ExtendedModelManagerUI(jarvis_instance)

# Im _build_ui Tab erstellen
with dpg.tab(label="  🧠 Models  "):
    self.model_manager_ui.build_ui(dpg.last_container())
```

**Option 2: Standalone-Nutzung**

Verwende die Klassen direkt:

```python
from desktop.model_manager_extended import ModelBenchmark, ModelDownloadManager

# Benchmarking
benchmark = ModelBenchmark(jarvis_instance)
result = benchmark.run_benchmark("mistral")
print(f"Performance: {result.tokens_per_second:.2f} tokens/sec")

# Download mit Progress
download_manager = ModelDownloadManager(jarvis_instance)
download_manager.register_callback(lambda p: print(f"Progress: {p.percent}%"))
download_manager.download_model("llama3")
```

---

## 🔧 API-Referenz

### ModelBenchmark

```python
class ModelBenchmark:
    def __init__(self, jarvis_instance)
    def run_benchmark(self, model_key: str, progress_callback: Optional[Callable] = None) -> Optional[BenchmarkResult]
    def get_latest_result(self, model_key: str) -> Optional[BenchmarkResult]
    def get_average_performance(self, model_key: str) -> Optional[Dict[str, float]]
```

**Beispiel:**
```python
benchmark = ModelBenchmark(jarvis)

# Run benchmark
result = benchmark.run_benchmark(
    "mistral",
    progress_callback=lambda data: print(data['status'])
)

if result:
    print(f"Tokens/sec: {result.tokens_per_second}")
    print(f"Inference: {result.inference_time} ms")
    print(f"Memory: {result.memory_usage_mb} MB")

# Get historical data
avg = benchmark.get_average_performance("mistral")
print(f"Average: {avg['avg_tokens_per_second']} tokens/sec")
```

---

### ModelDownloadManager

```python
class ModelDownloadManager:
    def __init__(self, jarvis_instance)
    def register_callback(self, callback: Callable)
    def download_model(self, model_key: str) -> bool
    def get_progress(self, model_key: str) -> Optional[DownloadProgress]
    def is_downloading(self, model_key: str) -> bool
```

**Beispiel:**
```python
download_manager = ModelDownloadManager(jarvis)

# Register callback for progress updates
def on_progress(progress: DownloadProgress):
    print(f"Status: {progress.status}")
    print(f"Progress: {progress.percent}%")
    print(f"Speed: {format_speed(progress.speed)}")
    print(f"ETA: {format_eta(progress.eta)}")

download_manager.register_callback(on_progress)

# Start download
success = download_manager.download_model("llama3")
if success:
    print("Download completed!")
```

---

### ContextWindowVisualizer

```python
class ContextWindowVisualizer:
    @staticmethod
    def create_visualization(context_used: int, context_available: int, parent_tag: str)
```

**Beispiel:**
```python
ContextWindowVisualizer.create_visualization(
    context_used=158,
    context_available=8192,
    parent_tag="my_window"
)
```

---

### ExtendedModelManagerUI

```python
class ExtendedModelManagerUI:
    def __init__(self, jarvis_instance)
    def build_ui(self, parent_tag: str)
```

**Beispiel:**
```python
model_ui = ExtendedModelManagerUI(jarvis)

# In DearPyGui window/tab
with dpg.window(label="Models"):
    model_ui.build_ui(dpg.last_container())
```

---

## 📊 Datenformate

### DownloadProgress

```python
@dataclass
class DownloadProgress:
    model: str                      # Model key (e.g., "mistral")
    status: str                     # "in_progress", "completed", "failed", "error"
    downloaded: int                 # Bytes downloaded
    total: int                      # Total bytes
    percent: Optional[float]        # Progress percentage (0-100)
    speed: Optional[float]          # Download speed (bytes/sec)
    eta: Optional[float]            # Estimated time remaining (seconds)
    message: Optional[str]          # Optional status message
```

---

### BenchmarkResult

```python
@dataclass
class BenchmarkResult:
    model_key: str                  # Model identifier
    tokens_per_second: float        # Throughput
    inference_time: float           # Time in milliseconds
    context_used: int               # Tokens used in benchmark
    context_available: int          # Max context window size
    timestamp: datetime             # When benchmark was run
    prompt_tokens: int              # Input tokens
    completion_tokens: int          # Output tokens
    memory_usage_mb: float          # RAM usage
```

---

### Benchmark Storage Format

**Datei:** `data/model_benchmarks.json`

```json
{
  "mistral": [
    {
      "model_key": "mistral",
      "tokens_per_second": 45.32,
      "inference_time": 3250.5,
      "context_used": 158,
      "context_available": 8192,
      "timestamp": "2025-12-10T19:30:45.123456",
      "prompt_tokens": 25,
      "completion_tokens": 133,
      "memory_usage_mb": 4829.3
    }
  ],
  "llama3": [...],
  "deepseek": [...]
}
```

---

## 🎨 UI-Komponenten

### Action Buttons

```python
[🔄 Refresh] [📥 Download] [⚡ Benchmark] [🔍 Compare] [🔴 Unload All]
```

- **Refresh**: Aktualisiert Modellliste mit aktuellen Informationen
- **Download**: Öffnet Download-Dialog für verfügbare Modelle
- **Benchmark**: Startet Performance-Test für geladene Modelle
- **Compare**: Zeigt Vergleichstabelle für gebenchmarkte Modelle
- **Unload All**: Entlädt alle aktuell geladenen Modelle

---

### Download Dialog

**Features:**
- Liste aller nicht-heruntergeladenen Modelle
- Anzeige von Name, Beschreibung, Größe, Context-Length
- Download-Button pro Modell
- Automatisches Schließen nach Auswahl

---

### Progress Window

**Features:**
- Echtzeit-Progress-Bar mit Prozentanzeige
- Heruntergeladene/Gesamt-Bytes
- Download-Geschwindigkeit (MB/s)
- ETA (Estimated Time Arrival)
- Status-Text mit Fehlermeldungen
- Deaktivierter Close-Button während Download

---

### Benchmark Dialog

**Features:**
- Liste aller verfügbaren Modelle
- Kennzeichnung bereits geladener Modelle
- Einzeln- oder Alle-Benchmarking
- Automatisches Laden falls nötig

---

### Comparison View

**Features:**
- Sortierbare Tabelle mit allen Metriken
- Highlighting des schnellsten Modells (🏆)
- Highlighting des effizientesten Modells (💾)
- Farbcodierte Performance-Indikatoren

---

## 🔍 Troubleshooting

### Problem: Benchmark schlägt fehl

**Ursache:** Modell nicht geladen oder llama_cpp nicht verfügbar

**Lösung:**
```python
# Prüfe ob Modell bereit ist
if jarvis.llm_manager.is_model_ready("mistral"):
    jarvis.llm_manager.load_model("mistral")
    benchmark.run_benchmark("mistral")
```

---

### Problem: Download hängt

**Ursache:** Netzwerkprobleme oder falsche URL

**Lösung:**
```python
# Prüfe Download-Status
progress = download_manager.get_progress("mistral")
if progress.status == "error":
    print(f"Error: {progress.message}")

# Retry download
download_manager.download_model("mistral")
```

---

### Problem: Benchmarks werden nicht gespeichert

**Ursache:** Keine Schreibrechte für `data/` Verzeichnis

**Lösung:**
```bash
mkdir -p data
chmod 755 data
```

---

## 🚀 Performance-Tipps

### GPU-Beschleunigung

```bash
# Aktiviere GPU für schnellere Benchmarks
export LLAMA_USE_GPU=1
export LLAMA_GPU_LAYERS=-1  # Alle Layer auf GPU
```

### Cache-Management

```python
# Disable cache for accurate benchmarks
result = llm_manager.generate_response(
    prompt=test_prompt,
    enable_cache=False  # Wichtig für Benchmarking!
)
```

### Benchmark-Frequenz

- **Empfehlung:** 1x pro Woche oder nach Modell-Updates
- **Nicht empfohlen:** Nach jedem Load (zu zeitintensiv)

---

## 📝 Changelog

### Version 1.0.0 (2025-12-10)

**Features:**
- ✅ Initial Release
- ✅ Download Progress Tracking
- ✅ Model Benchmarking
- ✅ Model Comparison
- ✅ Context Window Visualization
- ✅ Persistent Benchmark Storage
- ✅ Enhanced Model List

---

## 🤝 Contributing

Verbesserungsvorschläge willkommen!

**Geplante Features:**
- [ ] Live-Context-Monitoring während Inferenz
- [ ] Export von Benchmark-Ergebnissen als CSV
- [ ] Automatische Benchmark-Scheduling
- [ ] Model-Performance-History-Charts
- [ ] GPU-Memory-Monitoring

---

## 📄 Lizenz

Apache 2.0 - Siehe [LICENSE](../LICENSE)

---

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/Lautloserspieler/JarvisCore/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Lautloserspieler/JarvisCore/discussions)
- **Email:** emeyer@fn.de
