#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. FastAPI Backend
RESTful API und WebSocket-Server für die Web-UI
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import asyncio
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# Import GPU Manager
from src.jarviscore.api.gpu_settings import gpu_manager

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

# Thread pool for blocking operations
_executor = ThreadPoolExecutor(max_workers=4)

# GLOBAL download progress tracking
_download_progress: Dict[str, Any] = {
    "model": None,
    "status": None,
    "downloaded": 0,
    "total": 0,
    "percent": 0,
    "speed": 0,
    "eta": 0,
    "message": "",
}
_progress_lock = threading.Lock()

# Active downloads tracking (for multiple concurrent downloads)
_active_downloads: Dict[str, Dict[str, Any]] = {}

def update_download_progress(progress_data: Dict[str, Any]):
    """Updates global download progress - called from LLM Manager"""
    global _download_progress, _active_downloads
    with _progress_lock:
        _download_progress.update(progress_data)
        
        # Update active downloads
        model_key = progress_data.get('model')
        if model_key:
            _active_downloads[model_key] = progress_data
            
            # Cleanup completed/failed downloads after 5 seconds
            if progress_data.get('status') in ['completed', 'failed', 'error']:
                def cleanup():
                    time.sleep(5)
                    with _progress_lock:
                        _active_downloads.pop(model_key, None)
                threading.Thread(target=cleanup, daemon=True).start()
        
        print(f"[API] Progress updated: {progress_data}")

def set_jarvis_instance(jarvis):
    """Setzt die globale JARVIS-Instanz und bindet Callbacks"""
    global _jarvis_instance
    _jarvis_instance = jarvis
    # Bind progress callback to LLM manager
    if hasattr(jarvis, 'llm_manager') and jarvis.llm_manager:
        jarvis.llm_manager._progress_callback = update_download_progress
        print("✅ Download progress callback bound to LLM manager")

def get_jarvis():
    """Gibt die JARVIS-Instanz zurück"""
    if _jarvis_instance is None:
        raise HTTPException(status_code=503, detail="JARVIS ist noch nicht initialisiert")
    return _jarvis_instance

def get_download_progress() -> Dict[str, Any]:
    """Returns current download progress"""
    with _progress_lock:
        return _download_progress.copy()

def get_active_downloads() -> Dict[str, Dict[str, Any]]:
    """Returns all active downloads"""
    with _progress_lock:
        return _active_downloads.copy()

# Pydantic Models
class CommandRequest(BaseModel):
    command: str
    mode: Optional[str] = "text"

class ChatMessageRequest(BaseModel):
    text: str
    stream: Optional[bool] = False

class LLMActionRequest(BaseModel):
    action: str  # load, unload, download
    model: Optional[str] = None

class SettingRequest(BaseModel):
    section: str
    key: str
    value: Any

class ModelDownloadRequest(BaseModel):
    model_key: str
    quantization: Optional[str] = "Q4_K_M"

class ModelDeleteRequest(BaseModel):
    model_key: str

class GPUInstallRequest(BaseModel):
    gpu_type: str  # cuda, rocm, metal, cpu

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
# GPU SETTINGS API ENDPOINTS
# ============================================================================

@app.get("/api/settings/gpu")
async def get_gpu_info():
    """Get GPU information and availability"""
    try:
        return gpu_manager.get_gpu_info()
    except Exception as e:
        print(f"[API] GPU info error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/settings/gpu/install")
async def install_gpu_support(request: GPUInstallRequest):
    """Install GPU support for specified backend"""
    try:
        gpu_type = request.gpu_type.lower()
        
        if gpu_type not in ['cpu', 'cuda', 'rocm', 'metal']:
            raise HTTPException(status_code=400, detail=f"Invalid GPU type: {gpu_type}")
        
        # Run installation in background
        def background_install():
            try:
                print(f"[GPU] Starting {gpu_type.upper()} installation...")
                result = asyncio.run(gpu_manager.install_gpu_support(gpu_type))
                print(f"[GPU] Installation result: {result}")
                return result
            except Exception as e:
                print(f"[GPU] Installation error: {e}")
                return {
                    'status': 'error',
                    'message': 'Installation error'
                }
        
        # Start installation in thread
        install_thread = threading.Thread(target=background_install, daemon=True)
        install_thread.start()
        
        return {
            'status': 'processing',
            'message': f'{gpu_type.upper()} installation started',
            'gpu_type': gpu_type
        }
    except Exception as e:
        print(f"[API] GPU install error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# MODEL DOWNLOAD API ENDPOINTS
# ============================================================================

@app.get("/api/models/available")
async def get_available_models():
    """Get list of all available models with download status"""
    try:
        jarvis = get_jarvis()
        llm_manager = getattr(jarvis, 'llm_manager', None)
        
        if not llm_manager:
            raise HTTPException(status_code=503, detail="LLM Manager not available")
        
        # Get model overview from LLM manager
        models_info = llm_manager.get_model_overview()
        
        return {
            "success": True,
            "models": models_info
        }
    except Exception as e:
        print(f"[API] Error getting available models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/models/download")
async def download_model(request: ModelDownloadRequest):
    """Start model download"""
    try:
        jarvis = get_jarvis()
        llm_manager = getattr(jarvis, 'llm_manager', None)
        
        if not llm_manager:
            raise HTTPException(status_code=503, detail="LLM Manager not available")
        
        model_key = request.model_key
        quantization = request.quantization
        
        # Check if already downloading
        with _progress_lock:
            if model_key in _active_downloads:
                current_status = _active_downloads[model_key].get('status')
                if current_status == 'downloading':
                    return JSONResponse(
                        status_code=409,
                        content={
                            "success": False,
                            "error": "Model is already being downloaded"
                        }
                    )
        
        # Ensure callback is bound
        llm_manager._progress_callback = update_download_progress
        
        print(f"[API] Starting download for model: {model_key} ({quantization})")
        
        # Start download in background thread
        def background_download():
            try:
                print(f"[LLM] Download thread: starting {model_key}...")
                llm_manager.download_model(
                    model_key,
                    quantization=quantization,
                    progress_cb=update_download_progress
                )
                print(f"[LLM] Download thread: completed {model_key}")
            except Exception as e:
                print(f"[LLM] Download thread error: {e}")
                with _progress_lock:
                    error_data = {
                        "model": model_key,
                        "status": "error",
                        "message": "Internal server error",
                        "error": "Internal server error"
                    }
                    _download_progress.update(error_data)
                    _active_downloads[model_key] = error_data
        
        # Start download thread
        download_thread = threading.Thread(target=background_download, daemon=True)
        download_thread.start()
        
        return {
            "success": True,
            "model": model_key,
            "quantization": quantization,
            "message": f"Download started for {model_key}"
        }
    except Exception as e:
        print(f"[API] Download error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/models/download/progress")
async def download_progress_sse(model_key: Optional[str] = Query(None)):
    """SSE endpoint for real-time download progress"""
    async def event_generator():
        try:
            last_sent = {}
            
            while True:
                await asyncio.sleep(0.5)  # Update every 500ms
                
                if model_key:
                    # Single model progress
                    with _progress_lock:
                        if model_key in _active_downloads:
                            progress = _active_downloads[model_key]
                        else:
                            progress = {"model": model_key, "status": "not_found"}
                    
                    # Only send if changed
                    if progress != last_sent.get(model_key):
                        last_sent[model_key] = progress
                        yield f"data: {json.dumps(progress)}\n\n"
                    
                    # Stop if completed or failed
                    if progress.get('status') in ['completed', 'failed', 'error']:
                        break
                else:
                    # All active downloads
                    all_downloads = get_active_downloads()
                    
                    if all_downloads != last_sent:
                        last_sent = all_downloads.copy()
                        yield f"data: {json.dumps(all_downloads)}\n\n"
        
        except asyncio.CancelledError:
            print("[SSE] Client disconnected")
        except Exception as e:
            print(f"[SSE] Error: {e}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/models/download/status")
async def download_status(model_key: Optional[str] = Query(None)):
    """Get current download status (polling alternative to SSE)"""
    if model_key:
        with _progress_lock:
            if model_key in _active_downloads:
                return _active_downloads[model_key]
            else:
                return {"model": model_key, "status": "not_found"}
    else:
        return get_active_downloads()

@app.post("/api/models/cancel")
async def cancel_download(request: Dict[str, str]):
    """Cancel ongoing download"""
    try:
        model_key = request.get('model_key')
        
        if not model_key:
            raise HTTPException(status_code=400, detail="model_key required")
        
        jarvis = get_jarvis()
        llm_manager = getattr(jarvis, 'llm_manager', None)
        
        if not llm_manager:
            raise HTTPException(status_code=503, detail="LLM Manager not available")
        
        # Try to cancel download
        downloader = getattr(llm_manager, 'downloader', None)
        if downloader:
            success = downloader.cancel_download(model_key)
        else:
            success = False
        
        # Update status
        if success:
            with _progress_lock:
                if model_key in _active_downloads:
                    _active_downloads[model_key]['status'] = 'cancelled'
        
        return {
            "success": success,
            "message": "Download cancelled" if success else "No active download found"
        }
    except Exception as e:
        print(f"[API] Cancel error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/models/variants")
async def get_model_variants(model_key: str = Query(...)):
    """Get all quantization variants for a model"""
    try:
        from core.model_registry import ModelRegistry
        
        variants = ModelRegistry.get_variants(model_key)
        
        # Parse variant info from URLs
        variant_list = []
        for url in variants:
            filename = url.split('/')[-1]
            # Extract quantization from filename
            quant = "unknown"
            for q in ["Q4_K_M", "Q4_K_S", "Q5_K_M", "Q6_K", "Q8_0"]:
                if q in filename:
                    quant = q
                    break
            
            variant_list.append({
                "name": filename,
                "url": url,
                "quantization": quant,
                "size_estimate": _estimate_size(quant)
            })
        
        return {
            "success": True,
            "model_key": model_key,
            "variants": variant_list
        }
    except Exception as e:
        print(f"[API] Error getting variants: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/models/delete")
async def delete_model(request: ModelDeleteRequest):
    """Delete a downloaded model"""
    try:
        jarvis = get_jarvis()
        llm_manager = getattr(jarvis, 'llm_manager', None)
        
        if not llm_manager:
            raise HTTPException(status_code=503, detail="LLM Manager not available")
        
        model_key = request.model_key
        
        # Find and delete model file
        models_dir = llm_manager.models_dir
        deleted = False
        
        for model_file in models_dir.glob("*.gguf"):
            if model_key in model_file.stem.lower():
                model_file.unlink()
                deleted = True
                print(f"[LLM] Deleted model: {model_file}")
                break
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Model {model_key} not found")
        
        return {
            "success": True,
            "message": f"Model {model_key} deleted successfully"
        }
    except Exception as e:
        print(f"[API] Delete error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def _estimate_size(quantization: str) -> str:
    """Estimate model size based on quantization"""
    size_map = {
        "Q4_K_M": "~4 GB",
        "Q4_K_S": "~3.5 GB",
        "Q5_K_M": "~5 GB",
        "Q6_K": "~6 GB",
        "Q8_0": "~8 GB"
    }
    return size_map.get(quantization, "Unknown")

# ============================================================================
# EXISTING API ENDPOINTS
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
            content={"status": "error", "message": "Internal server error"}
        )

@app.get("/api/status")
async def get_status():
    """Detaillierter System-Status"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_runtime_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/metrics")
async def get_metrics():
    """System-Metriken (CPU, RAM, Disk)"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_system_metrics(include_details=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/llm/status")
async def llm_status():
    """LLM Status und verfügbare Modelle"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_llm_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/llm/action")
async def llm_action(request: LLMActionRequest):
    """LLM Aktion (load/unload/download)"""
    try:
        jarvis = get_jarvis()
        
        # For download, redirect to new endpoint
        if request.action == "download":
            return await download_model(
                ModelDownloadRequest(
                    model_key=request.model,
                    quantization="Q4_K_M"
                )
            )
        
        result = jarvis.control_llm_model(request.action, request.model)
        return result
    except Exception as e:
        print(f"[API] LLM action error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/llm/load")
async def load_model(request: dict):
    """Lädt ein LLM-Modell"""
    try:
        jarvis = get_jarvis()
        model_key = request.get("model", "mistral")
        result = jarvis.control_llm_model("load", model_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/llm/unload")
async def unload_model():
    """Entlädt das aktuelle LLM-Modell"""
    try:
        jarvis = get_jarvis()
        result = jarvis.control_llm_model("unload")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/plugins")
async def get_plugins():
    """Liste aller Plugins"""
    try:
        jarvis = get_jarvis()
        return jarvis.get_plugin_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/chat/message")
async def chat_message(request: ChatMessageRequest):
    """Chat endpoint - sends message to command processor"""
    try:
        jarvis = get_jarvis()
        processor = getattr(jarvis, "command_processor", None)
        if not processor:
            raise HTTPException(status_code=503, detail="Command Processor nicht verfügbar")
        
        print(f"[API] Processing chat message: {request.text}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            _executor,
            processor.process_command,
            request.text
        )
        
        print(f"[API] Chat response: {response}")
        
        return {
            "success": True,
            "response": response,
            "text": response
        }
    except Exception as e:
        print(f"[API] Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/voice/start")
async def start_listening():
    """Startet die Spracherkennung"""
    try:
        jarvis = get_jarvis()
        success = jarvis.start_listening()
        return {"success": success, "listening": jarvis.listening}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/voice/stop")
async def stop_listening():
    """Stoppt die Spracherkennung"""
    try:
        jarvis = get_jarvis()
        success = jarvis.stop_listening()
        return {"success": success, "listening": jarvis.listening}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# WEBSOCKET
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket-Verbindung für Echtzeit-Updates"""
    await manager.connect(websocket)
    print("✅ WebSocket connected")
    
    try:
        while True:
            # Empfange Nachrichten vom Client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Verarbeite Nachricht
            msg_type = message.get("type")
            print(f"[WS] Received: {msg_type}")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif msg_type == "command":
                command_text = message.get("command", "")
                print(f"[WS] Processing command: {command_text}")
                
                try:
                    jarvis = get_jarvis()
                    processor = getattr(jarvis, "command_processor", None)
                    if processor:
                        # Run blocking command in thread pool
                        loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(
                            _executor,
                            processor.process_command,
                            command_text
                        )
                        
                        print(f"[WS] Command response: {response}")
                        
                        await websocket.send_json({
                            "type": "command_response",
                            "response": response
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Command Processor nicht verfügbar"
                        })
                        
                except Exception as e:
                    print(f"[WS] Command error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Internal server error"
                    })
            
            elif msg_type == "chat":
                chat_text = message.get("text", "")
                print(f"[WS] Processing chat: {chat_text}")
                
                try:
                    jarvis = get_jarvis()
                    processor = getattr(jarvis, "command_processor", None)
                    if processor:
                        # Run blocking command in thread pool
                        loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(
                            _executor,
                            processor.process_command,
                            chat_text
                        )
                        
                        print(f"[WS] Chat response: {response}")
                        
                        await websocket.send_json({
                            "type": "chat_response",
                            "text": response,
                            "response": response
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Command Processor nicht verfügbar"
                        })
                        
                except Exception as e:
                    print(f"[WS] Chat error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Internal server error"
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("❌ WebSocket disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
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
    _executor.shutdown(wait=False)