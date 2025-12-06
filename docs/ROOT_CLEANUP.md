# 🧹 Root Directory Cleanup Guide

**Ziel:** Hauptverzeichnis aufräumen und Dateien logisch organisieren.

---

## 📊 Problem

**Aktuelles Root-Verzeichnis:**
```
JarvisCore/
├── AUTO_REFACTOR.md           # Doc im Root
├── CLEANUP_SUMMARY.md          # Doc im Root
├── QUICKSTART_CLEANUP.md       # Doc im Root
├── REFACTORING_GUIDE.md        # Doc im Root
├── UI_CONSOLIDATION.md         # Doc im Root
├── ARCHITECTURE.md             # Doc im Root
├── start_jarvis.bat            # Start-Script
├── run_jarvis.bat              # Start-Script (Duplikat?)
├── start_jarvis.sh             # Start-Script
├── run_jarvis.sh               # Start-Script (Duplikat?)
├── start_jarvis.py             # Entry Point
├── main.py                     # Entry Point
├── bootstrap.py                # Entry Point
├── setup.py                    # Setup
├── package-lock.json           # Fast leer
├── webapp/                     # Sollte gelöscht sein
└── ... (35+ Dateien)
```

**Probleme:**
- ⚠️ 6 Dokumentations-Dateien im Root (gehören in `docs/`)
- ⚠️ Doppelte Start-Scripts (2x Windows, 2x Linux)
- ⚠️ Zu viele Entry Points (4 Stück)
- ⚠️ `webapp/` existiert noch (sollte weg sein)
- ⚠️ Unnötiges `package-lock.json`
- ⚠️ Unübersichtliches Root

---

## ✅ Lösung

### 1. Dokumentation nach `docs/` verschieben

**Verschieben:**
```bash
mv AUTO_REFACTOR.md docs/
mv CLEANUP_SUMMARY.md docs/
mv QUICKSTART_CLEANUP.md docs/
mv REFACTORING_GUIDE.md docs/
mv UI_CONSOLIDATION.md docs/
mv ARCHITECTURE.md docs/
```

**Resultat:**
```
docs/
├── ARCHITECTURE.md
├── AUTO_REFACTOR.md
├── CLEANUP_SUMMARY.md
├── QUICKSTART_CLEANUP.md
├── REFACTORING_GUIDE.md
├── UI_CONSOLIDATION.md
├── CHANGELOG.md
├── PERFORMANCE.md
└── SECURITY.md
```

### 2. Start-Scripts konsolidieren

**Behalten:**
- `start_jarvis.bat` (Windows)
- `start_jarvis.sh` (Linux/macOS)

**Löschen:**
```bash
rm run_jarvis.bat
rm run_jarvis.sh
```

### 3. Entry Points aufräumen

**Behalten:**
- `main.py` - Haupt-Einstiegspunkt
- `setup.py` - Installation/Setup

**Nach `scripts/` verschieben:**
```bash
mv start_jarvis.py scripts/
mv bootstrap.py scripts/
```

### 4. webapp/ löschen

```bash
rm -rf webapp/
```

### 5. Unnötiges entfernen

```bash
rm package-lock.json
```

---

## 🚀 Automatisches Cleanup

### Script nutzen

```bash
# Dry-Run (Vorschau)
python scripts/cleanup_root.py

# Ausführen
python scripts/cleanup_root.py --execute
```

### Oder Shell-Scripts

**Windows:**
```bash
scripts\cleanup_root.bat
```

**Linux/macOS:**
```bash
chmod +x scripts/cleanup_root.sh
./scripts/cleanup_root.sh
```

---

## 📊 Vorher → Nachher

| Kategorie | Vorher | Nachher | Verbesserung |
|-----------|--------|---------|-------------|
| **Root .md Dateien** | 11 | 3 | -73% |
| **Start Scripts** | 6 | 2 | -67% |
| **Entry Points** | 4 | 2 | -50% |
| **Unnötige Dirs** | 1 (webapp) | 0 | -100% |
| **Root Files gesamt** | ~35 | ~20 | -43% |

---

## ✅ Sauberes Root-Verzeichnis

**Nach dem Cleanup:**

```
JarvisCore/
├── .gitattributes
├── .github/
├── .gitignore
├── LICENSE
├── NOTICE
├── README.md
├── README_GB.md
├── config/
├── core/
├── data/
├── desktop/              # Desktop-App
├── docs/                 # Alle Dokumentation
├── go/
├── logs/
├── main.py               # Haupt-Entry Point
├── models/
├── plugins/
├── pyproject.toml
├── requirements.txt
├── scripts/              # Alle Scripts
├── services/
├── setup.py              # Setup
├── start_jarvis.bat      # Windows Start
├── start_jarvis.sh       # Linux/macOS Start
├── tests/
└── utils/
```

**Übersichtlich und professionell!** ✨

---

## 🧪 Testen

```bash
# Start-Scripts funktionieren?
./start_jarvis.sh         # Linux/macOS
start_jarvis.bat          # Windows

# Hauptprogramm läuft?
python main.py --help

# Desktop-App?
cd desktop && wails dev

# Dokumentation zugänglich?
ls docs/
```

---

## 🎯 Zusammenfassung

**Ergebnis:**
- ✅ Sauberes Root-Verzeichnis (-43% Files)
- ✅ Alle Docs in `docs/` organisiert
- ✅ Keine doppelten Scripts mehr
- ✅ Klare Entry Points
- ✅ `webapp/` endlich weg
- ✅ Professionelle Projekt-Struktur

**Empfehlung:** ✅ Sofort durchführen!
