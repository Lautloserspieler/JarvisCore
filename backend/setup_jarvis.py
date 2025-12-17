#!/usr/bin/env python3
"""JARVIS Complete Setup - Build Tools + llama-cpp-python in einem Schritt"""

import sys
import os
import subprocess
from pathlib import Path

# Import setup_buildtools_path functions
sys.path.insert(0, str(Path(__file__).parent))
from setup_buildtools_path import setup_build_environment, apply_environment

def main():
    print("""
    ╭────────────────────────────────────────────────────────────╮
    │            JARVIS Core - Komplette Installation               │
    │       Build Tools + llama.cpp mit GPU-Unterstützung         │
    ╰────────────────────────────────────────────────────────────╯
    """)
    
    print("[INFO] 🚀 Schritt 1/2: Build Tools aktivieren...\n")
    
    # Setup Build Environment
    env_vars = setup_build_environment()
    
    if env_vars:
        # Apply environment to current process
        if apply_environment(env_vars):
            print("\n[INFO] ✅ Build Tools aktiviert!\n")
        else:
            print("\n[WARNUNG] ⚠️  Build Tools nicht vollständig konfiguriert\n")
    else:
        print("\n[WARNUNG] ⚠️  Build Tools nicht gefunden - Installation läuft im CPU-Modus\n")
    
    print("="*60)
    print("\n[INFO] 🚀 Schritt 2/2: llama-cpp-python installieren...\n")
    print("="*60 + "\n")
    
    # Now call setup_llama.py in the SAME process with inherited environment
    setup_llama_path = Path(__file__).parent / "setup_llama.py"
    
    if not setup_llama_path.exists():
        print(f"[FEHLER] setup_llama.py nicht gefunden: {setup_llama_path}")
        return 1
    
    # Execute setup_llama.py with current environment
    result = subprocess.run(
        [sys.executable, str(setup_llama_path)],
        env=os.environ.copy()  # Pass current environment with build tools
    )
    
    if result.returncode == 0:
        print("\n" + "✅"*30)
        print("\n[ERFOLG] 🎉 JARVIS Core Setup abgeschlossen!")
        print("\n[INFO] 💡 Du kannst jetzt starten:")
        print("       python backend/main.py")
        print("\n" + "✅"*30 + "\n")
    else:
        print("\n❌ Setup fehlgeschlagen! Siehe Fehler oben.\n")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
