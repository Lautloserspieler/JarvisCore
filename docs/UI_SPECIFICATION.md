# 🎮 J.A.R.V.I.S. UI Specification - Complete Tab & Function Overview

**Version:** 1.0.0  
**Last Updated:** December 10, 2025  
**Target:** UE5-Style ImGui Desktop Application

---

## 📋 Table of Contents

1. [UI Overview](#ui-overview)
2. [Tab 1: Dashboard](#tab-1--dashboard)
3. [Tab 2: Chat](#tab-2--chat)
4. [Tab 3: Models](#tab-3--models)
5. [Tab 4: Plugins](#tab-4--plugins)
6. [Tab 5: Memory](#tab-5--memory)
7. [Tab 6: Logs](#tab-6--logs)
8. [Tab 7: Settings](#tab-7--settings)
9. [Global Components](#global-components)
10. [Backend Integration](#backend-integration)
11. [Future Enhancements](#future-enhancements)

---

## 🎨 UI Overview

### Main Window Layout

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🎮 J.A.R.V.I.S. Control Center              🟢 ONLINE    FPS: 60    │
├────────────────────────────────────────────────────────────────────────┤
│ [📊 Dashboard] [💬 Chat] [🧠 Models] [🧩 Plugins] [🗄️ Memory]        │
│ [📜 Logs] [⚙️ Settings]                                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│                     [TAB CONTENT AREA]                                 │
│                                                                        │
│                                                                        │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│ ● System Ready                 FPS: 60         Powered by UE5 Design  │
└────────────────────────────────────────────────────────────────────────┘
```

### Color Scheme (UE5 Dark Theme)

- **Background:** RGB(28, 28, 30)
- **Card Background:** RGB(35, 35, 37)
- **Accent Orange:** RGB(255, 140, 0) - Primary actions
- **Accent Blue:** RGB(100, 180, 255) - Info
- **Success Green:** RGB(100, 255, 100)
- **Error Red:** RGB(255, 100, 100)
- **Text Primary:** RGB(240, 240, 240)
- **Text Secondary:** RGB(180, 180, 180)

---

## Tab 1: 📊 Dashboard

### Purpose
Echtzeit-System-Monitoring mit Live-Graphen und detaillierten Metriken.

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📊 SYSTEM METRICS                                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│ │ 🖥️ CPU Usage │ │ 💾 RAM Usage │ │ 🎮 GPU Usage │                │
│ │              │ │              │ │              │                │
│ │ [Graph 45%] │ │ [Graph 60%]  │ │ [Graph 30%]  │                │
│ │              │ │              │ │              │                │
│ └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 📈 DETAILED STATISTICS                                      │   │
│ │                                                             │   │
│ │ 🖥️ CPU: 45.3% (12 cores)                                   │   │
│ │ 💾 RAM: 16.2 GB / 32.0 GB (50.6%)                          │   │
│ │ 🎮 GPU: NVIDIA RTX 4090 (30.1%)                            │   │
│ │ 🌡️ Temperature: 65°C                                        │   │
│ │ ⚡ Power: 180W                                               │   │
│ └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Features & Functions

#### 1. Live System Graphs (3 Cards)

**CPU Usage Graph:**
- **Function:** Echtzeit CPU-Auslastung über 100 Datenpunkte (100s Historie)
- **Update:** Jede Sekunde via Background-Thread
- **Display:** Simple Line Plot mit Overlay (Prozent)
- **Backend Call:** `jarvis.get_system_metrics()["summary"]["cpu_percent"]`
- **Interactive:** Keine (Read-only)

**RAM Usage Graph:**
- **Function:** Echtzeit RAM-Auslastung über 100 Datenpunkte
- **Update:** Jede Sekunde
- **Display:** Simple Line Plot mit Overlay
- **Backend Call:** `jarvis.get_system_metrics()["summary"]["memory_percent"]`
- **Interactive:** Keine

**GPU Usage Graph:**
- **Function:** Echtzeit GPU-Auslastung über 100 Datenpunkte
- **Update:** Jede Sekunde
- **Display:** Simple Line Plot mit Overlay ("N/A" wenn keine GPU)
- **Backend Call:** `jarvis.get_system_metrics()["summary"]["gpu_utilization"]`
- **Interactive:** Keine

#### 2. Detailed Statistics Card

**Angezeigt:**
- CPU: Prozent, Core-Count
- RAM: GB Used/Total, Prozent
- GPU: Name, Prozent
- Temperature: CPU-Temp in °C
- Power: Watt-Verbrauch

**Backend Call:** `jarvis.get_system_metrics()` → Returns:
```python
{
  "summary": {
    "cpu_percent": 45.3,
    "cpu_count": 12,
    "memory_percent": 50.6,
    "memory_used_gb": 16.2,
    "memory_total_gb": 32.0,
    "gpu_utilization": 30.1,
    "gpu_name": "NVIDIA RTX 4090",
    "cpu_temp": 65.0,
    "power_usage": 180.0
  }
}
```

**Update:** Jede Sekunde via Background-Thread

#### 3. Background Worker

**Thread:** `metrics_loop()` - Läuft während UI aktiv
- **Interval:** 1 Sekunde
- **Tasks:**
  - Metrics von Backend abrufen
  - History-Deques updaten (`cpu_history`, `ram_history`, `gpu_history`)
  - UI-Elemente updaten (`dpg.set_value`, `dpg.configure_item`)

### Backend Integration Points

```python
# core/system_monitor.py
class SystemMonitor:
    def get_metrics(self) -> Dict[str, Any]:
        return {
            "summary": {
                "cpu_percent": psutil.cpu_percent(),
                "cpu_count": psutil.cpu_count(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_gb": psutil.virtual_memory().used / (1024**3),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "gpu_utilization": self._get_gpu_usage(),
                "gpu_name": self._get_gpu_name(),
                "cpu_temp": self._get_cpu_temp(),
                "power_usage": self._get_power_usage()
            }
        }
```

---

## Tab 2: 💬 Chat

### Purpose
Interaktiver Chat mit JARVIS - Befehle senden, Antworten erhalten, Historie anzeigen.

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ 💬 CHAT WITH JARVIS                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ 👤 USER:                                                    │   │
│ │ Hey JARVIS, what's the weather?                            │   │
│ │                                                             │   │
│ │ 🤖 JARVIS:                                                  │   │
│ │ I'm an offline assistant without weather API access.       │   │
│ │ You can add a weather plugin or check manually.            │   │
│ │                                                             │   │
│ │ 👤 USER:                                                    │   │
│ │ Load llama3 model                                           │   │
│ │                                                             │   │
│ │ 🤖 JARVIS:                                                  │   │
│ │ ✅ Loading llama3... Done! Model ready.                    │   │
│ └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ ┌──────────────────────────────────────────┐ ┌────────────────┐   │
│ │ Enter command...                         │ │  🚀 SEND       │   │
│ └──────────────────────────────────────────┘ └────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Features & Functions

#### 1. Chat History Display

**Function:** Zeigt Konversationsverlauf (User + Assistant)
- **Storage:** `deque(maxlen=100)` - Letzte 100 Messages
- **Format:**
  ```
  👤 USER:
  <user_message>
  
  🤖 JARVIS:
  <assistant_response>
  ```
- **Update:** Nach jedem Send (sofort)
- **Scrolling:** Automatisch zum Ende (manuell scrollbar)
- **Wrapping:** Text wraps bei Window-Breite

#### 2. Input Field + Send Button

**Input Field:**
- **Tag:** `chat_input`
- **Type:** `dpg.add_input_text`
- **Features:**
  - Hint: "Enter command..."
  - Enter-to-Send: `on_enter=True`
  - Multi-line: Nein (Single-line)
  - Width: Full width minus button (190px)
  - Height: 45px (Large)

**Send Button:**
- **Label:** "🚀 SEND"
- **Width:** 190px
- **Height:** 45px
- **Callback:** `_on_chat_send()`
- **Action:**
  1. Get text from `chat_input`
  2. Clear input field
  3. Add user message to history
  4. Process via `jarvis.command_processor.process_command(text)`
  5. Add assistant response to history
  6. Update display

#### 3. Command Processing Flow

```python
def _on_chat_send(self):
    text = dpg.get_value("chat_input").strip()
    if not text:
        return
    
    # Display user message
    self.add_user_message(text)
    dpg.set_value("chat_input", "")
    
    # Process command
    if self.jarvis and hasattr(self.jarvis, 'command_processor'):
        try:
            response = self.jarvis.command_processor.process_command(text)
            self.add_assistant_message(response or "✅ Command executed.")
        except Exception as e:
            self.add_assistant_message(f"❌ Error: {e}")
    else:
        self.add_assistant_message("❌ Command processor not available.")
```

### Backend Integration Points

```python
# core/command_processor.py
class CommandProcessor:
    def process_command(self, user_input: str) -> str:
        """
        1. Intent Recognition (config/intents.json)
        2. Context Loading (Memory)
        3. Security Check (safe_mode)
        4. Plugin Routing (if needed)
        5. LLM Generation (if conversational)
        6. Return response
        """
        # ... implementation
        return response_text
```

### Supported Commands (Examples)

| Command | Backend Action | Response |
|---------|---------------|----------|
| `load llama3` | `llm_manager.load_model("llama3")` | "✅ Model loaded" |
| `unload model` | `llm_manager.unload_model()` | "✅ Model unloaded" |
| `list plugins` | `plugin_manager.get_overview()` | Plugin list |
| `enable wikipedia` | `plugin_manager.enable("wikipedia")` | "✅ Enabled" |
| `search <query>` | `knowledge_manager.search(query)` | Search results |
| `system status` | `system_monitor.get_metrics()` | Metrics summary |
| Free-form question | `llm_manager.generate_response()` | LLM answer |

---

## Tab 3: 🧠 Models

### Purpose
LLM Model Management - Download, Load, Unload, Benchmark, Compare.

### Layout (Current Simple Version)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🧠 LLM MODEL MANAGER                                                │
├─────────────────────────────────────────────────────────────────────┤
│ [🔄 Refresh] [📥 Download Model] [🔴 Unload All]                   │
├─────────────────────────────────────────────────────────────────────┤
│ ═══════════════════════════════════════════════════════════════     │
│                                                                     │
│ ✅  LLAMA3  🟢 ACTIVE  🔵 LOADED                                    │
│      📁 File: Meta-Llama-3-8B-Instruct.Q4_K_M.gguf                 │
│      📏 Size: 4368.2 MB                                             │
│                                                                     │
│ ───────────────────────────────────────────────────────────────     │
│                                                                     │
│ ✅  MISTRAL                                                         │
│      📁 File: Nous-Hermes-2-Mistral-7B-DPO.Q4_K_M.gguf            │
│      📏 Size: 4108.5 MB                                             │
│                                                                     │
│ ───────────────────────────────────────────────────────────────     │
│                                                                     │
│ ❌  DEEPSEEK                                                        │
│      📁 File: DeepSeek-R1-8B-f16.gguf                              │
│      📏 Size: 0.0 MB (NOT DOWNLOADED)                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Features & Functions

#### 1. Action Buttons (Top Bar)

**🔄 Refresh Button:**
- **Function:** Refresh model status from backend
- **Backend Call:** `jarvis.get_llm_status()` + `jarvis.llm_manager.get_model_overview()`
- **Updates:**
  - Available models
  - Downloaded status (file exists)
  - Loaded status (in memory)
  - Active model (current)
  - File size, context window
- **Width:** 160px
- **Height:** 40px

**📥 Download Model Button:**
- **Function:** Opens dialog with downloadable models
- **Backend Call:** `jarvis.llm_manager.get_model_overview()` → Filter `downloaded=False`
- **Dialog:** Lists models with:
  - Name, Description, Size (GB), Context Length
  - Download button per model
- **Action:** `jarvis.llm_manager.download_model(model_key)`
- **Width:** 180px
- **Height:** 40px

**🔴 Unload All Button:**
- **Function:** Unload all models from memory
- **Backend Call:** `jarvis.llm_manager.unload_model()` (no args = unload all)
- **Effect:** Frees RAM, no model active
- **Confirmation:** None (instant)
- **Width:** 160px
- **Height:** 40px

#### 2. Model Status Display

**Per Model Shows:**
- **Status Icons:**
  - ✅/❌ Downloaded (file exists)
  - 🟢 ACTIVE (currently in use)
  - 🔵 LOADED (in memory)
- **Metadata:**
  - 📁 Filename
  - 📏 Size (MB)
  - 📊 Context Length (not shown in current)
- **Separator:** ─── between models

**Backend Data Source:**
```python
# core/llm_manager.py
def get_model_overview(self) -> Dict[str, Dict[str, Any]]:
    return {
        "llama3": {
            "available": True,
            "downloaded": True,
            "filename": "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf",
            "size_mb": 4368.2,
            "context_length": 8192,
            "display_name": "Llama 3 8B Instruct",
            "description": "Meta's Llama 3..."
        },
        # ...
    }

def get_llm_status(self) -> Dict[str, Any]:
    return {
        "current": "llama3",  # Active model
        "loaded": ["llama3", "mistral"],  # In memory
        "available": {...}  # Same as get_model_overview
    }
```

### Enhanced Model Manager (Future)

**See:** `docs/ENHANCED_MODEL_MANAGER.md` for:
- Card-based layout with visual hierarchy
- Download progress tracking (real-time)
- Model benchmarking (tokens/sec, inference time)
- Model comparison table
- Context window visualization
- GPU layer info, load time stats

---

## Tab 4: 🧩 Plugins

### Purpose
Plugin Management - Enable/Disable, View Status, Configure.

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🧩 PLUGIN SYSTEM                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ [🔄 Refresh]                                                        │
├─────────────────────────────────────────────────────────────────────┤
│ ═══════════════════════════════════════════════════════════════     │
│                                                                     │
│ 🟢 ENABLED  WIKIPEDIA                                               │
│      🏷️  Type: ConversationPlugin                                  │
│      📝  Wikipedia search and article summaries                    │
│                                                                     │
│ ───────────────────────────────────────────────────────────────     │
│                                                                     │
│ 🟢 ENABLED  WIKIDATA                                                │
│      🏷️  Type: ConversationPlugin                                  │
│      📝  Structured knowledge from Wikidata                        │
│                                                                     │
│ ───────────────────────────────────────────────────────────────     │
│                                                                     │
│ 🔴 DISABLED  PUBMED                                                 │
│      🏷️  Type: ConversationPlugin                                  │
│      📝  Medical research papers and abstracts                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Features & Functions

#### 1. Refresh Button

**Function:** Reload plugin status from backend
- **Backend Call:** `jarvis.get_plugin_overview()`
- **Returns:** List of plugins with:
  ```python
  [
    {
      "name": "Wikipedia",
      "type": "ConversationPlugin",
      "description": "Wikipedia search...",
      "enabled": True,
      "priority": 90,
      "patterns": ["search wikipedia", "wiki"]
    },
    # ...
  ]
  ```
- **Updates:** Plugin status display
- **Width:** 160px, **Height:** 40px

#### 2. Plugin Status Display

**Per Plugin Shows:**
- **Status:**
  - 🟢 ENABLED - Plugin aktiv
  - 🔴 DISABLED - Plugin inaktiv
- **Name:** UPPERCASE
- **Type:** ConversationPlugin, SystemPlugin, etc.
- **Description:** Kurzbeschreibung (wrap)
- **Separator:** ─── zwischen Plugins

#### 3. Backend Integration

```python
# core/plugin_manager.py
class PluginManager:
    def get_overview(self) -> List[Dict[str, Any]]:
        plugins = []
        for name, plugin in self.plugins.items():
            plugins.append({
                "name": name,
                "type": type(plugin).__name__,
                "description": plugin.description,
                "enabled": plugin.enabled,
                "priority": plugin.priority,
                "patterns": plugin.patterns
            })
        return plugins
    
    def enable_plugin(self, name: str):
        if name in self.plugins:
            self.plugins[name].enabled = True
    
    def disable_plugin(self, name: str):
        if name in self.plugins:
            self.plugins[name].enabled = False
```

### Available Plugins (Default)

| Plugin | Type | Description |
|--------|------|-------------|
| **Wikipedia** | Conversation | Wikipedia search + summaries |
| **Wikidata** | Conversation | Structured knowledge queries |
| **PubMed** | Conversation | Medical research papers |
| **Semantic Scholar** | Conversation | Academic papers |
| **OpenStreetMap** | Conversation | Location queries |
| **OpenLibrary** | Conversation | Book information |
| **Memory** | Conversation | Long-term memory queries |
| **Clarification** | Conversation | Ask for clarification |

### Future Enhancements

- **Enable/Disable Buttons** per Plugin (inline)
- **Configuration Dialog** (click on plugin → settings)
- **Priority Slider** (adjust plugin priority)
- **Pattern Editor** (edit trigger patterns)
- **Usage Statistics** (calls, success rate)

---

## Tab 5: 🗄️ Memory

### Purpose
Memory Core - View/Search short-term, long-term, timeline memories.

### Current Status

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🗄️ MEMORY CORE                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ [🔄 Refresh] [🗑️ Clear Cache]                                       │
├─────────────────────────────────────────────────────────────────────┤
│ 🚧 Memory viewer under construction...                              │
└─────────────────────────────────────────────────────────────────────┘
```

**Note:** Placeholder - Implementation noch nicht fertig.

### Planned Features

#### 1. Memory Type Tabs (Sub-Tabs)

**Short-Term Memory:**
- Last N conversations (deque)
- Recent facts/entities
- Current session context

**Long-Term Memory:**
- Persistent facts (SQLite/Pickle)
- User preferences
- Learned patterns

**Timeline Memory:**
- Chronological event log
- Date-based queries
- Context reconstruction

**Vector Memory:**
- Semantic search results
- Embedding-based retrieval
- Similar memory queries

#### 2. Action Buttons

**🔄 Refresh:**
- Reload memory from backend
- Backend Call: `jarvis.memory_manager.get_all_memories()`

**🗑️ Clear Cache:**
- Clear short-term memory
- Backend Call: `jarvis.memory_manager.clear_short_term()`

**🔍 Search:**
- Search bar for memory queries
- Semantic + keyword search
- Backend Call: `jarvis.memory_manager.search(query)`

#### 3. Display Format

**Memory Entry Card:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🕐 2025-12-10 20:15:32                                     │
│ 📝 Type: Conversation                                       │
│                                                             │
│ User: "What's the weather in Berlin?"                      │
│ Assistant: "I don't have weather API access..."            │
│                                                             │
│ Context: [weather, location, api]                          │
│ Importance: ⭐⭐⭐ (Medium)                                   │
└─────────────────────────────────────────────────────────────┘
```

### Backend Integration

```python
# core/memory/memory_manager.py
class MemoryManager:
    def get_all_memories(self, type: str = None) -> List[Dict]:
        # Return memories filtered by type
        pass
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        # Semantic + keyword search
        pass
    
    def clear_short_term(self):
        # Clear short-term memory
        pass
```

---

## Tab 6: 📜 Logs

### Purpose
Live Log Viewer - System logs mit Auto-Scroll, Filter, Clear.

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📜 SYSTEM LOGS                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ [🔄 Refresh] [🗑️ Clear] ☑ Auto-scroll                              │
├─────────────────────────────────────────────────────────────────────┤
│ 2025-12-10 20:15:32 [INFO] JARVIS started                          │
│ 2025-12-10 20:15:33 [INFO] Loading model: llama3                   │
│ 2025-12-10 20:15:45 [INFO] Model loaded successfully               │
│ 2025-12-10 20:16:02 [DEBUG] Processing command: "load model"       │
│ 2025-12-10 20:16:02 [WARNING] Model already loaded                 │
│ 2025-12-10 20:17:15 [ERROR] Plugin WikiData failed: Timeout        │
│ ...                                                                 │
│ ...                                                                 │
│ ...                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Features & Functions

#### 1. Action Buttons

**🔄 Refresh Button:**
- **Function:** Reload logs from file
- **Source:** `logs/jarvis.log`
- **Read:** Last 100KB (prevents overflow)
- **Encoding:** UTF-8 with error ignore
- **Update:** Immediate
- **Width:** 140px, **Height:** 40px

**🗑️ Clear Button:**
- **Function:** Clear log display (UI only)
- **Action:** `dpg.set_value("log_viewer", "")`
- **Note:** Does NOT delete log file
- **Width:** 140px, **Height:** 40px

**☑ Auto-scroll Checkbox:**
- **Function:** Enable/disable auto-refresh
- **Tag:** `log_autoscroll`
- **Default:** Checked (True)
- **Behavior:** When checked, logs auto-refresh every 3s

#### 2. Log Display

**Display Element:**
- **Tag:** `log_viewer`
- **Type:** `dpg.add_text` with `wrap=0` (horizontal scroll)
- **Content:** Raw log file content
- **Scrolling:** Vertical + Horizontal
- **Font:** Monospace (if available)

#### 3. Background Worker

**Thread:** `log_loop()`
- **Interval:** 3 seconds
- **Condition:** Only if `log_autoscroll` checked
- **Action:**
  1. Read `logs/jarvis.log`
  2. Take last 100KB
  3. Update `log_viewer`

#### 4. Log Format (Example)

```
2025-12-10 20:15:32,123 [INFO] core.jarvis - JARVIS initialized
2025-12-10 20:15:33,456 [INFO] core.llm_manager - Loading model: llama3
2025-12-10 20:15:45,789 [INFO] core.llm_manager - Model loaded (8.3s)
2025-12-10 20:16:02,012 [DEBUG] core.command_processor - Command: load model
2025-12-10 20:16:02,034 [WARNING] core.llm_manager - Model already loaded
2025-12-10 20:17:15,567 [ERROR] plugins.wikidata - Request timeout (30s)
```

### Backend Integration

```python
# utils/logger.py
import logging

logger = logging.getLogger("jarvis")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("logs/jarvis.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
)
logger.addHandler(file_handler)
```

### Future Enhancements

- **Log Level Filter** (INFO/DEBUG/WARNING/ERROR)
- **Search/Grep** functionality
- **Export** (save filtered logs)
- **Color-Coding** (red for errors, orange for warnings)
- **Tail Mode** (always show last N lines)

---

## Tab 7: ⚙️ Settings

### Purpose
Konfiguration - LLM, TTS, Speech Recognition, System Settings.

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚙️ SETTINGS                                                         │
├─────────────────────────────────────────────────────────────────────┤
│ 🧠 LLM Settings                                                     │
│ ───────────────────────────────────────────────────────────────     │
│ ☑ Enable LLM                                                        │
│ Context Length:  [════════════════░░░] 2048                         │
│ Temperature:     [════════░░░░░░░░░░░] 0.7                          │
│                                                                     │
│ 🔊 TTS Settings                                                     │
│ ───────────────────────────────────────────────────────────────     │
│ ☑ Enable TTS                                                        │
│ Speech Rate:     [════════════════░░░] 150 WPM                      │
│ Volume:          [════════════════════] 100%                        │
│                                                                     │
│ 🎤 Speech Recognition                                               │
│ ───────────────────────────────────────────────────────────────     │
│ ☑ Enable Wake Word                                                  │
│ ☐ Continuous Listening                                              │
│                                                                     │
│ [💾 SAVE SETTINGS]                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Features & Functions

#### 1. LLM Settings

**☑ Enable LLM Checkbox:**
- **Tag:** `setting_llm_enabled`
- **Default:** True
- **Effect:** Disable → No LLM responses (fallback to rules)

**Context Length Slider:**
- **Tag:** `setting_context_length`
- **Type:** `dpg.add_slider_int`
- **Range:** 512 - 8192
- **Default:** 2048
- **Step:** 256
- **Width:** 400px
- **Effect:** Max tokens for context window

**Temperature Slider:**
- **Tag:** `setting_temperature`
- **Type:** `dpg.add_slider_float`
- **Range:** 0.0 - 2.0
- **Default:** 0.7
- **Step:** 0.1
- **Width:** 400px
- **Effect:** LLM creativity (0=deterministic, 2=random)

#### 2. TTS Settings

**☑ Enable TTS Checkbox:**
- **Tag:** `setting_tts_enabled`
- **Default:** True
- **Effect:** Disable → No voice output

**Speech Rate Slider:**
- **Tag:** `setting_speech_rate`
- **Type:** `dpg.add_slider_int`
- **Range:** 50 - 300 WPM
- **Default:** 150
- **Step:** 10
- **Width:** 400px
- **Effect:** Words per minute for TTS

**Volume Slider:**
- **Tag:** `setting_volume`
- **Type:** `dpg.add_slider_int`
- **Range:** 0 - 100%
- **Default:** 100
- **Step:** 5
- **Width:** 400px
- **Effect:** TTS output volume

#### 3. Speech Recognition Settings

**☑ Enable Wake Word Checkbox:**
- **Tag:** `setting_wake_word`
- **Default:** True
- **Effect:** Require "Hey JARVIS" to activate

**☐ Continuous Listening Checkbox:**
- **Tag:** `setting_continuous`
- **Default:** False
- **Effect:** Always listen (no wake word needed)
- **Warning:** High CPU usage!

#### 4. Save Button

**💾 SAVE SETTINGS:**
- **Width:** 250px
- **Height:** 50px
- **Callback:** `_save_settings()`
- **Action:**
  1. Read all values from UI
  2. Update `data/settings.json`
  3. Reload backend config
  4. Show confirmation

### Backend Integration

```python
def _save_settings(self):
    settings = {
        "llm": {
            "enabled": dpg.get_value("setting_llm_enabled"),
            "context_length": dpg.get_value("setting_context_length"),
            "temperature": dpg.get_value("setting_temperature")
        },
        "tts": {
            "enabled": dpg.get_value("setting_tts_enabled"),
            "rate": dpg.get_value("setting_speech_rate"),
            "volume": dpg.get_value("setting_volume")
        },
        "speech": {
            "wake_word_enabled": dpg.get_value("setting_wake_word"),
            "continuous_listening": dpg.get_value("setting_continuous")
        }
    }
    
    # Save to file
    with open("data/settings.json", "r+") as f:
        data = json.load(f)
        data.update(settings)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
    
    # Reload in backend
    if self.jarvis:
        self.jarvis.reload_settings()
    
    print("✅ Settings saved!")
```

### Future Enhancements

- **Advanced Settings Tab:**
  - Security (Safe Mode, Auth)
  - Remote Control (WebSocket)
  - Plugins (Enable/Disable list)
  - Knowledge (Auto-Expand, Crawler)
- **Model Selection Dropdown** (instead of load via chat)
- **TTS Voice Selection** (if multiple voices available)
- **Theme Selector** (Dark/Light/Custom)

---

## 🌐 Global Components

### Header Bar

```
┌────────────────────────────────────────────────────────────────────┐
│ 🎮 J.A.R.V.I.S. Control Center              🟢 ONLINE    FPS: 60  │
└────────────────────────────────────────────────────────────────────┘
```

**Components:**
- **Logo + Title:** "🎮 J.A.R.V.I.S. Control Center"
  - Font: Large (28px)
  - Color: Orange (255, 140, 0)
- **Status Indicator:** "🟢 ONLINE" / "🔴 OFFLINE"
  - Tag: `status_indicator`
  - Color: Green (online) / Red (offline)
  - Font: Medium (22px)
- **FPS Counter:** "FPS: 60"
  - Tag: `fps_display`
  - Update: Every frame
  - Source: `dpg.get_frame_rate()`

### Footer Bar

```
┌────────────────────────────────────────────────────────────────────┐
│ ● System Ready                 FPS: 60         Powered by UE5 Design│
└────────────────────────────────────────────────────────────────────┘
```

**Components:**
- **System Status:** "● System Ready" / "● Processing..."
  - Tag: `footer_status`
  - Color: Green/Orange
- **FPS Display:** Same as header
- **Branding:** "⚡ Powered by Unreal Engine 5 Design"
  - Color: Gray (120, 120, 120)

### Tab Bar

**7 Tabs:**
1. 📊 Dashboard
2. 💬 Chat
3. 🧠 Models
4. 🧩 Plugins
5. 🗄️ Memory
6. 📜 Logs
7. ⚙️ Settings

**Properties:**
- **Font:** Default (18px)
- **Padding:** Extra spacing for readability
- **Active Tab:** Lighter background (60, 60, 65)
- **Inactive Tab:** Dark background (40, 40, 42)

---

## 🔌 Backend Integration

### Core Classes & Methods Used by UI

#### JarvisAssistant (`core/jarvis.py`)

```python
class JarvisAssistant:
    def get_system_metrics(self) -> Dict[str, Any]:
        """Returns CPU/RAM/GPU metrics for Dashboard"""
        return self.system_monitor.get_metrics()
    
    def get_llm_status(self) -> Dict[str, Any]:
        """Returns LLM status for Models tab"""
        return {
            "current": self.llm_manager.current_model,
            "loaded": list(self.llm_manager.loaded_models.keys()),
            "available": self.llm_manager.get_model_overview()
        }
    
    def get_plugin_overview(self) -> List[Dict[str, Any]]:
        """Returns plugin list for Plugins tab"""
        return self.plugin_manager.get_overview()
    
    def reload_settings(self):
        """Reload settings from file (after Settings save)"""
        self.settings = self._load_settings()
        self._apply_settings()
```

#### CommandProcessor (`core/command_processor.py`)

```python
class CommandProcessor:
    def process_command(self, user_input: str) -> str:
        """Process chat command, return response"""
        # Intent recognition → Plugin routing → LLM fallback
        return response
```

#### LLMManager (`core/llm_manager.py`)

```python
class LLMManager:
    def get_model_overview(self) -> Dict[str, Dict]:
        """Model metadata for Models tab"""
    
    def load_model(self, model_key: str):
        """Load model into memory"""
    
    def unload_model(self, model_key: str = None):
        """Unload specific or all models"""
    
    def download_model(self, model_key: str):
        """Download model from remote (future)"""
```

#### SystemMonitor (`core/system_monitor.py`)

```python
class SystemMonitor:
    def get_metrics(self) -> Dict[str, Any]:
        """Real-time system metrics"""
        return {
            "summary": {
                "cpu_percent": float,
                "memory_percent": float,
                "gpu_utilization": float,
                # ...
            }
        }
```

#### PluginManager (`core/plugin_manager.py`)

```python
class PluginManager:
    def get_overview(self) -> List[Dict]:
        """Plugin status for Plugins tab"""
    
    def enable_plugin(self, name: str):
        """Enable plugin"""
    
    def disable_plugin(self, name: str):
        """Disable plugin"""
```

---

## 🚀 Future Enhancements

### High Priority

1. **Memory Tab Implementation**
   - Short/Long/Timeline/Vector views
   - Search functionality
   - Memory editing

2. **Enhanced Model Manager**
   - Card-based layout (see `docs/ENHANCED_MODEL_MANAGER.md`)
   - Download progress tracking
   - Benchmarking (tokens/sec)
   - Model comparison

3. **Plugin Configuration**
   - Enable/Disable buttons per plugin
   - Configuration dialogs
   - Priority adjustment

4. **Settings Extensions**
   - Security settings (Safe Mode, Auth)
   - Remote Control config
   - Theme selector
   - Advanced LLM options (GPU layers, etc.)

### Medium Priority

5. **Log Viewer Enhancements**
   - Log level filter
   - Search/Grep
   - Color-coding
   - Export

6. **Dashboard Extensions**
   - Disk I/O graph
   - Network traffic
   - Model inference time history
   - Plugin usage stats

7. **Chat Improvements**
   - Command autocomplete
   - Command history (up/down arrows)
   - Multi-line input
   - Markdown rendering in responses

### Low Priority

8. **Custom Themes**
   - Light mode
   - Custom color palettes
   - User-defined fonts

9. **Keyboard Shortcuts**
   - Ctrl+Tab: Switch tabs
   - Ctrl+R: Refresh current tab
   - Ctrl+Enter: Send chat message
   - Ctrl+L: Focus log viewer

10. **Notifications**
    - Toast notifications for events
    - Sound alerts
    - System tray integration

---

## 📝 Summary

### Tabs & Main Functions

| Tab | Icon | Main Functions |
|-----|------|----------------|
| **Dashboard** | 📊 | Live CPU/RAM/GPU graphs, Detailed stats, Auto-refresh |
| **Chat** | 💬 | Send commands, View history, LLM interaction |
| **Models** | 🧠 | Load/Unload LLMs, Download models, View status |
| **Plugins** | 🧩 | View enabled plugins, Refresh status |
| **Memory** | 🗄️ | (Planned) View/Search memories, Timeline |
| **Logs** | 📜 | View system logs, Auto-scroll, Clear |
| **Settings** | ⚙️ | Configure LLM/TTS/Speech, Save changes |

### Total Buttons & Controls

- **15 Action Buttons** (Refresh, Download, Send, etc.)
- **11 Sliders** (Context Length, Temperature, Speech Rate, Volume)
- **6 Checkboxes** (Enable LLM/TTS, Wake Word, Continuous, Auto-scroll)
- **7 Tabs** (Main navigation)
- **3 Live Graphs** (CPU, RAM, GPU)
- **2 Background Threads** (Metrics, Logs)

### Lines of Code (Estimated)

- **UI Code:** ~800 lines (`jarvis_imgui_app_full.py`)
- **Backend Integration:** ~2000 lines (Command Processor, Managers)
- **Total:** ~2800 lines for full UI + Backend

---

**Version:** 1.0.0  
**Status:** ✅ Production (mit geplanten Enhancements)  
**Last Updated:** December 10, 2025
