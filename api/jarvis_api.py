#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS FastAPI Backend for React Web UI
Provides REST API + WebSocket for real-time communication

Endpoints:
- REST API: /api/*
- WebSocket: /ws
- Static Files: / (serves React build)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="JARVIS API",
    description="AI Assistant Backend for React Web UI",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # CRA default
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global JARVIS instance (set from main.py)
jarvis_instance = None

def set_jarvis_instance(jarvis):
    """Set global JARVIS instance"""
    global jarvis_instance
    jarvis_instance = jarvis
    logger.info("✅ JARVIS instance registered with API")

# ==================== Pydantic Models ====================

class CommandRequest(BaseModel):
    text: str

class LoadModelRequest(BaseModel):
    model_key: str

class HealthResponse(BaseModel):
    status: str
    version: str
    jarvis_ready: bool

# ==================== REST API Endpoints ====================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "version": "2.0.0",
        "jarvis_ready": jarvis_instance is not None
    }

@app.get("/api/system/metrics")
async def get_system_metrics():
    """
    Get system metrics for Dashboard
    Returns: CPU, RAM, GPU usage, temps, etc.
    """
    if not jarvis_instance:
        raise HTTPException(status_code=503, detail="JARVIS not initialized")
    
    try:
        metrics = jarvis_instance.get_system_metrics()
        return metrics.get("summary", {})
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/llm/status")
async def get_llm_status():
    """
    Get LLM model status
    Returns: current model, loaded models, available models
    """
    if not jarvis_instance:
        raise HTTPException(status_code=503, detail="JARVIS not initialized")
    
    try:
        status = jarvis_instance.get_llm_status()
        return status
    except Exception as e:
        logger.error(f"LLM status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/llm/models")
async def get_models():
    """
    Get available models with metadata
    Returns: List of models with download status, size, context length
    """
    if not jarvis_instance:
        return {"models": {}}
    
    try:
        overview = jarvis_instance.llm_manager.get_model_overview()
        return {"models": overview}
    except Exception as e:
        logger.error(f"Models list error: {e}")
        return {"models": {}}

@app.post("/api/llm/load")
async def load_model(request: LoadModelRequest):
    """
    Load a specific LLM model
    Body: {"model_key": "llama3"}
    """
    if not jarvis_instance:
        raise HTTPException(status_code=503, detail="JARVIS not initialized")
    
    try:
        logger.info(f"Loading model: {request.model_key}")
        jarvis_instance.llm_manager.load_model(request.model_key)
        return {"success": True, "model": request.model_key}
    except Exception as e:
        logger.error(f"Model load error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/unload")
async def unload_model():
    """
    Unload all LLM models from memory
    """
    if not jarvis_instance:
        raise HTTPException(status_code=503, detail="JARVIS not initialized")
    
    try:
        logger.info("Unloading all models")
        jarvis_instance.llm_manager.unload_model()
        return {"success": True}
    except Exception as e:
        logger.error(f"Model unload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plugins")
async def get_plugins():
    """
    Get plugin overview
    Returns: List of plugins with enabled status
    """
    if not jarvis_instance:
        return {"plugins": []}
    
    try:
        plugins = jarvis_instance.get_plugin_overview()
        return {"plugins": plugins}
    except Exception as e:
        logger.error(f"Plugins list error: {e}")
        return {"plugins": []}

@app.post("/api/chat/message")
async def send_message(request: CommandRequest):
    """
    Process chat message
    Body: {"text": "What is the weather?"}
    Returns: {"success": true, "response": "..."}
    """
    if not jarvis_instance:
        raise HTTPException(status_code=503, detail="JARVIS not initialized")
    
    try:
        logger.info(f"Processing message: {request.text[:50]}...")
        response = jarvis_instance.command_processor.process_command(request.text)
        return {
            "success": True,
            "response": response or "Command executed."
        }
    except Exception as e:
        logger.error(f"Command error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """
    Get last N lines of logs
    Query: ?lines=100
    """
    try:
        log_file = Path("logs/jarvis.log")
        if not log_file.exists():
            return {"logs": ""}
        
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:]
            return {"logs": "".join(last_lines)}
    except Exception as e:
        logger.error(f"Logs error: {e}")
        return {"logs": ""}

# ==================== WebSocket for Real-Time Updates ====================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication
    
    Client -> Server messages:
    - {"type": "ping"}
    - {"type": "chat", "text": "..."}
    - {"type": "voice_start"}
    - {"type": "voice_end"}
    
    Server -> Client messages:
    - {"type": "pong"}
    - {"type": "chat_response", "text": "...", "response": "..."}
    - {"type": "state_change", "state": "listening|processing|speaking|idle"}
    - {"type": "metrics_update", "data": {...}}
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            logger.debug(f"WS received: {msg_type}")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif msg_type == "chat":
                # Process chat message
                text = message.get("text", "")
                if jarvis_instance:
                    try:
                        await manager.broadcast({"type": "state_change", "state": "processing"})
                        response = jarvis_instance.command_processor.process_command(text)
                        # Send response with both 'text' and 'response' keys for compatibility
                        await websocket.send_json({
                            "type": "chat_response",
                            "text": response or "Command executed.",
                            "response": response or "Command executed."
                        })
                        await manager.broadcast({"type": "state_change", "state": "idle"})
                    except Exception as e:
                        logger.error(f"Chat processing error: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e)
                        })
            
            elif msg_type == "voice_start":
                await manager.broadcast({"type": "state_change", "state": "listening"})
            
            elif msg_type == "voice_end":
                await manager.broadcast({"type": "state_change", "state": "processing"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ==================== Background Tasks ====================

async def metrics_broadcaster():
    """
    Push system metrics to all clients every 2 seconds
    """
    while True:
        await asyncio.sleep(2)
        
        if jarvis_instance and len(manager.active_connections) > 0:
            try:
                metrics = jarvis_instance.get_system_metrics()
                await manager.broadcast({
                    "type": "metrics_update",
                    "data": metrics.get("summary", {})
                })
            except Exception as e:
                logger.error(f"Metrics broadcast error: {e}")

@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    asyncio.create_task(metrics_broadcaster())
    logger.info("🚀 JARVIS API started")
    logger.info("📁 API Docs: http://localhost:8000/api/docs")

# ==================== Static Files (React Build) ====================

# Serve React build in production
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
    
    @app.get("/")
    async def serve_react_app():
        return FileResponse("frontend/dist/index.html")
    
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        """Catch-all route for React Router"""
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse("frontend/dist/index.html")
else:
    logger.warning("⚠️  Frontend build not found. Run 'npm run build' in frontend/")
    
    @app.get("/")
    async def root():
        return {
            "message": "JARVIS API is running",
            "docs": "/api/docs",
            "frontend": "Build frontend with: cd frontend && npm install && npm run build"
        }