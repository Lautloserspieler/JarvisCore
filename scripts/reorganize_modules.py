#!/usr/bin/env python3
"""
Automatisches Modul-Reorganisations-Script für JarvisCore

Dieses Script reorganisiert die flache core/-Struktur in logische Submodule:
- core/memory/     - Alle Memory-Komponenten
- core/speech/     - Alle Speech-Komponenten
- core/llm/        - Alle LLM-Komponenten
- core/knowledge/  - Alle Knowledge-Komponenten
- core/security/   - Alle Security-Komponenten
- core/system/     - Alle System-Komponenten
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import re

# Modul-Zuordnungen
MODULE_MAPPING: Dict[str, List[str]] = {
    'memory': [
        'memory_manager.py',
        'short_term_memory.py',
        'long_term_memory.py',
        'vector_memory.py',
        'timeline_memory.py',
        'memory_system.py',  # Falls unterschiedlich zu memory_manager
    ],
    'speech': [
        'speech_recognition.py',
        'text_to_speech.py',
        'speech_manager.py',
        'hotword_manager.py',
        'audio_playback.py',
    ],
    'llm': [
        'llm_manager.py',
        'llm_router.py',
        'async_llm_wrapper.py',
    ],
    'knowledge': [
        'knowledge_manager.py',
        'knowledge_processor.py',
        'knowledge_expansion_agent.py',
        'local_knowledge_importer.py',
        'local_knowledge_scanner.py',
    ],
    'security': [
        'security_manager.py',
        'security_protocol.py',
        'adaptive_access_control.py',
        'safe_shell.py',
        'sensitive_safe.py',
    ],
    'system': [
        'system_control.py',
        'system_monitor.py',
    ],
    'learning': [
        'learning_manager.py',
        'reinforcement_learning.py',
        'long_term_trainer.py',
    ],
}

# Import-Mappings für automatische Anpassung
IMPORT_REWRITES = {
    'from core.memory_manager import': 'from core.memory import',
    'from core.short_term_memory import': 'from core.memory import',
    'from core.long_term_memory import': 'from core.memory import',
    'from core.vector_memory import': 'from core.memory import',
    'from core.timeline_memory import': 'from core.memory import',
    'from core.speech_recognition import': 'from core.speech import',
    'from core.text_to_speech import': 'from core.speech import',
    'from core.llm_manager import': 'from core.llm import',
    'from core.knowledge_manager import': 'from core.knowledge import',
    'from core.security_manager import': 'from core.security import',
    'from core.system_control import': 'from core.system import',
}

class ModuleReorganizer:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.root = Path.cwd()
        self.core_dir = self.root / 'core'
        self.changes: List[str] = []
        self.moved_files: Dict[str, str] = {}  # old_path -> new_path
        
    def log(self, message: str, level: str = "INFO"):
        prefix = "🔍 [DRY-RUN]" if self.dry_run else "✅ [EXEC]"
        print(f"{prefix} [{level}] {message}")
        self.changes.append(message)
    
    def create_submodule_structure(self):
        """Erstelle Submodul-Verzeichnisse mit __init__.py"""
        self.log("=" * 60)
        self.log("PHASE 1: Erstelle Submodul-Struktur", "PHASE")
        self.log("=" * 60)
        
        for module_name in MODULE_MAPPING.keys():
            module_dir = self.core_dir / module_name
            init_file = module_dir / '__init__.py'
            
            if not self.dry_run:
                module_dir.mkdir(parents=True, exist_ok=True)
                if not init_file.exists():
                    init_file.write_text(self._generate_init_content(module_name))
            
            self.log(f"Erstellt: core/{module_name}/__init__.py")
        
        self.log("")
    
    def _generate_init_content(self, module_name: str) -> str:
        """Generiere __init__.py Inhalt für ein Submodul"""
        files = MODULE_MAPPING[module_name]
        imports = []
        exports = []
        
        for filename in files:
            if not filename.endswith('.py'):
                continue
            module = filename[:-3]  # Entferne .py
            # Konvertiere snake_case zu PascalCase für Klassennamen
            class_name = ''.join(word.capitalize() for word in module.split('_'))
            imports.append(f"from .{module} import {class_name}")
            exports.append(f"'{class_name}'")
        
        content = f'''"""
JarvisCore {module_name.capitalize()} Module

Dieses Modul enthält alle {module_name}-bezogenen Komponenten.
"""

{chr(10).join(imports)}

__all__ = [
    {(chr(10) + '    ').join(exports)}
]
'''
        return content
    
    def move_files(self):
        """Verschiebe Dateien in ihre Submodule"""
        self.log("=" * 60)
        self.log("PHASE 2: Verschiebe Dateien in Submodule", "PHASE")
        self.log("=" * 60)
        
        for module_name, files in MODULE_MAPPING.items():
            for filename in files:
                old_path = self.core_dir / filename
                new_path = self.core_dir / module_name / filename
                
                if not old_path.exists():
                    self.log(f"⚠️  Überspringe {filename} (nicht gefunden)", "SKIP")
                    continue
                
                if self.dry_run:
                    self.log(f"Würde verschieben: {filename} -> {module_name}/{filename}")
                else:
                    shutil.move(str(old_path), str(new_path))
                    self.log(f"Verschoben: {filename} -> {module_name}/{filename}", "MOVE")
                
                self.moved_files[str(old_path.relative_to(self.root))] = str(new_path.relative_to(self.root))
        
        self.log(f"\nGesamt verschoben: {len(self.moved_files)} Dateien\n")
    
    def update_imports(self):
        """Aktualisiere Imports in allen Python-Dateien"""
        self.log("=" * 60)
        self.log("PHASE 3: Aktualisiere Imports", "PHASE")
        self.log("=" * 60)
        
        python_files = list(self.root.rglob('*.py'))
        updated_count = 0
        
        for py_file in python_files:
            if '.git' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                # Ersetze alte Imports durch neue
                for old_import, new_import in IMPORT_REWRITES.items():
                    content = content.replace(old_import, new_import)
                
                # Wenn Änderungen gemacht wurden
                if content != original_content:
                    if not self.dry_run:
                        py_file.write_text(content, encoding='utf-8')
                    updated_count += 1
                    rel_path = py_file.relative_to(self.root)
                    self.log(f"Imports aktualisiert in: {rel_path}", "UPDATE")
                    
            except Exception as e:
                self.log(f"Fehler beim Verarbeiten von {py_file}: {e}", "ERROR")
        
        self.log(f"\nImports in {updated_count} Dateien aktualisiert\n")
    
    def create_migration_readme(self):
        """Erstelle README mit Migrations-Informationen"""
        self.log("=" * 60)
        self.log("PHASE 4: Erstelle Migrations-Dokumentation", "PHASE")
        self.log("=" * 60)
        
        readme_content = f'''# Modul-Reorganisation

**Datum:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Übersicht

Die flache `core/`-Struktur wurde in logische Submodule reorganisiert:

'''
        
        for module_name, files in MODULE_MAPPING.items():
            readme_content += f'''### core/{module_name}/

'''
            for filename in files:
                old_import = f"from core.{filename[:-3]} import"
                new_import = f"from core.{module_name} import"
                readme_content += f"- `{filename}` \n"
            readme_content += f'''
**Import-Änderung:**
```python
# Alt
from core.{files[0][:-3]} import ClassName

# Neu
from core.{module_name} import ClassName
```

'''
        
        readme_content += f'''## Verschobene Dateien

| Alt | Neu |
|-----|-----|
'''
        for old, new in self.moved_files.items():
            readme_content += f"| `{old}` | `{new}` |\n"
        
        readme_content += '''\n## Nächste Schritte

1. **Tests ausführen:**
   ```bash
   pytest
   python main.py --help
   ```

2. **Manuelle Import-Überprüfung:**
   - Prüfe ob alle Imports korrekt aktualisiert wurden
   - Achte auf dynamische Imports (importlib, __import__)

3. **Git Commit:**
   ```bash
   git add .
   git commit -m "refactor: reorganize core modules into logical submodules"
   ```

## Rollback

Falls Probleme auftreten:
```bash
git reset --hard HEAD~1
```
'''
        
        readme_file = self.root / 'MODULE_MIGRATION.md'
        if not self.dry_run:
            readme_file.write_text(readme_content, encoding='utf-8')
        
        self.log(f"Migrations-Dokumentation erstellt: MODULE_MIGRATION.md")
        self.log("")
    
    def run(self):
        """Führe vollständige Reorganisation durch"""
        print("\n" + "=" * 60)
        print("🏗️  JarvisCore - Modul-Reorganisation")
        print("=" * 60 + "\n")
        
        self.create_submodule_structure()
        self.move_files()
        self.update_imports()
        self.create_migration_readme()
        
        # Zusammenfassung
        print("\n" + "=" * 60)
        print("ZUSAMMENFASSUNG")
        print("=" * 60)
        
        if self.dry_run:
            print("🔍 Dies war ein DRY-RUN. Keine Änderungen wurden vorgenommen.")
            print("    Um die Änderungen durchzuführen:")
            print("    python scripts/reorganize_modules.py --execute")
        else:
            print("✅ Reorganisation abgeschlossen!")
            print(f"    {len(self.moved_files)} Dateien verschoben")
            print("    Imports aktualisiert")
            print("    Dokumentation erstellt")
        
        print("\nNächste Schritte:")
        print("1. Tests ausführen: pytest")
        print("2. Programm testen: python main.py --help")
        print("3. Änderungen committen")
        print("")

if __name__ == "__main__":
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("⚠️  DRY-RUN Modus - Keine Änderungen")
        print("    Führe mit --execute aus, um Änderungen durchzuführen\n")
    else:
        print("⚠️  EXECUTE Modus!")
        response = input("Modul-Reorganisation durchführen? (ja/nein): ")
        if response.lower() not in ["ja", "j", "yes", "y"]:
            print("Abgebrochen.")
            sys.exit(0)
        print("")
    
    reorganizer = ModuleReorganizer(dry_run=dry_run)
    reorganizer.run()
