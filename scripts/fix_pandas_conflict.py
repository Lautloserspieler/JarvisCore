#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS Pandas Conflict Fix

Löst den geopandas/pandas Versions-Konflikt
"""

import sys
import subprocess

print("🔧 JARVIS Pandas Conflict Fix")
print("="*50)
print()

if sys.prefix == sys.base_prefix:
    print("❌ Nicht in venv! Aktiviere zuerst:")
    print("  venv\\Scripts\\activate")
    sys.exit(1)

print("✅ Venv aktiv")
print()

print("📦 Deinstalliere alte pandas...")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "pandas"])

print("\n📦 Installiere pandas 2.x...")
subprocess.run([sys.executable, "-m", "pip", "install", "pandas>=2.0.0,<3.0"])

print("\n✅ Pandas Konflikt gelöst!")
print("\nStarte JARVIS:")
print("  python main.py")
