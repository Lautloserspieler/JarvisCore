from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from datetime import datetime
import json
import uuid
import asyncio
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

app = FastAPI(title="JARVIS Core API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
sessions_db = {}
messages_db = {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[+] Client verbunden. Aktive Verbindungen: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"[-] Client getrennt. Aktive Verbindungen: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# Smart chat response generator
def generate_jarvis_response(message: str) -> str:
    """Generate intelligent JARVIS responses based on message content"""
    message_lower = message.lower()
    
    # Greetings
    if any(word in message_lower for word in ['hallo', 'hi', 'hey', 'guten tag', 'servus']):
        return "Guten Tag. Ich bin JARVIS, Ihr persönlicher AI-Assistent. Wie kann ich Ihnen heute behilflich sein?"
    
    # Model commands
    if 'load' in message_lower and ('llama' in message_lower or 'model' in message_lower):
        return "Modell wird geladen... Dies kann einige Sekunden dauern. Ich informiere Sie, sobald das Modell einsatzbereit ist."
    
    if 'unload' in message_lower and 'model' in message_lower:
        return "Alle Modelle wurden aus dem RAM entladen. Speicher wurde freigegeben. Aktuelle RAM-Auslastung: 40%"
    
    # Plugin commands
    if 'plugin' in message_lower:
        if 'list' in message_lower or 'show' in message_lower or 'anzeigen' in message_lower:
            return """Aktive Plugins:
• Wikipedia Search (enabled) - Zugriff auf Wikipedia-Datenbank
• Wikidata Query (enabled) - Strukturierte Wissensdatenbank
• PubMed Search (enabled) - Medizinische Fachliteratur
• Semantic Scholar (enabled) - Wissenschaftliche Publikationen
• OpenStreetMap (enabled) - Geografische Daten
• Memory Manager (enabled) - Konversationshistorie"""
        return "Plugin-System aktiv. Verwenden Sie 'list plugins' für eine Übersicht aller verfügbaren Plugins."
    
    # Search queries
    if any(word in message_lower for word in ['search', 'suche', 'find', 'finde']):
        query = message.replace('search', '').replace('suche', '').replace('find', '').replace('finde', '').strip()
        return f"""Wissenssuche gestartet für: '{query}'

Durchsuche folgende Quellen:
→ Lokale Wissensdatenbank
→ Wikipedia
→ Wikidata
→ Wissenschaftliche Datenbanken

Ergebnisse werden in Kürze präsentiert."""
    
    # System status
    if 'status' in message_lower or 'system' in message_lower:
        return """Systemstatus - Alle Systeme operational:

CPU: 45% Auslastung (8 Cores)
RAM: 24.8GB / 64GB verwendet (39%)
GPU: NVIDIA RTX 4090 - 38% Auslastung
Storage: 2.4TB / 4TB verfügbar
Network: Online (250 Mbps)
Uptime: 14h 23m 15s

Alle Kern-Module sind online und funktionsfähig."""
    
    # Help
    if 'help' in message_lower or 'hilfe' in message_lower:
        return """JARVIS Kommando-Übersicht:

Allgemein:
• 'help' - Diese Hilfe anzeigen
• 'system status' - Systemstatus abfragen

Modelle:
• 'load llama3' - LLM laden
• 'unload model' - Modell entladen
• 'list models' - Verfügbare Modelle

Plugins:
• 'list plugins' - Plugin-Übersicht
• 'enable [plugin]' - Plugin aktivieren
• 'disable [plugin]' - Plugin deaktivieren

Suche:
• 'search [query]' - Wissenssuche starten

Was möchten Sie tun?"""
    
    # Question detection
    if '?' in message:
        return f"Das ist eine interessante Frage. Lassen Sie mich die verfügbaren Datenquellen durchsuchen und Ihnen eine fundierte Antwort geben."
    
    # Default responses
    responses = [
        "Ich habe Ihre Anfrage verstanden. Wie kann ich Ihnen weiterhelfen?",
        "Verstanden. Ich verarbeite Ihre Anfrage und stehe für weitere Fragen zur Verfügung.",
        "Ich habe die Information registriert. Gibt es noch etwas, das Sie wissen möchten?",
        "Ihre Nachricht wurde verarbeitet. Wie kann ich Sie sonst noch unterstützen?",
        "Notiert. Ich stehe für weitere Aufgaben bereit.",
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
                
                # Store user message
                message_id = str(uuid.uuid4())
                timestamp = datetime.now().isoformat()
                
                if session_id not in messages_db:
                    messages_db[session_id] = []
                
                messages_db[session_id].append({
                    'id': message_id,
                    'text': user_message,
                    'isUser': True,
                    'timestamp': timestamp
                })
                
                # Send typing indicator
                await manager.send_personal_message({
                    'type': 'typing',
                    'isTyping': True
                }, websocket)
                
                # Simulate processing delay
                await asyncio.sleep(1.5)
                
                # Generate response
                response_text = generate_jarvis_response(user_message)
                response_id = str(uuid.uuid4())
                
                # Store AI response
                messages_db[session_id].append({
                    'id': response_id,
                    'text': response_text,
                    'isUser': False,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Send response
                await manager.send_personal_message({
                    'type': 'chat_response',
                    'messageId': response_id,
                    'response': response_text,
                    'sessionId': session_id,
                    'timestamp': datetime.now().isoformat()
                }, websocket)
                
                # Stop typing indicator
                await manager.send_personal_message({
                    'type': 'typing',
                    'isTyping': False
                }, websocket)
            
            elif message.get('type') == 'ping':
                await manager.send_personal_message({'type': 'pong'}, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# REST API Endpoints

@app.get("/")
async def root():
    return {
        "message": "JARVIS Core API v1.0.0",
        "status": "online",
        "endpoints": {
            "websocket": "/ws",
            "docs": "/docs",
            "health": "/api/health"
        }
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "connections": len(manager.active_connections)
    }

# Chat API
@app.get("/api/chat/sessions")
async def get_chat_sessions():
    return [
        {
            "id": session_id,
            "title": f"Session {session_id[:8]}",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "messages": messages_db.get(session_id, [])
        }
        for session_id in messages_db.keys()
    ]

@app.post("/api/chat/sessions")
async def create_chat_session(title: str = None):
    session_id = str(uuid.uuid4())
    sessions_db[session_id] = {
        "id": session_id,
        "title": title or "New Conversation",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    messages_db[session_id] = []
    return sessions_db[session_id]

@app.get("/api/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    return messages_db.get(session_id, [])

@app.post("/api/chat/messages")
async def send_message(request: dict):
    message = request.get('message', '')
    session_id = request.get('sessionId', 'default')
    
    # Store user message
    if session_id not in messages_db:
        messages_db[session_id] = []
    
    user_msg_id = str(uuid.uuid4())
    messages_db[session_id].append({
        'id': user_msg_id,
        'text': message,
        'isUser': True,
        'timestamp': datetime.now().isoformat()
    })
    
    # Generate response
    response_text = generate_jarvis_response(message)
    response_id = str(uuid.uuid4())
    
    messages_db[session_id].append({
        'id': response_id,
        'text': response_text,
        'isUser': False,
        'timestamp': datetime.now().isoformat()
    })
    
    return {
        "messageId": response_id,
        "response": response_text,
        "sessionId": session_id
    }

# Models API
@app.get("/api/models")
async def get_models():
    return [
        {
            "id": "gpt-4",
            "name": "GPT-4",
            "provider": "OpenAI",
            "type": "text",
            "isActive": True,
            "capabilities": ["text-generation", "reasoning", "code"]
        },
        {
            "id": "claude-3",
            "name": "Claude 3",
            "provider": "Anthropic",
            "type": "text",
            "isActive": False,
            "capabilities": ["text-generation", "reasoning", "analysis"]
        },
        {
            "id": "llama3",
            "name": "Llama 3",
            "provider": "Meta",
            "type": "text",
            "isActive": False,
            "capabilities": ["text-generation", "multilingual"]
        }
    ]

@app.get("/api/models/active")
async def get_active_model():
    return {
        "id": "gpt-4",
        "name": "GPT-4",
        "provider": "OpenAI",
        "type": "text",
        "isActive": True,
        "capabilities": ["text-generation", "reasoning", "code"]
    }

# Plugins API
@app.get("/api/plugins")
async def get_plugins():
    return [
        {
            "id": "weather",
            "name": "Weather",
            "description": "Get weather information",
            "version": "1.0.0",
            "author": "JARVIS",
            "isEnabled": True,
            "isInstalled": True,
            "category": "utility",
            "capabilities": ["weather-query"]
        },
        {
            "id": "calendar",
            "name": "Calendar",
            "description": "Manage calendar events",
            "version": "1.0.0",
            "author": "JARVIS",
            "isEnabled": True,
            "isInstalled": True,
            "category": "productivity",
            "capabilities": ["event-management"]
        },
        {
            "id": "wikipedia",
            "name": "Wikipedia Search",
            "description": "Search Wikipedia articles",
            "version": "1.0.0",
            "author": "JARVIS",
            "isEnabled": True,
            "isInstalled": True,
            "category": "knowledge",
            "capabilities": ["search", "knowledge-base"]
        }
    ]

# Memory API
@app.get("/api/memory")
async def get_memories(type: Optional[str] = None):
    memories = [
        {
            "id": str(uuid.uuid4()),
            "type": "conversation",
            "content": "User prefers detailed explanations",
            "timestamp": datetime.now().isoformat(),
            "relevance": 0.95
        },
        {
            "id": str(uuid.uuid4()),
            "type": "preference",
            "content": "User is interested in AI technology",
            "timestamp": datetime.now().isoformat(),
            "relevance": 0.88
        }
    ]
    if type:
        memories = [m for m in memories if m['type'] == type]
    return memories

@app.get("/api/memory/stats")
async def get_memory_stats():
    return {
        "totalMemories": 150,
        "byType": {
            "conversation": 80,
            "fact": 40,
            "preference": 20,
            "context": 10
        },
        "storageUsed": 1024000,
        "lastUpdated": datetime.now().isoformat()
    }

# Logs API
@app.get("/api/logs")
async def get_logs(
    level: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100
):
    return [
        {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "category": "system",
            "message": "System initialized successfully",
            "metadata": {}
        },
        {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "category": "websocket",
            "message": f"Active connections: {len(manager.active_connections)}",
            "metadata": {}
        }
    ]

@app.get("/api/logs/stats")
async def get_log_stats():
    return {
        "total": 1000,
        "byLevel": {
            "debug": 200,
            "info": 500,
            "warning": 200,
            "error": 80,
            "critical": 20
        },
        "byCategory": {
            "system": 400,
            "api": 300,
            "websocket": 200,
            "model": 100
        },
        "timeRange": {
            "start": datetime.now().isoformat(),
            "end": datetime.now().isoformat()
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
