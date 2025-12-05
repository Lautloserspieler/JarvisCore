# 🧠 J.A.R.V.I.S. (JarvisCore)

J.A.R.V.I.S. (JarvisCore) ist ein modularer, vollständig lokaler Sprach- und Automationsassistent mit **Web-UI und nativer Desktop-Anwendung**, Spracherkennung, Text-zu-Sprache, Wissensdatenbank, Plugin-System und GPU-beschleunigten LLMs.  
Fokus: Datenschutz, Erweiterbarkeit, echte Offline-Intelligenz.

> Hinweis: Sprach-Ein- und -Ausgabe sind noch in aktiver Entwicklung. Stabilität und Funktionsumfang können sich ändern.

---

## 🚀 Features

- Vollständig lokale Pipeline für Spracheingabe und -ausgabe (kein Cloud-Zwang).
- CUDA-beschleunigter LLM-Kern (LLaMA 3, Mistral, Hermes, DeepSeek) via `llama-cpp-python`.
- **Zwei UI-Optionen:**
  - 🌐 **Web-Dashboard** mit Live-Telemetrie, Model-Verwaltung und Plugin-Steuerung
  - 🖥️ **Native Desktop-App** (Wails + Vue.js) - Single Binary, ~20-30MB
- Rollenbasiertes Sicherheitsmodell mit AES-256 / RSA-4096, Safe-Mode und Notfallprotokoll.
- Modularer Aufbau mit Plugins, Training-/Debug-Modus und Task-Automation.

Mehr Details findest du in der ausführlichen Doku im Ordner [`docs/`](./docs).

---

## 🖥️ Desktop UI (NEU!)

**Native Desktop-Anwendung als Alternative zur Web-UI.**

### Vorteile
- ✅ **Native Performance** - Kein Browser-Overhead
- ✅ **System-Integration** - Tray-Icon, Shortcuts, Benachrichtigungen
- ✅ **Single Binary** - Nur ~20-30MB
- ✅ **Offline-First** - Keine Port-Konflikte
- ✅ **Cross-Platform** - Windows, Linux, macOS

### Quick Start

```bash
# 1) JarvisCore starten
python main.py

# 2) Desktop UI starten (in separatem Terminal)
cd desktop
wails dev
```

**Mehr Infos:** [`desktop/README.md`](./desktop/README.md)

---

## 🧩 Architektur

Siehe ausführlicher: [`docs/architecture.md`](./docs/architecture.md).

Kurzüberblick:

- Sprachverarbeitung:
  - Wake-Word: „Hey Jarvis“
  - STT: VOSK / Whisper / Faster-Whisper
  - TTS: XTTS v2 / Coqui / pyttsx3
- Intelligenz-Kern:
  - Lokale LLMs (LLaMA 3, Mistral, Hermes, DeepSeek) mit GPU-Beschleunigung
- Wissen:
  - Lokaler Cache + Wikipedia + OpenLibrary + Semantic Scholar + OSM
  - Cross-Encoder (MiniLM L6 v2) für semantisches Ranking
- Oberfläche:
  - 🌐 Web-Dashboard (AIOHTTP)
  - 🖥️ **Native Desktop-App (Wails + Vue.js + Go)** ← NEU!
- Sicherheit:
  - AES-256 + RSA-4096
  - Rollen, Safe-Mode, Security-Logs

---

## ⚙️ Systemanforderungen

### Python Backend
- OS: Windows 10/11 (empfohlen), Linux/macOS mit Anpassungen
- Python: 3.11 x64
- RAM: ≥ 16 GB
- GPU: NVIDIA mit CUDA ≥ 12.0 (AMD nur eingeschränkt)
- Git: für Repository-Klon

### Desktop UI (optional)
- Go: 1.21+
- Node.js: 18+
- Wails CLI: `go install github.com/wailsapp/wails/v2/cmd/wails@latest`

---

## ⚡ Schnellstart (Windows / PowerShell)

### Web-UI (Standard)

```
# 1) Repository klonen oder entpacken
cd C:\Users\<du>\Desktop
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2) Automatische Einrichtung + Start
py -3.11 bootstrap.py --run
# oder per Doppelklick:
run_jarvis.bat
```

### Desktop UI (Alternative)

```bash
# Terminal 1: JarvisCore Backend
cd JarvisCore
python main.py

# Terminal 2: Desktop UI
cd desktop
npm install
wails dev
```

> Bei Problemen: siehe [`docs/troubleshooting.md`](./docs/troubleshooting.md).

---

## 📦 Installation

Ausführliche Infos: [`docs/installation.md`](./docs/installation.md).

Kurzform (manuell):

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Beim ersten Start werden `data/`, `logs/`, `models/` und `data/settings.json` erstellt.

---

## 🎮 Nutzung

### Web-UI

Standardstart:

```
cd JarvisCore
python main.py
```

- Web-Dashboard: http://127.0.0.1:5050
- Token (default): `12345678` (änderbar in `data/settings.json`)

Tabs in der Web-UI:

- Chat – Text/Sprachsteuerung, Verlauf, Markdown
- System – Hardware- und Leistungsmonitor
- Modelle – LLM-Verwaltung
- Plugins / Memory / Training / Logs / Einstellungen

### Desktop UI

```bash
# Development
cd desktop
wails dev

# Production Build
cd desktop
wails build
# Binary: ./build/bin/jarvis-desktop.exe
```

Mehr in [`docs/usage.md`](./docs/usage.md) und [`desktop/README.md`](./desktop/README.md).

---

## 🔒 Sicherheit

- AES-256 + RSA-4096 für sensible Daten.
- Rollenbasiertes Zugriffssystem.
- Safe-Mode zur Begrenzung kritischer Aktionen.
- Sicherheits-Logs unter `logs/security.log`.

Details: [`docs/security.md`](./docs/security.md).

---

## 🧠 Modelle & Lizenzen

Übersicht aller eingebundenen Modelle, Lizenzen und Quellen: [`docs/models.md`](./docs/models.md).

---

## 🧩 Plugins

JarvisCore bietet ein Plugin-System zur Erweiterung (Automation, Tools, Crawler, usw.).  
Siehe: [`docs/plugins.md`](./docs/plugins.md).

---

## 🤝 Beiträge

Beiträge sind willkommen! Lies bitte zuerst [`CONTRIBUTING.md`](./CONTRIBUTING.md).

- Bug melden: GitHub Issue mit Log-Auszug und Reproduktionsschritten.
- Feature vorschlagen: Issue mit Use-Case.
- Code beitragen: Fork → Branch → PR.

---

## ⚖️ Lizenz

Copyright © 2025 Lautloserspieler

Lizenziert unter der Apache License 2.0 mit Zusatzklausel:  
Kommerzielle Nutzung, Verkauf oder Weiterverbreitung dieses Projekts sind ohne vorherige schriftliche Genehmigung untersagt.

Drittanbieter-Komponenten unterliegen ihren jeweiligen Lizenzen (siehe `third_party_licenses`).

---

## 💬 Kontakt

- GitHub: https://github.com/Lautloserspieler
- Feedback & Issues: bitte über den Issue-Tracker des Repos.
