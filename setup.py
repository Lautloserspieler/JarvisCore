#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Core - Vollautomatisches Setup-Script
Ein-Klick-Installation mit ImGui Desktop-UI
"""

import sys
import os
import subprocess
import platform
import json
import shutil
from pathlib import Path


class Colors:
    """ANSI Color Codes für Terminal"""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


class JarvisSetup:
    """Automatisches Setup für J.A.R.V.I.S. Core"""
    
    def __init__(self):
        self.root = Path(__file__).parent
        self.venv_path = self.root / "venv"
        self.data_path = self.root / "data"
        self.logs_path = self.root / "logs"
        self.models_path = self.root / "models"
        self.settings_file = self.data_path / "settings.json"
        self.os_type = platform.system()
        
    def print_header(self):
        """Zeigt Banner"""
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("="*60)
        print("🤖  J.A.R.V.I.S. Core - Automatisches Setup")
        print("="*60)
        print(f"{Colors.END}")
        print(f"{Colors.GREEN}Willkommen zum automatischen Setup!{Colors.END}")
        print(f"Dieses Script installiert alles für dich.\n")
    
    def check_python_version(self):
        """Prüft Python-Version"""
        print(f"{Colors.CYAN}➤ Prüfe Python-Version...{Colors.END}")
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 11):
            print(f"{Colors.RED}❌ Python 3.11+ benötigt! (Aktuell: {version.major}.{version.minor}){Colors.END}")
            sys.exit(1)
        
        print(f"{Colors.GREEN}✅ Python {version.major}.{version.minor}.{version.micro} gefunden{Colors.END}\n")
    
    def create_directories(self):
        """Erstellt notwendige Verzeichnisse"""
        print(f"{Colors.CYAN}➤ Erstelle Verzeichnisse...{Colors.END}")
        
        dirs = [
            self.data_path,
            self.logs_path,
            self.models_path,
            self.models_path / "llm",
            self.models_path / "stt",
            self.models_path / "tts",
            self.data_path / "secure",
            self.root / "backups"
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            print(f"  📁 {d.name}/")
        
        print(f"{Colors.GREEN}✅ Verzeichnisse erstellt{Colors.END}\n")
    
    def is_venv_valid(self):
        """Prüft ob venv gültig ist"""
        if not self.venv_path.exists():
            return False
        
        # Check if Python executable exists
        python_path = self.get_python_path()
        if not python_path.exists():
            return False
        
        # Check if pip exists
        pip_path = self.get_pip_path()
        if not pip_path.exists():
            return False
        
        # Try to run python --version
        try:
            result = subprocess.run(
                [str(python_path), "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def create_venv(self, force=False):
        """Erstellt virtuelle Umgebung mit Validation und Force-Option"""
        
        # Check if venv exists
        if self.venv_path.exists():
            # Validate existing venv
            if self.is_venv_valid():
                if force:
                    print(f"{Colors.YELLOW}🔄 Force-Recreate: Lösche existierende venv...{Colors.END}")
                    try:
                        shutil.rmtree(self.venv_path)
                        print(f"{Colors.GREEN}✅ Alte venv gelöscht{Colors.END}")
                    except Exception as e:
                        print(f"{Colors.RED}❌ Fehler beim Löschen: {e}{Colors.END}")
                        print(f"{Colors.YELLOW}Versuche manuell zu löschen: rmdir /s venv{Colors.END}")
                        sys.exit(1)
                else:
                    print(f"{Colors.YELLOW}⚠️  Virtuelle Umgebung existiert bereits und ist gültig (venv/)\n{Colors.END}")
                    return
            else:
                print(f"{Colors.YELLOW}⚠️  Existierende venv ist beschädigt, erstelle neu...{Colors.END}")
                try:
                    shutil.rmtree(self.venv_path)
                    print(f"{Colors.GREEN}✅ Beschädigte venv entfernt{Colors.END}")
                except Exception as e:
                    print(f"{Colors.RED}❌ Fehler beim Löschen: {e}{Colors.END}")
                    sys.exit(1)
        
        print(f"{Colors.CYAN}➤ Erstelle virtuelle Umgebung (venv/)...{Colors.END}")
        
        try:
            # Create venv with upgraded pip and setuptools
            subprocess.run(
                [sys.executable, "-m", "venv", "--upgrade-deps", str(self.venv_path)],
                check=True,
                capture_output=False  # Show output
            )
            print(f"{Colors.GREEN}✅ Virtuelle Umgebung erstellt (mit aktuellen pip/setuptools){Colors.END}")
            
            # Verify creation
            if not self.is_venv_valid():
                print(f"{Colors.RED}❌ venv-Erstellung fehlgeschlagen (Validation Check failed){Colors.END}")
                sys.exit(1)
            
            print(f"{Colors.GREEN}✅ venv Validation erfolgreich{Colors.END}\n")
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ Fehler beim Erstellen der venv: {e}{Colors.END}")
            print(f"{Colors.YELLOW}\nTroubleshooting:{Colors.END}")
            print(f"  1. Stelle sicher, dass Python korrekt installiert ist")
            print(f"  2. Versuche: python -m venv --help")
            print(f"  3. Installiere venv: apt install python3-venv (Linux)\n")
            sys.exit(1)
    
    def get_pip_path(self):
        """Gibt Pfad zu pip in venv zurück"""
        if self.os_type == "Windows":
            return self.venv_path / "Scripts" / "pip.exe"
        return self.venv_path / "bin" / "pip"
    
    def get_python_path(self):
        """Gibt Pfad zu Python in venv zurück"""
        if self.os_type == "Windows":
            return self.venv_path / "Scripts" / "python.exe"
        return self.venv_path / "bin" / "python"
    
    def install_dependencies(self):
        """Installiert Dependencies"""
        print(f"{Colors.CYAN}➤ Installiere Dependencies...{Colors.END}")
        print(f"{Colors.YELLOW}(Dies kann einige Minuten dauern)\n{Colors.END}")
        
        pip = str(self.get_pip_path())
        python = str(self.get_python_path())
        requirements = self.root / "requirements.txt"
        
        if not requirements.exists():
            print(f"{Colors.RED}❌ requirements.txt nicht gefunden!{Colors.END}")
            sys.exit(1)
        
        try:
            # Verify pip works
            print(f"  🔍 Verifiziere pip...\n")
            result = subprocess.run(
                [pip, "--version"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"  ✅ {result.stdout.strip()}\n")
            else:
                print(f"{Colors.RED}❌ pip funktioniert nicht korrekt{Colors.END}")
                sys.exit(1)
            
            # Upgrade pip explicitly (in case --upgrade-deps didn't work)
            print(f"  🔄 Stelle sicher, dass pip aktuell ist...\n")
            result = subprocess.run(
                [python, "-m", "pip", "install", "--upgrade", "pip"],
                check=False
            )
            
            if result.returncode != 0:
                print(f"\n{Colors.YELLOW}⚠️  Pip upgrade fehlgeschlagen, fahre trotzdem fort...{Colors.END}\n")
            else:
                print(f"\n{Colors.GREEN}✅ pip aktualisiert{Colors.END}\n")
            
            # Install requirements (show output)
            print(f"  📦 Installiere Pakete aus requirements.txt...\n")
            subprocess.run(
                [pip, "install", "-r", str(requirements)],
                check=True
            )
            
            print(f"\n{Colors.GREEN}✅ Dependencies installiert{Colors.END}\n")
        except subprocess.CalledProcessError as e:
            print(f"\n{Colors.RED}❌ Fehler bei der Installation: {e}{Colors.END}")
            print(f"{Colors.YELLOW}\nVersuche manuell:{Colors.END}")
            print(f"  1. Aktiviere venv: {Colors.CYAN}venv\\Scripts\\activate{Colors.END}")
            print(f"  2. Installiere: {Colors.CYAN}pip install -r requirements.txt{Colors.END}\n")
            sys.exit(1)
    
    def configure_settings(self):
        """Erstellt/Aktualisiert settings.json"""
        print(f"{Colors.CYAN}➤ Konfiguriere settings.json...{Colors.END}")
        
        # Default Settings
        default_settings = {
            "language": "de",
            "desktop_app": {
                "enabled": True,
                "width": 1920,
                "height": 1080,
                "fullscreen": False,
                "vsync": True,
                "theme": "ue5"
            },
            "llm": {
                "enabled": True,
                "default_model": "mistral",
                "context_length": 2048,
                "temperature": 0.7,
                "auto_load": False
            },
            "speech": {
                "wake_word_enabled": True,
                "stream_tts": True,
                "min_command_words": 3
            },
            "web_interface": {
                "enabled": False
            },
            "remote_control": {
                "enabled": False,
                "host": "127.0.0.1",
                "port": 8765
            },
            "go_services": {
                "auto_start": False
            },
            "security": {
                "safe_mode": True,
                "require_auth": False
            },
            "knowledge": {
                "auto_update": True,
                "scan_interval_hours": 24
            }
        }
        
        # Load existing or create new
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                
                # Merge with defaults (update nur desktop_app)
                existing["desktop_app"] = default_settings["desktop_app"]
                settings = existing
                print(f"  📄 Bestehende Settings aktualisiert")
            except Exception as e:
                print(f"  ⚠️  Fehler beim Laden: {e}")
                settings = default_settings
        else:
            settings = default_settings
            print(f"  ✨ Neue Settings erstellt")
        
        # Save
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            print(f"{Colors.GREEN}✅ Settings konfiguriert{Colors.END}")
            print(f"  📁 Datei: {self.settings_file}\n")
        except Exception as e:
            print(f"{Colors.RED}❌ Fehler beim Speichern: {e}{Colors.END}")
    
    def print_next_steps(self):
        """Zeigt nächste Schritte"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
        print("✅ SETUP ABGESCHLOSSEN!")
        print(f"{'='*60}{Colors.END}\n")
        
        print(f"{Colors.GREEN}{Colors.BOLD}NÄCHSTE SCHRITTE:{Colors.END}\n")
        
        if self.os_type == "Windows":
            activate_cmd = "venv\\Scripts\\activate"
        else:
            activate_cmd = "source venv/bin/activate"
        
        print(f"1️⃣  Aktiviere virtuelle Umgebung:")
        print(f"   {Colors.CYAN}{activate_cmd}{Colors.END}\n")
        
        print(f"2️⃣  Starte J.A.R.V.I.S.:")
        print(f"   {Colors.CYAN}python main.py{Colors.END}\n")
        
        print(f"{Colors.YELLOW}💡 TIPPS:{Colors.END}")
        print(f"  • ImGui Desktop-UI startet automatisch")
        print(f"  • Settings: data/settings.json")
        print(f"  • Logs: logs/jarvis.log")
        print(f"  • Doku: docs/IMGUI_SETUP.md\n")
        
        print(f"{Colors.CYAN}🚀 Viel Spaß mit J.A.R.V.I.S.!{Colors.END}\n")
    
    def ask_auto_start(self):
        """Fragt ob automatisch starten"""
        print(f"{Colors.YELLOW}Möchtest du J.A.R.V.I.S. jetzt starten? (y/n): {Colors.END}", end="")
        
        try:
            response = input().strip().lower()
            return response in ['y', 'yes', 'j', 'ja']
        except (EOFError, KeyboardInterrupt):
            print()
            return False
    
    def start_jarvis(self):
        """Startet JARVIS"""
        print(f"\n{Colors.CYAN}➤ Starte J.A.R.V.I.S...{Colors.END}\n")
        
        python = str(self.get_python_path())
        main_py = self.root / "main.py"
        
        if not main_py.exists():
            print(f"{Colors.RED}❌ main.py nicht gefunden!{Colors.END}")
            return
        
        try:
            # Set environment variable
            env = os.environ.copy()
            env["JARVIS_DESKTOP"] = "1"
            
            # Start JARVIS
            subprocess.run([python, str(main_py)], env=env)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⚠️  J.A.R.V.I.S. wurde beendet{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}❌ Fehler beim Start: {e}{Colors.END}")
    
    def run(self, force_recreate=False):
        """Führt vollständiges Setup durch"""
        try:
            self.print_header()
            self.check_python_version()
            self.create_directories()
            self.create_venv(force=force_recreate)
            self.install_dependencies()
            self.configure_settings()
            self.print_next_steps()
            
            # Auto-start fragen
            if self.ask_auto_start():
                self.start_jarvis()
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⚠️  Setup abgebrochen{Colors.END}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{Colors.RED}❌ Unerwarteter Fehler: {e}{Colors.END}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Entry Point"""
    # Check for --force flag
    force = "--force" in sys.argv or "-f" in sys.argv
    
    if force:
        print(f"{Colors.YELLOW}⚠️  Force-Recreate Modus aktiviert{Colors.END}\n")
    
    setup = JarvisSetup()
    setup.run(force_recreate=force)


if __name__ == "__main__":
    main()
