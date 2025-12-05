#!/usr/bin/env python3
"""
Web UI Cleanup Script

Entfernt die alte Web UI (webapp/) aus dem Repository.
Nach der Migration zur Desktop UI ist die Web UI obsolet.

Usage:
    python scripts/cleanup_webapp.py
"""

import os
import shutil
from pathlib import Path

# Liste der zu löschenden Dateien/Verzeichnisse
WEBAPP_FILES = [
    'webapp/',  # Komplettes webapp-Verzeichnis
]

# Liste der Dateien, die Referenzen zur Web UI enthalten könnten
FILES_TO_CHECK = [
    'main.py',
    'README.md',
    'requirements.txt',
    'docs/SETUP.md',
]

def main():
    repo_root = Path(__file__).parent.parent
    print("🧹 Web UI Cleanup wird gestartet...\n")
    print(f"Repository Root: {repo_root}\n")
    
    # 1. Lösche webapp-Verzeichnis
    print("=" * 60)
    print("1. Lösche webapp-Verzeichnis")
    print("=" * 60)
    
    for item in WEBAPP_FILES:
        path = repo_root / item
        if path.exists():
            if path.is_dir():
                print(f"❌ Lösche Verzeichnis: {path}")
                shutil.rmtree(path)
            else:
                print(f"❌ Lösche Datei: {path}")
                path.unlink()
        else:
            print(f"⚠️  Nicht gefunden: {path}")
    
    print("\n" + "=" * 60)
    print("2. Prüfe Dateien auf Web UI Referenzen")
    print("=" * 60)
    
    # 2. Prüfe Referenzen (nur Warnung, kein automatisches Ändern)
    references_found = False
    for file_path in FILES_TO_CHECK:
        path = repo_root / file_path
        if path.exists() and path.is_file():
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Suche nach Web UI Referenzen
            keywords = ['webapp', 'web ui', 'web-ui', 'web interface', 'browser interface']
            found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
            
            if found_keywords:
                print(f"\n⚠️  {file_path} enthält mögliche Web UI Referenzen:")
                for kw in found_keywords:
                    print(f"   - '{kw}'")
                references_found = True
    
    if not references_found:
        print("\n✅ Keine Web UI Referenzen in Standard-Dateien gefunden.")
    
    # 3. Git Status
    print("\n" + "=" * 60)
    print("3. Git Status")
    print("=" * 60)
    print("\nFühre folgende Befehle aus, um die Änderungen zu committen:\n")
    print("git add -A")
    print('git commit -m "chore: remove deprecated Web UI (webapp/)"')
    print("git push origin main")
    
    print("\n" + "=" * 60)
    print("✅ Cleanup abgeschlossen!")
    print("=" * 60)
    print("\n💡 Nächste Schritte:")
    print("   1. Prüfe die Dateien in FILES_TO_CHECK manuell")
    print("   2. Entferne Web UI Referenzen aus README/Docs")
    print("   3. Update main.py: Entferne webapp Import")
    print("   4. Committe die Änderungen")
    print("\n🚀 Die Desktop UI ist jetzt das einzige Frontend!\n")

if __name__ == '__main__':
    main()
