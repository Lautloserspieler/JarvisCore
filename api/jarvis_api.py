#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. FastAPI Backend
RESTful API und WebSocket-Server für die Web-UI
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import asyncio
import json

app = FastAPI(
    title="J.A.R.V.I.S. API",
    description="RESTful API für den J.A.R.V.I.S. Sprachassistenten",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global JARVIS instance
_jarvis_instance = None

def set_jarvis_instance(jarvis):
    """Setzt die globale JARVIS-Instanz"""
    global _jarvis_instance
    _jarvis_instance = jarvis

def get_jarvis():
    """Gibt die JARVIS-Instanz zurück"""
    if _jarvis_instance is None:
        raise HTTPException(status_code=503, detail="JARVIS ist noch nicht initialisiert")
    return _jarvis_instance

# Pydantic Models
class CommandRequest(BaseModel):
    command: str
    mode: Optional[str] = "text"

class LLMActionRequest(BaseModel):
    action: str  # load, unload, download
    model: Optional[str] = None

class SettingRequest(BaseModel):
    section: str
    key: str
    value: Any

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/health")
async def health_check():
    """System-Gesundheitscheck"""
    try:
        jarvis = get_jarvis()
        return {
            "status": "ok",
            "version": "2.0.0",
            "running": jarvis.is_running,
            "listening": jarvis.listening,
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/status")
async def get_status():
    """Detaillierter System-Status"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_runtime_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    """System-Metriken (CPU, RAM, Disk)"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_system_metrics(include_details=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/llm/status")
async def llm_status():
    """LLM Status und verfügbare Modelle"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_llm_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/action")
async def llm_action(request: LLMActionRequest):
    """LLM Aktion (load/unload/download)"""
    try:
        jarvis = get_jarvis()
        result = jarvis.control_llm_model(request.action, request.model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/load")
async def load_model(request: dict):
    """Lädt ein LLM-Modell"""
    try:
        jarvis = get_jarvis()
        model_key = request.get("model", "mistral")
        result = jarvis.control_llm_model("load", model_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/unload")
async def unload_model():
    """Entlädt das aktuelle LLM-Modell"""
    try:
        jarvis = get_jarvis()
        result = jarvis.control_llm_model("unload")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plugins")
async def get_plugins():
    """Liste aller Plugins"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_plugin_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/command")
async def execute_command(request: CommandRequest):
    """Führt einen Befehl aus"""
    try:
        jarvis = get_jarvis()
        processor = getattr(jarvis, "command_processor", None)
        if not processor:
            raise HTTPException(status_code=503, detail="Command Processor nicht verfügbar")
        
        response = processor.process_command(request.command)
        return {"success": True, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
async def save_setting(request: SettingRequest):
    """Speichert eine Einstellung"""
    try:
        jarvis = get_jarvis()
        settings = getattr(jarvis, "settings", None)
        if not settings:
            raise HTTPException(status_code=503, detail="Settings nicht verfügbar")
        
        # Get current section or create empty dict
        current = settings.get(request.section, {})
        if not isinstance(current, dict):
            current = {}
        
        # Update value
        current[request.key] = request.value
        settings.set(request.section, current)
        
        # Force save to disk
        settings.save()
        
        # If HuggingFace token was updated, reload LLM manager settings
        if request.section == 'llm' and request.key == 'huggingface_token':
            llm_manager = getattr(jarvis, 'llm_manager', None)
            if llm_manager:
                # Reload settings in LLM manager
                llm_manager.settings = settings
                print(f"✅ HuggingFace Token updated and LLM manager reloaded")
        
        return {"success": True, "message": "Einstellung gespeichert"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/start")
async def start_listening():
    """Startet die Spracherkennung"""
    try:
        jarvis = get_jarvis()
        success = jarvis.start_listening()
        return {"success": success, "listening": jarvis.listening}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/stop")
async def stop_listening():
    """Stoppt die Spracherkennung"""
    try:
        jarvis = get_jarvis()
        success = jarvis.stop_listening()
        return {"success": success, "listening": jarvis.listening}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WEBSOCKET
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket-Verbindung für Echtzeit-Updates"""
    await manager.connect(websocket)
    print("WebSocket connected")
    
    try:
        while True:
            # Empfange Nachrichten vom Client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Verarbeite Nachricht
            msg_type = message.get("type")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif msg_type == "command":
                try:
                    jarvis = get_jarvis()
                    processor = getattr(jarvis, "command_processor", None)
                    if processor:
                        response = processor.process_command(message.get("command", ""))
                        await websocket.send_json({
                            "type": "command_response",
                            "response": response
                        })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ============================================================================
# STATIC FILES & SPA
# ============================================================================

# Frontend dist Ordner
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    # Serve static assets
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    # Serve index.html für alle anderen Routes (SPA)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # API routes nicht abfangen
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        
        # index.html für alle SPA-Routes
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404)

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print("📡 FastAPI Backend gestartet")
    print("🌐 Web-UI: http://localhost:8000")
    print("📜 API Docs: http://localhost:8000/api/docs")

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 FastAPI Backend wird beendet")
