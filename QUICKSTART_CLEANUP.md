# 🚀 Quick Start - JarvisCore Bereinigung

## ⚡ Schnell-Anleitung (5 Minuten)

### Schritt 1: Branches aktualisieren

```bash
cd /pfad/zu/JarvisCore

# Alle Änderungen holen
git fetch origin

# Cleanup-Branch (bereits gemergt)
git checkout main
git pull origin main

# Module-Reorganisation (vorbereitet)
git checkout refactor/organize-modules
git pull origin refactor/organize-modules
```

### Schritt 2: Bereinigung durchführen

```bash
# Zurück zu main
git checkout main

# Lokale Cache-Bereinigung
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Status prüfen
git status
```

### Schritt 3: Modul-Reorganisation (Optional)

```bash
# Branch mergen (oder lokal testen)
git merge refactor/organize-modules

# Reorganisations-Script ausführen
python scripts/reorganize_modules.py --execute

# Tests
pytest
python main.py --help

# Bei Erfolg committen
git add .
git commit -m "refactor: apply module reorganization"
git push origin main
```

## 📝 Was wurde gemacht?

### ✅ Bereits gemergt (PR #3)

1. **.gitignore hinzugefügt**
   - Ignoriert `__pycache__/`, `*.pyc`, `*.log`
   - Ignoriert große Model-Dateien
   - Schützt sensitive Daten

2. **Redundante TTS-Dateien gelöscht (7 Dateien, ~50 KB)**
   - `xtts_manager.py`
   - `xtts_tts.py`
   - `xtts_tts_fixed.py`
   - `xttsv2_tts.py`
   - `xttsv2_clone.py`
   - `reliable_tts.py`
   - `simple_tts.py`
   - **Behalten:** `text_to_speech.py`

3. **Duplikate entfernt**
   - `context_manager.py` → `adaptive_context_manager.py`
   - `clarification_module.py` → `clarification.py`

4. **.gitkeep Dateien**
   - `logs/.gitkeep`
   - `models/.gitkeep`

### ⏳ Vorbereitet (PR #4)

**Modul-Reorganisation:**
- Script: `scripts/reorganize_modules.py`
- Guide: `REFACTORING_GUIDE.md`
- Reorganisiert `core/` in logische Submodule

## 🧪 Schnelltest

```bash
# TTS-System testen
python -c "from core.text_to_speech import TextToSpeech; print('✅ TTS funktioniert')"

# Context Manager testen
python -c "from core.adaptive_context_manager import AdaptiveContextManager; print('✅ Context funktioniert')"

# Clarification testen
python -c "from core.clarification import ClarificationSystem; print('✅ Clarification funktioniert')"

# Hauptprogramm
python main.py --help
```

## 📊 Ergebnis

### Cleanup (PR #3)
- ✅ 9 redundante Dateien entfernt
- ✅ ~58 KB Code gespart
- ✅ .gitignore hinzugefügt
- ✅ Projekt-Hygiene verbessert

### Module-Reorg (PR #4)
- ⏳ 50+ Dateien → 7 logische Module
- ⏳ Bessere Navigation
- ⏳ Klarere Struktur

## ⚠️ Troubleshooting

### Problem: Import-Fehler nach Cleanup

```bash
# Lösung: Alte .pyc Dateien löschen
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Python neu starten
python main.py
```

### Problem: Modul nicht gefunden

```python
# Fehler: ModuleNotFoundError: No module named 'core.xtts_manager'

# Lösung: Diese Dateien wurden gelöscht
# Verwende stattdessen:
from core.text_to_speech import TextToSpeech
```

### Problem: Git Merge-Konflikt

```bash
# Rollback
git merge --abort

# Oder reset
git reset --hard origin/main
```

## 🔄 Rollback (falls nötig)

### Cleanup rückgängig machen

```bash
# Zurück vor den Cleanup
git log --oneline -20  # Finde Commit-Hash vor Cleanup
git reset --hard <commit-hash>

# Oder mit Tag (falls erstellt)
git reset --hard pre-cleanup-backup
```

### Modul-Reorganisation rückgängig machen

```bash
# Falls bereits ausgeführt
git reset --hard HEAD~1

# Falls committed aber nicht gepusht
git reset --hard origin/main
```

## 📚 Weitere Infos

- **Cleanup Details:** `CLEANUP_SUMMARY.md`
- **Modul-Reorg:** `REFACTORING_GUIDE.md`
- **Script Hilfe:** `python scripts/reorganize_modules.py --help`

## ✅ Fertig!

Dein JarvisCore ist jetzt sauberer und besser organisiert! 🎉

**Nächste Empfehlungen:**
1. Tests regelmäßig ausführen: `pytest`
2. Pre-commit Hooks einrichten (zukünftig)
3. CI/CD Pipeline konfigurieren (zukünftig)
4. Type Hints hinzufügen (schrittweise)
