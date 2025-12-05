# 🏗️ Modul-Reorganisation - Anleitung

## 🎯 Ziel

Die flache `core/`-Struktur (50+ Dateien) wird in logische, übersichtliche Submodule reorganisiert.

## 📁 Neue Struktur

```
core/
├── memory/              # 🧠 Gedächtnissystem
│   ├── __init__.py
│   ├── manager.py       # memory_manager.py
│   ├── short_term.py    # short_term_memory.py
│   ├── long_term.py     # long_term_memory.py
│   ├── vector.py        # vector_memory.py
│   └── timeline.py      # timeline_memory.py
│
├── speech/              # 🎤 Sprachverarbeitung
│   ├── __init__.py
│   ├── recognition.py   # speech_recognition.py
│   ├── synthesis.py     # text_to_speech.py
│   ├── manager.py       # speech_manager.py
│   ├── hotword.py       # hotword_manager.py
│   └── playback.py      # audio_playback.py
│
├── llm/                 # 🤖 LLM-Integration
│   ├── __init__.py
│   ├── manager.py       # llm_manager.py
│   ├── router.py        # llm_router.py
│   └── async_wrapper.py # async_llm_wrapper.py
│
├── knowledge/           # 📚 Wissensverwaltung
│   ├── __init__.py
│   ├── manager.py       # knowledge_manager.py
│   ├── processor.py     # knowledge_processor.py
│   ├── expansion_agent.py
│   ├── local_importer.py
│   └── local_scanner.py
│
├── security/            # 🔒 Sicherheit
│   ├── __init__.py
│   ├── manager.py       # security_manager.py
│   ├── protocol.py      # security_protocol.py
│   ├── adaptive_access.py
│   ├── safe_shell.py
│   └── sensitive_safe.py
│
├── system/              # ⚙️ Systemsteuerung
│   ├── __init__.py
│   ├── control.py       # system_control.py
│   └── monitor.py       # system_monitor.py
│
├── learning/            # 🎯 Lern-Mechanismen
│   ├── __init__.py
│   ├── manager.py       # learning_manager.py
│   ├── reinforcement.py # reinforcement_learning.py
│   └── trainer.py       # long_term_trainer.py
│
└── ... (verbleibende Core-Dateien)
```

## 🚀 Ausführung

### Option 1: Automatisches Script (Empfohlen)

```bash
# 1. Dry-Run (Vorschau)
python scripts/reorganize_modules.py

# 2. Tatsächliche Ausführung
python scripts/reorganize_modules.py --execute

# 3. Tests
pytest
python main.py --help

# 4. Commit
git add .
git commit -m "refactor: reorganize core modules into logical submodules"
```

### Option 2: Manuell

Falls das Script nicht funktioniert, siehe `scripts/reorganize_modules.py` für die genaue Zuordnung.

## 🔄 Import-Änderungen

### Memory-System

```python
# ❌ Alt
from core.memory_manager import MemoryManager
from core.short_term_memory import ShortTermMemory
from core.long_term_memory import LongTermMemory

# ✅ Neu
from core.memory import MemoryManager, ShortTermMemory, LongTermMemory
```

### Speech-System

```python
# ❌ Alt
from core.speech_recognition import SpeechRecognition
from core.text_to_speech import TextToSpeech

# ✅ Neu
from core.speech import SpeechRecognition, TextToSpeech
```

### LLM-System

```python
# ❌ Alt
from core.llm_manager import LLMManager
from core.llm_router import LLMRouter

# ✅ Neu
from core.llm import LLMManager, LLMRouter
```

### Knowledge-System

```python
# ❌ Alt
from core.knowledge_manager import KnowledgeManager
from core.knowledge_processor import KnowledgeProcessor

# ✅ Neu
from core.knowledge import KnowledgeManager, KnowledgeProcessor
```

### Security-System

```python
# ❌ Alt
from core.security_manager import SecurityManager
from core.security_protocol import SecurityProtocol

# ✅ Neu
from core.security import SecurityManager, SecurityProtocol
```

### System-Control

```python
# ❌ Alt
from core.system_control import SystemControl
from core.system_monitor import SystemMonitor

# ✅ Neu
from core.system import SystemControl, SystemMonitor
```

## ✨ Vorteile

### Code-Organisation
- ✅ Klare Modul-Verantwortlichkeiten
- ✅ Reduzierte Dateianzahl in `core/` (50+ → ~30)
- ✅ Bessere IDE-Navigation
- ✅ Einfachere Orientierung für neue Entwickler

### Wartbarkeit
- ✅ Logische Gruppierung verwandter Funktionalität
- ✅ Einfachere Refactorings innerhalb von Modulen
- ✅ Bessere Testbarkeit durch klare Modul-Grenzen
- ✅ Reduzierte Cognitive Load

### Performance
- ✅ Schnellere IDE-Indexierung
- ✅ Gezieltere Imports (nur benötigte Komponenten)
- ✅ Bessere Code-Completion

## ⚠️ Breaking Changes

**JA** - Alle Imports müssen angepasst werden!

Das automatische Script `reorganize_modules.py` aktualisiert die meisten Imports automatisch.

**Manuelle Nacharbeit erforderlich für:**
- Dynamische Imports (`importlib.import_module(...)`)
- String-basierte Imports
- Imports in Konfigurationsdateien (JSON/YAML)
- Dokumentation

## 🧪 Test-Strategie

### Nach der Migration:

```bash
# 1. Import-Tests
python -c "from core.memory import MemoryManager; print('✅ Memory OK')"
python -c "from core.speech import SpeechRecognition; print('✅ Speech OK')"
python -c "from core.llm import LLMManager; print('✅ LLM OK')"
python -c "from core.knowledge import KnowledgeManager; print('✅ Knowledge OK')"
python -c "from core.security import SecurityManager; print('✅ Security OK')"
python -c "from core.system import SystemControl; print('✅ System OK')"

# 2. Hauptprogramm
python main.py --help

# 3. Vollständige Tests
pytest -v

# 4. Coverage-Report
pytest --cov=core --cov-report=html
```

## 🔙 Rollback

Falls Probleme auftreten:

```bash
# Git Rollback
git reset --hard HEAD~1

# Oder Branch verwerfen
git checkout main
git branch -D refactor/organize-modules
```

## 📝 Checklist

- [ ] Script `reorganize_modules.py` dry-run ausgeführt
- [ ] Dry-run Output überprüft
- [ ] Script mit `--execute` ausgeführt
- [ ] Import-Tests bestanden
- [ ] `main.py --help` funktioniert
- [ ] pytest Tests bestanden
- [ ] Manuelle Funktionstests durchgeführt
- [ ] Dynamische Imports überprüft
- [ ] Dokumentation aktualisiert
- [ ] Änderungen committed
- [ ] Pull Request erstellt

## 📈 Migration Tracking

| Modul | Dateien | Status | Tests |
|-------|---------|--------|-------|
| memory | 5 | ⏳ Pending | ⏳ |
| speech | 5 | ⏳ Pending | ⏳ |
| llm | 3 | ⏳ Pending | ⏳ |
| knowledge | 5 | ⏳ Pending | ⏳ |
| security | 5 | ⏳ Pending | ⏳ |
| system | 2 | ⏳ Pending | ⏳ |
| learning | 3 | ⏳ Pending | ⏳ |

Legende:
- ⏳ Pending
- 🔄 In Progress
- ✅ Done
- ❌ Failed

---

**Erstellt:** 05. Dezember 2025  
**Branch:** `refactor/organize-modules`  
**Verantwortlich:** @Lautloserspieler
