# 🔄 Migration: ImGui → React Web UI

**From:** Python DearPyGui Desktop App  
**To:** React + TypeScript + Tailwind Web UI  
**Date:** December 10, 2025

---

## 📋 Migration Overview

### Why Migrate?

✅ **Better UX** - Modern web interface with animations  
✅ **Cross-Platform** - Works on any device with browser  
✅ **Remote Access** - Control JARVIS from anywhere  
✅ **Better Design** - JARVIS futuristic theme with glows  
✅ **Easier Deployment** - No desktop dependencies

### What We're Replacing

❌ **Old:** `desktop/jarvis_imgui_app_full.py` (800 lines DearPyGui)  
✅ **New:** `frontend/` (React + TypeScript)

---

## 🚀 Step-by-Step Migration

### Phase 1: Backend API Setup (30 min)

#### 1.1 Create FastAPI Backend

**File:** `api/jarvis_api.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS FastAPI Backend for Web UI
Provides REST API + WebSocket for real-time communication
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="JARVIS API",
    description="AI Assistant Backend",
    version="2.0.0"
)

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global JARVIS instance (initialized in main.py)
jarvis_instance = None

def set_jarvis_instance(jarvis):
    """Set global JARVIS instance"""
    global jarvis_instance
    jarvis_instance = jarvis

# ==================== REST API Endpoints ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "version": "2.0.0",
        "jarvis_ready": jarvis_instance is not None
    }

@app.get("/api/system/metrics")
async def get_system_metrics():
    """Get system metrics for Dashboard"""
    if not jarvis_instance:
        return {"error": "JARVIS not initialized"}
    
    try:
        metrics = jarvis_instance.get_system_metrics()
        return metrics["summary"]
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return {"error": str(e)}

@app.get("/api/llm/status")
async def get_llm_status():
    """Get LLM model status"""
    if not jarvis_instance:
        return {"error": "JARVIS not initialized"}
    
    try:
        status = jarvis_instance.get_llm_status()
        return status
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/llm/models")
async def get_models():
    """Get available models"""
    if not jarvis_instance:
        return {"models": []}
    
    try:
        overview = jarvis_instance.llm_manager.get_model_overview()
        return {"models": overview}
    except Exception as e:
        return {"error": str(e)}

class LoadModelRequest(BaseModel):
    model_key: str

@app.post("/api/llm/load")
async def load_model(request: LoadModelRequest):
    """Load a specific model"""
    if not jarvis_instance:
        return {"error": "JARVIS not initialized"}
    
    try:
        jarvis_instance.llm_manager.load_model(request.model_key)
        return {"success": True, "model": request.model_key}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/llm/unload")
async def unload_model():
    """Unload all models"""
    if not jarvis_instance:
        return {"error": "JARVIS not initialized"}
    
    try:
        jarvis_instance.llm_manager.unload_model()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/plugins")
async def get_plugins():
    """Get plugin overview"""
    if not jarvis_instance:
        return {"plugins": []}
    
    try:
        plugins = jarvis_instance.get_plugin_overview()
        return {"plugins": plugins}
    except Exception as e:
        return {"error": str(e)}

class CommandRequest(BaseModel):
    text: str

@app.post("/api/chat/message")
async def send_message(request: CommandRequest):
    """Process chat message"""
    if not jarvis_instance:
        return {"error": "JARVIS not initialized"}
    
    try:
        response = jarvis_instance.command_processor.process_command(request.text)
        return {
            "success": True,
            "response": response or "Command executed."
        }
    except Exception as e:
        logger.error(f"Command error: {e}")
        return {"error": str(e)}

# ==================== WebSocket for Real-Time Updates ====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            msg_type = message.get("type")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif msg_type == "chat":
                # Process chat message
                text = message.get("text", "")
                if jarvis_instance:
                    response = jarvis_instance.command_processor.process_command(text)
                    await websocket.send_json({
                        "type": "chat_response",
                        "text": response
                    })
            
            elif msg_type == "voice_start":
                # Voice input started
                await manager.broadcast({
                    "type": "state_change",
                    "state": "listening"
                })
            
            elif msg_type == "voice_end":
                # Voice input ended
                await manager.broadcast({
                    "type": "state_change",
                    "state": "processing"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Background task for pushing metrics
async def metrics_broadcaster():
    """Push system metrics to all clients every 2 seconds"""
    while True:
        await asyncio.sleep(2)
        
        if jarvis_instance and len(manager.active_connections) > 0:
            try:
                metrics = jarvis_instance.get_system_metrics()
                await manager.broadcast({
                    "type": "metrics_update",
                    "data": metrics["summary"]
                })
            except Exception as e:
                logger.error(f"Metrics broadcast error: {e}")

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(metrics_broadcaster())
    logger.info("JARVIS API started")

# Serve React build (production)
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
```

#### 1.2 Update main.py

**File:** `main.py`

```python
# Add at top
from api.jarvis_api import app, set_jarvis_instance
import uvicorn
import threading

# In main() function, replace UI initialization:

def main():
    # ... existing JARVIS initialization ...
    
    jarvis = JarvisAssistant()
    
    # NEW: Set JARVIS instance for API
    set_jarvis_instance(jarvis)
    
    # OLD: Remove this
    # if settings.get("desktop_app", {}).get("enabled", False):
    #     gui = create_jarvis_imgui_gui_full(jarvis)
    #     gui.run()
    
    # NEW: Start FastAPI server
    print("🚀 Starting JARVIS Web UI...")
    print("📡 API: http://localhost:8000")
    print("🌐 Web UI: http://localhost:8000")
    
    # Run FastAPI in background thread
    def run_api():
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down JARVIS...")
        sys.exit(0)
```

---

### Phase 2: Frontend Setup (20 min)

#### 2.1 Copy Your React Files

```bash
# Create frontend directory
mkdir -p frontend/src

# Copy your files
cp Index.tsx frontend/src/pages/
cp VoiceVisualizer.tsx frontend/src/components/
cp index.css frontend/src/
cp main.tsx frontend/src/
# ... copy all other files
```

#### 2.2 Create API Client

**File:** `frontend/src/lib/api.ts`

```typescript
// API Client for JARVIS Backend

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  gpu_utilization: number;
  cpu_count: number;
  memory_used_gb: number;
  memory_total_gb: number;
  gpu_name: string;
  cpu_temp: number;
  power_usage: number;
}

export interface Model {
  key: string;
  available: boolean;
  downloaded: boolean;
  filename: string;
  size_mb: number;
  context_length: number;
  display_name: string;
  description: string;
}

export interface LLMStatus {
  current: string | null;
  loaded: string[];
  available: Record<string, Model>;
}

class JarvisAPI {
  private ws: WebSocket | null = null;
  private wsHandlers: Map<string, Function[]> = new Map();

  // REST API Methods
  async getHealth() {
    const res = await fetch(`${API_BASE}/api/health`);
    return res.json();
  }

  async getMetrics(): Promise<SystemMetrics> {
    const res = await fetch(`${API_BASE}/api/system/metrics`);
    return res.json();
  }

  async getLLMStatus(): Promise<LLMStatus> {
    const res = await fetch(`${API_BASE}/api/llm/status`);
    return res.json();
  }

  async getModels() {
    const res = await fetch(`${API_BASE}/api/llm/models`);
    return res.json();
  }

  async loadModel(modelKey: string) {
    const res = await fetch(`${API_BASE}/api/llm/load`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_key: modelKey })
    });
    return res.json();
  }

  async unloadModel() {
    const res = await fetch(`${API_BASE}/api/llm/unload`, {
      method: 'POST'
    });
    return res.json();
  }

  async getPlugins() {
    const res = await fetch(`${API_BASE}/api/plugins`);
    return res.json();
  }

  async sendMessage(text: string) {
    const res = await fetch(`${API_BASE}/api/chat/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    return res.json();
  }

  // WebSocket Methods
  connectWebSocket() {
    if (this.ws) return;

    const wsUrl = API_BASE.replace('http', 'ws');
    this.ws = new WebSocket(`${wsUrl}/ws`);

    this.ws.onopen = () => {
      console.log('🔌 WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const handlers = this.wsHandlers.get(message.type) || [];
      handlers.forEach(handler => handler(message));
    };

    this.ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      this.ws = null;
      // Reconnect after 3 seconds
      setTimeout(() => this.connectWebSocket(), 3000);
    };
  }

  onWebSocketMessage(type: string, handler: Function) {
    if (!this.wsHandlers.has(type)) {
      this.wsHandlers.set(type, []);
    }
    this.wsHandlers.get(type)!.push(handler);
  }

  sendWebSocketMessage(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}

export const api = new JarvisAPI();
```

#### 2.3 Update Index.tsx to Use API

**File:** `frontend/src/pages/Index.tsx`

```typescript
// Add imports
import { api } from '@/lib/api';
import { useEffect, useState } from 'react';

// Add state
const [metrics, setMetrics] = useState(null);
const [llmStatus, setLLMStatus] = useState(null);

// Connect WebSocket on mount
useEffect(() => {
  api.connectWebSocket();
  
  // Listen for metrics updates
  api.onWebSocketMessage('metrics_update', (msg) => {
    setMetrics(msg.data);
  });
  
  // Listen for state changes
  api.onWebSocketMessage('state_change', (msg) => {
    setCoreState(msg.state);
  });
  
  // Initial data fetch
  fetchInitialData();
}, []);

const fetchInitialData = async () => {
  const [metricsData, statusData] = await Promise.all([
    api.getMetrics(),
    api.getLLMStatus()
  ]);
  setMetrics(metricsData);
  setLLMStatus(statusData);
};

// Send message via API
const handleSendMessage = async () => {
  if (!input.trim()) return;
  
  const userMessage = input;
  setInput('');
  
  // Add user message to chat
  setMessages(prev => [...prev, {
    role: 'user',
    content: userMessage
  }]);
  
  setCoreState('processing');
  
  // Send to API
  const response = await api.sendMessage(userMessage);
  
  // Add assistant response
  setMessages(prev => [...prev, {
    role: 'assistant',
    content: response.response
  }]);
  
  setCoreState('idle');
};
```

---

### Phase 3: Build & Deploy (15 min)

#### 3.1 Frontend Build

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build
# Creates: frontend/dist/
```

#### 3.2 Test Locally

```bash
# Terminal 1: Start Python backend
python main.py
# → API at http://localhost:8000

# Terminal 2: Dev mode (optional)
cd frontend
npm run dev
# → Dev server at http://localhost:5173
```

#### 3.3 Production Mode

```bash
# Just run Python - it serves React build
python main.py

# Open browser
xdg-open http://localhost:8000  # Linux
open http://localhost:8000      # macOS
start http://localhost:8000     # Windows
```

---

### Phase 4: Remove Old UI (5 min)

#### 4.1 Delete ImGui Files

```bash
# Backup first
mkdir -p backup/old-ui
cp desktop/jarvis_imgui_app_full.py backup/old-ui/

# Remove old UI
rm desktop/jarvis_imgui_app_full.py
rm desktop/jarvis_imgui_app.py

# Remove ImGui dependencies from requirements.txt
sed -i '/dearpygui/d' requirements.txt
```

#### 4.2 Update data/settings.json

```json
{
  "desktop_app": {
    "enabled": false
  },
  "web_ui": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

#### 4.3 Update README.md

```markdown
## 🚀 Quick Start

### Run JARVIS Web UI

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start JARVIS (includes web server)
python main.py

# 3. Open browser
# → http://localhost:8000
```

### Development Mode

```bash
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend (hot reload)
cd frontend
npm run dev
```
```

---

## 📁 New Project Structure

```
JarvisCore/
├── api/
│   └── jarvis_api.py          # FastAPI backend
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Index.tsx      # Main page
│   │   ├── components/
│   │   │   ├── VoiceVisualizer.tsx
│   │   │   └── ...
│   │   ├── lib/
│   │   │   └── api.ts         # API client
│   │   ├── hooks/
│   │   ├── main.tsx
│   │   └── index.css
│   ├── dist/                  # Build output (gitignore)
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── core/                      # Python backend (unchanged)
├── plugins/
├── models/
├── data/
├── main.py                    # Updated with FastAPI
└── requirements.txt           # Add fastapi, uvicorn
```

---

## ✅ Migration Checklist

### Backend
- [ ] Create `api/jarvis_api.py`
- [ ] Update `main.py` with FastAPI
- [ ] Add `fastapi`, `uvicorn`, `websockets` to requirements.txt
- [ ] Test REST endpoints: `/api/health`, `/api/system/metrics`
- [ ] Test WebSocket: `/ws`

### Frontend
- [ ] Copy React files to `frontend/src/`
- [ ] Create `api.ts` client
- [ ] Update `Index.tsx` with API calls
- [ ] Configure Vite for production build
- [ ] Test in dev mode (`npm run dev`)
- [ ] Build for production (`npm run build`)

### Cleanup
- [ ] Backup old UI files
- [ ] Remove `desktop/jarvis_imgui_app*.py`
- [ ] Remove `dearpygui` from requirements.txt
- [ ] Update `data/settings.json`
- [ ] Update `README.md`
- [ ] Test production mode

### Documentation
- [ ] Update architecture docs
- [ ] Add API documentation (Swagger at `/docs`)
- [ ] Update screenshots
- [ ] Add deployment guide

---

## 🐛 Troubleshooting

### Issue: CORS Errors

**Solution:** Check `allow_origins` in `jarvis_api.py`:
```python
allow_origins=["http://localhost:5173", "http://localhost:3000"]
```

### Issue: WebSocket Won't Connect

**Check:**
1. Backend running? `curl http://localhost:8000/api/health`
2. Firewall blocking port 8000?
3. Check browser console for errors

### Issue: API Returns "JARVIS not initialized"

**Fix:** Ensure `set_jarvis_instance(jarvis)` is called in `main.py`

### Issue: Frontend Build Fails

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 🚀 Next Steps

### Enhancements
1. **Authentication** - Add JWT tokens
2. **Multi-user** - User sessions
3. **Mobile App** - React Native version
4. **PWA** - Install as app
5. **Voice Input** - Browser speech recognition
6. **File Upload** - Document analysis

### Deployment
1. **Docker** - Containerize app
2. **NGINX** - Reverse proxy
3. **SSL** - HTTPS with Let's Encrypt
4. **Cloud** - Deploy to AWS/Azure/GCP

---

## 📚 Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Vite Docs:** https://vitejs.dev/
- **WebSocket Guide:** https://fastapi.tiangolo.com/advanced/websockets/
- **React TypeScript:** https://react-typescript-cheatsheet.netlify.app/

---

**Status:** ✅ Ready for Implementation  
**Estimated Time:** 1-2 hours  
**Difficulty:** Medium
