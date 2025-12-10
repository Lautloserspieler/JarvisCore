#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS Quick Fix - Repariert venv Installation

Verwendung:
  python scripts/quick_fix_venv.py
"""

import sys
import subprocess
from pathlib import Path

print("🔧 JARVIS Quick Fix - Venv Reparatur")
print("="*50)

# Check if in venv
if sys.prefix == sys.base_prefix:
    print("❌ Nicht in venv!")
    print("\nFühre aus:")
    print("  venv\\Scripts\\activate  (Windows)")
    print("  source venv/bin/activate  (Linux/Mac)")
    sys.exit(1)

print("✅ Venv aktiv")
print(f"   Pfad: {sys.prefix}\n")

# Critical packages
critical = [
    "numpy>=1.24.3",
    "pandas>=2.0.0",
    "torch>=2.1.0",
    "fastapi>=0.111.0",
    "uvicorn>=0.23.0",
]

print("📦 Installiere kritische Pakete...\n")

for pkg in critical:
    print(f"  ➤ {pkg}")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            check=True,
            capture_output=True
        )
        print(f"    ✅ Installiert")
    except subprocess.CalledProcessError as e:
        print(f"    ❌ Fehler: {e}")

print("\n📦 Installiere alle requirements...\n")

req_file = Path("requirements.txt")
if req_file.exists():
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True
        )
        print("\n✅ Alle Pakete installiert!")
    except subprocess.CalledProcessError:
        print("\n⚠️  Einige Pakete fehlgeschlagen")
else:
    print("❌ requirements.txt nicht gefunden")

print("\n" + "="*50)
print("✅ Fix abgeschlossen!")
print("\nStarte JARVIS:")
print("  python main.py")
