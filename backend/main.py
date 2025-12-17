from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
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
from backend.model_downloader import model_downloader

# Initialize plugin manager IMMEDIATELY at import time
print("[BACKEND] Initializing plugin manager...")
try:
    from backend.plugin_manager import PluginManager
    plugin_manager = PluginManager()
    print(f"[BACKEND] Plugin manager ready: {len(plugin_manager.plugins)} plugins")
except Exception as e:
    print(f"[ERROR] Failed to init plugin manager: {e}")
    plugin_manager = None

# Import settings router
try:
    from backend.api.settings import router as settings_router
    print("[BACKEND] Settings API loaded")
except Exception as e:
    print(f"[ERROR] Failed to load settings API: {e}")
    settings_router = None

app = FastAPI(title="JARVIS Core API", version="1.1.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
if settings_router:
    app.include_router(settings_router)
    print("[BACKEND] Settings router mounted")

# In-memory storage
sessions_db = {}
messages_db = {}
memories_db: List[Dict] = []  # For memory tab
logs_db: List[Dict] = []  # For logs tab

print("[INFO] JARVIS Core API initializing...")

# Add initial log entry
logs_db.append({
    "id": str(uuid.uuid4()),
    "timestamp": datetime.now().isoformat(),
    "level": "info",
    "message": "JARVIS Core API initialized",
    "source": "backend"
})

# AI Response Generator mit llama.cpp
async def generate_ai_response(message: str, session_id: str) -> str:
    if not llama_runtime.is_loaded:
        return "Bitte laden Sie zuerst ein Modell unter 'Modelle'."
    
    try:
        history = []
        if session_id in messages_db:
            for msg in messages_db[session_id][-5:]:
                history.append({
                    'role': 'user' if msg['isUser'] else 'assistant',
                    'content': msg['text']
                })
        
        result = llama_runtime.chat(
            message=message,
            history=history,
            system_prompt="Du bist JARVIS, ein hilfreicher deutscher KI-Assistent. Antworte praezise und freundlich.",
            max_tokens=512,
            temperature=0.7
        )
        
        if result['success']:
            print(
                f"[INFO] Generated {result['tokens_generated']} tokens "
                f"with {result['model']} on {result['device']} "
                f"({result['tokens_per_second']:.1f} tok/s)"
            )
            return result['text']
        else:
            print(f"[ERROR] Generation failed: {result.get('error', 'Unknown error')}")
            return f"Fehler bei der Antwort-Generierung: {result.get('error', 'Unbekannter Fehler')}"
        
    except Exception as e:
        print(f"[ERROR] AI generation exception: {e}")
        return f"Fehler bei der Antwort-Generierung: {str(e)}"

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
                
                print(f"[INFO] Chat message received: {user_message[:50]}...")
                
                if session_id not in messages_db:
                    messages_db[session_id] = []
                
                message_id = str(uuid.uuid4())
                messages_db[session_id].append({
                    'id': message_id,
                    'text': user_message,
                    'isUser': True,
                    'timestamp': datetime.now().isoformat()
                })
                
                await websocket.send_text(json.dumps({
                    'type': 'typing_start',
                    'sessionId': session_id
                }))
                
                response_text = await generate_ai_response(user_message, session_id)
                response_id = str(uuid.uuid4())
                
                messages_db[session_id].append({
                    'id': response_id,
                    'text': response_text,
                    'isUser': False,
                    'timestamp': datetime.now().isoformat()
                })
                
                await websocket.send_text(json.dumps({
                    'type': 'chat_response',
                    'messageId': response_id,
                    'response': response_text,
                    'sessionId': session_id
                }))
                
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
        
        return {
            "cpu": {"usage": cpu_percent, "count": cpu_count},
            "memory": {"total": round(mem_total, 2), "used": round(mem_used, 2), "percent": mem_percent},
            "disk": {"total": round(disk_total, 2), "used": round(disk_used, 2), "percent": disk_percent},
            "system": system_info,
            "llama": llama_status,
            "plugins": plugin_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"[ERROR] System info error: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

# Health API  
@app.get("/api/health")
async def health_check():
    enabled_plugins = plugin_manager.get_enabled_plugins() if plugin_manager else []
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.0",
        "llama_cpp": llama_runtime.get_status(),
        "plugins": len(enabled_plugins)
    }

# Models API
@app.get("/api/models")
async def get_models():
    models = [
        {"id": "mistral", "name": "Mistral 7B Nemo", "provider": "Mistral AI", "description": "Code, technische Details, Systembefehle", "size": "7.5 GB", "hf_model": "second-state/Mistral-Nemo-Instruct-2407-GGUF", "capabilities": ["code", "technical", "german"], "isDownloaded": model_downloader.is_model_downloaded("mistral"), "isActive": llama_runtime.is_loaded and llama_runtime.model_name == "mistral"},
        {"id": "qwen", "name": "Qwen 2.5 7B", "provider": "Alibaba", "description": "Vielseitig, mehrsprachig, balanciert", "size": "5.2 GB", "hf_model": "bartowski/Qwen2.5-7B-Instruct-GGUF", "capabilities": ["multilingual", "balanced", "fast"], "isDownloaded": model_downloader.is_model_downloaded("qwen"), "isActive": llama_runtime.is_loaded and llama_runtime.model_name == "qwen"},
        {"id": "deepseek", "name": "DeepSeek R1 8B", "provider": "DeepSeek", "description": "Analysen, Reasoning, komplexe Daten", "size": "6.9 GB", "hf_model": "Triangle104/DeepSeek-R1-Distill-Llama-8B-Q4_K_M-GGUF", "capabilities": ["analysis", "reasoning", "data"], "isDownloaded": model_downloader.is_model_downloaded("deepseek"), "isActive": llama_runtime.is_loaded and llama_runtime.model_name == "deepseek"},
        {"id": "llama32-3b", "name": "Llama 3.2 3B", "provider": "Meta", "description": "Klein, schnell, effizient fuer einfache Aufgaben", "size": "2.0 GB", "hf_model": "bartowski/Llama-3.2-3B-Instruct-GGUF", "capabilities": ["fast", "lightweight", "efficient"], "isDownloaded": model_downloader.is_model_downloaded("llama32-3b"), "isActive": llama_runtime.is_loaded and llama_runtime.model_name == "llama32-3b"},
        {"id": "phi3-mini", "name": "Phi-3 Mini", "provider": "Microsoft", "description": "Kompakt, schnell, optimiert fuer Konversation", "size": "2.3 GB", "hf_model": "bartowski/Phi-3-mini-128k-instruct-GGUF", "capabilities": ["compact", "chat", "quick"], "isDownloaded": model_downloader.is_model_downloaded("phi3-mini"), "isActive": llama_runtime.is_loaded and llama_runtime.model_name == "phi3-mini"},
        {"id": "gemma2-9b", "name": "Gemma 2 9B", "provider": "Google", "description": "Stark, vielseitig, ausgewogen", "size": "5.4 GB", "hf_model": "bartowski/gemma-2-9b-it-GGUF", "capabilities": ["powerful", "versatile", "balanced"], "isDownloaded": model_downloader.is_model_downloaded("gemma2-9b"), "isActive": llama_runtime.is_loaded and llama_runtime.model_name == "gemma2-9b"},
        {"id": "llama33-70b", "name": "Llama 3.3 70B", "provider": "Meta", "description": "Sehr gross, sehr stark, hoechste Qualitaet", "size": "40 GB", "hf_model": "bartowski/Llama-3.3-70B-Instruct-GGUF", "capabilities": ["flagship", "high-quality", "advanced"], "isDownloaded": model_downloader.is_model_downloaded("llama33-70b"), "isActive": llama_runtime.is_loaded and llama_runtime.model_name == "llama33-70b"}
    ]
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
async def download_model(model_id: str):
    print(f"[INFO] Download request for model: {model_id}")
    status = model_downloader.get_download_status()
    if status["is_downloading"]:
        return {"success": False, "message": f"Bereits am Herunterladen von {status['current_model']}", "status": status}
    
    logs_db.append({"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "level": "info", "message": f"Starting model download: {model_id}", "source": "models"})
    loop = asyncio.get_event_loop()
    
    def progress_callback(progress: float, status_text: str):
        print(f"[DOWNLOAD] {model_id}: {progress:.1f}% - {status_text}")
    
    result = await loop.run_in_executor(None, lambda: model_downloader.download_model(model_id, progress_callback))
    
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
    return {
        "message": "JARVIS Core API v1.1.0",
        "status": "online",
        "llama_cpp": llama_runtime.get_status(),
        "plugins": plugins_count,
        "endpoints": {
            "websocket": "/ws",
            "docs": "/docs",
            "health": "/api/health",
            "models": "/api/models",
            "system": "/api/system/info",
            "memory": "/api/memory",
            "logs": "/api/logs",
            "plugins": "/api/plugins",
            "settings": "/api/settings"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║          JARVIS Core Backend v1.1.0                  ║
    ║         Just A Rather Very Intelligent System        ║
    ║         with llama.cpp local inference               ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    print("[INFO] Starting JARVIS Core API...")
    print(f"[INFO] llama.cpp available: {llama_runtime.get_status()['available']}")
    print(f"[INFO] Device: {llama_runtime.device}")
    
    uvicorn.run(app, host="0.0.0.0", port=5050)
