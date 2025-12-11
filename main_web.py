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

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import JARVIS core components
try:
    from core.system_control import SystemControl
    from core.knowledge_manager import KnowledgeManager
    from core.command_processor import CommandProcessor
    from core.plugin_manager import PluginManager
    from core.text_to_speech import TextToSpeech
    from core.llm_manager import LLMManager
    from config.settings import Settings
except ImportError as e:
    logger.error(f"❌ Error importing JARVIS components: {e}")
    print("❌ Error: Could not import JARVIS components")
    print("Make sure you're in the JarvisCore directory and all dependencies are installed")
    sys.exit(1)

# Import API
try:
    from api.jarvis_api import app, set_jarvis_instance
except ImportError as e:
    logger.error(f"❌ Error importing jarvis_api: {e}")
    print("❌ Error: Could not import jarvis_api")
    print("Make sure api/jarvis_api.py exists")
    sys.exit(1)

class JarvisAssistant:
    """Wrapper class that provides unified interface for Web API"""
    def __init__(self):
        logger.info("Initializing JARVIS components...")
        
        # Load settings
        self.settings = Settings()
        
        # Initialize core components
        self.system_control = SystemControl(self.settings)
        self.knowledge_manager = KnowledgeManager()
        self.text_to_speech = TextToSpeech(self.settings)
        self.llm_manager = LLMManager(settings=self.settings)
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager()
        
        # Initialize command processor
        self.command_processor = CommandProcessor(
            knowledge_manager=self.knowledge_manager,
            system_control=self.system_control,
            tts=self.text_to_speech,
            plugin_manager=self.plugin_manager,
            llm_manager=self.llm_manager,
            settings=self.settings
        )
        
        logger.info("✅ All JARVIS components initialized")
    
    def get_system_metrics(self):
        """Get system metrics for dashboard"""
        try:
            if hasattr(self.system_control, 'get_system_metrics'):
                return self.system_control.get_system_metrics()
            return {"summary": {}}
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {"summary": {}}
    
    def get_llm_status(self):
        """Get LLM status"""
        try:
            if hasattr(self.llm_manager, 'get_status'):
                return self.llm_manager.get_status()
            return {"current": None, "available": []}
        except Exception as e:
            logger.error(f"Error getting LLM status: {e}")
            return {"current": None, "available": []}
    
    def get_plugin_overview(self):
        """Get plugin overview"""
        try:
            if hasattr(self.plugin_manager, 'get_plugin_list'):
                return self.plugin_manager.get_plugin_list()
            return []
        except Exception as e:
            logger.error(f"Error getting plugin overview: {e}")
            return []

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
        logger.error(f"❌ Failed to initialize JARVIS: {e}", exc_info=True)
        print(f"❌ Failed to initialize JARVIS: {e}")
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