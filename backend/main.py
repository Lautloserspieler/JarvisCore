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

app = FastAPI(title="JARVIS Core API", version="1.0.1")

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

print("[INFO] JARVIS Core API initializing...")

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

# Health API  
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.1",
        "llama_cpp": llama_runtime.get_status()
    }

# Models API
@app.get("/api/models")
async def get_models():
    """Get all available models with status"""
    # Basic models (diese sollten später aus llm_manager kommen)
    models = [
        {
            "id": "mistral",
            "name": "Mistral 7B Nemo",
            "description": "Code, technische Details, Systembefehle",
            "size": "7.5 GB",
            "downloaded": Path("models/llm/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf").exists(),
            "loaded": llama_runtime.is_loaded and llama_runtime.model_name == "mistral"
        },
        {
            "id": "qwen",
            "name": "Qwen 2.5 7B",
            "description": "Vielseitig, mehrsprachig, balanciert",
            "size": "5.2 GB",
            "downloaded": Path("models/llm/Qwen2.5-7B-Instruct-Q4_K_M.gguf").exists(),
            "loaded": llama_runtime.is_loaded and llama_runtime.model_name == "qwen"
        },
        {
            "id": "deepseek",
            "name": "DeepSeek R1 8B",
            "description": "Analysen, Reasoning, komplexe Daten",
            "size": "6.9 GB",
            "downloaded": Path("models/llm/deepseek-r1-distill-llama-8b-q4_k_m.gguf").exists(),
            "loaded": llama_runtime.is_loaded and llama_runtime.model_name == "deepseek"
        }
    ]
    return models

@app.get("/api/models/active")
async def get_active_model():
    """Get currently active model"""
    status = llama_runtime.get_status()
    
    if status['loaded']:
        return {
            "id": status['model_name'],
            "name": status['model_name'],
            "loaded": True,
            "device": status['device'],
            "context_window": status['context_window']
        }
    
    return {"message": "Kein Modell aktiv", "loaded": False}

@app.post("/api/models/{model_id}/load")
async def load_model(model_id: str):
    """Load a model into memory"""
    print(f"[INFO] Load request for model: {model_id}")
    
    # Model paths (sollten später aus llm_manager kommen)
    model_files = {
        "mistral": "models/llm/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "qwen": "models/llm/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "deepseek": "models/llm/deepseek-r1-distill-llama-8b-q4_k_m.gguf"
    }
    
    if model_id not in model_files:
        return {"success": False, "message": "Modell nicht gefunden"}
    
    model_path = Path(model_files[model_id])
    
    if not model_path.exists():
        return {
            "success": False,
            "message": f"Modell-Datei nicht gefunden: {model_path}"
        }
    
    try:
        success = llama_runtime.load_model(
            model_path=model_path,
            model_name=model_id,
            n_ctx=8192,  # 8K context
            verbose=False
        )
        
        if success:
            return {
                "success": True,
                "message": f"Modell {model_id} geladen",
                "model": llama_runtime.get_status()
            }
        else:
            return {
                "success": False,
                "message": "Fehler beim Laden des Modells"
            }
            
    except Exception as e:
        print(f"[ERROR] Model load failed: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/models/unload")
async def unload_model():
    """Unload current model"""
    print("[INFO] Unload model request")
    
    try:
        success = llama_runtime.unload_model()
        return {"success": success, "message": "Modell entladen"}
    except Exception as e:
        print(f"[ERROR] Model unload failed: {e}")
        return {"success": False, "message": str(e)}

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

@app.get("/")
async def root():
    return {
        "message": "JARVIS Core API v1.0.1",
        "status": "online",
        "llama_cpp": llama_runtime.get_status(),
        "endpoints": {
            "websocket": "/ws",
            "docs": "/docs",
            "health": "/api/health",
            "models": "/api/models"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║          JARVIS Core Backend v1.0.1                  ║
    ║         Just A Rather Very Intelligent System        ║
    ║         with llama.cpp local inference               ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    print("[INFO] Starting JARVIS Core API...")
    print(f"[INFO] llama.cpp available: {llama_runtime.get_status()['available']}")
    print(f"[INFO] Device: {llama_runtime.device}")
    
    # Starte Backend
    uvicorn.run(app, host="0.0.0.0", port=5050)
