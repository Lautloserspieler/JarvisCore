#!/usr/bin/env python3
"""
JARVIS Core - Unified Startup Script
Starts both Backend (FastAPI) and Frontend (Vite) in one terminal
"""

import subprocess
import sys
import os
import time
import signal
import threading
import queue
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
    DIM = '\033[2m'
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
    print(f"{Colors.YELLOW}●{Colors.END} Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"{Colors.RED}✗{Colors.END} Python 3.8 or higher is required")
        sys.exit(1)
    
    # Check if backend directory exists
    backend_path = Path("backend")
    if not backend_path.exists():
        print(f"{Colors.RED}✗{Colors.END} Backend directory not found")
        sys.exit(1)
    
    # Check if frontend directory exists
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print(f"{Colors.RED}✗{Colors.END} Frontend directory not found")
        sys.exit(1)
    
    # Check if node_modules exists
    node_modules = frontend_path / "node_modules"
    if not node_modules.exists():
        print(f"{Colors.YELLOW}⚠{Colors.END}  Frontend dependencies not installed")
        print(f"{Colors.BLUE}➜{Colors.END}  Running: npm install...")
        subprocess.run(["npm", "install"], cwd="frontend", check=True)
    
    # Check if Python packages are installed
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print(f"{Colors.YELLOW}⚠{Colors.END}  Backend dependencies not installed")
        print(f"{Colors.BLUE}➜{Colors.END}  Running: pip install -r requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"], check=True)
    
    print(f"{Colors.GREEN}✓{Colors.END} All requirements satisfied\n")

class LogStreamReader(threading.Thread):
    """Thread to read and display process output with color coding"""
    
    def __init__(self, process, prefix, color):
        super().__init__(daemon=True)
        self.process = process
        self.prefix = prefix
        self.color = color
        self.running = True
    
    def run(self):
        while self.running and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line:
                    # Clean and format output
                    clean_line = line.strip()
                    if clean_line:
                        # Skip ANSI escape sequences from original output
                        import re
                        clean_line = re.sub(r'\x1b\[[0-9;]*m', '', clean_line)
                        
                        # Format with prefix
                        print(f"{self.color}{self.prefix}{Colors.END} {Colors.DIM}{clean_line}{Colors.END}")
            except Exception as e:
                if self.running:
                    print(f"{Colors.RED}Error reading {self.prefix}:{Colors.END} {e}")
                break
    
    def stop(self):
        self.running = False

class ProcessManager:
    """Manage backend and frontend processes with unified output"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.readers: List[LogStreamReader] = []
        self.running = False
    
    def start_backend(self):
        """Start FastAPI backend server"""
        print(f"{Colors.BLUE}▶{Colors.END} Starting Backend (FastAPI)...")
        
        backend_cmd = [
            sys.executable,
            "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]
        
        process = subprocess.Popen(
            backend_cmd,
            cwd="backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        self.processes.append(process)
        
        # Start log reader thread
        reader = LogStreamReader(process, "[BACKEND]", Colors.BLUE)
        reader.start()
        self.readers.append(reader)
        
        print(f"{Colors.GREEN}✓{Colors.END} Backend started on {Colors.CYAN}http://localhost:8000{Colors.END}")
        
        return process
    
    def start_frontend(self):
        """Start Vite development server"""
        print(f"{Colors.MAGENTA}▶{Colors.END} Starting Frontend (Vite)...")
        
        # Use different commands based on OS
        if sys.platform == "win32":
            frontend_cmd = ["npm.cmd", "run", "dev"]
        else:
            frontend_cmd = ["npm", "run", "dev"]
        
        process = subprocess.Popen(
            frontend_cmd,
            cwd="frontend",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        self.processes.append(process)
        
        # Start log reader thread
        reader = LogStreamReader(process, "[FRONTEND]", Colors.MAGENTA)
        reader.start()
        self.readers.append(reader)
        
        print(f"{Colors.GREEN}✓{Colors.END} Frontend started on {Colors.CYAN}http://localhost:8080{Colors.END}")
        
        return process
    
    def monitor_processes(self):
        """Monitor process health"""
        print(f"\n{Colors.BOLD}{Colors.GREEN}✓ JARVIS System Online!{Colors.END}")
        print(f"{Colors.BOLD}─" * 60 + f"{Colors.END}")
        print(f"{Colors.CYAN}🌐 Frontend:{Colors.END}     http://localhost:8080")
        print(f"{Colors.CYAN}🔧 Backend API:{Colors.END}  http://localhost:8000")
        print(f"{Colors.CYAN}📚 API Docs:{Colors.END}     http://localhost:8000/docs")
        print(f"{Colors.CYAN}🔌 WebSocket:{Colors.END}    ws://localhost:8000/ws")
        print(f"{Colors.BOLD}─" * 60 + f"{Colors.END}")
        print(f"{Colors.YELLOW}🔑 Press Ctrl+C to shutdown{Colors.END}\n")
        
        self.running = True
        
        try:
            while self.running:
                time.sleep(1)
                
                # Check if any process died
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        name = "Backend" if i == 0 else "Frontend"
                        print(f"\n{Colors.RED}✗ {name} process died unexpectedly!{Colors.END}")
                        self.shutdown()
                        return
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}● Shutdown signal received...{Colors.END}")
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown all processes"""
        self.running = False
        print(f"\n{Colors.YELLOW}● Stopping all services...{Colors.END}")
        
        # Stop log readers
        for reader in self.readers:
            reader.stop()
        
        # Stop processes
        for i, process in enumerate(self.processes):
            name = "Backend" if i == 0 else "Frontend"
            try:
                print(f"{Colors.BLUE}➜{Colors.END} Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print(f"{Colors.GREEN}✓{Colors.END} {name} stopped")
                except subprocess.TimeoutExpired:
                    print(f"{Colors.YELLOW}⚠{Colors.END}  Force killing {name}...")
                    process.kill()
                    process.wait()
                    print(f"{Colors.GREEN}✓{Colors.END} {name} killed")
            except Exception as e:
                print(f"{Colors.RED}✗{Colors.END} Error stopping {name}: {e}")
        
        print(f"\n{Colors.GREEN}✓ All services stopped{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}Thank you for using JARVIS!{Colors.END}\n")

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
        print(f"{Colors.BOLD}{Colors.GREEN}● Initializing JARVIS Core System...{Colors.END}\n")
        
        backend_process = manager.start_backend()
        time.sleep(2)  # Wait for backend to initialize
        
        frontend_process = manager.start_frontend()
        time.sleep(2)  # Wait for frontend to initialize
        
        # Monitor processes
        manager.monitor_processes()
        
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to start system:{Colors.END} {e}")
        manager.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()
