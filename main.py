#!/usr/bin/env python3
"""
JARVIS Core - Unified Startup Script
Starts both Backend (FastAPI) and Frontend (Vite) simultaneously
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from typing import List

# Colors for terminal output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Print JARVIS ASCII banner"""
    banner = f"""{Colors.CYAN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════╗
    ║              JARVIS CORE SYSTEM v1.0.0               ║
    ║         Just A Rather Very Intelligent System        ║
    ╚═══════════════════════════════════════════════════════╝
    {Colors.END}"""
    print(banner)

def check_requirements():
    """Check if all required dependencies are available"""
    print(f"{Colors.YELLOW}[CHECK]{Colors.END} Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"{Colors.RED}[ERROR]{Colors.END} Python 3.8 or higher is required")
        sys.exit(1)
    
    # Check if backend directory exists
    backend_path = Path("backend")
    if not backend_path.exists():
        print(f"{Colors.RED}[ERROR]{Colors.END} Backend directory not found")
        sys.exit(1)
    
    # Check if frontend directory exists
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print(f"{Colors.RED}[ERROR]{Colors.END} Frontend directory not found")
        sys.exit(1)
    
    # Check if node_modules exists
    node_modules = frontend_path / "node_modules"
    if not node_modules.exists():
        print(f"{Colors.YELLOW}[WARN]{Colors.END} Frontend dependencies not installed")
        print(f"{Colors.BLUE}[INFO]{Colors.END} Running: npm install...")
        subprocess.run(["npm", "install"], cwd="frontend", check=True)
    
    # Check if Python packages are installed
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print(f"{Colors.YELLOW}[WARN]{Colors.END} Backend dependencies not installed")
        print(f"{Colors.BLUE}[INFO]{Colors.END} Running: pip install -r requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"], check=True)
    
    print(f"{Colors.GREEN}[OK]{Colors.END} All requirements satisfied\n")

class ProcessManager:
    """Manage backend and frontend processes"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = False
    
    def start_backend(self):
        """Start FastAPI backend server"""
        print(f"{Colors.BLUE}[BACKEND]{Colors.END} Starting FastAPI server...")
        
        backend_cmd = [
            sys.executable,
            "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        
        process = subprocess.Popen(
            backend_cmd,
            cwd="backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        self.processes.append(process)
        print(f"{Colors.GREEN}[BACKEND]{Colors.END} Server started on {Colors.CYAN}http://localhost:8000{Colors.END}")
        print(f"{Colors.GREEN}[BACKEND]{Colors.END} WebSocket on {Colors.CYAN}ws://localhost:8000/ws{Colors.END}")
        print(f"{Colors.GREEN}[BACKEND]{Colors.END} API Docs: {Colors.CYAN}http://localhost:8000/docs{Colors.END}\n")
        
        return process
    
    def start_frontend(self):
        """Start Vite development server"""
        print(f"{Colors.MAGENTA}[FRONTEND]{Colors.END} Starting Vite dev server...")
        
        frontend_cmd = ["npm", "run", "dev"]
        
        process = subprocess.Popen(
            frontend_cmd,
            cwd="frontend",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        self.processes.append(process)
        print(f"{Colors.GREEN}[FRONTEND]{Colors.END} Server started on {Colors.CYAN}http://localhost:8080{Colors.END}\n")
        
        return process
    
    def monitor_processes(self):
        """Monitor process outputs"""
        print(f"{Colors.BOLD}{Colors.GREEN}[JARVIS]{Colors.END} System is online!")
        print(f"{Colors.BOLD}═══════════════════════════════════════════════════════{Colors.END}")
        print(f"{Colors.CYAN}Frontend:{Colors.END} http://localhost:8080")
        print(f"{Colors.CYAN}Backend API:{Colors.END} http://localhost:8000")
        print(f"{Colors.CYAN}API Docs:{Colors.END} http://localhost:8000/docs")
        print(f"{Colors.CYAN}WebSocket:{Colors.END} ws://localhost:8000/ws")
        print(f"{Colors.BOLD}═══════════════════════════════════════════════════════{Colors.END}")
        print(f"{Colors.YELLOW}Press Ctrl+C to shutdown{Colors.END}\n")
        
        self.running = True
        
        try:
            while self.running:
                time.sleep(0.5)
                
                # Check if any process died
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        name = "Backend" if i == 0 else "Frontend"
                        print(f"{Colors.RED}[ERROR]{Colors.END} {name} process died unexpectedly")
                        self.shutdown()
                        return
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[SHUTDOWN]{Colors.END} Received shutdown signal...")
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown all processes"""
        self.running = False
        print(f"{Colors.YELLOW}[SHUTDOWN]{Colors.END} Stopping all services...")
        
        for i, process in enumerate(self.processes):
            name = "Backend" if i == 0 else "Frontend"
            try:
                print(f"{Colors.BLUE}[SHUTDOWN]{Colors.END} Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"{Colors.GREEN}[SHUTDOWN]{Colors.END} {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"{Colors.YELLOW}[SHUTDOWN]{Colors.END} Force killing {name}...")
                process.kill()
                process.wait()
        
        print(f"{Colors.GREEN}[SHUTDOWN]{Colors.END} All services stopped")
        print(f"{Colors.CYAN}{Colors.BOLD}Thank you for using JARVIS!{Colors.END}")

def main():
    """Main entry point"""
    print_banner()
    
    # Check requirements
    check_requirements()
    
    # Initialize process manager
    manager = ProcessManager()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        manager.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start services
        print(f"{Colors.BOLD}{Colors.GREEN}[JARVIS]{Colors.END} Initializing system...\n")
        
        backend_process = manager.start_backend()
        time.sleep(2)  # Wait for backend to initialize
        
        frontend_process = manager.start_frontend()
        time.sleep(3)  # Wait for frontend to initialize
        
        # Monitor processes
        manager.monitor_processes()
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR]{Colors.END} Failed to start system: {e}")
        manager.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()
