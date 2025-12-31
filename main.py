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
import socket
import signal
from pathlib import Path
from dotenv import load_dotenv

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
        self.running = True

        self.env_errors = []
        self.env_warnings = []

        load_dotenv(self.root / ".env")
        
        # Load ports from environment or use defaults
        self.backend_port = self._get_env_int("JARVIS_BACKEND_PORT", 5050, min_value=1, max_value=65535)
        self.frontend_port = self._get_env_int("JARVIS_FRONTEND_PORT", 5000, min_value=1, max_value=65535)

        self._validate_environment()
        self._report_environment_validation()
        if self.env_errors:
            sys.exit(1)
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, self._signal_handler)

    def _add_env_error(self, message):
        self.env_errors.append(message)

    def _add_env_warning(self, message):
        self.env_warnings.append(message)

    def _get_env_int(self, key, default, min_value=None, max_value=None):
        raw_value = os.getenv(key)
        if raw_value is None or raw_value == "":
            return default
        try:
            value = int(raw_value)
        except ValueError:
            self._add_env_error(f"{key} muss eine ganze Zahl sein (aktuell: '{raw_value}').")
            return default
        if min_value is not None and value < min_value:
            self._add_env_error(f"{key} muss mindestens {min_value} sein (aktuell: {value}).")
        if max_value is not None and value > max_value:
            self._add_env_error(f"{key} darf maximal {max_value} sein (aktuell: {value}).")
        return value

    def _validate_enum(self, key, allowed_values):
        value = os.getenv(key)
        if value is None or value == "":
            return
        if value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            self._add_env_error(f"{key} ist ungültig ('{value}'). Erlaubt: {allowed}.")

    def _validate_bool(self, key):
        value = os.getenv(key)
        if value is None or value == "":
            return
        normalized = value.strip().lower()
        if normalized not in {"true", "false", "1", "0", "yes", "no"}:
            self._add_env_error(
                f"{key} muss ein boolescher Wert sein (true/false/1/0). Aktuell: '{value}'."
            )

    def _validate_float_range(self, key, min_value=None, max_value=None):
        value = os.getenv(key)
        if value is None or value == "":
            return
        try:
            numeric = float(value)
        except ValueError:
            self._add_env_error(f"{key} muss eine Zahl sein (aktuell: '{value}').")
            return
        if min_value is not None and numeric < min_value:
            self._add_env_error(f"{key} muss mindestens {min_value} sein (aktuell: {numeric}).")
        if max_value is not None and numeric > max_value:
            self._add_env_error(f"{key} darf maximal {max_value} sein (aktuell: {numeric}).")

    def _validate_int_range(self, key, min_value=None, max_value=None):
        value = os.getenv(key)
        if value is None or value == "":
            return
        try:
            numeric = int(value)
        except ValueError:
            self._add_env_error(f"{key} muss eine ganze Zahl sein (aktuell: '{value}').")
            return
        if min_value is not None and numeric < min_value:
            self._add_env_error(f"{key} muss mindestens {min_value} sein (aktuell: {numeric}).")
        if max_value is not None and numeric > max_value:
            self._add_env_error(f"{key} darf maximal {max_value} sein (aktuell: {numeric}).")

    def _validate_environment(self):
        self._validate_enum("JARVIS_MODE", {"development", "production", "desktop"})
        self._validate_enum("JARVIS_LOG_LEVEL", {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
        self._validate_enum("LLM_DEVICE", {"cuda", "cpu", "mps"})
        self._validate_enum("TTS_ENGINE", {"xtts", "pyttsx3"})
        self._validate_enum("TTS_DEVICE", {"cuda", "cpu"})
        self._validate_enum("TTS_LANGUAGE", {"de", "en"})
        self._validate_enum("STT_ENGINE", {"faster-whisper", "whisper"})
        self._validate_enum("STT_MODEL", {"tiny", "base", "small", "medium", "large"})
        self._validate_enum("STT_LANGUAGE", {"de", "en", "auto"})
        self._validate_enum("STT_DEVICE", {"cuda", "cpu"})

        self._validate_float_range("LLM_TEMPERATURE", 0.0, 2.0)
        self._validate_float_range("TTS_VOLUME", 0.0, 1.0)

        self._validate_int_range("LLM_CONTEXT_SIZE", 1)
        self._validate_int_range("LLM_MAX_TOKENS", 1)
        self._validate_int_range("LLM_MAX_CACHED_MODELS", 0)
        self._validate_int_range("LLM_CACHE_TTL", 1)
        self._validate_int_range("LLM_GPU_LAYERS", -1)

        for key in [
            "JARVIS_AUTO_INSTALL",
            "TTS_ENABLED",
            "ENABLE_VOICE_CONTROL",
            "ENABLE_DESKTOP_NOTIFICATIONS",
            "ENABLE_SYSTEM_TRAY",
            "ENABLE_TELEMETRY",
            "ENABLE_PLUGIN_HOTRELOAD",
            "DEBUG",
            "ENABLE_CORS",
        ]:
            self._validate_bool(key)

        for key in [
            "OPENWEATHER_API_KEY",
            "NEWS_API_KEY",
            "GOOGLE_API_KEY",
            "DEEPL_API_KEY",
        ]:
            value = os.getenv(key)
            if value and ("your_" in value or value.endswith("_here")):
                self._add_env_warning(
                    f"{key} scheint noch ein Platzhalter zu sein. Bitte echten API-Key setzen."
                )

    def _report_environment_validation(self):
        if self.env_warnings:
            print(f"{Colors.YELLOW}⚠️  Hinweis zur .env-Konfiguration:{Colors.END}")
            for warning in self.env_warnings:
                print(f"{Colors.YELLOW}   - {warning}{Colors.END}")

        if self.env_errors:
            print(f"{Colors.RED}❌ Fehler in der .env-Konfiguration:{Colors.END}")
            for error in self.env_errors:
                print(f"{Colors.RED}   - {error}{Colors.END}")
            print(
                f"{Colors.RED}Bitte korrigiere die Werte in deiner .env (siehe .env.example).{Colors.END}"
            )
    
    def _signal_handler(self, sig, frame):
        """Handle SIGTERM, SIGINT, SIGBREAK for graceful shutdown"""
        print(f"\n{Colors.YELLOW}● Received signal {sig}, shutting down gracefully...{Colors.END}")
        self.running = False
        self.shutdown()
        sys.exit(0)
        
    def print_banner(self):
        """Print JARVIS banner"""
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("\n" + "="*60)
        print("    ╔══════════════════════════════════════════════════════╗")
        print("    ║              JARVIS CORE SYSTEM v1.1.0               ║")
        print("    ║         Just A Rather Very Intelligent System        ║")
        print("    ╚══════════════════════════════════════════════════════╝")
        print("="*60)
        print(f"{Colors.END}")
    
    def is_port_available(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False
    
    def find_available_port(self, start_port, max_attempts=10):
        """Find an available port starting from start_port"""
        for i in range(max_attempts):
            port = start_port + i
            if self.is_port_available(port):
                return port
        return None
    
    def check_python_dependencies(self):
        """Check if Python dependencies are installed"""
        print(f"{Colors.CYAN}  • Checking Python dependencies...{Colors.END}")
        
        requirements_file = self.backend_dir / "requirements.txt"
        if not requirements_file.exists():
            print(f"{Colors.YELLOW}    ⚠️  requirements.txt not found{Colors.END}")
            return True
        
        # Check if key packages are installed
        try:
            import fastapi
            import uvicorn
            import requests
            import tqdm
            print(f"{Colors.GREEN}    ✓ Python dependencies OK{Colors.END}")
            return True
        except ImportError as e:
            print(f"{Colors.YELLOW}    ⚠️  Missing Python dependencies: {e}{Colors.END}")
            response = input(f"{Colors.CYAN}    Install now? (y/n): {Colors.END}").lower()
            
            if response == 'y':
                print(f"{Colors.CYAN}    Installing dependencies...{Colors.END}")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                    capture_output=True
                )
                if result.returncode == 0:
                    print(f"{Colors.GREEN}    ✓ Dependencies installed{Colors.END}")
                    return True
                else:
                    print(f"{Colors.RED}    ❌ Installation failed{Colors.END}")
                    return False
            return False
    
    def check_node_modules(self):
        """Check if node_modules are installed"""
        if not self.frontend_dir.exists():
            return True
        
        print(f"{Colors.CYAN}  • Checking Node.js dependencies...{Colors.END}")
        
        node_modules = self.frontend_dir / "node_modules"
        if node_modules.exists():
            print(f"{Colors.GREEN}    ✓ Node modules OK{Colors.END}")
            return True
        
        print(f"{Colors.YELLOW}    ⚠️  node_modules not found{Colors.END}")
        response = input(f"{Colors.CYAN}    Run npm install? (y/n): {Colors.END}").lower()
        
        if response == 'y':
            print(f"{Colors.CYAN}    Installing Node modules...{Colors.END}")
            try:
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=str(self.frontend_dir),
                    shell=(sys.platform == "win32"),
                    capture_output=True
                )
                if result.returncode == 0:
                    print(f"{Colors.GREEN}    ✓ Node modules installed{Colors.END}")
                    return True
                else:
                    print(f"{Colors.RED}    ❌ Installation failed{Colors.END}")
                    return False
            except Exception as e:
                print(f"{Colors.RED}    ❌ Error: {e}{Colors.END}")
                return False
        return False
    
    def check_requirements(self):
        """Check if required directories and dependencies exist"""
        print(f"\n{Colors.CYAN}● Checking system requirements...{Colors.END}")
        
        if not self.backend_dir.exists():
            print(f"{Colors.RED}❌ Backend directory not found!{Colors.END}")
            return False
        
        if not (self.backend_dir / "main.py").exists():
            print(f"{Colors.RED}❌ Backend main.py not found!{Colors.END}")
            return False
        
        # Check dependencies
        if not self.check_python_dependencies():
            return False
        
        if not self.check_node_modules():
            print(f"{Colors.YELLOW}  ⚠️  Frontend will be skipped{Colors.END}")
        
        # Check ports
        print(f"{Colors.CYAN}  • Checking ports...{Colors.END}")
        
        if not self.is_port_available(self.backend_port):
            print(f"{Colors.YELLOW}    ⚠️  Port {self.backend_port} is in use{Colors.END}")
            new_port = self.find_available_port(self.backend_port)
            if new_port:
                print(f"{Colors.GREEN}    ✓ Using port {new_port} instead{Colors.END}")
                self.backend_port = new_port
            else:
                print(f"{Colors.RED}    ❌ No available ports found{Colors.END}")
                return False
        else:
            print(f"{Colors.GREEN}    ✓ Backend port {self.backend_port} available{Colors.END}")
        
        if not self.is_port_available(self.frontend_port):
            print(f"{Colors.YELLOW}    ⚠️  Port {self.frontend_port} is in use{Colors.END}")
            new_port = self.find_available_port(self.frontend_port)
            if new_port:
                print(f"{Colors.GREEN}    ✓ Using port {new_port} instead{Colors.END}")
                self.frontend_port = new_port
            else:
                print(f"{Colors.YELLOW}    ⚠️  Frontend will use random port{Colors.END}")
        else:
            print(f"{Colors.GREEN}    ✓ Frontend port {self.frontend_port} available{Colors.END}")
        
        print(f"{Colors.GREEN}\n✓ All requirements satisfied{Colors.END}")
        return True
    
    def start_backend(self):
        """Start FastAPI backend"""
        print(f"\n{Colors.CYAN}▶ Starting Backend (FastAPI)...{Colors.END}")
        
        try:
            # Set environment variable for backend port
            env = os.environ.copy()
            env['JARVIS_PORT'] = str(self.backend_port)
            
            if sys.platform == "win32":
                python_exe = Path(sys.executable)
            else:
                python_exe = "python3"
            
            # CRITICAL FIX: Don't capture stdout/stderr to prevent pipe buffer overflow
            # This allows model downloads with progress bars to work without hanging
            backend_process = subprocess.Popen(
                [str(python_exe), "main.py"],
                cwd=str(self.backend_dir),
                env=env,
                # No stdout/stderr capture - output goes directly to terminal
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            self.processes.append(backend_process)
            time.sleep(3)
            
            print(f"{Colors.GREEN}✓ Backend started on http://localhost:{self.backend_port}{Colors.END}")
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
        
        if not (self.frontend_dir / "node_modules").exists():
            print(f"{Colors.YELLOW}⚠️  node_modules not found, skipping frontend{Colors.END}")
            return None
        
        try:
            subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                shell=(sys.platform == "win32"),
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.YELLOW}⚠️  npm not found, skipping frontend{Colors.END}")
            return None
        
        try:
            # Set port for Vite
            env = os.environ.copy()
            env['PORT'] = str(self.frontend_port)
            
            # CRITICAL FIX: Don't capture stdout/stderr for frontend either
            if sys.platform == "win32":
                frontend_process = subprocess.Popen(
                    f"npm run dev -- --port {self.frontend_port}",
                    cwd=str(self.frontend_dir),
                    shell=True,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                frontend_process = subprocess.Popen(
                    ["npm", "run", "dev", "--", "--port", str(self.frontend_port)],
                    cwd=str(self.frontend_dir),
                    env=env
                )
            
            self.processes.append(frontend_process)
            time.sleep(3)
            
            print(f"{Colors.GREEN}✓ Frontend started on http://localhost:{self.frontend_port}{Colors.END}")
            return frontend_process
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Could not start frontend: {e}{Colors.END}")
            return None
    
    def print_info(self):
        """Print access information"""
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ JARVIS System Online!{Colors.END}")
        print("─" * 60)
        print(f"🌐 Frontend:     {Colors.CYAN}http://localhost:{self.frontend_port}{Colors.END}")
        print(f"🔧 Backend API:  {Colors.CYAN}http://localhost:{self.backend_port}{Colors.END}")
        print(f"📚 API Docs:     {Colors.CYAN}http://localhost:{self.backend_port}/docs{Colors.END}")
        print(f"🔌 WebSocket:    {Colors.CYAN}ws://localhost:{self.backend_port}/ws{Colors.END}")
        print("─" * 60)
        print(f"\n{Colors.CYAN}💡 Tip: Set custom ports with environment variables:{Colors.END}")
        print(f"{Colors.CYAN}   JARVIS_BACKEND_PORT={self.backend_port}{Colors.END}")
        print(f"{Colors.CYAN}   JARVIS_FRONTEND_PORT={self.frontend_port}{Colors.END}")
        print(f"\n{Colors.YELLOW}🔑 Press Ctrl+C to shutdown{Colors.END}")
        print(f"\n{Colors.CYAN}📝 Note: Backend and frontend output will be displayed directly below{Colors.END}\n")
    
    def shutdown(self):
        """Shutdown all processes gracefully"""
        if not self.running:
            return  # Prevent multiple shutdown attempts
        
        self.running = False
        print(f"\n\n{Colors.YELLOW}● Shutting down JARVIS...{Colors.END}")
        
        for process in self.processes:
            try:
                if sys.platform == "win32":
                    # On Windows, send CTRL_BREAK_EVENT to process group
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                else:
                    # On Unix, send SIGTERM then SIGKILL if needed
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
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
            
            backend = self.start_backend()
            if not backend:
                print(f"{Colors.RED}❌ Failed to start backend{Colors.END}")
                sys.exit(1)
            
            frontend = self.start_frontend()
            self.print_info()
            
            # Monitor processes without capturing output
            while self.running:
                time.sleep(1)
                if backend.poll() is not None:
                    print(f"\n{Colors.RED}❌ Backend crashed!{Colors.END}")
                    self.running = False
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
