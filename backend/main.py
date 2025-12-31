from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import json
import uuid
import asyncio
import sys
import os
import subprocess
import threading
import psutil
import platform
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import llama.cpp inference
from core.llama_inference import llama_runtime
# Import model downloader
from backend.model_downloader import model_downloader, MODEL_URLS

# Plugin manager wird beim Startup initialisiert
plugin_manager = None

# Import settings router and current settings
try:
    from backend.api.settings import router as settings_router, current_settings
    print("[BACKEND] Settings API loaded")
except Exception as e:
    print(f"[ERROR] Failed to load settings API: {e}")
    settings_router = None
    current_settings = None

# Import TTS router and initialize service
try:
    from backend.api.tts_endpoints import router as tts_router
    from backend.core.tts_service import init_tts_service
    
    print("[BACKEND] Initializing TTS service...")
    tts_service = init_tts_service()
    if tts_service and tts_service.is_available():
        status = tts_service.get_status()
        print(f"[BACKEND] ✅ TTS service ready: {status['engine']} on {status['device']}")
    else:
        print("[BACKEND] ⚠️  TTS service initialized with fallback or unavailable")
except Exception as e:
    print(f"[WARNING] TTS service unavailable: {e}")
    tts_router = None
    tts_service = None

# Load JARVIS System Prompts
def load_system_prompt_file(filename: str) -> str:
    """Load a system prompt from config file"""
    prompt_path = project_root / "config" / filename
    try:
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
                print(f"[INFO] Loaded {filename} ({len(prompt)} characters)")
                return prompt
        else:
            print(f"[WARNING] System prompt file not found: {prompt_path}")
    except Exception as e:
        print(f"[ERROR] Failed to load {filename}: {e}")
    
    return ""

# Load both prompts at startup
JARVIS_PROMPT_FULL = load_system_prompt_file("system_prompt_full.txt")
JARVIS_PROMPT_COMPACT = load_system_prompt_file("system_prompt_compact.txt")

# Fallback prompt if both fail to load
JARVIS_PROMPT_FALLBACK = "You are JARVIS, a sophisticated AI assistant. Be helpful, witty, and professional."

def get_system_prompt(model_name: str) -> str:
    """
    Select appropriate system prompt based on model size.
    
    Small models (≤3B): Use compact prompt for better performance
    Large models (7B+): Use full detailed prompt for richer personality
    """
    # Define small models that need compact prompt
    small_models = [
        "llama32-3b",
        "phi3-mini",
        "tinyllama",
    ]
    
    # Check if current model is small
    is_small_model = any(small in model_name.lower() for small in small_models)
    
    if is_small_model:
        print(f"[INFO] Using COMPACT prompt for {model_name} (small model)")
        return JARVIS_PROMPT_COMPACT if JARVIS_PROMPT_COMPACT else JARVIS_PROMPT_FALLBACK
    else:
        print(f"[INFO] Using FULL prompt for {model_name} (large model)")
        return JARVIS_PROMPT_FULL if JARVIS_PROMPT_FULL else JARVIS_PROMPT_FALLBACK

app = FastAPI(title="JARVIS Core API", version="1.2.0")

# CORS Configuration - Pinokio Port 5050
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5050", "http://127.0.0.1:5050"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
if settings_router:
    app.include_router(settings_router)
    print("[BACKEND] Settings router mounted")

if tts_router:
    app.include_router(tts_router)
    print("[BACKEND] TTS router mounted")


@app.on_event("startup")
async def startup_event():
    global plugin_manager
    print("[BACKEND] Initializing plugin manager on startup...")
    try:
        from backend.plugin_manager import PluginManager
        plugin_manager = PluginManager()
        print(f"[BACKEND] Plugin manager ready: {len(plugin_manager.plugins)} plugins")
    except Exception as e:
        print(f"[ERROR] Failed to init plugin manager: {e}")
        plugin_manager = None

# In-memory storage
sessions_db = {}
messages_db = {}
memories_db: List[Dict] = []  # For memory tab
logs_db: List[Dict] = []  # For logs tab

# HuggingFace token storage (in-memory, can be persisted to file later)
hf_token_storage: Optional[str] = None

print("[INFO] JARVIS Core API initializing...")

# Add initial log entry
logs_db.append({
    "id": str(uuid.uuid4()),
    "timestamp": datetime.now().isoformat(),
    "level": "info",
    "message": "JARVIS Core API initialized",
    "source": "backend"
})

# Try to load token from environment on startup
if os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"):
    hf_token_storage = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    print("[INFO] HuggingFace token loaded from environment")

# AI Response Generator mit Plugin-Integration und llama.cpp
async def generate_ai_response(message: str, session_id: str) -> Tuple[str, bool, Optional[int], Optional[float]]:
    """
    Generate AI response with plugin processing:
    1. Check if plugins can handle the message
    2. If not, use llama.cpp for general response
    
    Returns: (response_text, is_plugin_response, tokens, tokens_per_second)
    """
    
    print(f"\n[DEBUG] === generate_ai_response called ===")
    print(f"[DEBUG] Message: {message[:100]}")
    print(f"[DEBUG] Session: {session_id}")
    
    # STEP 1: Try plugin processing first
    if plugin_manager:
        plugin_response = plugin_manager.process_message(message, {"session_id": session_id})
        if plugin_response:
            print(f"[DEBUG] ✅ Plugin handled message")
            print(f"[DEBUG] Plugin response: {plugin_response[:100]}...")
            logs_db.append({
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": f"Plugin processed command: {message[:50]}",
                "source": "plugins"
            })
            return plugin_response, True, None, None  # Plugins don't have token stats
    
    print(f"[DEBUG] ⚠️ No plugin handled message, using LLM")
    
    # STEP 2: No plugin handled it -> use LLM
    if not llama_runtime.is_loaded:
        return "Bitte laden Sie zuerst ein Modell unter 'Modelle'.", False, None, None
    
    try:
        # Build history - ONLY include non-plugin messages
        history = []
        if session_id in messages_db:
            print(f"[DEBUG] Session has {len(messages_db[session_id])} total messages")
            
            # Filter: nur messages die NICHT von Plugins sind
            for i, msg in enumerate(messages_db[session_id][-10:]):
                is_plugin = msg.get('isPlugin', False)
                is_user = msg.get('isUser', False)
                text_preview = msg.get('text', '')[:50]
                
                print(f"[DEBUG] Msg {i}: isUser={is_user}, isPlugin={is_plugin}, text={text_preview}")
                
                # Skip plugin responses
                if is_plugin:
                    print(f"[DEBUG]   → SKIPPED (plugin response)")
                    continue
                    
                history.append({
                    'role': 'user' if is_user else 'assistant',
                    'content': msg['text']
                })
                print(f"[DEBUG]   → ADDED to history")
        
        print(f"[DEBUG] Final history length: {len(history)} messages")
        
        # Limit to last 10 messages
        history = history[-10:]
        
        # Get appropriate system prompt for current model
        model_name = llama_runtime.model_name if llama_runtime.model_name else "unknown"
        system_prompt = get_system_prompt(model_name)
        
        # Get generation parameters from settings
        max_tokens = 512  # Default fallback
        temperature = 0.7  # Default fallback
        
        if current_settings:
            max_tokens = current_settings.llama.max_tokens
            temperature = current_settings.llama.temperature
            print(f"[INFO] Using settings: max_tokens={max_tokens}, temperature={temperature}")
        
        result = llama_runtime.chat(
            message=message,
            history=history,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if result['success']:
            tokens_generated = result.get('tokens_generated', 0)
            tokens_per_sec = result.get('tokens_per_second', 0.0)
            
            print(
                f"[INFO] Generated {tokens_generated} tokens "
                f"with {result['model']} on {result['device']} "
                f"({tokens_per_sec:.1f} tok/s)"
            )
            print(f"[DEBUG] LLM response: {result['text'][:100]}...")
            return result['text'], False, tokens_generated, tokens_per_sec
        else:
            print(f"[ERROR] Generation failed: {result.get('error', 'Unknown error')}")
            return f"Fehler bei der Antwort-Generierung: {result.get('error', 'Unbekannter Fehler')}", False, None, None
        
    except Exception as e:
        print(f"[ERROR] AI generation exception: {e}")
        import traceback
        traceback.print_exc()
        return f"Fehler bei der Antwort-Generierung: {str(e)}", False, None, None

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'chat_message':
                user_message = message.get('message', '')
                session_id = message.get('sessionId', 'default')
                
                print(f"\n[INFO] ═════════════════════════════════════════════════════")
                print(f"[INFO] Chat message received: {user_message[:50]}...")
                print(f"[INFO] ═════════════════════════════════════════════════════")
                
                if session_id not in messages_db:
                    messages_db[session_id] = []
                
                message_id = str(uuid.uuid4())
                messages_db[session_id].append({
                    'id': message_id,
                    'text': user_message,
                    'isUser': True,
                    'isPlugin': False,  # User messages are never plugin responses
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"[DEBUG] Stored user message with isPlugin=False")
                
                await websocket.send_text(json.dumps({
                    'type': 'typing_start',
                    'sessionId': session_id
                }))
                
                # Get response with token statistics
                response_text, is_plugin, tokens, tokens_per_sec = await generate_ai_response(user_message, session_id)
                response_id = str(uuid.uuid4())
                
                print(f"[DEBUG] Response generated: is_plugin={is_plugin}, tokens={tokens}, tok/s={tokens_per_sec}")
                print(f"[DEBUG] Response preview: {response_text[:100]}...")
                
                # Store response with plugin flag and token stats
                stored_message = {
                    'id': response_id,
                    'text': response_text,
                    'isUser': False,
                    'isPlugin': is_plugin,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add token stats if available (only for LLM responses)
                if tokens is not None:
                    stored_message['tokens'] = tokens
                if tokens_per_sec is not None:
                    stored_message['tokensPerSecond'] = tokens_per_sec
                
                messages_db[session_id].append(stored_message)
                
                print(f"[DEBUG] Stored response with isPlugin={is_plugin}, tokens={tokens}")
                print(f"[INFO] ═════════════════════════════════════════════════════\n")
                
                # Build WebSocket response with token stats
                ws_response = {
                    'type': 'chat_response',
                    'messageId': response_id,
                    'response': response_text,
                    'sessionId': session_id
                }
                
                # Include token stats if available
                if tokens is not None:
                    ws_response['tokens'] = tokens
                if tokens_per_sec is not None:
                    ws_response['tokensPerSecond'] = tokens_per_sec
                
                await websocket.send_text(json.dumps(ws_response))
                
                await websocket.send_text(json.dumps({
                    'type': 'typing_stop',
                    'sessionId': session_id
                }))
            
            elif message.get('type') == 'ping':
                await websocket.send_text(json.dumps({
                    'type': 'pong'
                }))
                
    except WebSocketDisconnect:
        print("[INFO] WebSocket disconnected")
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e}")
        import traceback
        traceback.print_exc()

# Logs API
@app.get("/api/logs")
async def get_logs():
    return logs_db[-100:]

@app.get("/api/logs/stats")
async def get_logs_stats():
    return {
        "total": len(logs_db),
        "errors": len([log for log in logs_db if log.get('level') == 'error']),
        "warnings": len([log for log in logs_db if log.get('level') == 'warning']),
        "info": len([log for log in logs_db if log.get('level') == 'info'])
    }

@app.post("/api/logs/clear")
async def clear_logs():
    global logs_db
    logs_db = []
    return {"success": True, "message": "Logs cleared"}

# Plugins API
@app.get("/api/plugins")
async def get_plugins():
    if plugin_manager is None:
        return []
    return plugin_manager.get_all_plugins()


@app.get("/api/plugins/status")
async def get_plugins_status():
    if plugin_manager is None:
        return []
    return plugin_manager.get_plugin_statuses()

@app.post("/api/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    if plugin_manager is None:
        return {"success": False, "message": "Plugin Manager not ready"}
    
    result = plugin_manager.enable_plugin(plugin_id)
    
    if result.get('success'):
        logs_db.append({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": f"Plugin enabled: {plugin_id}",
            "source": "plugins"
        })
    else:
        logs_db.append({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "level": "warning",
            "message": f"Plugin {plugin_id} requires API key",
            "source": "plugins"
        })
    
    return result

@app.post("/api/plugins/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    if plugin_manager is None:
        return {"success": False, "message": "Plugin Manager not ready"}
    
    success = plugin_manager.disable_plugin(plugin_id)
    
    if success:
        logs_db.append({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": f"Plugin disabled: {plugin_id}",
            "source": "plugins"
        })
        return {"success": True, "message": f"Plugin {plugin_id} deaktiviert"}
    else:
        return {"success": False, "message": f"Plugin {plugin_id} konnte nicht deaktiviert werden"}

@app.post("/api/plugins/reload")
async def reload_plugins():
    if plugin_manager is None:
        return {"success": False, "message": "Plugin Manager not ready"}
    
    plugin_manager.reload_plugins()
    return {
        "success": True,
        "message": "Plugins neu geladen",
        "count": len(plugin_manager.plugins)
    }

# Memory API
@app.get("/api/memory")
async def get_memories():
    return memories_db

@app.get("/api/memory/stats")
async def get_memory_stats():
    return {
        "total": len(memories_db),
        "categories": {},
        "recent": memories_db[-5:] if memories_db else []
    }

@app.post("/api/memory")
async def add_memory(memory: dict):
    memory['id'] = str(uuid.uuid4())
    memory['timestamp'] = datetime.now().isoformat()
    memories_db.append(memory)
    return {"success": True, "memory": memory}

@app.delete("/api/memory/{memory_id}")
async def delete_memory(memory_id: str):
    global memories_db
    memories_db = [m for m in memories_db if m.get('id') != memory_id]
    return {"success": True}

# System Info API
@app.get("/api/system/info")
async def get_system_info():
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        
        mem = psutil.virtual_memory()
        mem_total = mem.total / (1024**3)
        mem_used = mem.used / (1024**3)
        mem_percent = mem.percent
        
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024**3)
        disk_used = disk.used / (1024**3)
        disk_percent = disk.percent
        
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
        }
        
        llama_status = llama_runtime.get_status()
        
        plugins = plugin_manager.get_all_plugins() if plugin_manager else []
        plugin_stats = {
            "total": len(plugins),
            "enabled": len([p for p in plugins if p['enabled']])
        }
        
        # Add TTS status
        tts_status = None
        if tts_service:
            tts_status = tts_service.get_status()
        
        return {
            "cpu": {"usage": cpu_percent, "count": cpu_count},
            "memory": {"total": round(mem_total, 2), "used": round(mem_used, 2), "percent": mem_percent},
            "disk": {"total": round(disk_total, 2), "used": round(disk_used, 2), "percent": disk_percent},
            "system": system_info,
            "llama": llama_status,
            "plugins": plugin_stats,
            "tts": tts_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"[ERROR] System info error: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

# Health API  
@app.get("/api/health")
async def health_check():
    enabled_plugins = plugin_manager.get_enabled_plugins() if plugin_manager else []
    tts_available = tts_service.is_available() if tts_service else False
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.2.0",
        "llama_cpp": llama_runtime.get_status(),
        "plugins": len(enabled_plugins),
        "tts": tts_available
    }

# HuggingFace Token API
@app.get("/api/hf-token/status")
async def get_hf_token_status():
    """Check if HF token is configured"""
    return {
        "has_token": hf_token_storage is not None,
        "source": "environment" if (os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")) else "stored"
    }

@app.post("/api/hf-token")
async def set_hf_token(data: dict = Body(...)):
    """Store HuggingFace token"""
    global hf_token_storage
    token = data.get("token", "").strip()
    
    if not token:
        return {"success": False, "message": "Token cannot be empty"}
    
    # Basic validation (HF tokens start with 'hf_')
    if not token.startswith("hf_"):
        return {"success": False, "message": "Invalid token format. HuggingFace tokens start with 'hf_'"}
    
    hf_token_storage = token
    print("[INFO] HuggingFace token stored")
    
    logs_db.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "level": "info",
        "message": "HuggingFace token configured",
        "source": "models"
    })
    
    return {"success": True, "message": "Token saved successfully"}

@app.delete("/api/hf-token")
async def delete_hf_token():
    """Remove stored HuggingFace token"""
    global hf_token_storage
    hf_token_storage = None
    print("[INFO] HuggingFace token removed")
    return {"success": True, "message": "Token removed"}

# Models API
@app.get("/api/models")
async def get_models():
    models = []
    for model_id, model_info in MODEL_URLS.items():
        model_data = {
            "id": model_id,
            "name": model_id.replace("-", " ").title(),
            "size": f"{model_info['size_gb']} GB",
            "requires_token": model_info.get("requires_token", False),
            "isDownloaded": model_downloader.is_model_downloaded(model_id),
            "isActive": llama_runtime.is_loaded and llama_runtime.model_name == model_id
        }
        
        # Add metadata based on model
        if model_id == "mistral":
            model_data.update({"name": "Mistral 7B Nemo", "provider": "Mistral AI", "description": "Code, technische Details, Systembefehle", "hf_model": "second-state/Mistral-Nemo-Instruct-2407-GGUF", "capabilities": ["code", "technical", "german"]})
        elif model_id == "qwen":
            model_data.update({"name": "Qwen 2.5 7B", "provider": "Alibaba", "description": "Vielseitig, mehrsprachig, balanciert", "hf_model": "bartowski/Qwen2.5-7B-Instruct-GGUF", "capabilities": ["multilingual", "balanced", "fast"]})
        elif model_id == "deepseek":
            model_data.update({"name": "DeepSeek R1 8B", "provider": "DeepSeek", "description": "Analysen, Reasoning, komplexe Daten", "hf_model": "Triangle104/DeepSeek-R1-Distill-Llama-8B-Q4_K_M-GGUF", "capabilities": ["analysis", "reasoning", "data"]})
        elif model_id == "llama32-3b":
            model_data.update({"name": "Llama 3.2 3B", "provider": "Meta", "description": "Klein, schnell, effizient fuer einfache Aufgaben", "hf_model": "bartowski/Llama-3.2-3B-Instruct-GGUF", "capabilities": ["fast", "lightweight", "efficient"]})
        elif model_id == "phi3-mini":
            model_data.update({"name": "Phi-3 Mini", "provider": "Microsoft", "description": "Kompakt, schnell, optimiert fuer Konversation", "hf_model": "bartowski/Phi-3-mini-128k-instruct-GGUF", "capabilities": ["compact", "chat", "quick"]})
        elif model_id == "gemma2-9b":
            model_data.update({"name": "Gemma 2 9B", "provider": "Google", "description": "Stark, vielseitig, ausgewogen", "hf_model": "bartowski/gemma-2-9b-it-GGUF", "capabilities": ["powerful", "versatile", "balanced"]})
        elif model_id == "llama33-70b":
            model_data.update({"name": "Llama 3.3 70B", "provider": "Meta", "description": "Sehr gross, sehr stark, hoechste Qualitaet", "hf_model": "bartowski/Llama-3.3-70B-Instruct-GGUF", "capabilities": ["flagship", "high-quality", "advanced"]})
        
        models.append(model_data)
    
    return models

@app.get("/api/models/active")
async def get_active_model():
    status = llama_runtime.get_status()
    if status['loaded']:
        return {"id": status['model_name'], "name": status['model_name'], "loaded": True, "device": status['device'], "context_window": status['context_window']}
    return {"message": "Kein Modell aktiv", "loaded": False}

@app.get("/api/models/download/status")
async def get_download_status():
    return model_downloader.get_download_status()

@app.post("/api/models/{model_id}/download")
async def download_model(model_id: str, data: dict = Body(default={})):
    print(f"[INFO] Download request for model: {model_id}")
    status = model_downloader.get_download_status()
    if status["is_downloading"]:
        return {"success": False, "message": f"Bereits am Herunterladen von {status['current_model']}", "status": status}
    
    # Get token from request or stored token
    hf_token = data.get("token") or hf_token_storage
    
    # Check if model requires token
    if model_downloader.requires_token(model_id) and not hf_token:
        return {
            "success": False,
            "message": "This model requires a HuggingFace token",
            "requires_token": True
        }
    
    logs_db.append({"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "level": "info", "message": f"Starting model download: {model_id}", "source": "models"})
    loop = asyncio.get_event_loop()
    
    def progress_callback(progress: float, status_text: str):
        print(f"[DOWNLOAD] {model_id}: {progress:.1f}% - {status_text}")
    
    result = await loop.run_in_executor(None, lambda: model_downloader.download_model(model_id, hf_token, progress_callback))
    
    if result["success"]:
        logs_db.append({"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "level": "info", "message": f"Model {model_id} downloaded successfully", "source": "models"})
    else:
        logs_db.append({"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "level": "error", "message": f"Model {model_id} download failed: {result['message']}", "source": "models"})
    
    return result

@app.post("/api/models/{model_id}/load")
async def load_model(model_id: str):
    print(f"[INFO] Load request for model: {model_id}")
    logs_db.append({"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "level": "info", "message": f"Loading model: {model_id}", "source": "models"})
    
    model_path = model_downloader.get_model_path(model_id)
    if not model_path:
        return {"success": False, "message": "Modell nicht gefunden"}
    
    if not model_path.exists():
        return {"success": False, "message": f"Modell-Datei nicht gefunden: {model_path}"}
    
    try:
        success = llama_runtime.load_model(model_path=model_path, model_name=model_id, n_ctx=8192, verbose=False)
        if success:
            logs_db.append({"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "level": "info", "message": f"Model {model_id} loaded successfully", "source": "models"})
            return {"success": True, "message": f"Modell {model_id} geladen", "model": llama_runtime.get_status()}
        else:
            logs_db.append({"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "level": "error", "message": f"Failed to load model {model_id}", "source": "models"})
            return {"success": False, "message": "Fehler beim Laden des Modells"}
    except Exception as e:
        print(f"[ERROR] Model load failed: {e}")
        logs_db.append({"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "level": "error", "message": f"Model load exception: {str(e)}", "source": "models"})
        return {"success": False, "message": str(e)}

@app.post("/api/models/unload")
async def unload_model():
    print("[INFO] Unload model request")
    try:
        success = llama_runtime.unload_model()
        logs_db.append({"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "level": "info", "message": "Model unloaded", "source": "models"})
        return {"success": success, "message": "Modell entladen"}
    except Exception as e:
        print(f"[ERROR] Model unload failed: {e}")
        return {"success": False, "message": str(e)}

# Chat API
@app.get("/api/chat/sessions")
async def get_chat_sessions():
    return [{
        "id": session_id,
        "title": f"Session {session_id[:8]}",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "messages": messages_db.get(session_id, [])
    } for session_id in messages_db.keys()]

@app.get("/")
async def root():
    plugins_count = len(plugin_manager.get_all_plugins()) if plugin_manager else 0
    tts_available = tts_service.is_available() if tts_service else False
    
    return {
        "message": "JARVIS Core API v1.2.0",
        "status": "online",
        "llama_cpp": llama_runtime.get_status(),
        "plugins": plugins_count,
        "tts": tts_available,
        "endpoints": {
            "websocket": "/ws",
            "docs": "/docs",
            "health": "/api/health",
            "models": "/api/models",
            "system": "/api/system/info",
            "memory": "/api/memory",
            "logs": "/api/logs",
            "plugins": "/api/plugins",
            "settings": "/api/settings",
            "hf_token": "/api/hf-token",
            "tts": "/api/tts"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║          JARVIS Core Backend v1.2.0                  ║
    ║         Just A Rather Very Intelligent System        ║
    ║         with llama.cpp + TTS voice synthesis         ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    print("[INFO] Starting JARVIS Core API...")
    print(f"[INFO] llama.cpp available: {llama_runtime.get_status()['available']}")
    print(f"[INFO] Device: {llama_runtime.device}")
    if tts_service:
        print(f"[INFO] TTS available: {tts_service.is_available()}")
    
    uvicorn.run(app, host="127.0.0.1", port=5050)
