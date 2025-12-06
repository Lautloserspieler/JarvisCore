# 🚀 J.A.R.V.I.S. Core - Quickstart

**Schnellste Installation in 2 Minuten!**

---

## ⚡ Blitzschnelle Installation

### Option 1: Automatisches Setup (Empfohlen)

```bash
# 1. Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2. Setup ausführen (macht ALLES automatisch)
python setup.py

# Das war's! 🎉
```

**Was passiert automatisch:**
- ✅ Python-Version prüfen (3.11+)
- ✅ Verzeichnisse erstellen (data/, logs/, models/)
- ✅ Virtuelle Umgebung erstellen (venv/)
- ✅ Dependencies installieren (pip install -r requirements.txt)
- ✅ Settings konfigurieren (data/settings.json)
- ✅ ImGui Desktop-UI aktivieren
- ✅ Optional: JARVIS direkt starten

---

## 🖥️ Starten

### Windows

```cmd
REM Doppelklick auf:
start_jarvis.bat

REM Oder manuell:
venv\Scripts\activate
python main.py
```

### Linux / macOS

```bash
# Executable machen (nur einmal)
chmod +x start_jarvis.sh

# Starten
./start_jarvis.sh

# Oder manuell:
source venv/bin/activate
python main.py
```

---

## 🎮 Desktop UI

**ImGui-Oberfläche öffnet sich automatisch!**

### 7 Tabs:
1. **📊 Dashboard** - Live CPU/RAM/GPU Graphen
2. **💬 Chat** - Interaktiver Chat mit JARVIS
3. **🧠 Models** - LLM Download/Load/Unload
4. **🧩 Plugins** - Plugin-System
5. **🗄️ Memory** - Gedächtnis-Viewer
6. **📋 Logs** - Live Log-Viewer
7. **⚙️ Settings** - LLM/TTS/Speech Config

---

## 🔧 Troubleshooting

### Problem: Setup schlägt fehl

```bash
# Python-Version prüfen
python --version  # Muss 3.11+ sein

# Manuell installieren
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Problem: ImGui öffnet nicht

```bash
# In data/settings.json prüfen:
"desktop_app": { "enabled": true }

# Oder Environment Variable:
export JARVIS_DESKTOP=1  # Linux/macOS
set JARVIS_DESKTOP=1     # Windows
```

### Problem: DearPyGui fehlt

```bash
pip install dearpygui
```

---

## 📚 Weitere Dokumentation

- **[README.md](README.md)** - Vollständige Projekt-Doku
- **[docs/IMGUI_SETUP.md](docs/IMGUI_SETUP.md)** - ImGui UI Anleitung
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System-Architektur

---

## ✨ Features

- 🧠 **3 lokale LLMs** (Llama 3, Mistral, DeepSeek)
- 🎤 **Voice Control** (Whisper + Piper)
- 📚 **Knowledge Base** (Semantische Suche)
- 🧩 **Plugin System** (Wikipedia, PubMed, etc.)
- 🎮 **UE5-Style UI** (Moderne Desktop-Oberfläche)
- 🔒 **100% Offline** (Alle Daten lokal)

---

<div align="center">

**Made with ❤️ by [@Lautloserspieler](https://github.com/Lautloserspieler)**

⭐ **Star dieses Projekt!** ⭐

</div>
