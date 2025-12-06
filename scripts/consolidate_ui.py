#!/usr/bin/env python3
"""
UI Consolidation Script
Entfernt WebApp und konsolidiert zu Desktop-App als einzige UI
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List

class UIConsolidator:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.root = Path.cwd()
        self.changes: List[str] = []
        
    def log(self, message: str, level: str = "INFO"):
        prefix = "🔍 [DRY-RUN]" if self.dry_run else "✅ [EXEC]"
        print(f"{prefix} [{level}] {message}")
        self.changes.append(message)
    
    def create_deprecation_notice(self) -> bool:
        """Erstelle Deprecation Notice in webapp/"""
        self.log("=" * 60, "PHASE")
        self.log("PHASE 1: Deprecation Notice erstellen", "PHASE")
        self.log("=" * 60, "PHASE")
        
        webapp_dir = self.root / 'webapp'
        
        if not webapp_dir.exists():
            self.log("✅ webapp/ existiert nicht (bereits entfernt)", "SKIP")
            return False
        
        deprecated_file = webapp_dir / 'DEPRECATED.md'
        
        content = '''# ❌ DEPRECATED - WebApp wurde eingestellt

**Status:** Diese WebApp ist veraltet und wird entfernt.

## ⚠️ Wichtig

Diese WebApp wurde zugunsten der **Desktop-App** eingestellt.

## ✅ Alternative: Desktop-App

**Bitte verwende die offizielle Desktop-App:**

- **Standort:** `desktop/`
- **README:** [desktop/README.md](../desktop/README.md)
- **QuickStart:** [desktop/QUICKSTART.md](../desktop/QUICKSTART.md)

### Vorteile der Desktop-App

- ✅ Native Anwendung (Windows, Linux, macOS)
- ✅ Bessere Performance
- ✅ Keine Port-Exposition
- ✅ Systemintegration (Tray, Hotkeys)
- ✅ Moderne Web-UI im nativen Container
- ✅ Aktive Entwicklung & Support

## 🚀 Migration

### Quick Start Desktop-App

```bash
# Entwicklung
cd desktop
wails dev

# Build
cd desktop
./build.sh    # Linux/macOS
./build.bat   # Windows

# Run
./desktop/build/bin/JarvisCore
```

### Konfiguration übertragen

Falls du spezifische webapp-Konfigurationen hast:

1. Öffne `webapp/config.json` (falls vorhanden)
2. Kopiere relevante Einstellungen
3. Füge sie in `desktop/config.json` ein

## 📝 Details

Siehe [UI_CONSOLIDATION.md](../UI_CONSOLIDATION.md) für vollständige Details.

## 📅 Timeline

- **06.12.2025:** Deprecated (dieses Dokument erstellt)
- **Nächstes Release:** Vollständig entfernt aus Repository

---

**Fragen?** Erstelle ein Issue auf GitHub.
'''
        
        if self.dry_run:
            self.log(f"Würde erstellen: {deprecated_file}")
        else:
            deprecated_file.write_text(content, encoding='utf-8')
            self.log(f"Erstellt: {deprecated_file}", "CREATE")
        
        return True
    
    def remove_webapp(self) -> bool:
        """Entferne webapp/ Verzeichnis komplett"""
        self.log("\n" + "=" * 60, "PHASE")
        self.log("PHASE 2: webapp/ entfernen", "PHASE")
        self.log("=" * 60, "PHASE")
        
        webapp_dir = self.root / 'webapp'
        
        if not webapp_dir.exists():
            self.log("✅ webapp/ existiert nicht (bereits entfernt)", "SKIP")
            return False
        
        # Berechne Größe
        total_size = 0
        file_count = 0
        for path in webapp_dir.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
                file_count += 1
        
        size_kb = total_size / 1024
        
        if self.dry_run:
            self.log(f"Würde löschen: {webapp_dir}")
            self.log(f"  Dateien: {file_count}")
            self.log(f"  Größe: {size_kb:.1f} KB")
        else:
            try:
                shutil.rmtree(webapp_dir)
                self.log(f"Gelöscht: {webapp_dir}", "DELETE")
                self.log(f"  Dateien: {file_count}")
                self.log(f"  Größe: {size_kb:.1f} KB")
            except Exception as e:
                self.log(f"Fehler beim Löschen: {e}", "ERROR")
                return False
        
        return True
    
    def update_readme(self) -> bool:
        """Update README.md - entferne webapp Referenzen"""
        self.log("\n" + "=" * 60, "PHASE")
        self.log("PHASE 3: README.md aktualisieren", "PHASE")
        self.log("=" * 60, "PHASE")
        
        readme = self.root / 'README.md'
        
        if not readme.exists():
            self.log("⚠️  README.md nicht gefunden", "SKIP")
            return False
        
        content = readme.read_text(encoding='utf-8')
        original_content = content
        
        # Entferne webapp-Referenzen
        replacements = [
            ('webapp/', ''),
            ('WebApp', ''),
            ('Flask-Server', ''),
            ('Browser-UI', ''),
        ]
        
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
        
        # Füge Desktop-App Hinweis hinzu (falls nicht vorhanden)
        if 'Desktop-App' not in content and 'desktop/' in str(self.root):
            desktop_section = '''
## 🖥️ Desktop-App

JarvisCore verwendet eine native Desktop-Anwendung als primäre Benutzeroberfläche.

**Standort:** `desktop/`  
**Technologie:** Wails (Go Backend + Web Frontend)  
**Plattformen:** Windows, Linux, macOS

### Quick Start

```bash
cd desktop
wails dev          # Entwicklung
./build.sh         # Production Build
```

Siehe [desktop/README.md](desktop/README.md) für Details.
'''
            content = content + "\n" + desktop_section
        
        if content != original_content:
            if self.dry_run:
                self.log("Würde README.md aktualisieren")
            else:
                readme.write_text(content, encoding='utf-8')
                self.log("README.md aktualisiert", "UPDATE")
            return True
        else:
            self.log("README.md benötigt keine Änderungen", "SKIP")
            return False
    
    def update_gitignore(self) -> bool:
        """Update .gitignore - entferne webapp-spezifische Einträge"""
        self.log("\n" + "=" * 60, "PHASE")
        self.log("PHASE 4: .gitignore bereinigen", "PHASE")
        self.log("=" * 60, "PHASE")
        
        gitignore = self.root / '.gitignore'
        
        if not gitignore.exists():
            self.log("⚠️  .gitignore nicht gefunden", "SKIP")
            return False
        
        content = gitignore.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Entferne webapp-spezifische Zeilen
        webapp_patterns = [
            'webapp/static/uploads/',
            'webapp/static/temp/',
            'webapp/__pycache__/',
            'webapp/*.pyc',
        ]
        
        new_lines = []
        removed_count = 0
        for line in lines:
            should_keep = True
            for pattern in webapp_patterns:
                if pattern in line:
                    should_keep = False
                    removed_count += 1
                    break
            if should_keep:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        if removed_count > 0:
            if self.dry_run:
                self.log(f"Würde .gitignore bereinigen ({removed_count} Zeilen)")
            else:
                gitignore.write_text(new_content, encoding='utf-8')
                self.log(f".gitignore bereinigt ({removed_count} Zeilen entfernt)", "UPDATE")
            return True
        else:
            self.log(".gitignore benötigt keine Änderungen", "SKIP")
            return False
    
    def create_summary(self):
        """Erstelle Zusammenfassung"""
        self.log("\n" + "=" * 60, "PHASE")
        self.log("ZUSAMMENFASSUNG", "PHASE")
        self.log("=" * 60, "PHASE")
        
        if self.dry_run:
            self.log("🔍 Dies war ein DRY-RUN")
            self.log("")
            self.log("Um die Änderungen durchzuführen:")
            self.log("  python scripts/consolidate_ui.py --execute")
        else:
            self.log("✅ UI-Konsolidierung abgeschlossen!")
            self.log("")
            self.log("Durchgeführte Änderungen:")
            for change in self.changes:
                if 'CREATE' in change or 'DELETE' in change or 'UPDATE' in change:
                    self.log(f"  - {change}")
        
        self.log("")
        self.log("Nächste Schritte:")
        self.log("1. Desktop-App testen: cd desktop && wails dev")
        self.log("2. Desktop-App bauen: cd desktop && ./build.sh")
        self.log("3. Änderungen committen")
        self.log("4. Pull Request erstellen")
    
    def run(self):
        """Führe vollständige UI-Konsolidierung durch"""
        print("\n" + "=" * 60)
        print("🖥️  JarvisCore - UI-Konsolidierung")
        print("Ziel: Nur Desktop-App behalten")
        print("=" * 60 + "\n")
        
        # Phase 1: Deprecation Notice (nur wenn webapp/ existiert)
        self.create_deprecation_notice()
        
        # Phase 2: WebApp entfernen
        self.remove_webapp()
        
        # Phase 3: README aktualisieren
        self.update_readme()
        
        # Phase 4: .gitignore bereinigen
        self.update_gitignore()
        
        # Zusammenfassung
        self.create_summary()

if __name__ == "__main__":
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("⚠️  DRY-RUN Modus - Keine Änderungen")
        print("    Führe mit --execute aus, um Änderungen durchzuführen\n")
    else:
        print("⚠️  EXECUTE Modus!")
        response = input("WebApp entfernen und zu Desktop-App konsolidieren? (ja/nein): ")
        if response.lower() not in ["ja", "j", "yes", "y"]:
            print("Abgebrochen.")
            sys.exit(0)
        print("")
    
    consolidator = UIConsolidator(dry_run=dry_run)
    consolidator.run()
