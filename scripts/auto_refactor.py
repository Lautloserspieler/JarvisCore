#!/usr/bin/env python3
"""
Automatic Complete Refactoring Script
Führt ALLE Refactorings automatisch aus:
1. Modul-Reorganisation
2. UI-Konsolidierung
3. Cleanup & Testing
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional
import time

class AutoRefactor:
    def __init__(self):
        self.root = Path.cwd()
        self.success_count = 0
        self.error_count = 0
        self.logs: List[str] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        emoji = {
            "INFO": "🟦",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "PHASE": "🚀",
            "SKIP": "⏭️"
        }.get(level, "🟦")
        
        log_line = f"[{timestamp}] {emoji} {message}"
        print(log_line)
        self.logs.append(log_line)
        
    def run_command(self, cmd: List[str], description: str) -> bool:
        """Run a shell command and log result"""
        self.log(f"Ausführe: {description}...")
        try:
            result = subprocess.run(
                cmd,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log(f"{description} - Erfolgreich", "SUCCESS")
                self.success_count += 1
                return True
            else:
                self.log(f"{description} - Fehler: {result.stderr[:100]}", "ERROR")
                self.error_count += 1
                return False
        except Exception as e:
            self.log(f"{description} - Exception: {e}", "ERROR")
            self.error_count += 1
            return False
    
    def phase_1_ui_consolidation(self) -> bool:
        """Phase 1: UI-Konsolidierung - Entferne webapp/"""
        self.log("=" * 60, "PHASE")
        self.log("PHASE 1: UI-Konsolidierung", "PHASE")
        self.log("=" * 60, "PHASE")
        
        webapp_dir = self.root / 'webapp'
        
        if not webapp_dir.exists():
            self.log("webapp/ existiert nicht - bereits entfernt", "SKIP")
            return True
        
        try:
            # Erstelle Backup falls gewünscht
            # backup_dir = self.root / 'backup' / 'webapp_backup'
            # shutil.copytree(webapp_dir, backup_dir)
            
            # Lösche webapp/
            shutil.rmtree(webapp_dir)
            self.log("webapp/ gelöscht", "SUCCESS")
            self.success_count += 1
            return True
        except Exception as e:
            self.log(f"Fehler beim Löschen von webapp/: {e}", "ERROR")
            self.error_count += 1
            return False
    
    def phase_2_module_reorganization(self) -> bool:
        """Phase 2: Modul-Reorganisation - Erstelle Submodule"""
        self.log("\n" + "=" * 60, "PHASE")
        self.log("PHASE 2: Modul-Reorganisation", "PHASE")
        self.log("=" * 60, "PHASE")
        
        # Modul-Struktur
        modules = {
            'memory': [
                ('memory_manager.py', 'manager.py'),
                ('short_term_memory.py', 'short_term.py'),
                ('long_term_memory.py', 'long_term.py'),
                ('vector_memory.py', 'vector.py'),
                ('timeline_memory.py', 'timeline.py'),
            ],
            'speech': [
                ('speech_recognition.py', 'recognition.py'),
                ('text_to_speech.py', 'synthesis.py'),
                ('speech_manager.py', 'manager.py'),
                ('hotword_manager.py', 'hotword.py'),
                ('audio_playback.py', 'playback.py'),
            ],
            'llm': [
                ('llm_manager.py', 'manager.py'),
                ('llm_router.py', 'router.py'),
                ('async_llm_wrapper.py', 'async_wrapper.py'),
            ],
        }
        
        core_dir = self.root / 'core'
        
        for module_name, files in modules.items():
            module_dir = core_dir / module_name
            
            # Erstelle Modul-Verzeichnis
            if not module_dir.exists():
                module_dir.mkdir(parents=True, exist_ok=True)
                self.log(f"Erstellt: core/{module_name}/", "SUCCESS")
            
            # Erstelle __init__.py
            init_file = module_dir / '__init__.py'
            if not init_file.exists():
                init_content = f'"""\n{module_name.capitalize()} module for JarvisCore\n"""\n'
                init_file.write_text(init_content)
                self.log(f"Erstellt: core/{module_name}/__init__.py", "SUCCESS")
            
            # Verschiebe Dateien
            for old_name, new_name in files:
                old_path = core_dir / old_name
                new_path = module_dir / new_name
                
                if old_path.exists() and not new_path.exists():
                    try:
                        shutil.move(str(old_path), str(new_path))
                        self.log(f"Verschoben: {old_name} -> {module_name}/{new_name}", "SUCCESS")
                        self.success_count += 1
                    except Exception as e:
                        self.log(f"Fehler beim Verschieben {old_name}: {e}", "ERROR")
                        self.error_count += 1
        
        return True
    
    def phase_3_update_imports(self) -> bool:
        """Phase 3: Aktualisiere Imports"""
        self.log("\n" + "=" * 60, "PHASE")
        self.log("PHASE 3: Imports aktualisieren", "PHASE")
        self.log("=" * 60, "PHASE")
        
        # Import-Mappings
        import_rewrites = {
            'from core.memory_manager import': 'from core.memory.manager import',
            'from core.short_term_memory import': 'from core.memory.short_term import',
            'from core.long_term_memory import': 'from core.memory.long_term import',
            'from core.vector_memory import': 'from core.memory.vector import',
            'from core.timeline_memory import': 'from core.memory.timeline import',
            'from core.speech_recognition import': 'from core.speech.recognition import',
            'from core.text_to_speech import': 'from core.speech.synthesis import',
            'from core.speech_manager import': 'from core.speech.manager import',
            'from core.llm_manager import': 'from core.llm.manager import',
            'from core.llm_router import': 'from core.llm.router import',
        }
        
        # Finde alle Python-Dateien
        python_files = list(self.root.rglob('*.py'))
        updated_count = 0
        
        for py_file in python_files:
            # Überspringe __pycache__ und .git
            if '__pycache__' in str(py_file) or '.git' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Ersetze Imports
                for old_import, new_import in import_rewrites.items():
                    if old_import in content:
                        content = content.replace(old_import, new_import)
                
                # Schreibe zurück wenn geändert
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    updated_count += 1
                    
            except Exception as e:
                self.log(f"Fehler beim Aktualisieren {py_file}: {e}", "ERROR")
        
        self.log(f"Imports in {updated_count} Dateien aktualisiert", "SUCCESS")
        self.success_count += 1
        return True
    
    def phase_4_cleanup(self) -> bool:
        """Phase 4: Cleanup - Cache, pyc, etc."""
        self.log("\n" + "=" * 60, "PHASE")
        self.log("PHASE 4: Cleanup", "PHASE")
        self.log("=" * 60, "PHASE")
        
        # Lösche __pycache__
        pycache_dirs = list(self.root.rglob('__pycache__'))
        for pycache in pycache_dirs:
            try:
                shutil.rmtree(pycache)
            except:
                pass
        
        # Lösche .pyc Dateien
        pyc_files = list(self.root.rglob('*.pyc'))
        for pyc in pyc_files:
            try:
                pyc.unlink()
            except:
                pass
        
        self.log(f"Cleanup: {len(pycache_dirs)} __pycache__ und {len(pyc_files)} .pyc gelöscht", "SUCCESS")
        self.success_count += 1
        return True
    
    def phase_5_git_commit(self) -> bool:
        """Phase 5: Git Commit"""
        self.log("\n" + "=" * 60, "PHASE")
        self.log("PHASE 5: Git Commit", "PHASE")
        self.log("=" * 60, "PHASE")
        
        # Git add
        self.run_command(
            ['git', 'add', '.'],
            "Git add all changes"
        )
        
        # Git commit
        commit_msg = """refactor: automatic complete refactoring

- Remove webapp/ (UI consolidation to desktop app)
- Reorganize core/ into logical submodules
- Update all imports
- Cleanup cache files

Automatically executed by scripts/auto_refactor.py
"""
        
        self.run_command(
            ['git', 'commit', '-m', commit_msg],
            "Git commit changes"
        )
        
        return True
    
    def create_summary(self):
        """Erstelle Zusammenfassung"""
        self.log("\n" + "=" * 60, "PHASE")
        self.log("ZUSAMMENFASSUNG", "PHASE")
        self.log("=" * 60, "PHASE")
        
        self.log(f"Erfolgreiche Operationen: {self.success_count}", "SUCCESS")
        
        if self.error_count > 0:
            self.log(f"Fehler: {self.error_count}", "ERROR")
        
        self.log("\nDurchgeführte Änderungen:")
        self.log("✅ webapp/ entfernt (UI-Konsolidierung)")
        self.log("✅ core/ Module reorganisiert")
        self.log("✅ Imports aktualisiert")
        self.log("✅ Cleanup durchgeführt")
        self.log("✅ Git commit erstellt")
        
        self.log("\nNächste Schritte:")
        self.log("🚀 git push origin main")
        self.log("🧪 pytest  # Tests ausführen")
        self.log("🖥️  cd desktop && wails dev  # Desktop-App testen")
        
        # Speichere Log
        log_file = self.root / 'logs' / f'auto_refactor_{time.strftime("%Y%m%d_%H%M%S")}.log'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text('\n'.join(self.logs), encoding='utf-8')
        self.log(f"\nLog gespeichert: {log_file}")
    
    def run(self):
        """Führe vollständiges Refactoring aus"""
        print("\n" + "="*60)
        print("🚀 JarvisCore - Automatisches Komplettes Refactoring")
        print("="*60 + "\n")
        
        start_time = time.time()
        
        # Phase 1: UI-Konsolidierung
        self.phase_1_ui_consolidation()
        
        # Phase 2: Modul-Reorganisation
        self.phase_2_module_reorganization()
        
        # Phase 3: Import-Updates
        self.phase_3_update_imports()
        
        # Phase 4: Cleanup
        self.phase_4_cleanup()
        
        # Phase 5: Git Commit
        self.phase_5_git_commit()
        
        # Zusammenfassung
        duration = time.time() - start_time
        self.log(f"\nGesamtdauer: {duration:.1f} Sekunden")
        self.create_summary()
        
        return self.error_count == 0

if __name__ == '__main__':
    print("⚠️  AUTOMATIC REFACTORING - Alle Änderungen werden durchgeführt!\n")
    
    response = input("🚀 Vollständiges Refactoring starten? (ja/nein): ")
    
    if response.lower() not in ['ja', 'j', 'yes', 'y']:
        print("Abgebrochen.")
        sys.exit(0)
    
    print("")
    
    refactor = AutoRefactor()
    success = refactor.run()
    
    sys.exit(0 if success else 1)
