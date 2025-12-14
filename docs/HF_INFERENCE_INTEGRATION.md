# HuggingFace Inference Integration - Implementierungsanleitung

## ✅ Was bereits implementiert ist

### 1. Neue Datei: `backend/core/hf_inference.py`
- **HFInferenceRuntime Klasse** für Modell-Loading und Inferenz
- Automatische Device-Erkennung (CUDA/MPS/CPU)
- Optimierte Konfiguration für GPU/CPU
- Chat-Funktion mit Kontext-Historie
- Memory-Management mit automatischem Unload

### 2. Dependencies: `backend/requirements.txt`
- `transformers>=4.36.0` - HuggingFace Transformers
- `torch>=2.1.0` - PyTorch für Inferenz
- `accelerate>=0.25.0` - Multi-GPU Support
- `safetensors>=0.4.0` - Sicheres Model-Loading
- `sentencepiece>=0.1.99` - Tokenizer Support
- `protobuf>=4.25.0` - Protocol Buffers

---

## 🛠️ Nächste Schritte: Integration in bestehenden Code

### Schritt 1: `llm_manager.py` anpassen

**Datei:** `backend/core/llm_manager.py`

#### Änderung 1: Import hinzufügen
```python
# Am Anfang der Datei nach bestehenden Imports
from core.hf_inference import hf_runtime
```

#### Änderung 2: `load_model()` Methode erweitern

Suchen Sie diese Zeilen (ca. Zeile 200-220):
```python
# Load new model
model['isActive'] = True
self.config['active_model'] = model_id
self.save_config()

log_info(f"Loaded model: {model['name']}", category='model')
log_info(f"Model path: {model_path}", category='model')

return True
```

**ERSETZEN durch:**
```python
# Load new model
model['isActive'] = True
self.config['active_model'] = model_id
self.save_config()

log_info(f"Loaded model: {model['name']}", category='model')
log_info(f"Model path: {model_path}", category='model')

# NEU: HF Runtime laden
log_info("Loading model into inference runtime...", category='model')
success = hf_runtime.load_model(model_path, model_id)

if not success:
    log_error("Failed to load model into runtime", category='model')
    model['isActive'] = False
    self.config['active_model'] = None
    self.save_config()
    return False

log_info(f"✓ Model {model['name']} ready for inference", category='model')
return True
```

#### Änderung 3: `unload_model()` Methode erweitern

Suchen Sie die `unload_model()` Methode (ca. Zeile 240-250):
```python
def unload_model(self) -> bool:
    """Unload current model"""
    from core.logger import log_info
    
    for model in self.config['available_models']:
        model['isActive'] = False
    self.config['active_model'] = None
    self.save_config()
    
    log_info("Model unloaded", category='model')
    return True
```

**ERSETZEN durch:**
```python
def unload_model(self) -> bool:
    """Unload current model"""
    from core.logger import log_info
    
    # NEU: Runtime unload
    hf_runtime.unload_model()
    
    for model in self.config['available_models']:
        model['isActive'] = False
    self.config['active_model'] = None
    self.save_config()
    
    log_info("Model unloaded", category='model')
    return True
```

---

### Schritt 2: `main.py` anpassen - Chat mit echter AI

**Datei:** `backend/main.py`

#### Änderung 1: Import hinzufügen
```python
# Nach den anderen imports
from core.hf_inference import hf_runtime
```

#### Änderung 2: Neue Chat-Funktion erstellen

**HINZUFÜGEN** nach der bestehenden `generate_jarvis_response()` Funktion:
```python
async def generate_ai_response(message: str, session_id: str) -> str:
    """
    Generiert AI-Response mit geladenem HuggingFace Model
    Falls kein Model geladen ist, wird Fallback-Response zurückgegeben
    """
    from core.logger import log_info, log_warning, log_error
    
    # Check if model loaded
    if not hf_runtime.is_loaded():
        log_warning("No model loaded, using fallback response", category='chat')
        return "Bitte laden Sie zuerst ein Model unter 'Modelle'."
    
    try:
        # Get chat history for context
        history = []
        if session_id in messages_db:
            for msg in messages_db[session_id][-5:]:  # Last 5 messages
                history.append({
                    'role': 'user' if msg['isUser'] else 'assistant',
                    'content': msg['text']
                })
        
        # Generate response
        result = hf_runtime.chat(
            message=message,
            history=history,
            system_prompt="Du bist JARVIS, ein hilfreicher deutscher KI-Assistent. Antworte präzise und freundlich."
        )
        
        log_info(
            f"Generated {result['tokens_generated']} tokens with {result['model']} on {result['device']}",
            category='chat'
        )
        
        return result['text']
        
    except Exception as e:
        log_error(f"AI generation failed: {e}", category='chat', exc_info=True)
        return f"Fehler bei der Antwort-Generierung: {str(e)}"
```

#### Änderung 3: WebSocket Handler anpassen

Suchen Sie im WebSocket Handler diese Zeile (ca. Zeile 150-170):
```python
response_text = generate_jarvis_response(user_message)
```

**ERSETZEN durch:**
```python
response_text = await generate_ai_response(user_message, session_id)
```

#### Änderung 4: Startup Auto-Load hinzufügen

Suchen Sie die `startup()` Funktion:
```python
@app.on_event("startup")
async def startup():
    log_info("JARVIS Core API starting...", category='startup')
```

**ERWEITERN um:**
```python
@app.on_event("startup")
async def startup():
    log_info("JARVIS Core API starting...", category='startup')
    
    # NEU: Auto-load letztes aktives Model
    active_model = llm_manager.get_active_model()
    if active_model and active_model['isDownloaded']:
        log_info(f"Auto-loading last active model: {active_model['name']}", category='startup')
        success = llm_manager.load_model(active_model['id'])
        if success:
            log_info(f"✓ {active_model['name']} loaded and ready", category='startup')
        else:
            log_warning(f"Failed to auto-load {active_model['name']}", category='startup')
```

---

## 📦 Installation der Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Hinweis für PyTorch:** Falls CUDA/GPU Support benötigt wird:
```bash
# Für NVIDIA GPU (CUDA 12.1)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Für CPU only
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

---

## ✅ Testing

### 1. Backend starten
```bash
cd backend
python main.py
```

### 2. Model Download (Web-UI)
1. Öffne [http://localhost:5050](http://localhost:5050)
2. Gehe zu **"Modelle"** Tab
3. Klick **"Download"** bei TinyLlama 1.1B (~2.2 GB)
4. Warte bis Download complete (Progress-Bar)

### 3. Model Load
1. Klick **"Load"** bei TinyLlama
2. Check Console Logs:
   - `Loading model into inference runtime...`
   - `Using device: cuda/cpu/mps`
   - `✓ Model tinyllama-1.1b loaded successfully`

### 4. Chat Test
1. Gehe zu **"Chat"** Tab
2. Schreib: `"Hallo, wer bist du?"`
3. Erwarte: **Echte AI-Antwort** von TinyLlama (nicht Mock)

---

## 🔧 Troubleshooting

### Problem: "No model loaded"
- **Lösung:** Model zuerst downloaden und dann "Load" klicken

### Problem: "CUDA out of memory"
- **Lösung:** Kleineres Model wählen oder CPU verwenden
- CPU-Modus in `hf_inference.py` erzwingen:
  ```python
  def _get_device(self) -> str:
      return "cpu"  # Force CPU
  ```

### Problem: Sehr langsame Inferenz
- **Ursache:** CPU-Modus aktiv
- **Lösung:** GPU installieren oder quantisierte Modelle verwenden

### Problem: Import Error "No module named 'transformers'"
- **Lösung:** `pip install -r requirements.txt` ausführen

---

## 📄 API Übersicht

### HFInferenceRuntime Methoden

```python
from core.hf_inference import hf_runtime

# Model laden
hf_runtime.load_model(Path('./models/tinyllama-1.1b'), 'tinyllama-1.1b')

# Text generieren
result = hf_runtime.generate(
    prompt="Was ist Python?",
    max_new_tokens=256,
    temperature=0.7
)
print(result['text'])

# Chat mit Historie
result = hf_runtime.chat(
    message="Erkläre Machine Learning",
    history=[
        {'role': 'user', 'content': 'Hallo'},
        {'role': 'assistant', 'content': 'Hallo! Wie kann ich helfen?'}
    ]
)

# Model Info
info = hf_runtime.get_info()
print(info['device'])  # cuda/mps/cpu

# Model entladen
hf_runtime.unload_model()
```

---

## 🚀 Nächste Erweiterungen

### Phase 2: Voice Integration
- Whisper für Speech-to-Text
- XTTS/Piper für Text-to-Speech
- WebSocket Audio Streaming

### Phase 3: Knowledge Base / RAG
- FAISS Vector Store
- Embedding-Models (sentence-transformers)
- Document Ingestion Pipeline

### Phase 4: Advanced Features
- Multi-Model Support (parallel loading)
- Quantisierte Modelle (GGUF/GGML)
- Streaming Response (Server-Sent Events)
- GPU Memory Optimization

---

## 📝 Zusammenfassung

**Implementiert:**
- ✅ `hf_inference.py` - Inference Runtime
- ✅ `requirements.txt` - Dependencies

**TODO (manuelle Änderungen):**
- ☐ `llm_manager.py` - Runtime-Integration (3 Änderungen)
- ☐ `main.py` - Chat-Integration (4 Änderungen)
- ☐ Dependencies installieren
- ☐ Testing durchführen

**Geschätzter Zeitaufwand:** 30-45 Minuten
