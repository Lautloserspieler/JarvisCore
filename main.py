#!/usr/bin/env python3
"""
JARVIS Core System - Main Entry Point

This script automatically starts the JARVIS backend and frontend.
It redirects to backend/main.py for the actual implementation.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Change to backend directory
os.chdir(backend_dir)

# Import and run backend main
try:
    from main import *
    
    if __name__ == "__main__":
        import uvicorn
        
        print("""
    ╔══════════════════════════════════════════════════════╗
    ║          JARVIS Core Backend v1.0.0                  ║
    ║         Just A Rather Very Intelligent System        ║
    ╚══════════════════════════════════════════════════════╝
        """)
        
        from core.logger import log_info
        log_info("Starting JARVIS Core API...")
        
        # Starte Frontend in separatem Thread
        import threading
        frontend_thread = threading.Thread(target=start_frontend, daemon=True)
        frontend_thread.start()
        
        # Warte kurz damit Frontend-Meldung sichtbar ist
        import time
        time.sleep(2)
        
        # Starte Backend
        uvicorn.run(app, host="0.0.0.0", port=5050)
        
except ImportError as e:
    print(f"\n❌ Error: Could not import backend/main.py")
    print(f"   {e}")
    print(f"\n👉 Please run from the backend directory instead:")
    print(f"   cd backend")
    print(f"   python main.py\n")
    sys.exit(1)
