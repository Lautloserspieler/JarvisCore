<div align="center">

# 🤖 J.A.R.V.I.S. Core

**Lokaler KI-Assistent mit STT/TTS, LLM-Routing, Wissensbasis und Plugins**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org)
[![DearPyGui](https://img.shields.io/badge/DearPyGui-1.10+-purple.svg)](https://github.com/hoffstadt/DearPyGui)

**100% Offline. Privacy-First. Open Source.**

[Features](#-features) •
[Quick Start](#-quick-start) •
[Architektur](#-architektur) •
[Installation](#-installation) •
[Dokumentation](#-dokumentation)

</div>

---

## 📚 Über J.A.R.V.I.S. Core

**J.A.R.V.I.S. Core** ist ein vollständig **offline funktionierender** KI-Assistent mit Python-Backend, optionalen Go-Microservices und moderner **Unreal Engine 5-Style Desktop-UI**.

### 🎯 Kernmerkmale

- 🧠 **3 lokale LLMs** (Llama 3, Mistral, DeepSeek) - keine Cloud, volle Privacy
- 🎤 **Voice Control** - Whisper STT + Piper TTS
- 📚 **Knowledge Base** - Semantische Suche mit lokalen Embeddings
- 🧩 **Plugin System** - Wikipedia, Wikidata, PubMed, OSM, etc.
- 🎮 **UE5-Style ImGui UI** - Moderne Desktop-Oberfläche mit Live-Monitoring
- 🔒 **100% Offline** - Alle Daten bleiben lokal

---

## ✨ Features

### 🤖 AI-Modelle & Routing

- **LLM-Manager** mit Modellwechsel zur Laufzeit
- **Intelligentes Routing** - Use-Case-basierte Modellauswahl
- **GGUF-Support** - Quantisierte Modelle (Q4/Q8)
- **GPU/CPU Fallback** - Automatisch oder konfigurierbar

### 🗣️ Speech & Audio

- **Whisper-basierte STT** - Mehrsprachig, lokal
- **Piper TTS** - Natürliche Sprachausgabe
- **Wake Word Detection** - "Hey Jarvis" Aktivierung
- **Streaming Support** - Echtzeit-Audio-Verarbeitung

### 📚 Wissensmanagement

- **Semantische Suche** - Sentence-Transformers + FAISS/ChromaDB
- **Auto-Import** - Markdown, PDF, Code-Files
- **Expansion Agent** - KI erweitert Wissen automatisch
- **Crawler-Integration** - Externe Wissensquellen

### 🧩 Plugin-Ökosystem

**Built-in Plugins:**
- 🌐 Wikipedia, Wikidata
- 🧬 PubMed (Med. Forschung)
- 📖 Semantic Scholar (Papers)
- 🗺️ OpenStreetMap
- 📚 OpenLibrary

### 🎮 Desktop UI (UE5-Style ImGui)

- **7 Haupt-Tabs:** Dashboard, Chat, Models, Plugins, Memory, Logs, Settings
- **Live-Monitoring:** CPU/RAM/GPU Graphen (Echtzeit)
- **Modell-Manager:** Download/Load/Unload von LLMs
- **Settings:** LLM, TTS, Speech Recognition Konfiguration
- **Dark Theme:** Inspiriert von Unreal Engine 5 Editor
- **GPU-beschleunigt:** DearPyGui mit nativer Performance

### 🔒 Sicherheit & Kontrolle

- **Adaptive Security** - Lernende Zugriffskontrolle
- **Safe Execution Mode** - Sandboxed Commands
- **TOTP 2FA** - Optionale Authenticator-App
- **Audit Logging** - Alle kritischen Aktionen geloggt

---

## 🚀 Quick Start

### Voraussetzungen

- **Python** 3.11+ (64-bit)
- **pip** & **venv**
- **(Optional)** CUDA 12.1+ für GPU-Beschleunigung
- **(Optional)** Go 1.21+ für Microservices

### Installation (3 Schritte)

```bash
# 1. Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Starten (UE5-Style ImGui UI)
python main.py
```

**Das war's!** 🎉 JARVIS startet mit der UE5-Style Desktop-UI.

---

## 🏛️ Architektur

### Projektüberblick

**Lokaler KI-Assistent** mit STT/TTS, LLM-Routing, Wissensbasis und Plugins; **Python-Backend** (`main.py`) plus optionale **Go-Microservices** und **Desktop-UI** (ImGui).

### Kernlogik (Python)

#### Orchestrierung
- **main.py** startet `JarvisAssistant`
- Initialisiert: Settings, Security, Authenticator, LLM/TTS/STT, Plugins, Knowledge- & Learning-Manager, Scheduler
- Optionale Go-Services per `JARVIS_START_GO=1`
- **Desktop-UI:** `desktop/jarvis_imgui_app_full.py` (UE5-Style) oder Fallback `HeadlessGUI`

#### Befehlsfluss
```
Audio → core/speech_recognition.py (Wakeword/Whisper)
      → core/command_processor.py (Intent/Plugin-Routing, Kontext, Sicherheit)
      → Aktionen/LLM-Antwort
      → core/text_to_speech.py für Ausgabe
```

#### LLM-Steuerung
- **core/llm_manager.py** + **core/llm_router.py**
- Laden/Wechseln/Download von GGUF-Modellen
- Model-Metadata, Routing nach Use-Case

#### Wissen
- **core/knowledge_manager.py** mit Import/Scan (`core/local_knowledge_*`)
- Semantische Suche/Embeddings
- Crawler-Anbindung (`core/crawler_client.py`)
- Expansion-Agent (`core/knowledge_expansion_agent.py`)

#### Speicher & Lernen
- **core/memory_*** (Kurz-/Langzeit/Timeline/Vector)
- **core/reinforcement_learning.py**, **core/long_term_trainer.py**
- **core/learning_manager.py** für Feedback und kontinuierliches Lernen

#### Sicherheit & Ausführung
- **core/security_protocol.py** + **core/security_manager.py** (Safe-Mode, Prioritäten, Auditing)
- **core/system_control.py** (Systembefehle)
- **core/system_monitor.py** (CPU/RAM/GPU Metriken)
- **core/safe_shell.py**/**core/sensitive_safe.py** für abgesicherte Befehle

#### Plugins
- **core/plugin_manager.py** lädt Module aus `plugins/`
- Wikipedia, Wikidata, PubMed, SemanticScholar, OSM, OpenLibrary, Memory/Clarification
- Basis-Interfaces in `plugins/conversation_plugin_base.py`

### Konfiguration & Daten

#### Laufzeitkonfiguration
- **data/settings.json** (Sprache/STT/TTS, Wakewords, Modelle, Remote-Control, Desktop-Flags, Security-Policy, Crawler, Response-Limits)
- Vorlagen/Defaults in **config/settings.py**
- Intents/Patterns in **config/intents.json** & **config/command_patterns.json**
- Persona in **config/persona.py**
- Plugin-List in **config/plugins.json**

#### Datenpfade
- **models/** - LLM/STT/TTS Modelle
- **data/** - Wissensbasis/Embeddings/Settings
- **logs/** - Systemlogs
- **backups/** - Sicherungen

### Services (Go)

**Optional** per Env/Settings (`go_services.auto_start`):

Microservices unter `go/cmd/*`:
- **securityd** - Token/JWT-Prüfung, Role/Policy-Mapping, Audit
- **gatewayd** - API-Gateway
- **memoryd** - Gedächtnis-Service
- **systemd** - System-Monitor
- **speechtaskd** - Speech-Task-Queue
- **commandd** - Command-Router

Gemeinsamer Code in `go/internal/*` (z.B. `go/internal/security/service.go`).

### Desktop UI (ImGui - UE5 Style)

#### Haupt-UI: `desktop/jarvis_imgui_app_full.py`

**7 Tabs:**
1. **📊 Dashboard** - Live CPU/RAM/GPU Graphen + Detailed Stats
2. **💬 Chat** - Interaktiver Chat mit Command Processing
3. **🧠 Models** - LLM Status, Download/Load/Unload
4. **🧩 Plugins** - Plugin-Übersicht, Enable/Disable
5. **🗄️ Memory** - Gedächtnis-Viewer (Under Construction)
6. **📜 Logs** - Live Log-Viewer mit Auto-Scroll
7. **⚙️ Settings** - LLM/TTS/Speech Settings

**Features:**
- **Unreal Engine 5 Design** - Dark Flat Theme, Orange/Blue Accents
- **Live-Updates** - Background-Threads für Metriken (1s) und Logs (3s)
- **GPU-beschleunigt** - DearPyGui native Rendering
- **FPS Counter** - Performance-Monitor im Footer

#### Startskripte
- **desktop/build.sh|bat** - Build-Scripts
- **desktop/start-dev.bat** - Dev-Mode

### Hilfs- und Automationslayer

- **Scheduler:** `core/update_scheduler.py` für periodische Crawler-Syncs/Training/Modelle
- **Error-Handling:** `utils/logger.py`, `utils/error_reporter.py`
- **Authenticator/TOTP:** `utils/authenticator.py`
- **Textkondensation:** `utils/text_shortener.py`

### Services & Hintergrundjobs

- **Crawler-Service:** `services/crawler_service/main.py` mit Queue/Storage/Security-Guard
- Konfig: `services/crawler_service/config_crawler.json`

---

## 🛠️ Technologie-Stack

### Backend (Python)

| Kategorie | Technologien |
|-----------|-------------|
| **LLM** | llama-cpp-python, transformers |
| **Speech** | faster-whisper, piper-tts |
| **Embeddings** | sentence-transformers |
| **Vector DB** | chromadb, faiss |
| **API** | FastAPI, websockets |
| **ML** | torch, numpy, scipy |
| **Security** | pyotp, cryptography |
| **System** | psutil, pywin32 |

### Desktop UI

| Komponente | Technologie |
|------------|-------------|
| **Framework** | DearPyGui (ImGui) |
| **Rendering** | GPU-accelerated |
| **Theme** | Custom UE5-Style |
| **Updates** | Threading (asyncio) |

### Infrastructure

- **OS:** Windows, Linux, macOS
- **GPU:** CUDA 12.1+ (optional)
- **Storage:** SQLite, JSON, Pickle
- **Go Services:** HTTP/gRPC APIs

---

## 📁 Projekt-Struktur

```
JarvisCore/
├── core/                  # 💻 Python Core Module
│   ├── memory/           # Gedächtnis-System
│   ├── llm_manager.py    # LLM-Verwaltung
│   ├── speech_recognition.py
│   ├── text_to_speech.py
│   ├── knowledge_manager.py
│   ├── command_processor.py
│   ├── security_protocol.py
│   └── system_control.py
│
├── desktop/              # 🎮 Desktop UI
│   ├── jarvis_imgui_app_full.py  # UE5-Style ImGui UI
│   ├── frontend/         # (Deprecated Wails/Vue3)
│   └── backend/          # (Deprecated Go Backend)
│
├── plugins/              # 🧩 Plugin-System
│   ├── wikipedia/
│   ├── wikidata/
│   ├── pubmed/
│   └── semanticscholar/
│
├── go/                   # 🕸️ Go Microservices
│   ├── cmd/              # Service Entrypoints
│   │   ├── securityd/
│   │   ├── gatewayd/
│   │   └── memoryd/
│   └── internal/         # Shared Code
│
├── models/               # 🧠 LLM Models (lokal)
├── data/                 # 📚 Knowledge Base
│   ├── settings.json     # Runtime Config
│   └── secure/           # Encrypted Data
│
├── config/               # ⚙️ Konfiguration
│   ├── settings.py       # Default Settings
│   ├── intents.json
│   └── command_patterns.json
│
├── scripts/              # 🤖 Automation
│   ├── bootstrap.py      # Setup Script
│   └── download_models.py
│
├── tests/                # 🧪 Unit Tests
├── logs/                 # 📜 Systemlogs
├── backups/              # 💾 Sicherungen
└── main.py               # 🚀 Entry Point
```

---

## 📝 Installation & Setup

### Option 1: Standard (ImGui UI)

```bash
# 1. Klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2. Venv erstellen
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 3. Dependencies
pip install -r requirements.txt

# 4. ImGui UI aktivieren (falls nicht default)
export JARVIS_DESKTOP=1  # Linux/macOS
set JARVIS_DESKTOP=1     # Windows

# 5. Starten
python main.py
```

### Option 2: Mit Go-Services

```bash
# Zusätzlich zu Option 1:

# Go-Services aktivieren
export JARVIS_START_GO=1  # Linux/macOS
set JARVIS_START_GO=1     # Windows

# Starten
python main.py
```

### Option 3: Headless (ohne UI)

```bash
# ImGui deaktivieren in data/settings.json:
{
  "desktop_app": {
    "enabled": false
  }
}

# Starten
python main.py
```

### Modelle herunterladen

```bash
# LLM-Modelle (GGUF)
python scripts/download_models.py --model llama3
python scripts/download_models.py --model mistral
python scripts/download_models.py --model deepseek

# Oder manuell in models/llm/ ablegen:
# - Meta-Llama-3-8B-Instruct.Q4_K_M.gguf
# - Nous-Hermes-2-Mistral-7B-DPO.Q4_K_M.gguf
# - DeepSeek-R1-8B-f16.gguf
```

---

## ⚙️ Konfiguration

### Haupt-Config: `data/settings.json`

```json
{
  "language": "de",
  "llm": {
    "enabled": true,
    "default_model": "mistral",
    "context_length": 2048,
    "temperature": 0.7
  },
  "speech": {
    "wake_word_enabled": true,
    "stream_tts": true,
    "min_command_words": 3
  },
  "desktop_app": {
    "enabled": true
  },
  "go_services": {
    "auto_start": false
  },
  "security": {
    "safe_mode": true,
    "require_auth": false
  },
  "remote_control": {
    "enabled": false,
    "host": "127.0.0.1",
    "port": 8765
  }
}
```

### ImGui UI Einstellungen

In der UI unter **⚙️ Settings** Tab:
- **LLM:** Context Length, Temperature
- **TTS:** Speech Rate, Volume
- **Speech Recognition:** Wake Word, Continuous Listening

---

## 🛡️ Sicherheit & Risiken

### 🟢 Sicherheitsfeatures

- **Adaptive Security** - Lernende Zugriffskontrolle
- **Safe-Mode** - Sandboxed Command Execution
- **TOTP 2FA** - Optionalé Authenticator-App
- **Audit Logging** - Alle kritischen Aktionen
- **Encrypted Storage** - Sensitive Daten verschlüsselt

### ⚠️ Bekannte Risiken

1. **Token-Validierung** - Go-Services akzeptieren teilweise Tokens ohne Secret bei `AllowAnonymous`
2. **Fehlende Tests** - Kernkomponenten (LLM, Speech, Security, Plugins) weitgehend ungetestet → hohes Regressionsrisiko
3. **Model-Abhängigkeit** - Ohne lokale Modelle Fallback oder Exceptions möglich
4. **Remote-Control** - Standardmäßig deaktiviert, aber WebSocket existiert

### 🔧 Best Practices

- **Produktive Nutzung:** `safe_mode: true`, `require_auth: true`, `remote_control.enabled: false`
- **Regelmäßige Backups:** `backups/` Verzeichnis
- **Logs prüfen:** `logs/jarvis.log` für Warnungen
- **Updates:** Regelmäßig `git pull` für Sicherheitsfixes

---

## 📚 Dokumentation

### Entwickler-Docs

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detaillierte System-Architektur
- **[SECURITY.md](docs/SECURITY.md)** - Sicherheits-Richtlinien
- **[PERFORMANCE.md](docs/PERFORMANCE.md)** - Performance-Optimierung
- **[AUTO_REFACTOR.md](docs/AUTO_REFACTOR.md)** - Automatisches Refactoring
- **[UI_CONSOLIDATION.md](docs/UI_CONSOLIDATION.md)** - Desktop-App Migration

### API-Dokumentation

```bash
# API-Docs generieren
python scripts/generate_api_docs.py

# Öffnen
open docs/api/index.html
```

---

## 🧪 Tests & Qualität

### Tests ausführen

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=core --cov-report=html

# Spezifische Tests
pytest tests/test_crawler_*.py
```

### Code-Qualität

```bash
# Formatierung
black .

# Linting
ruff check .

# Type Checking
mypy core/
```

### ⚠️ Aktueller Status

- **Tests:** Wenige Unit-Tests (`tests/test_crawler_*.py`)
- **Coverage:** < 10% (geschätzt)
- **Risiko:** Hoch - Kernkomponenten ungetestet

---

## 🤝 Contributing

Beiträge sind willkommen!

### Development Setup

```bash
# 1. Fork & Clone
git clone https://github.com/YOUR_USERNAME/JarvisCore.git

# 2. Dev-Dependencies
pip install -r requirements-dev.txt

# 3. Pre-commit Hooks
pre-commit install

# 4. Branch erstellen
git checkout -b feature/my-feature

# 5. Entwickeln & Testen
pytest

# 6. Commit & Push
git commit -m "feat: add my feature"
git push origin feature/my-feature

# 7. Pull Request öffnen
```

### Commit Convention

Wir nutzen [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - Neues Feature
- `fix:` - Bugfix
- `docs:` - Dokumentation
- `refactor:` - Code-Refactoring
- `test:` - Tests
- `chore:` - Build/Dependencies

---

## 📝 Changelog

### v0.9.0 (2025-12-06) - UE5 ImGui UI

**✨ Neue Features:**
- 🎮 UE5-Style ImGui Desktop-UI (7 Tabs)
- 📊 Live-Monitoring (CPU/RAM/GPU Graphen)
- 🧠 LLM Model Manager (Download/Load/Unload)
- ⚙️ Settings Tab (LLM/TTS/Speech)
- 📜 Live Log-Viewer mit Auto-Scroll

**🔧 Verbesserungen:**
- Alte minimalistische ImGui-App entfernt
- Main.py lädt jetzt `jarvis_imgui_app_full.py`
- Background-Threads für Updates (1s/3s)
- FPS Counter im Footer

**🐛 Bugfixes:**
- MediaRouter Import-Fehler behoben
- Settings-Load Fehler gefixed

---

## 📞 Kontakt & Support

- **GitHub Issues:** [Bug Reports & Feature Requests](https://github.com/Lautloserspieler/JarvisCore/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Lautloserspieler/JarvisCore/discussions)
- **Email:** emeyer@fn.de

---

## 📜 Lizenz

**Apache License 2.0**

Dieses Projekt ist unter der Apache 2.0 Lizenz lizenziert - siehe [LICENSE](LICENSE) für Details.

**Wichtige Hinweise:**
- ✅ Kommerzielle Nutzung erlaubt
- ✅ Modifikation erlaubt
- ✅ Distribution erlaubt
- ⚠️ Haftungsausschluss - Keine Garantien
- ⚠️ Patent Grant - Siehe Lizenz

---

## 🙏 Danksagungen

- **Meta AI** - Llama Modelle
- **Microsoft** - Phi-3 Modelle
- **Mistral AI** - Mistral Modelle
- **DeepSeek** - DeepSeek-R1 Modell
- **OpenAI** - Whisper Speech Recognition
- **Rhasspy** - Piper TTS
- **DearPyGui** - GPU-accelerated ImGui für Python
- **Sentence-Transformers** - Semantic Search

---

<div align="center">

**Made with ❤️ by [@Lautloserspieler](https://github.com/Lautloserspieler)**

⭐ **Star dieses Projekt wenn es dir gefällt!** ⭐

[⬆ Back to Top](#-jarvis-core)

</div>
