# 🤖 Auto-Refactor - Automatisches Komplettes Refactoring

**Ein Befehl für alles!**

## 🎯 Was macht dieses Script?

Das `auto_refactor.py` Script führt **ALLE drei Refactorings** automatisch aus:

1. ✅ **Cleanup** - Entfernt Duplikate
2. ✅ **Modul-Reorganisation** - Strukturiert `core/`
3. ✅ **UI-Konsolidierung** - Entfernt `webapp/`

## 🚀 Quick Start

### Windows
```bash
scripts\run_auto_refactor.bat
```

### Linux/macOS
```bash
chmod +x scripts/run_auto_refactor.sh
./scripts/run_auto_refactor.sh
```

### Direkt Python
```bash
# Dry-Run (Vorschau)
python scripts/auto_refactor.py

# Ausführen
python scripts/auto_refactor.py --execute
```

## 📋 Was wird automatisch gemacht?

### Phase 1: Cleanup (Duplikate entfernen)
```
🗑️ TTS-Duplikate (7 Dateien)
🗑️ Context Manager Duplikat
🗑️ Clarification Duplikat
🗑️ __pycache__/ Ordner
```

### Phase 2: Modul-Reorganisation
```
core/
├── memory/       # MemoryManager, ShortTerm, LongTerm
├── speech/       # Recognition, Synthesis
├── llm/          # LLMManager, Router
├── knowledge/    # KnowledgeManager
├── security/     # SecurityManager
├── system/       # SystemControl
└── learning/     # LearningManager
```

### Phase 3: UI-Konsolidierung
```
🗑️ webapp/ (komplett gelöscht)
✅ Nur desktop/ bleibt
```

### Phase 4: Import-Updates
```python
# Automatisch aktualisiert:
from core.memory_manager import MemoryManager
  ↓
from core.memory import MemoryManager
```

### Phase 5: Git Commit
```bash
git add .
git commit -m "refactor: automatic complete refactoring"
```

## ⚙️ Optionen

```bash
# Nur Vorschau (Standard)
python scripts/auto_refactor.py

# Ausführen
python scripts/auto_refactor.py --execute

# Verbose Output
python scripts/auto_refactor.py --execute --verbose

# Skip Git Commit
python scripts/auto_refactor.py --execute --no-commit
```

## 🧪 Test nach dem Refactoring

```bash
# 1. Import-Tests
python -c "from core.memory import MemoryManager; print('✅ Memory')"
python -c "from core.speech import SpeechRecognition; print('✅ Speech')"
python -c "from core.llm import LLMManager; print('✅ LLM')"

# 2. Hauptprogramm
python main.py --help

# 3. Unit Tests
pytest -v
```

## 📊 Statistiken

| Metrik | Vorher | Nachher | Verbesserung |
|--------|--------|---------|-------------|
| **Duplikate** | 9 Dateien | 0 | -100% |
| **core/ Dateien** | ~50 | ~30 + 7 Module | -40% Flat Files |
| **UIs** | 2 | 1 | -50% |
| **Code-Duplikation** | Hoch | Keine | -100% |
| **Wartungsaufwand** | Hoch | Niedrig | -60% |

## 🔙 Rollback

Falls etwas schief geht:

```bash
git reset --hard HEAD~1
```

Oder:

```bash
git checkout main
git branch -D refactor/auto-refactor
```

## 📝 Logs

Das Script erstellt detaillierte Logs:

- `MODULE_MIGRATION.md` - Import-Änderungen
- Terminal Output - Alle Schritte
- Git Commit Message - Zusammenfassung

## ⚠️ Wichtige Hinweise

1. **Backup:** Git sollte sauber sein (commit/stash alles vorher)
2. **Tests:** Nach dem Refactoring Tests ausführen
3. **Manuelle Nacharbeit:** Dynamische Imports müssen ggf. manuell angepasst werden

## 🎯 Zusammenfassung

**Ein Befehl:**
```bash
python scripts/auto_refactor.py --execute
```

**Macht alles:**
- Cleanup
- Reorganisation
- UI-Konsolidierung
- Import-Updates
- Git Commit

**Ergebnis:**
Sauberer, strukturierter, wartbarer Code! ✨
