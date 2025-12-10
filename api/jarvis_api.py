#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. FastAPI Backend

REST API + WebSocket für die Web-UI
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# JARVIS Instance (wird von main.py gesetzt)
_jarvis_instance: Optional[Any] = None


def set_jarvis_instance(jarvis):
    """Setzt die JARVIS-Instanz für die API."""
    global _jarvis_instance
    _jarvis_instance = jarvis


def get_jarvis():
    """Gibt die aktuelle JARVIS-Instanz zurück."""
    if _jarvis_instance is None:
        raise RuntimeError("JARVIS instance not initialized")
    return _jarvis_instance


# FastAPI App
app = FastAPI(
    title="J.A.R.V.I.S. API",
    description="REST API + WebSocket für JARVIS Web-UI",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files (Frontend)
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatMessage(BaseModel):
    """Chat-Nachricht vom User"""
    text: str
    stream: bool = False


class LLMLoadRequest(BaseModel):
    """LLM Model laden"""
    model: str


class LLMActionRequest(BaseModel):
    """LLM Aktion (load/unload/download)"""
    action: str  # load, unload, download
    model: Optional[str] = None


# ============================================================================
# Health & Status
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health Check"""
    try:
        jarvis = get_jarvis()
        return {
            "status": "ok",
            "running": jarvis.is_running,
            "version": "2.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/status")
async def get_status():
    """Vollständiger Status"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_runtime_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Metrics
# ============================================================================

@app.get("/api/system/metrics")
async def get_system_metrics(details: bool = False):
    """System-Metriken (CPU, RAM, GPU, etc.)"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_system_metrics(include_details=details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LLM Management
# ============================================================================

@app.get("/api/llm/status")
async def get_llm_status():
    """LLM Status (welches Model geladen ist, etc.)"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_llm_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/llm/models")
async def list_llm_models():
    """Liste aller verfügbaren LLM-Modelle"""
    try:
        jarvis = get_jarvis()
        llm_manager = getattr(jarvis, "llm_manager", None)
        if not llm_manager:
            return {"available": {}, "loaded": []}
        
        available = llm_manager.get_model_overview()
        loaded = list(getattr(llm_manager, "loaded_models", {}).keys())
        
        return {
            "available": available,
            "loaded": loaded,
            "current": getattr(llm_manager, "current_model", None)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/llm/load")
async def load_llm_model(request: LLMLoadRequest):
    """LLM Model laden"""
    try:
        jarvis = get_jarvis()
        result = jarvis.control_llm_model(action="load", model_key=request.model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/llm/unload")
async def unload_llm_model():
    """Aktuelles LLM Model entladen"""
    try:
        jarvis = get_jarvis()
        result = jarvis.control_llm_model(action="unload")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/llm/action")
async def llm_action(request: LLMActionRequest):
    """LLM Aktion ausführen (load/unload/download)"""
    try:
        jarvis = get_jarvis()
        result = jarvis.control_llm_model(
            action=request.action,
            model_key=request.model
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Plugins
# ============================================================================

@app.get("/api/plugins")
async def get_plugins():
    """Liste aller Plugins"""
    try:
        jarvis = get_jarvis()
        return {"plugins": jarvis.get_plugin_overview()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Chat
# ============================================================================

@app.post("/api/chat/message")
async def send_chat_message(message: ChatMessage):
    """Chat-Nachricht senden"""
    try:
        jarvis = get_jarvis()
        
        # Command Processor aufrufen
        if hasattr(jarvis, "command_processor"):
            response = jarvis.command_processor.process_command(message.text)
            return {
                "response": response,
                "status": "ok"
            }
        else:
            return {
                "response": "Command processor nicht verfügbar",
                "status": "error"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Logs
# ============================================================================

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Letzte N Zeilen der Logs"""
    try:
        log_file = Path("logs/jarvis.log")
        if not log_file.exists():
            return {"logs": []}
        
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {"logs": [line.strip() for line in recent]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket
# ============================================================================

class ConnectionManager:
    """WebSocket Connection Manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Nachricht an alle Clients senden"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket für Realtime-Updates"""
    await manager.connect(websocket)
    
    try:
        jarvis = get_jarvis()
        
        # Begrüßung
        await websocket.send_json({
            "type": "connected",
            "message": "Verbindung zu JARVIS hergestellt"
        })
        
        # Message Loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif msg_type == "chat":
                text = message.get("text", "")
                if hasattr(jarvis, "command_processor"):
                    response = jarvis.command_processor.process_command(text)
                    await websocket.send_json({
                        "type": "chat_response",
                        "text": response
                    })
            
            elif msg_type == "get_status":
                status = jarvis.get_runtime_status()
                await websocket.send_json({
                    "type": "status",
                    "data": status
                })
            
            elif msg_type == "get_metrics":
                metrics = jarvis.get_system_metrics(include_details=False)
                await websocket.send_json({
                    "type": "metrics",
                    "data": metrics
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket Error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# Frontend (SPA)
# ============================================================================

@app.get("/")
async def serve_frontend():
    """Serve Frontend SPA"""
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Frontend nicht gebaut",
                "message": "Führe aus: cd frontend && npm install && npm run build"
            }
        )


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Catch-all für SPA Routing"""
    # Wenn Datei existiert, serve sie
    file_path = frontend_dist / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    
    # Sonst: index.html (SPA Routing)
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "Frontend nicht gefunden"}
        )


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """FastAPI Startup"""
    print("📡 FastAPI Backend gestartet")
    print("🌐 Web-UI: http://localhost:8000")
    print("📜 API Docs: http://localhost:8000/api/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI Shutdown"""
    print("👋 FastAPI Backend wird beendet")
