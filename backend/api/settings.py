"""Settings API - Configuration Management"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import json
from pathlib import Path

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Settings Models
class LlamaSettings(BaseModel):
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    top_k: int = Field(40, ge=0, le=100)
    repeat_penalty: float = Field(1.1, ge=1.0, le=2.0)
    max_tokens: int = Field(512, ge=128, le=32768)
    context_window: int = Field(8192, ge=1024, le=32768)
    n_gpu_layers: int = Field(-1, ge=-1, le=128)
    n_threads: int = Field(8, ge=1, le=64)
    stream_mode: bool = False

class UISettings(BaseModel):
    theme: str = "dark"
    fontSize: str = "medium"
    autoScroll: bool = True
    notifications: bool = True
    soundEffects: bool = False

class APISettings(BaseModel):
    backend_url: str = "http://localhost:5050"
    ws_url: str = "ws://localhost:5050"
    timeout: int = 30000
    retry_attempts: int = 3
    api_key: Optional[str] = None

class AllSettings(BaseModel):
    llama: LlamaSettings
    ui: UISettings
    api: APISettings
    system_prompt: str = "Du bist JARVIS, ein hilfreicher deutscher KI-Assistent."

# Global settings storage
CONFIG_DIR = Path("config")
CONFIG_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# Current settings
current_settings = AllSettings(
    llama=LlamaSettings(),
    ui=UISettings(),
    api=APISettings(),
    system_prompt="Du bist JARVIS, ein hilfreicher deutscher KI-Assistent. Antworte präzise und freundlich."
)

def load_settings():
    """Load settings from disk"""
    global current_settings
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                current_settings = AllSettings(**data)
                print(f"[INFO] Settings loaded from {SETTINGS_FILE}")
        except Exception as e:
            print(f"[ERROR] Failed to load settings: {e}")

def save_settings():
    """Save settings to disk"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_settings.dict(), f, ensure_ascii=False, indent=2)
        print(f"[INFO] Settings saved to {SETTINGS_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to save settings: {e}")

# Load settings on module import
load_settings()

# API Endpoints

@router.get("/llama")
async def get_llama_settings() -> LlamaSettings:
    """Get current llama.cpp inference settings"""
    return current_settings.llama

@router.post("/llama")
async def update_llama_settings(settings: LlamaSettings):
    """Update llama.cpp inference settings"""
    global current_settings
    
    # Update settings
    current_settings.llama = settings
    save_settings()
    
    # Apply to llama_runtime if model is loaded
    from core.llama_inference import llama_runtime
    if llama_runtime.is_loaded:
        llama_runtime.default_temperature = settings.temperature
        llama_runtime.default_top_p = settings.top_p
        llama_runtime.default_top_k = settings.top_k
        llama_runtime.default_repeat_penalty = settings.repeat_penalty
        llama_runtime.default_max_tokens = settings.max_tokens
        # Note: n_ctx, n_gpu_layers require model reload
    
    return {"success": True, "message": "Settings updated successfully"}

@router.get("/llama/info")
async def get_llama_info():
    """Get information about loaded model"""
    from core.llama_inference import llama_runtime
    
    if not llama_runtime.is_loaded:
        raise HTTPException(status_code=404, detail="No model loaded")
    
    return {
        "model": llama_runtime.model_name,
        "context_window": llama_runtime.n_ctx,
        "device": llama_runtime.device,
        "gpu_layers": llama_runtime.n_gpu_layers,
        "max_layers": 32  # TODO: Get from model metadata
    }

@router.get("/ui")
async def get_ui_settings() -> UISettings:
    """Get UI settings"""
    return current_settings.ui

@router.post("/ui")
async def update_ui_settings(settings: UISettings):
    """Update UI settings"""
    global current_settings
    current_settings.ui = settings
    save_settings()
    return {"success": True, "message": "UI settings updated"}

@router.get("/api")
async def get_api_settings() -> APISettings:
    """Get API settings"""
    return current_settings.api

@router.post("/api")
async def update_api_settings(settings: APISettings):
    """Update API settings"""
    global current_settings
    current_settings.api = settings
    save_settings()
    return {"success": True, "message": "API settings updated"}

@router.get("/all")
async def get_all_settings() -> AllSettings:
    """Get all settings"""
    return current_settings

@router.post("/all")
async def update_all_settings(settings: AllSettings):
    """Update all settings"""
    global current_settings
    current_settings = settings
    save_settings()
    return {"success": True, "message": "All settings updated"}

@router.post("/reset")
async def reset_settings():
    """Reset all settings to defaults"""
    global current_settings
    current_settings = AllSettings(
        llama=LlamaSettings(),
        ui=UISettings(),
        api=APISettings(),
        system_prompt="Du bist JARVIS, ein hilfreicher deutscher KI-Assistent. Antworte präzise und freundlich."
    )
    save_settings()
    return {"success": True, "message": "Settings reset to defaults"}

@router.get("/system-prompt")
async def get_system_prompt() -> str:
    """Get system prompt"""
    return current_settings.system_prompt

@router.post("/system-prompt")
async def update_system_prompt(prompt: str):
    """Update system prompt"""
    global current_settings
    current_settings.system_prompt = prompt
    save_settings()
    return {"success": True, "message": "System prompt updated"}
