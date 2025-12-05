#!/usr/bin/env python3
"""
JarvisCore - Automatisches Setup
Installiert alle Dependencies inklusive automatischer CUDA-Erkennung
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class JarvisCoreSetup:
    """Vollautomatisches Setup für JarvisCore"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.venv_dir = self.project_root / "venv"
        self.use_venv = "--no-venv" not in sys.argv

    def print_banner(self):
        """Banner ausgeben"""
        print("\n" + "=" * 70)
        print("🤖 J.A.R.V.I.S. Core - Automatisches Setup")
        print("=" * 70)
        print("Just A Rather Very Intelligent System")
        print("Version: 1.0.0 - Desktop Edition")
        print("=" * 70 + "\n")

    def check_python_version(self) -> bool:
        """Prüft Python-Version"""
        print("🔍 Prüfe Python-Version...")
        version = sys.version_info

        if version.major < 3 or (version.major == 3 and version.minor < 10):
            print(f"❌ Python {version.major}.{version.minor} ist zu alt!")
            print("✅ Erforderlich: Python 3.10 oder höher")
            print("   Download: https://www.python.org/downloads/")
            return False

        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True

    def create_virtualenv(self) -> bool:
        """Erstellt Virtual Environment"""
        if not self.use_venv:
            print("⚠️  Virtual Environment übersprungen (--no-venv)")
            return True

        print("\n📦 Erstelle Virtual Environment...")

        if self.venv_dir.exists():
            print(f"ℹ️  venv existiert bereits: {self.venv_dir}")
            response = input("   Neu erstellen? (j/n): ").lower()
            if response == 'j':
                import shutil
                print("   Lösche altes venv...")
                shutil.rmtree(self.venv_dir)
            else:
                print("✅ Verwende existierendes venv")
                return True

        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_dir)],
                check=True,
            )
            print(f"✅ Virtual Environment erstellt: {self.venv_dir}")
            print("\n💡 Aktivierung:")
            if platform.system() == "Windows":
                print(f"   {self.venv_dir}\\Scripts\\activate")
            else:
                print(f"   source {self.venv_dir}/bin/activate")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Fehler beim Erstellen des venv: {e}")
            return False

    def get_pip_executable(self) -> str:
        """Findet pip in venv oder system"""
        if self.use_venv and self.venv_dir.exists():
            if platform.system() == "Windows":
                pip = self.venv_dir / "Scripts" / "pip.exe"
            else:
                pip = self.venv_dir / "bin" / "pip"

            if pip.exists():
                return str(pip)

        # Fallback zu system pip
        return "pip"

    def install_base_requirements(self) -> bool:
        """Installiert Basis-Requirements (ohne llama-cpp-python)"""
        print("\n📦 Installiere Basis-Dependencies...")

        if not self.requirements_file.exists():
            print(f"❌ requirements.txt nicht gefunden: {self.requirements_file}")
            return False

        # requirements.txt lesen und llama-cpp-python ausschließen
        with open(self.requirements_file, 'r') as f:
            requirements = [
                line.strip()
                for line in f
                if line.strip()
                and not line.strip().startswith('#')
                and 'llama-cpp-python' not in line.lower()
            ]

        # Temporäre requirements ohne llama-cpp-python
        temp_requirements = self.project_root / "requirements_base.tmp"
        with open(temp_requirements, 'w') as f:
            f.write('\n'.join(requirements))

        try:
            pip = self.get_pip_executable()
            print(f"   Verwende pip: {pip}")
            print("   (Das kann einige Minuten dauern...)\n")

            subprocess.run(
                [pip, "install", "--upgrade", "pip"],
                check=True,
            )

            subprocess.run(
                [pip, "install", "-r", str(temp_requirements)],
                check=True,
            )

            temp_requirements.unlink()  # Temp-Datei löschen
            print("✅ Basis-Dependencies installiert")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Installation fehlgeschlagen: {e}")
            if temp_requirements.exists():
                temp_requirements.unlink()
            return False

    def install_cuda_and_llama(self) -> bool:
        """Ruft setup_cuda.py für automatische CUDA-Erkennung auf"""
        print("\n🚀 Starte automatische CUDA-Erkennung...")

        setup_cuda_script = self.project_root / "scripts" / "setup_cuda.py"

        if not setup_cuda_script.exists():
            print(f"⚠️  setup_cuda.py nicht gefunden: {setup_cuda_script}")
            print("   Installiere llama-cpp-python ohne CUDA...")
            try:
                pip = self.get_pip_executable()
                subprocess.run(
                    [pip, "install", "llama-cpp-python"],
                    check=True,
                )
                return True
            except subprocess.CalledProcessError:
                return False

        try:
            # Python executable ermitteln (venv falls vorhanden)
            if self.use_venv and self.venv_dir.exists():
                if platform.system() == "Windows":
                    python_exe = str(self.venv_dir / "Scripts" / "python.exe")
                else:
                    python_exe = str(self.venv_dir / "bin" / "python")
            else:
                python_exe = sys.executable

            # setup_cuda.py ausführen
            result = subprocess.run(
                [python_exe, str(setup_cuda_script)],
                check=False,  # Ignoriere Exit-Code, da auch CPU-Install OK ist
            )

            return True  # Erfolgreich, auch wenn CPU-only

        except Exception as e:
            print(f"❌ CUDA Setup fehlgeschlagen: {e}")
            return False

    def create_config_if_needed(self) -> bool:
        """Erstellt settings.py aus Example falls nicht vorhanden"""
        print("\n⚙️  Prüfe Konfiguration...")

        config_dir = self.project_root / "config"
        settings_file = config_dir / "settings.py"
        example_file = config_dir / "settings.example.py"

        if settings_file.exists():
            print(f"✅ Konfiguration existiert: {settings_file}")
            return True

        if not example_file.exists():
            print(f"⚠️  Weder settings.py noch settings.example.py gefunden")
            return True  # Nicht kritisch

        try:
            import shutil
            shutil.copy(example_file, settings_file)
            print(f"✅ Konfiguration erstellt: {settings_file}")
            print("💡 Bitte settings.py anpassen (API Keys, Pfade, etc.)")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Konfiguration: {e}")
            return False

    def create_directories(self) -> bool:
        """Erstellt benötigte Verzeichnisse"""
        print("\n📂 Erstelle Verzeichnisstruktur...")

        directories = [
            "data",
            "data/memory",
            "data/knowledge",
            "data/training",
            "logs",
            "models/llm",
            "plugins",
        ]

        for dir_name in directories:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ {dir_name}/")
            else:
                print(f"   ✓ {dir_name}/ (existiert)")

        return True

    def print_next_steps(self):
        """Gibt nächste Schritte aus"""
        print("\n" + "=" * 70)
        print("🎉 Setup abgeschlossen!")
        print("=" * 70)
        print("\n🚀 Nächste Schritte:\n")

        if self.use_venv:
            print("1️⃣ Virtual Environment aktivieren:")
            if platform.system() == "Windows":
                print(f"   {self.venv_dir}\\Scripts\\activate")
            else:
                print(f"   source {self.venv_dir}/bin/activate")
            print()

        print("2️⃣ Konfiguration anpassen:")
        print("   vim config/settings.py")
        print()

        print("3️⃣ J.A.R.V.I.S. starten:")
        print("   python start_jarvis.py")
        print("   # oder")
        print("   python main.py              # Backend")
        print("   cd desktop && make dev      # Desktop UI")
        print()

        print("4️⃣ LLM-Modelle herunterladen:")
        print("   - Über Desktop UI: Models View → Download Button")
        print("   - Oder manuell von Hugging Face:")
        print("     https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct-GGUF")
        print("     Dateien nach models/llm/ kopieren")
        print()

        print("📚 Dokumentation:")
        print("   README.md - Vollständige Übersicht")
        print("   desktop/README.md - Desktop UI Details")
        print("   MIGRATION.md - Web UI → Desktop Migration")
        print()

    def run(self) -> int:
        """Führt Setup aus"""
        self.print_banner()

        # 1. Python Version prüfen
        if not self.check_python_version():
            return 1

        # 2. Virtual Environment erstellen
        if not self.create_virtualenv():
            return 1

        # 3. Basis-Requirements installieren
        if not self.install_base_requirements():
            return 1

        # 4. CUDA + llama-cpp-python (automatisch)
        if not self.install_cuda_and_llama():
            print("⚠️  CUDA Setup hatte Probleme, aber fortfahren...")

        # 5. Konfiguration erstellen
        self.create_config_if_needed()

        # 6. Verzeichnisse erstellen
        self.create_directories()

        # 7. Nächste Schritte
        self.print_next_steps()

        return 0


def main():
    """Hauptfunktion"""
    try:
        setup = JarvisCoreSetup()
        return setup.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup abgebrochen durch Benutzer")
        return 1
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
