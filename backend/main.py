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

app = FastAPI(title="JARVIS Core API", version="1.1.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """
    Generiert AI-Response mit geladenem llama.cpp Model
    Falls kein Model geladen ist, wird Fallback-Response zurückgegeben
    """
    # Check if model loaded
    if not llama_runtime.is_loaded:
        return "Bitte laden Sie zuerst ein Modell unter 'Modelle'."
    
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
        result = llama_runtime.chat(
            message=message,
            history=history,
            system_prompt="Du bist JARVIS, ein hilfreicher deutscher KI-Assistent. Antworte präzise und freundlich.",
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
                
                # Send typing indicator
                await websocket.send_text(json.dumps({
                    'type': 'typing_start',
                    'sessionId': session_id
                }))
                
                # Generate AI response
                response_text = await generate_ai_response(user_message, session_id)
                response_id = str(uuid.uuid4())
                
                messages_db[session_id].append({
                    'id': response_id,
                    'text': response_text,
                    'isUser': False,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Send response
                await websocket.send_text(json.dumps({
                    'type': 'chat_response',
                    'messageId': response_id,
                    'response': response_text,
                    'sessionId': session_id
                }))
                
                # Stop typing
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
    """Get all system logs"""
    return logs_db[-100:]  # Last 100 logs

@app.get("/api/logs/stats")
async def get_logs_stats():
    """Get log statistics"""
    return {
        "total": len(logs_db),
        "errors": len([log for log in logs_db if log.get('level') == 'error']),
        "warnings": len([log for log in logs_db if log.get('level') == 'warning']),
        "info": len([log for log in logs_db if log.get('level') == 'info'])
    }

@app.post("/api/logs/clear")
async def clear_logs():
    """Clear all logs"""
    global logs_db
    logs_db = []
    return {"success": True, "message": "Logs cleared"}

# Plugins API
@app.get("/api/plugins")
async def get_plugins():
    """Get all available plugins"""
    if plugin_manager is None:
        return []
    return plugin_manager.get_all_plugins()

@app.post("/api/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    """Enable a plugin"""
    if plugin_manager is None:
        return {"success": False, "message": "Plugin Manager not ready"}
    
    result = plugin_manager.enable_plugin(plugin_id)
    
    # Result kann jetzt auch API-Key Anforderung enthalten!
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
    """Disable a plugin"""
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
        return {
            "success": True,
            "message": f"Plugin {plugin_id} deaktiviert"
        }
    else:
        return {
            "success": False,
            "message": f"Plugin {plugin_id} konnte nicht deaktiviert werden"
        }

@app.post("/api/plugins/reload")
async def reload_plugins():
    """Reload all plugins"""
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
    """Get all stored memories"""
    return memories_db

@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory statistics"""
    return {
        "total": len(memories_db),
        "categories": {},
        "recent": memories_db[-5:] if memories_db else []
    }

@app.post("/api/memory")
async def add_memory(memory: dict):
    """Add a new memory"""
    memory['id'] = str(uuid.uuid4())
    memory['timestamp'] = datetime.now().isoformat()
    memories_db.append(memory)
    return {"success": True, "memory": memory}

@app.delete("/api/memory/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory"""
    global memories_db
    memories_db = [m for m in memories_db if m.get('id') != memory_id]
    return {"success": True}

# System Info API
@app.get("/api/system/info")
async def get_system_info():
    """Get system information"""
    try:
        # CPU Info
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        
        # Memory Info
        mem = psutil.virtual_memory()
        mem_total = mem.total / (1024**3)  # GB
        mem_used = mem.used / (1024**3)    # GB
        mem_percent = mem.percent
        
        # Disk Info
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024**3)  # GB
        disk_used = disk.used / (1024**3)    # GB
        disk_percent = disk.percent
        
        # Platform Info
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
        }
        
        # llama.cpp status
        llama_status = llama_runtime.get_status()
        
        # Plugin stats
        plugins = plugin_manager.get_all_plugins() if plugin_manager else []
        plugin_stats = {
            "total": len(plugins),
            "enabled": len([p for p in plugins if p['enabled']])
        }
        
        return {
            "cpu": {
                "usage": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "total": round(mem_total, 2),
                "used": round(mem_used, 2),
                "percent": mem_percent
            },
            "disk": {
                "total": round(disk_total, 2),
                "used": round(disk_used, 2),
                "percent": disk_percent
            },
            "system": system_info,
            "llama": llama_status,
            "plugins": plugin_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"[ERROR] System info error: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

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

# Models API (truncated for brevity...keeping existing implementation)
[REST OF FILE CONTINUES AS BEFORE]
