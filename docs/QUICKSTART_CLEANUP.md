# 🚀 Quick Start - Projekt-Bereinigung

**Ziel:** Duplikate entfernen und Repository aufräumen in unter 5 Minuten.

---

## ⚡ Schnellstart

### 1. Branch erstellen
```bash
git checkout -b cleanup/remove-duplicates
```

### 2. Cleanup ausführen
```bash
# Dry-Run (Vorschau)
python scripts/cleanup_duplicates.py

# Ausführen
python scripts/cleanup_duplicates.py --execute
```

### 3. Testen
```bash
# Import-Tests
python -c "from core.text_to_speech import TextToSpeech; print('TTS OK')"
python -c "from core.adaptive_context_manager import AdaptiveContextManager; print('Context OK')"
python -c "from core.clarification import ClarificationSystem; print('Clarification OK')"

# Hauptprogramm
python main.py --help
```

### 4. Committen & Mergen
```bash
git add .
git commit -m "chore: remove duplicate files and add .gitignore"
git push origin cleanup/remove-duplicates

# Pull Request erstellen & mergen
```

---

## 📋 Was wird gemacht?

### ✅ Gelöscht (9 Dateien)
- 7x TTS-Duplikate
- 1x Context Manager Duplikat  
- 1x Clarification Duplikat

### ✅ Hinzugefügt
- `.gitignore` (Python Best Practices)
- `logs/.gitkeep`
- `models/.gitkeep`

### ✅ Behalten (Master-Implementierungen)
- `core/text_to_speech.py`
- `core/adaptive_context_manager.py`
- `core/clarification.py`

---

## 🧪 Verifikation

**Alle Imports funktionieren?**
```bash
python -c "from core.text_to_speech import TextToSpeech; print('✅')"
python -c "from core.adaptive_context_manager import AdaptiveContextManager; print('✅')"
python -c "from core.clarification import ClarificationSystem; print('✅')"
```

**Hauptprogramm startet?**
```bash
python main.py --help
```

**Tests laufen?**
```bash
pytest -v
```

---

## ⚠️ Breaking Changes

**KEINE** - Alle Master-Implementierungen bleiben erhalten!

---

## 🎯 Ergebnis

- ✅ 9 Duplikate entfernt (~58 KB)
- ✅ .gitignore hinzugefügt
- ✅ Saubere Repo-Struktur
- ✅ Keine Breaking Changes
- ✅ Alle Features funktionieren

---

## 📖 Mehr Details

Für detaillierte Informationen siehe:
- `CLEANUP_SUMMARY.md` - Vollständige Auflistung
- `REFACTORING_GUIDE.md` - Nächste Schritte
