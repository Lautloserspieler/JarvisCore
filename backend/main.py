from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime
import json
import uuid
import asyncio
import sys
import os
import subprocess
import threading

# Add utils and core to path
sys.path.insert(0, os.path.dirname(__file__))

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import core systems
from utils.system_info import get_all_system_info
from core.llm_manager import llm_manager
from core.plugin_manager import plugin_manager
from core.logger import logger, log_buffer, log_info, log_error, log_warning
from core.event_system import (
    event_bus, get_ws_manager, Event, EventType
)
# Import HF Runtime
from core.hf_inference import hf_runtime

app = FastAPI(title="JARVIS Core API", version="1.0.0")

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

log_info("JARVIS Core API initializing...")

# Get WebSocket manager
ws_manager = get_ws_manager()

# Subscribe to events for broadcasting
async def broadcast_event(event: Event):
    """Broadcast events to all WebSocket clients"""
    await ws_manager.broadcast(event)

# Subscribe to all event types for broadcasting
for event_type in EventType:
    event_bus.subscribe(event_type, broadcast_event)

# Smart chat response generator (Fallback)
def generate_jarvis_response(message: str) -> str:
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['hallo', 'hi', 'hey', 'guten tag', 'servus']):
        return "Guten Tag. Ich bin JARVIS, Ihr persönlicher AI-Assistent. Wie kann ich Ihnen heute behilflich sein?"
    
    if 'help' in message_lower or 'hilfe' in message_lower:
        return """JARVIS Kommando-Übersicht:

Allgemein:
• 'help' - Diese Hilfe anzeigen
• 'system status' - Systemstatus abfragen

Modelle:
• 'load [model]' - LLM laden
• 'unload model' - Modell entladen
• 'list models' - Verfügbare Modelle

Plugins:
• 'list plugins' - Plugin-Übersicht

Suche:
• 'search [query]' - Wissenssuche starten"""
    
    responses = [
        "Ich habe Ihre Anfrage verstanden. Wie kann ich Ihnen weiterhelfen?",
        "Verstanden. Ich verarbeite Ihre Anfrage und stehe für weitere Fragen zur Verfügung.",
        "Ich habe die Information registriert. Gibt es noch etwas, das Sie wissen möchten?",
    ]
    import random
    return random.choice(responses)

# NEU: AI Response Generator mit HF Runtime
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

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'chat_message':
                user_message = message.get('message', '')
                session_id = message.get('sessionId', 'default')
                
                log_info(f"Chat message received: {user_message[:50]}...", category='chat')
                
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
                await event_bus.publish(Event(
                    EventType.TYPING_START,
                    {'sessionId': session_id},
                    source='chat'
                ))
                
                await asyncio.sleep(1.5)
                
                # NEU: Use AI Response statt Mock
                response_text = await generate_ai_response(user_message, session_id)
                response_id = str(uuid.uuid4())
                
                messages_db[session_id].append({
                    'id': response_id,
                    'text': response_text,
                    'isUser': False,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Send response
                await event_bus.publish(Event(
                    EventType.CHAT_RESPONSE,
                    {
                        'messageId': response_id,
                        'response': response_text,
                        'sessionId': session_id
                    },
                    source='chat'
                ))
                
                # Stop typing
                await event_bus.publish(Event(
                    EventType.TYPING_STOP,
                    {'sessionId': session_id},
                    source='chat'
                ))
            
            elif message.get('type') == 'ping':
                await ws_manager.send_to_client(
                    websocket,
                    Event(EventType.HEARTBEAT, {'pong': True}, source='websocket')
                )
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        log_error(f"WebSocket error: {e}", category='websocket', exc_info=True)
        ws_manager.disconnect(websocket)

# System Info API
@app.get("/api/system/info")
async def get_system_info():
    return get_all_system_info()

# Health API  
@app.get("/api/health")
async def health_check():
    sys_info = get_all_system_info()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "connections": len(ws_manager.connections),
        "system": sys_info
    }

# Models API - Using LLM Manager + Events
@app.get("/api/models")
async def get_models():
    models = llm_manager.get_all_models()
    log_info(f"Returning {len(models)} models", category='model')
    return models

@app.get("/api/models/active")
async def get_active_model():
    model = llm_manager.get_active_model()
    if model:
        return model
    return {"message": "Kein Modell aktiv"}

@app.post("/api/models/{model_id}/download")
async def download_model(model_id: str):
    log_info(f"Download request for model: {model_id}", category='model')
    
    # Publish download start event
    await event_bus.publish(Event(
        EventType.MODEL_DOWNLOAD_START,
        {'modelId': model_id},
        source='model_manager'
    ))
    
    try:
        result = await llm_manager.download_model(model_id)
        
        if result['success']:
            await event_bus.publish(Event(
                EventType.MODEL_DOWNLOAD_COMPLETE,
                {'modelId': model_id, 'message': result['message']},
                source='model_manager'
            ))
        else:
            await event_bus.publish(Event(
                EventType.MODEL_DOWNLOAD_ERROR,
                {'modelId': model_id, 'error': result['message']},
                source='model_manager'
            ))
        
        return result
        
    except Exception as e:
        log_error(f"Model download failed: {e}", category='model', exc_info=True)
        await event_bus.publish(Event(
            EventType.MODEL_DOWNLOAD_ERROR,
            {'modelId': model_id, 'error': str(e)},
            source='model_manager'
        ))
        return {'success': False, 'message': str(e)}

@app.get("/api/models/{model_id}/download/progress")
async def get_download_progress(model_id: str):
    progress = llm_manager.get_download_progress(model_id)
    if progress:
        return progress
    return {"progress": 0, "status": "idle"}

@app.post("/api/models/{model_id}/load")
async def load_model(model_id: str):
    log_info(f"Load request for model: {model_id}", category='model')
    
    # Publish load start event
    await event_bus.publish(Event(
        EventType.MODEL_LOAD_START,
        {'modelId': model_id},
        source='model_manager'
    ))
    
    try:
        success = llm_manager.load_model(model_id)
        
        if success:
            model = llm_manager.get_active_model()
            await event_bus.publish(Event(
                EventType.MODEL_LOAD_COMPLETE,
                {'modelId': model_id, 'model': model},
                source='model_manager'
            ))
            return {"success": True, "message": f"Modell {model_id} geladen", "model": model}
        else:
            await event_bus.publish(Event(
                EventType.MODEL_LOAD_ERROR,
                {'modelId': model_id, 'error': 'Modell nicht gefunden oder nicht heruntergeladen'},
                source='model_manager'
            ))
            return {"success": False, "message": "Modell nicht gefunden"}
            
    except Exception as e:
        log_error(f"Model load failed: {e}", category='model', exc_info=True)
        await event_bus.publish(Event(
            EventType.MODEL_LOAD_ERROR,
            {'modelId': model_id, 'error': str(e)},
            source='model_manager'
        ))
        return {"success": False, "message": str(e)}

@app.post("/api/models/unload")
async def unload_model():
    log_info("Unload model request", category='model')
    
    try:
        success = llm_manager.unload_model()
        
        if success:
            await event_bus.publish(Event(
                EventType.MODEL_UNLOAD,
                {'message': 'Modell entladen'},
                source='model_manager'
            ))
        
        return {"success": success, "message": "Modell entladen"}
        
    except Exception as e:
        log_error(f"Model unload failed: {e}", category='model', exc_info=True)
        return {"success": False, "message": str(e)}

# Plugins API - Using Plugin Manager + Events
@app.get("/api/plugins")
async def get_plugins():
    plugins = plugin_manager.get_all_plugins()
    log_info(f"Returning {len(plugins)} plugins", category='plugin')
    return plugins

@app.post("/api/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str):
    log_info(f"Toggle plugin: {plugin_id}", category='plugin')
    
    try:
        success = plugin_manager.toggle_plugin(plugin_id)
        
        if success:
            await event_bus.publish(Event(
                EventType.PLUGIN_TOGGLE,
                {'pluginId': plugin_id},
                source='plugin_manager'
            ))
        
        return {"success": success}
        
    except Exception as e:
        log_error(f"Plugin toggle failed: {e}", category='plugin', exc_info=True)
        return {"success": False, "error": str(e)}

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

# Memory API
@app.get("/api/memory")
async def get_memories(type: Optional[str] = None):
    return []

@app.get("/api/memory/stats")
async def get_memory_stats():
    return {
        "totalMemories": 0,
        "byType": {},
        "storageUsed": 0,
        "lastUpdated": datetime.now().isoformat()
    }

# Logs API - Using Log Buffer
@app.get("/api/logs")
async def get_logs(level: Optional[str] = None, category: Optional[str] = None, limit: int = 100):
    logs = log_buffer.get_logs(level=level, category=category, limit=limit)
    return logs

@app.get("/api/logs/stats")
async def get_log_stats():
    return log_buffer.get_stats()

@app.delete("/api/logs")
async def clear_logs():
    log_buffer.clear()
    log_info("Logs cleared", category='system')
    return {"success": True, "message": "Logs cleared"}

# Events API
@app.get("/api/events/history")
async def get_event_history(event_type: Optional[str] = None, limit: int = 50):
    """Get event history"""
    if event_type:
        try:
            et = EventType(event_type)
            return event_bus.get_history(et, limit)
        except ValueError:
            return event_bus.get_history(limit=limit)
    return event_bus.get_history(limit=limit)

@app.get("/")
async def root():
    return {
        "message": "JARVIS Core API v1.0.0",
        "status": "online",
        "endpoints": {
            "websocket": "/ws",
            "docs": "/docs",
            "health": "/api/health",
            "system": "/api/system/info",
            "events": "/api/events/history"
        }
    }

# NEU: Startup Event - Auto-load letztes Model
@app.on_event("startup")
async def startup():
    log_info("JARVIS Core API starting...", category='startup')
    
    # Check if active model exists and load it
    active_model = llm_manager.get_active_model()
    if active_model and active_model['isDownloaded']:
        log_info(f"Auto-loading last active model: {active_model['name']}", category='startup')
        success = llm_manager.load_model(active_model['id'])
        if success:
            log_info(f"✓ {active_model['name']} loaded and ready", category='startup')
        else:
            log_warning(f"Failed to auto-load {active_model['name']}", category='startup')

# NEU: Frontend Auto-Start
def start_frontend():
    """Startet das Frontend in einem separaten Prozess"""
    try:
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        
        if not os.path.exists(frontend_dir):
            log_warning("Frontend directory not found, skipping auto-start", category='startup')
            return
        
        log_info("Starting frontend server...", category='startup')
        
        # Prüfe ob npm installiert ist
        try:
            subprocess.run(['npm', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            log_warning("npm not found, skipping frontend auto-start", category='startup')
            return
        
        # Starte Frontend
        if sys.platform == 'win32':
            # Windows
            subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=frontend_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Linux/Mac
            subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        log_info("✓ Frontend started on http://localhost:5000", category='startup')
        
    except Exception as e:
        log_error(f"Failed to start frontend: {e}", category='startup')

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║          JARVIS Core Backend v1.0.0                  ║
    ║         Just A Rather Very Intelligent System        ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    log_info("Starting JARVIS Core API...")
    
    # Starte Frontend in separatem Thread
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    frontend_thread.start()
    
    # Warte kurz damit Frontend-Meldung sichtbar ist
    import time
    time.sleep(2)
    
    # Starte Backend
    uvicorn.run(app, host="0.0.0.0", port=5050)
