from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from datetime import datetime
import json
import uuid
import asyncio
import sys
import os

# Add utils and core to path
sys.path.insert(0, os.path.dirname(__file__))

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import managers and logger
from utils.system_info import get_all_system_info
from core.llm_manager import llm_manager
from core.plugin_manager import plugin_manager
from core.logger import logger, log_buffer

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

# Log startup
logger.info("JARVIS Core API starting...", extra={'category': 'system'})

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Active connections: {len(self.active_connections)}", extra={'category': 'websocket'})

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}", extra={'category': 'websocket'})

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# Smart chat response generator
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

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'chat_message':
                user_message = message.get('message', '')
                session_id = message.get('sessionId', 'default')
                
                logger.debug(f"Received message: {user_message[:50]}...", extra={'category': 'chat'})
                
                if session_id not in messages_db:
                    messages_db[session_id] = []
                
                message_id = str(uuid.uuid4())
                messages_db[session_id].append({
                    'id': message_id,
                    'text': user_message,
                    'isUser': True,
                    'timestamp': datetime.now().isoformat()
                })
                
                await manager.send_personal_message({'type': 'typing', 'isTyping': True}, websocket)
                await asyncio.sleep(1.5)
                
                response_text = generate_jarvis_response(user_message)
                response_id = str(uuid.uuid4())
                
                messages_db[session_id].append({
                    'id': response_id,
                    'text': response_text,
                    'isUser': False,
                    'timestamp': datetime.now().isoformat()
                })
                
                await manager.send_personal_message({
                    'type': 'chat_response',
                    'messageId': response_id,
                    'response': response_text,
                    'sessionId': session_id,
                    'timestamp': datetime.now().isoformat()
                }, websocket)
                
                await manager.send_personal_message({'type': 'typing', 'isTyping': False}, websocket)
            
            elif message.get('type') == 'ping':
                await manager.send_personal_message({'type': 'pong'}, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
        "connections": len(manager.active_connections),
        "system": sys_info
    }

# Models API - Using LLM Manager
@app.get("/api/models")
async def get_models():
    return llm_manager.get_all_models()

@app.get("/api/models/active")
async def get_active_model():
    model = llm_manager.get_active_model()
    if model:
        return model
    return {"message": "Kein Modell aktiv"}

@app.post("/api/models/{model_id}/download")
async def download_model(model_id: str):
    logger.info(f"Download request for model: {model_id}", extra={'category': 'model'})
    result = await llm_manager.download_model(model_id)
    return result

@app.get("/api/models/{model_id}/download/progress")
async def get_download_progress(model_id: str):
    progress = llm_manager.get_download_progress(model_id)
    if progress:
        return progress
    return {"progress": 0, "status": "idle"}

@app.post("/api/models/{model_id}/load")
async def load_model(model_id: str):
    success = llm_manager.load_model(model_id)
    return {"success": success, "message": f"Modell {model_id} {'geladen' if success else 'nicht gefunden'}"}

@app.post("/api/models/unload")
async def unload_model():
    success = llm_manager.unload_model()
    return {"success": success, "message": "Modell entladen"}

# Plugins API - Using Plugin Manager
@app.get("/api/plugins")
async def get_plugins():
    return plugin_manager.get_all_plugins()

@app.post("/api/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str):
    success = plugin_manager.toggle_plugin(plugin_id)
    logger.info(f"Plugin {plugin_id} toggled", extra={'category': 'plugin'})
    return {"success": success}

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

@app.post("/api/chat/messages")
async def send_message(request: dict):
    message = request.get('message', '')
    session_id = request.get('sessionId', 'default')
    
    if session_id not in messages_db:
        messages_db[session_id] = []
    
    user_msg_id = str(uuid.uuid4())
    messages_db[session_id].append({
        'id': user_msg_id,
        'text': message,
        'isUser': True,
        'timestamp': datetime.now().isoformat()
    })
    
    response_text = generate_jarvis_response(message)
    response_id = str(uuid.uuid4())
    
    messages_db[session_id].append({
        'id': response_id,
        'text': response_text,
        'isUser': False,
        'timestamp': datetime.now().isoformat()
    })
    
    return {"messageId": response_id, "response": response_text, "sessionId": session_id}

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
    return log_buffer.get_logs(level=level, category=category, limit=limit)

@app.get("/api/logs/stats")
async def get_log_stats():
    return log_buffer.get_stats()

@app.delete("/api/logs")
async def clear_logs():
    log_buffer.clear()
    logger.info("Logs cleared", extra={'category': 'system'})
    return {"success": True, "message": "Logs cleared"}

@app.get("/")
async def root():
    return {
        "message": "JARVIS Core API v1.0.0",
        "status": "online",
        "endpoints": {
            "websocket": "/ws",
            "docs": "/docs",
            "health": "/api/health",
            "system": "/api/system/info"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║          JARVIS Core Backend v1.0.0                  ║
    ║         Just A Rather Very Intelligent System        ║
    ╚══════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=5050)
