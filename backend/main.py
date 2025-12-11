from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from datetime import datetime
import json
import uuid

app = FastAPI(title="JARVIS Core API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'chat_message':
                # Process chat message
                response = {
                    'type': 'chat_response',
                    'messageId': str(uuid.uuid4()),
                    'response': f"Echo: {message.get('message', '')}",
                    'sessionId': message.get('sessionId', 'default'),
                    'timestamp': datetime.now().isoformat()
                }
                await manager.send_personal_message(response, websocket)
            
            elif message.get('type') == 'ping':
                await manager.send_personal_message({'type': 'pong'}, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# REST API Endpoints

@app.get("/")
async def root():
    return {"message": "JARVIS Core API v1.0.0", "status": "online"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Chat API
@app.get("/api/chat/sessions")
async def get_chat_sessions():
    return [
        {
            "id": "session-1",
            "title": "General Conversation",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "messages": []
        }
    ]

@app.post("/api/chat/sessions")
async def create_chat_session(title: Optional[str] = None):
    return {
        "id": str(uuid.uuid4()),
        "title": title or "New Conversation",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "messages": []
    }

@app.post("/api/chat/messages")
async def send_message(message: dict):
    return {
        "messageId": str(uuid.uuid4()),
        "response": f"Received: {message.get('message', '')}",
        "sessionId": message.get('sessionId', 'default')
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
        }
    ]

# Memory API
@app.get("/api/memory")
async def get_memories(type: Optional[str] = None):
    return [
        {
            "id": str(uuid.uuid4()),
            "type": "conversation",
            "content": "User prefers detailed explanations",
            "timestamp": datetime.now().isoformat(),
            "relevance": 0.95
        }
    ]

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
