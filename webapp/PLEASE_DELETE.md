# ⚠️ BITTE LÖSCHEN!

**Dieser Ordner `webapp/` ist DEPRECATED und sollte gelöscht werden.**

---

## Warum?

Die WebApp wurde durch die **Desktop UI** (Wails) ersetzt.

**Desktop UI ist besser:**
- ✅ Native Performance
- ✅ Cross-Platform (Windows/Linux/macOS)
- ✅ Kein Web-Server nötig
- ✅ Bessere Security
- ✅ Systemtray-Integration
- ✅ Offline-First

---

## Migration

**Alt (WebApp):**
```bash
python webapp/server.py
# Browser: http://localhost:5000
```

**Neu (Desktop UI):**
```bash
cd desktop
wails dev
# Native Desktop Window
```

---

## Wie löschen?

```bash
# Komplettes Verzeichnis entfernen
rm -rf webapp/

# Oder Windows:
rmdir /s /q webapp
```

---

**Siehe:** `docs/UI_CONSOLIDATION.md` für Details.
