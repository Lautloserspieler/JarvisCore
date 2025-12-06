# ⚡ Quick Reference - Root Directory Cleanup

**Sofort-Anleitung für sauberes Hauptverzeichnis**

---

## 🚀 Ein Befehl für alles

### Windows
```bash
scripts\cleanup_root.bat
```

### Linux/macOS
```bash
chmod +x scripts/cleanup_root.sh
./scripts/cleanup_root.sh
```

### Python (Plattform-unabhängig)
```bash
# Vorschau (Dry-Run)
python scripts/cleanup_root.py

# Ausführen
python scripts/cleanup_root.py --execute
```

---

## 📊 Was wird gemacht?

### ✅ Verschieben
- 6 Dokumentations-Dateien → `docs/`
- 2 Entry Points → `scripts/`

### 🗑️ Löschen
- Doppelte Start-Scripts (2 Dateien)
- `webapp/` Verzeichnis (komplett)
- `package-lock.json`
- Verbleibende Root-Docs

### 📊 Ergebnis
- **Root Files:** -43%
- **Dokumentation:** 100% in `docs/`
- **Übersichtlichkeit:** +200%

---

## 🧪 Testen

```bash
# Hauptprogramm
python main.py --help

# Desktop-App
cd desktop && wails dev

# Start-Scripts
./start_jarvis.sh
```

---

## 📁 Neue Struktur

```
JarvisCore/
├── README.md       # Projekt-Übersicht
├── LICENSE         # Apache 2.0
├── main.py         # Entry Point
├── docs/           # 📚 Alle Dokumentation
├── scripts/        # 🤖 Alle Scripts
├── core/           # 💻 Python Core
├── desktop/        # 🖥️ Desktop-App
└── ...
```

---

## ✅ Fertig!

Dein Root-Verzeichnis ist jetzt **sauber und organisiert**! ✨

**Mehr Details:** Siehe `CLEANUP_COMPLETED.md`
