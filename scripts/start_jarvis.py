#!/usr/bin/env python3
"""
J.A.R.V.I.S. Core - Unified Launcher

Startet automatisch:
1. Python Backend (API + WebSocket)
2. Desktop UI (Wails App)

Usage:
    python scripts/start_jarvis.py              # Production Mode
    python scripts/start_jarvis.py --dev        # Development Mode
    python scripts/start_jarvis.py --build      # Build Desktop Binary
"""

import sys
import os
import subprocess
import time
import signal
import platform
import argparse
import logging
from pathlib import Path

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fix paths - script is now in scripts/
REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)

# Globale Prozesse
backend_process = None
desktop_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("⚠️  Shutdown signal received...")
    cleanup()
    sys.exit(0)

def cleanup():
    """Kill all child processes"""
    global backend_process, desktop_process
    
    if desktop_process:
        logger.info("🛡️  Stopping Desktop UI...")
        try:
            desktop_process.terminate()
            desktop_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("⚠️  Desktop UI did not stop gracefully, forcing kill")
            desktop_process.kill()
        except Exception as e:
            logger.error(f"❌ Failed to stop Desktop UI: {e}")
            try:
                desktop_process.kill()
            except Exception as kill_error:
                logger.error(f"❌ Force kill failed: {kill_error}")
    
    if backend_process:
        logger.info("🛡️  Stopping Python Backend...")
        try:
            backend_process.terminate()
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("⚠️  Backend did not stop gracefully, forcing kill")
            backend_process.kill()
        except Exception as e:
            logger.error(f"❌ Failed to stop Backend: {e}")
            try:
                backend_process.kill()
            except Exception as kill_error:
                logger.error(f"❌ Force kill failed: {kill_error}")
    
    logger.info("✅ J.A.R.V.I.S. Core stopped.")

def check_dependencies():
    """Check if all required tools are installed"""
    logger.info("🔍 Checking dependencies...")
    
    # Check Python
    if sys.version_info < (3, 10):
        logger.error("❌ Python 3.10+ required!")
        return False
    
    # Check Go (für Wails)
    try:
        result = subprocess.run(['go', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ {result.stdout.strip()}")
        else:
            logger.warning("⚠️  Go not found - Desktop UI will not work")
    except FileNotFoundError:
        logger.warning("⚠️  Go not installed - skipping Desktop UI")
    except Exception as e:
        logger.warning(f"⚠️  Error checking Go: {e}")
    
    # Check Wails
    try:
        result = subprocess.run(['wails', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ {result.stdout.strip()}")
        else:
            logger.warning("⚠️  Wails not found")
    except FileNotFoundError:
        logger.warning("⚠️  Wails not installed - run: go install github.com/wailsapp/wails/v2/cmd/wails@latest")
    except Exception as e:
        logger.warning(f"⚠️  Error checking Wails: {e}")
    
    return True

def start_backend():
    """Start Python Backend"""
    global backend_process
    
    logger.info("🚀 Starting Python Backend...")
    
    # main.py starten
    backend_process = subprocess.Popen(
        [sys.executable, 'main.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Warte auf Backend-Start (check für "API: http://127.0.0.1:5050")
    logger.info("⏳ Waiting for backend to start...")
    timeout = 30
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        line = backend_process.stdout.readline()
        if line:
            print(f"  [Backend] {line.strip()}")
            if "API: http://127.0.0.1:5050" in line or "Backend gestartet" in line:
                logger.info("✅ Backend ready!")
                return True
        
        if backend_process.poll() is not None:
            logger.error("❌ Backend crashed during startup!")
            return False
        
        time.sleep(0.1)
    
    logger.error("❌ Backend startup timeout!")
    return False

def start_desktop_dev():
    """Start Desktop UI in Development Mode (wails dev)"""
    global desktop_process
    
    logger.info("🚀 Starting Desktop UI (Development Mode)...")
    
    desktop_dir = REPO_ROOT / 'desktop'
    if not desktop_dir.exists():
        logger.error("❌ desktop/ directory not found!")
        return False
    
    # Wails Dev Mode
    desktop_process = subprocess.Popen(
        ['wails', 'dev'],
        cwd=desktop_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    logger.info("✅ Desktop UI started in dev mode")
    logger.info("👀 Check terminal for Wails output")
    return True

def start_desktop_production():
    """Start Desktop UI from binary"""
    global desktop_process
    
    logger.info("🚀 Starting Desktop UI (Production Binary)...")
    
    # Platform-specific binary path
    system = platform.system()
    if system == 'Windows':
        binary = REPO_ROOT / 'desktop/build/bin/jarvis-desktop.exe'
    elif system == 'Darwin':  # macOS
        binary = REPO_ROOT / 'desktop/build/bin/jarvis-desktop.app/Contents/MacOS/jarvis-desktop'
    else:  # Linux
        binary = REPO_ROOT / 'desktop/build/bin/jarvis-desktop'
    
    if not binary.exists():
        logger.error(f"❌ Binary not found: {binary}")
        logger.info("💡 Run: python scripts/start_jarvis.py --build")
        return False
    
    # Start binary
    desktop_process = subprocess.Popen(
        [str(binary)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    logger.info("✅ Desktop UI started")
    return True

def build_desktop():
    """Build Desktop UI binary"""
    logger.info("🔨 Building Desktop UI...")
    
    desktop_dir = REPO_ROOT / 'desktop'
    if not desktop_dir.exists():
        logger.error("❌ desktop/ directory not found!")
        return False
    
    # Check if Makefile exists
    makefile = desktop_dir / 'Makefile'
    if makefile.exists():
        logger.info("🛠️  Using Makefile...")
        result = subprocess.run(
            ['make', 'build'],
            cwd=desktop_dir
        )
    else:
        logger.info("🛠️  Using wails build...")
        result = subprocess.run(
            ['wails', 'build'],
            cwd=desktop_dir
        )
    
    if result.returncode == 0:
        logger.info("✅ Build successful!")
        
        # Show binary location
        system = platform.system()
        if system == 'Windows':
            binary = 'desktop/build/bin/jarvis-desktop.exe'
        elif system == 'Darwin':
            binary = 'desktop/build/bin/jarvis-desktop.app'
        else:
            binary = 'desktop/build/bin/jarvis-desktop'
        
        logger.info(f"📦 Binary: {binary}")
        return True
    else:
        logger.error("❌ Build failed!")
        return False

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='J.A.R.V.I.S. Core Unified Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start_jarvis.py              # Start in production mode (uses binary)
  python scripts/start_jarvis.py --dev        # Start in development mode (hot-reload)
  python scripts/start_jarvis.py --build      # Build desktop binary
  python scripts/start_jarvis.py --backend    # Start backend only
        """
    )
    parser.add_argument('--dev', action='store_true', help='Start in development mode')
    parser.add_argument('--build', action='store_true', help='Build desktop binary and exit')
    parser.add_argument('--backend', action='store_true', help='Start backend only (no desktop UI)')
    args = parser.parse_args()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Banner
    print("┌" + "─" * 60 + "┐")
    print("│" + " " * 15 + "J.A.R.V.I.S. Core Launcher" + " " * 18 + "│")
    print("│" + " " * 20 + "v1.0.0" + " " * 33 + "│")
    print("└" + "─" * 60 + "┘")
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Build mode
    if args.build:
        if build_desktop():
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Start Backend
    if not start_backend():
        logger.error("❌ Failed to start backend!")
        cleanup()
        sys.exit(1)
    
    # Backend-only mode
    if args.backend:
        logger.info("🎯 Backend-only mode - Press Ctrl+C to stop")
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            pass
        cleanup()
        sys.exit(0)
    
    # Wait a bit for backend to fully initialize
    time.sleep(2)
    
    # Start Desktop UI
    if args.dev:
        if not start_desktop_dev():
            logger.error("❌ Failed to start desktop UI!")
            cleanup()
            sys.exit(1)
    else:
        if not start_desktop_production():
            logger.error("❌ Failed to start desktop UI!")
            logger.info("💡 Trying development mode...")
            if not start_desktop_dev():
                logger.error("❌ Both production and dev mode failed!")
                cleanup()
                sys.exit(1)
    
    # Success
    print()
    logger.info("✅ J.A.R.V.I.S. Core is running!")
    logger.info("🎯 Backend:    http://127.0.0.1:5050")
    logger.info("🎯 WebSocket:  ws://127.0.0.1:8765")
    logger.info("💻 Desktop UI: Running")
    print()
    logger.info("⚠️  Press Ctrl+C to stop")
    print()
    
    # Keep running and monitor processes
    try:
        while True:
            # Check if backend crashed
            if backend_process.poll() is not None:
                logger.error("❌ Backend process died!")
                break
            
            # Check if desktop crashed
            if desktop_process and desktop_process.poll() is not None:
                logger.error("❌ Desktop UI process died!")
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("⚠️  Shutdown requested...")
    
    # Cleanup
    cleanup()
    sys.exit(0)

if __name__ == '__main__':
    main()
