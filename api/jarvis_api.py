#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. FastAPI Backend
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

# JARVIS-Instanz (wird von main.py gesetzt)
_jarvis_instance = None

def set_jarvis_instance(jarvis):
    global _jarvis_instance
    _jarvis_instance = jarvis

def get_jarvis():
    if _jarvis_instance is None:
        raise RuntimeError("JARVIS instance not initialized")
    return _jarvis_instance

# FastAPI App
app = FastAPI(
    title="J.A.R.V.I.S. API",
    description="RESTful API für J.A.R.V.I.S. Sprachassistent",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ChatMessage(BaseModel):
    text: str
    stream: bool = False

class LLMLoadRequest(BaseModel):
    model: str

class LLMActionRequest(BaseModel):
    action: str  # "load", "unload", "download"
    model: Optional[str] = None

class SettingsUpdate(BaseModel):
    section: str
    key: str
    value: Any

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("WebSocket connected")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print("WebSocket disconnected")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/api/health")
async def health_check():
    """System Health Check"""
    jarvis = get_jarvis()
    return {
        "status": "ok",
        "running": jarvis.is_running,
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def get_status():
    """Runtime Status"""
    jarvis = get_jarvis()
    return jarvis.get_runtime_status()

@app.get("/api/metrics")
async def get_metrics(details: bool = False):
    """System Metrics (CPU, RAM, Disk)"""
    jarvis = get_jarvis()
    return jarvis.get_system_metrics(include_details=details)

# =============================================================================
# LLM ENDPOINTS
# =============================================================================

@app.get("/api/llm/status")
async def llm_status():
    """LLM Model Status"""
    jarvis = get_jarvis()
    return jarvis.get_llm_status()

@app.post("/api/llm/load")
async def llm_load(request: LLMLoadRequest):
    """Load LLM Model"""
    jarvis = get_jarvis()
    try:
        result = jarvis.control_llm_model("load", request.model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/unload")
async def llm_unload():
    """Unload Current LLM Model"""
    jarvis = get_jarvis()
    try:
        result = jarvis.control_llm_model("unload")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/action")
async def llm_action(request: LLMActionRequest):
    """Generic LLM Action (load/unload/download)"""
    jarvis = get_jarvis()
    try:
        result = jarvis.control_llm_model(request.action, request.model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# PLUGIN ENDPOINTS
# =============================================================================

@app.get("/api/plugins")
async def get_plugins():
    """Get Plugin Overview"""
    jarvis = get_jarvis()
    return jarvis.get_plugin_overview()

# =============================================================================
# SETTINGS ENDPOINTS
# =============================================================================

@app.post("/api/settings")
async def update_settings(update: SettingsUpdate):
    """Update Settings"""
    jarvis = get_jarvis()
    try:
        # Get settings object
        settings = jarvis.settings
        if not settings:
            raise HTTPException(status_code=500, detail="Settings not available")
        
        # Set value using dot notation (section.key)
        settings.set(f"{update.section}.{update.key}", update.value)
        
        return {
            "success": True,
            "message": "Settings updated",
            "section": update.section,
            "key": update.key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# CHAT ENDPOINT
# =============================================================================

@app.post("/api/chat/message")
async def send_chat_message(message: ChatMessage):
    """Send Chat Message"""
    jarvis = get_jarvis()
    
    # Process command
    response_text = "Verstanden. Befehl wird verarbeitet."
    
    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "chat_message",
        "data": {
            "message": message.text,
            "response": response_text,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    return {
        "response": response_text,
        "timestamp": datetime.now().isoformat()
    }

# =============================================================================
# LOGS ENDPOINT
# =============================================================================

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get Recent Logs"""
    try:
        log_file = Path("logs/jarvis.log")
        if not log_file.exists():
            return {"logs": []}
        
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total": len(all_lines)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# WEBSOCKET
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back for now
            await manager.broadcast({
                "type": "echo",
                "data": message
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# =============================================================================
# STATIC FILES (Frontend)
# =============================================================================

frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    # Serve static assets
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    # Serve index.html for all other routes (SPA)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Fallback to index.html for SPA routing
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "message": "J.A.R.V.I.S. API läuft",
            "docs": "/api/docs",
            "warning": "Frontend nicht gebaut. Führe aus: cd frontend && npm run build"
        }

if __name__ == "__main__":
    print("❌ Starte main.py statt dieser Datei!")
    sys.exit(1)
