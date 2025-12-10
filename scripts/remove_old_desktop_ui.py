#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS - Remove Old Desktop UI

Löscht die alte DearPyGui Desktop UI und alle zugehörigen Files.

USAGE:
  python scripts/remove_old_desktop_ui.py
"""

import shutil
import os
from pathlib import Path

print("🗑️  JARVIS Desktop UI Cleanup")
print("="*60)
print()

# Root directory
root = Path(__file__).parent.parent
desktop_dir = root / "desktop"

if not desktop_dir.exists():
    print("✅ Desktop UI bereits entfernt!")
    exit(0)

print("⚠️  Dies wird die alte Desktop UI entfernen:")
print(f"   {desktop_dir}")
print()
print("Folgende Dateien werden gelöscht:")
print()

# List files to delete
files_to_delete = [
    "jarvis_imgui_app_full.py",
    "README.md",
    "QUICKSTART.md",
    "Makefile",
    "build.bat",
    "build.sh",
    "wails.json",
    "go.mod",
    "config.json",
    "config.json.example",
    "start-dev.bat",
    "__init__.py",
    ".gitignore"
]

dirs_to_delete = [
    "backend",
    "frontend", 
    "docs"
]

for f in files_to_delete:
    fp = desktop_dir / f
    if fp.exists():
        print(f"  ❌ {f}")

for d in dirs_to_delete:
    dp = desktop_dir / d
    if dp.exists():
        print(f"  ❌ {d}/ (entire directory)")

print()
response = input("🚨 Wirklich löschen? (yes/no): ").strip().lower()

if response != "yes":
    print("\n⚠️  Abgebrochen. Nichts wurde gelöscht.")
    exit(0)

print()
print("🗑️  Lösche Dateien...")

# Delete files
for f in files_to_delete:
    fp = desktop_dir / f
    if fp.exists():
        try:
            fp.unlink()
            print(f"  ✅ Gelöscht: {f}")
        except Exception as e:
            print(f"  ❌ Fehler: {f} - {e}")

# Delete directories
for d in dirs_to_delete:
    dp = desktop_dir / d
    if dp.exists():
        try:
            shutil.rmtree(dp)
            print(f"  ✅ Gelöscht: {d}/")
        except Exception as e:
            print(f"  ❌ Fehler: {d}/ - {e}")

# Check if desktop dir is empty (except DEPRECATED.md)
remaining = list(desktop_dir.iterdir())
if len(remaining) <= 1:  # Only DEPRECATED.md should remain
    print()
    print("✅ Desktop UI erfolgreich entfernt!")
    print()
    print("🌐 Verwende jetzt die Web UI:")
    print("   python main_web.py")
    print("   http://localhost:8000")
else:
    print()
    print("⚠️  Einige Dateien konnten nicht gelöscht werden:")
    for item in remaining:
        if item.name != "DEPRECATED.md":
            print(f"   - {item.name}")

print()
