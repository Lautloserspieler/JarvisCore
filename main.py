#!/usr/bin/env python3
"""
JARVIS Core System - Main Entry Point

This script starts the complete JARVIS system:
- Backend (FastAPI on port 5050)
- Frontend (Vite on port 5000)
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Color codes for terminal output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

class JarvisLauncher:
    """Launcher for JARVIS Core System"""
    
    def __init__(self):
        self.root = Path(__file__).parent
        self.backend_dir = self.root / "backend"
        self.frontend_dir = self.root / "frontend"
        self.processes = []
        
    def print_banner(self):
        """Print JARVIS banner"""
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("\n" + "="*60)
        print("    ╔══════════════════════════════════════════════════════╗")
        print("    ║              JARVIS CORE SYSTEM v1.0.0               ║")
        print("    ║         Just A Rather Very Intelligent System        ║")
        print("    ╚══════════════════════════════════════════════════════╝")
        print("="*60)
        print(f"{Colors.END}")
    
    def check_requirements(self):
        """Check if required directories exist"""
        print(f"\n{Colors.CYAN}● Checking system requirements...{Colors.END}")
        
        if not self.backend_dir.exists():
            print(f"{Colors.RED}❌ Backend directory not found!{Colors.END}")
            return False
        
        if not (self.backend_dir / "main.py").exists():
            print(f"{Colors.RED}❌ Backend main.py not found!{Colors.END}")
            return False
        
        print(f"{Colors.GREEN}✓ All requirements satisfied{Colors.END}")
        return True
    
    def start_backend(self):
        """Start FastAPI backend"""
        print(f"\n{Colors.CYAN}▶ Starting Backend (FastAPI)...{Colors.END}")
        
        try:
            # Check if running in venv
            if sys.platform == "win32":
                python_exe = Path(sys.executable)
            else:
                python_exe = "python3"
            
            # Start backend
            backend_process = subprocess.Popen(
                [str(python_exe), "main.py"],
                cwd=str(self.backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(backend_process)
            
            # Give backend time to start
            time.sleep(3)
            
            print(f"{Colors.GREEN}✓ Backend started on http://localhost:5050{Colors.END}")
            return backend_process
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to start backend: {e}{Colors.END}")
            return None
    
    def start_frontend(self):
        """Start Vite frontend"""
        print(f"\n{Colors.CYAN}▶ Starting Frontend (Vite)...{Colors.END}")
        
        if not self.frontend_dir.exists():
            print(f"{Colors.YELLOW}⚠️  Frontend directory not found, skipping{Colors.END}")
            return None
        
        try:
            # Check if npm is available - use shell=True on Windows for PATH resolution
            check_result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                shell=(sys.platform == "win32"),
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.YELLOW}⚠️  npm not found, skipping frontend{Colors.END}")
            return None
        
        try:
            # Start frontend - shell=True fixes Windows PATH issues with npm
            if sys.platform == "win32":
                # Windows: Use shell=True to find npm in PATH
                frontend_process = subprocess.Popen(
                    "npm run dev",
                    cwd=str(self.frontend_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    shell=True
                )
            else:
                # Linux/Mac: Keep original method
                frontend_process = subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=str(self.frontend_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
            
            self.processes.append(frontend_process)
            
            # Give frontend time to start
            time.sleep(3)
            
            print(f"{Colors.GREEN}✓ Frontend started on http://localhost:5000{Colors.END}")
            return frontend_process
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Could not start frontend: {e}{Colors.END}")
            return None
    
    def print_info(self):
        """Print access information"""
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ JARVIS System Online!{Colors.END}")
        print("─" * 60)
        print(f"🌐 Frontend:     {Colors.CYAN}http://localhost:5000{Colors.END}")
        print(f"🔧 Backend API:  {Colors.CYAN}http://localhost:5050{Colors.END}")
        print(f"📚 API Docs:     {Colors.CYAN}http://localhost:5050/docs{Colors.END}")
        print(f"🔌 WebSocket:    {Colors.CYAN}ws://localhost:5050/ws{Colors.END}")
        print("─" * 60)
        print(f"\n{Colors.YELLOW}🔑 Press Ctrl+C to shutdown{Colors.END}\n")
    
    def stream_output(self, process, prefix):
        """Stream process output with prefix"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(f"{Colors.CYAN}[{prefix}]{Colors.END} {line.rstrip()}")
        except Exception:
            pass
    
    def shutdown(self):
        """Shutdown all processes"""
        print(f"\n\n{Colors.YELLOW}● Shutting down JARVIS...{Colors.END}")
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        
        print(f"{Colors.GREEN}✓ JARVIS shut down successfully{Colors.END}\n")
    
    def run(self):
        """Main run method"""
        try:
            self.print_banner()
            
            if not self.check_requirements():
                sys.exit(1)
            
            print(f"\n{Colors.CYAN}● Initializing JARVIS Core System...{Colors.END}")
            
            # Start backend
            backend = self.start_backend()
            if not backend:
                print(f"{Colors.RED}❌ Failed to start backend{Colors.END}")
                sys.exit(1)
            
            # Start frontend
            frontend = self.start_frontend()
            
            # Print access info
            self.print_info()
            
            # Stream backend output
            import threading
            backend_thread = threading.Thread(
                target=self.stream_output,
                args=(backend, "BACKEND"),
                daemon=True
            )
            backend_thread.start()
            
            # Stream frontend output if available
            if frontend:
                frontend_thread = threading.Thread(
                    target=self.stream_output,
                    args=(frontend, "FRONTEND"),
                    daemon=True
                )
                frontend_thread.start()
            
            # Wait for processes
            while True:
                time.sleep(1)
                
                # Check if backend is still running
                if backend.poll() is not None:
                    print(f"\n{Colors.RED}❌ Backend crashed!{Colors.END}")
                    break
                
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

def main():
    """Entry point"""
    launcher = JarvisLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
