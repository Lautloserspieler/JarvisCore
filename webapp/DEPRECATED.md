# ❌ DEPRECATED - WebApp wurde eingestellt

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
