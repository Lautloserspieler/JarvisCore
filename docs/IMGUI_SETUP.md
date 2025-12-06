# 🎮 ImGui Desktop UI - Setup & Customization Guide

**Vollständige Anleitung für die Unreal Engine 5-Style Desktop-Oberfläche**

---

## 📋 Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)
2. [Schnellstart](#schnellstart)
3. [Konfiguration](#konfiguration)
4. [UI Controls](#ui-controls)
5. [Design anpassen](#design-anpassen)
6. [Hard-Switch zu ImGui-Only](#hard-switch-zu-imgui-only)
7. [Troubleshooting](#troubleshooting)

---

## ✅ Voraussetzungen

### System
- **Python** 3.11+ (64-bit)
- **pip** und **venv**
- **Windows** (Linux/macOS mit angepassten Font-Pfaden)

### Dependencies

```bash
# ImGui-spezifische Pakete
pip install dearpygui

# Oder vollständige Installation
pip install -r requirements.txt
```

### Optionale GPU-Beschleunigung
- **OpenGL 3.3+** Support (automatisch erkannt)
- Für beste Performance: Dedicated GPU empfohlen

---

## 🚀 Schnellstart

### 1. Repository Setup

```bash
# Klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Dependencies
pip install -r requirements.txt
```

### 2. Settings prüfen

**In `data/settings.json` sicherstellen:**

```json
{
  "desktop_app": {
    "enabled": true
  }
}
```

**ODER per Environment Variable:**

```bash
# Linux/macOS
export JARVIS_DESKTOP=1

# Windows CMD
set JARVIS_DESKTOP=1

# Windows PowerShell
$env:JARVIS_DESKTOP=1
```

### 3. Starten

```bash
python main.py
```

**Was passiert beim ersten Start:**
- `logs/` Verzeichnis wird erstellt
- `data/` Verzeichnis wird erstellt
- ImGui-Fenster öffnet sich (1920x1080)

---

## ⚙️ Konfiguration

### Desktop-App Settings

**Vollständige Konfiguration in `data/settings.json`:**

```json
{
  "desktop_app": {
    "enabled": true,
    "width": 1920,
    "height": 1080,
    "fullscreen": false,
    "vsync": true,
    "theme": "ue5"
  },
  "language": "de",
  "llm": {
    "enabled": true,
    "default_model": "mistral"
  },
  "speech": {
    "wake_word_enabled": true,
    "stream_tts": true
  },
  "web_interface": {
    "enabled": false  // ImGui-Only Mode
  },
  "remote_control": {
    "enabled": false  // ImGui-Only Mode
  }
}
```

### Font-Konfiguration

**Standard-Fonts (Windows):**
- **Segoe UI** (`C:/Windows/Fonts/segoeui.ttf`)
- **Größen:** 18px (Standard), 22px (Subheader), 28px (Header)

**Linux Font-Pfade anpassen:**

```python
# In desktop/jarvis_imgui_app_full.py, _setup_fonts():
default_font = dpg.add_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
```

**macOS Font-Pfade:**

```python
default_font = dpg.add_font("/System/Library/Fonts/Helvetica.ttc", 18)
```

---

## 🎮 UI Controls

### Tab-Übersicht

#### 📊 Dashboard
- **Live-Graphen:** CPU/RAM/GPU Nutzung (Echtzeit)
- **Detailed Stats:** Detaillierte System-Metriken
- **Auto-Update:** Jede Sekunde

#### 💬 Chat
- **Eingabefeld:** Commands direkt eingeben
- **Send Button:** Oder Enter drücken
- **History:** Scrollbare Chat-Historie
- **Command Processing:** Direkt an Python-Backend

#### 🧠 Models
- **Refresh:** Modell-Status aktualisieren
- **Download Model:** Neue Modelle herunterladen (TODO)
- **Unload All:** Alle geladenen Modelle entladen
- **Status-Anzeige:**
  - ✅ Available
  - 🟢 ACTIVE (aktuell geladen)
  - 🔵 LOADED (im RAM)

#### 🧩 Plugins
- **Refresh:** Plugin-Status aktualisieren
- **Status-Anzeige:**
  - 🟢 ENABLED
  - 🔴 DISABLED
- **Info:** Type, Description

#### 🗂️ Memory
- **Under Construction** (v0.9.1 geplant)

#### 📋 Logs
- **Refresh:** Log-Datei neu laden
- **Clear:** Anzeige leeren
- **Auto-scroll:** Automatisch zu neuesten Logs
- **Source:** `logs/jarvis.log` (letzte 100KB)

#### ⚙️ Settings
- **LLM Settings:**
  - Enable/Disable
  - Context Length (512-8192)
  - Temperature (0.0-2.0)
- **TTS Settings:**
  - Enable/Disable
  - Speech Rate (50-300)
  - Volume (0-100)
- **Speech Recognition:**
  - Wake Word On/Off
  - Continuous Listening
- **Save Button:** Settings speichern (TODO: Persistence)

---

## 🎨 Design anpassen

### "Cooleren" Look erstellen

**Datei:** `desktop/jarvis_imgui_app_full.py`

### 1. Farben ändern (Theming)

**In `_apply_ue5_theme()` Methode:**

```python
def _apply_ue5_theme(self):
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # === DUNKLER BACKGROUND (Cyber Look) ===
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (22, 22, 26, 255))  # Dunkler
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (28, 28, 32, 255))
            
            # === CYAN ACCENTS (Holographic) ===
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 100, 140, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 140, 200, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 180, 240, 255))
            
            # === NEON BORDER (Glow-Effekt) ===
            dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 180, 216, 255))
            
            # === HELLERE TEXT (Kontrast) ===
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))  # Weiß
```

### 2. Schriftgröße anpassen

**In `_setup_fonts()` Methode:**

```python
def _setup_fonts(self):
    with dpg.font_registry():
        # === KOMPAKTER LOOK (kleinere Schrift) ===
        default_font = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 16)  # Statt 18
        large_font = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 24)    # Statt 28
        medium_font = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 20)   # Statt 22
        
        # === GROẞZÜGIGER LOOK (größere Schrift) ===
        default_font = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 20)  # Statt 18
        large_font = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 32)    # Statt 28
        medium_font = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 26)   # Statt 22
        
        # === BOLD FONT (SemiBold für mehr Präsenz) ===
        default_font = dpg.add_font("C:/Windows/Fonts/seguisb.ttf", 18)  # SemiBold
```

### 3. Abstände & Rounding

**In `_apply_ue5_theme()` nach den Farben:**

```python
# === FLACHER LOOK (minimal Rounding) ===
dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 1)   # Statt 3
dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 2)  # Statt 6
dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 1)   # Statt 4

# === CARD-LOOK (mehr Rounding) ===
dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)   # Statt 3
dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12) # Statt 6
dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)  # Statt 4

# === KOMPAKT (weniger Padding) ===
dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)   # Statt 12, 10
dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12) # Statt 20, 20
dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)    # Statt 12, 10

# === GROẞZÜGIG (mehr Padding) ===
dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 16, 12)  # Statt 12, 10
dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 24, 24) # Statt 20, 20
dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 16, 12)   # Statt 12, 10
```

### 4. Header & Tabs anpassen

**Emojis entfernen (cleaner Look):**

**In `_create_ui()` Methode:**

```python
# === MIT EMOJIS (Standard) ===
with dpg.tab(label="  📊 Dashboard  "):

# === OHNE EMOJIS (Clean) ===
with dpg.tab(label="  Dashboard  "):

# === UPPERCASE (Präsenter) ===
with dpg.tab(label="  DASHBOARD  "):
```

### 5. Beispiel: Cyberpunk-Theme

```python
def _apply_cyberpunk_theme(self):
    """Cyberpunk 2077 inspiriertes Theme"""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # Schwarzer Background
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (10, 10, 12, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (18, 18, 20, 255))
            
            # Neon Pink/Cyan Accents
            dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 0, 100, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 0, 140, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 255, 255, 255))  # Cyan
            
            # Weiße Schrift
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
            
            # Maximaler Rounding
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 12)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 16)
    
    dpg.bind_theme(theme)
```

---

## 🔒 Hard-Switch zu ImGui-Only

**Alle anderen UIs deaktivieren:**

### `data/settings.json` anpassen:

```json
{
  "desktop_app": {
    "enabled": true  // ImGui AN
  },
  "web_interface": {
    "enabled": false  // Web-UI AUS
  },
  "remote_control": {
    "enabled": false  // WebSocket AUS
  },
  "go_services": {
    "auto_start": false  // Go-Services AUS (optional)
  }
}
```

### Starten:

```bash
python main.py
```

**Nur noch die ImGui-UI wird gestartet!** 🎯

---

## 🐛 Troubleshooting

### Problem: ImGui-Fenster öffnet sich nicht

**Lösung 1: Settings prüfen**
```bash
# In data/settings.json:
"desktop_app": { "enabled": true }

# Oder per Env:
export JARVIS_DESKTOP=1
```

**Lösung 2: DearPyGui installieren**
```bash
pip install dearpygui
```

**Lösung 3: Logs prüfen**
```bash
tail -f logs/jarvis.log
# Windows: Get-Content logs/jarvis.log -Wait
```

### Problem: Schrift zu klein/groß

**Lösung:** In `desktop/jarvis_imgui_app_full.py`, `_setup_fonts()` Größen anpassen:

```python
default_font = dpg.add_font("...", 16)  # Kleiner
default_font = dpg.add_font("...", 20)  # Größer
```

### Problem: Font-Fehler (Linux/macOS)

**Lösung:** Font-Pfade anpassen:

```python
# Linux
default_font = dpg.add_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# macOS
default_font = dpg.add_font("/System/Library/Fonts/Helvetica.ttc", 18)
```

### Problem: UI friert ein

**Lösung 1: GPU-Treiber aktualisieren**

**Lösung 2: VSync deaktivieren**
```json
"desktop_app": {
  "vsync": false
}
```

**Lösung 3: Python Logs prüfen**
```bash
python main.py --debug
```

### Problem: Modelle werden nicht angezeigt

**Lösung:** LLM-Manager Status prüfen:

```bash
# In Python Console oder main.py:
status = jarvis.get_llm_status()
print(status)
```

**Modelle fehlen?**
```bash
python scripts/download_models.py --model mistral
```

### Problem: Plugins nicht geladen

**Lösung:** Plugin-Manager prüfen:

```bash
# In Python:
overview = jarvis.get_plugin_overview()
print(overview)
```

**Config prüfen:**
```bash
cat config/plugins.json
```

---

## 📚 Weitere Ressourcen

### Dokumentation
- **[README.md](../README.md)** - Projekt-Übersicht
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System-Architektur
- **[SECURITY.md](SECURITY.md)** - Sicherheits-Richtlinien

### DearPyGui
- **[Official Docs](https://dearpygui.readthedocs.io/)**
- **[GitHub](https://github.com/hoffstadt/DearPyGui)**
- **[Examples](https://github.com/hoffstadt/DearPyGui/tree/master/DearPyGui/examples)**

### Themes & Styling
- **[DearPyGui Themes](https://dearpygui.readthedocs.io/en/latest/tutorials/themes.html)**
- **[Color Picker Tool](https://htmlcolorcodes.com/)**

---

## 🎯 Quick Reference

### Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `desktop/jarvis_imgui_app_full.py` | Haupt-UI Code |
| `data/settings.json` | Runtime Config |
| `main.py` | Entry Point |
| `logs/jarvis.log` | System Logs |

### Wichtige Methoden

| Methode | Zweck |
|---------|-------|
| `_setup_fonts()` | Font-Größen |
| `_apply_ue5_theme()` | Farben & Styling |
| `_create_ui()` | UI-Layout |
| `_update_metrics()` | Live-Daten |

### Keyboard Shortcuts

| Shortcut | Aktion |
|----------|--------|
| **Enter** | Chat-Nachricht senden |
| **Ctrl+C** | Programm beenden (Terminal) |
| **Alt+F4** | Fenster schließen (Windows) |

---

<div align="center">

**Made with ❤️ by [@Lautloserspieler](https://github.com/Lautloserspieler)**

⭐ **Star dieses Projekt!** ⭐

[⬆ Back to Top](#-imgui-desktop-ui---setup--customization-guide)

</div>
