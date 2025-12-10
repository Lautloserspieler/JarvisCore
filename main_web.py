#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS Main Entry Point - Web UI Version

Replaces old ImGui desktop app with React Web UI.

Usage:
    python main_web.py
    
Then open: http://localhost:8000
"""

import sys
import os
import time
import logging
import threading
import uvicorn
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import JARVIS core
try:
    from core.jarvis import JarvisAssistant
except ImportError:
    print("❌ Error: Could not import JarvisAssistant")
    print("Make sure you're in the JarvisCore directory")
    sys.exit(1)

# Import API
try:
    from api.jarvis_api import app, set_jarvis_instance
except ImportError:
    print("❌ Error: Could not import jarvis_api")
    print("Make sure api/jarvis_api.py exists")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point - Initialize JARVIS and start web server
    """
    print("🤖" + "="*60)
    print("  J.A.R.V.I.S. - Just A Rather Very Intelligent System")
    print("  Version 2.0.0 - Web UI Edition")
    print("="*61)
    print()
    
    # Initialize JARVIS
    logger.info("🚀 Initializing JARVIS...")
    try:
        jarvis = JarvisAssistant()
        logger.info("✅ JARVIS initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize JARVIS: {e}")
        sys.exit(1)
    
    # Register JARVIS with API
    set_jarvis_instance(jarvis)
    
    # Check if frontend build exists
    frontend_dist = Path("frontend/dist")
    if not frontend_dist.exists():
        logger.warning("⚠️  Frontend build not found!")
        logger.warning("Run: cd frontend && npm install && npm run build")
        logger.info("API will still work, but no web UI.")
    else:
        logger.info("✅ Frontend build found")
    
    # Start FastAPI server
    print()
    print("🌐 Starting Web Server...")
    print("="*61)
    print(f"📡 API Docs:  http://localhost:8000/api/docs")
    print(f"📡 API:       http://localhost:8000/api/")
    print(f"🌐 Web UI:    http://localhost:8000/")
    print(f"🔌 WebSocket: ws://localhost:8000/ws")
    print("="*61)
    print()
    print("🟢 Server running. Press Ctrl+C to stop.")
    print()
    
    # Run server
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=False  # Reduce noise
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down JARVIS...")
        sys.exit(0)

if __name__ == "__main__":
    main()
