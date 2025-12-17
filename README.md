# 🤖 JARVIS Core System

<div align="center">

**Just A Rather Very Intelligent System**

Ein moderner KI-Assistent mit holographischer UI und **vollständig lokaler llama.cpp Inferenz**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-cyan.svg)](https://golang.org)
[![Vue](https://img.shields.io/badge/Vue-3.5+-green.svg)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF-orange.svg)](https://github.com/ggerganov/llama.cpp)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

[🇬🇧 English Version](./README_GB.md)

</div>

---

## ✨ Features

### 🧠 KI-Engine
- ✅ **llama.cpp Lokale Inferenz** - Vollständig implementiert und funktionsfähig!
- ✅ **Automatische GPU-Erkennung** - NVIDIA CUDA Support
- ✅ **7 GGUF-Modelle** - Mistral, Qwen, DeepSeek, Llama und mehr
- ✅ **Chat mit History** - Kontext-bewusste Konversationen
- ✅ **Bis 32K Context** - Lange Konversationen möglich
- ✅ **System-Prompts** - JARVIS-Persönlichkeit konfigurierbar

### 🎨 Frontend (Vue 3)
- ✅ **Holographische UI** - Beeindruckende JARVIS-inspirierte Benutzeroberfläche
- ✅ **Echtzeit-Chat** - WebSocket-basierte Live-Kommunikation
- ✅ **Sprach-Interface** - Voice-Input mit visueller Rückmeldung
- ✅ **Multi-Tab Navigation** - Chat, Dashboard, Memory, Models, Settings
- ✅ **Model-Management** - Download und Verwaltung von KI-Modellen
- ✅ **Plugin System** - Wetter, Timer, Notizen, News uvm.
- ✅ **Responsive Design** - Funktioniert auf allen Bildschirmgrößen
- ✅ **Dark Theme** - Cyberpunk-Ästhetik mit leuchtenden Effekten

### 🚀 Backend (Python + FastAPI)
- ✅ **FastAPI Server** - Hochperformanter Python Backend
- ✅ **llama.cpp Integration** - Native GGUF-Model-Inferenz
- ✅ **WebSocket Support** - Echtzeitkommunikation
- ✅ **RESTful API** - Vollständige REST-Endpunkte
- ✅ **Plugin System** - Erweiterbare Architektur
- ✅ **Memory Storage** - Konversationshistorie & Kontext

---

## 💻 Voraussetzungen

- **Python 3.11+** - [python.org](https://python.org)
- **Node.js 18+** - [nodejs.org](https://nodejs.org)
- **Git** - [git-scm.com](https://git-scm.com)
- **(Optional)** NVIDIA GPU mit CUDA für beschleunigte Inferenz

---

## 🚀 Installation & Start

### Schritt 1: Repository klonen

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore
```

### Schritt 2: Basis-Dependencies installieren

```bash
pip install -r requirements.txt
```

### Schritt 3: llama.cpp Setup (🆕 Automatisch!)

**NEU:** Automatische GPU-Erkennung und optimale Installation!

```bash
cd backend
python setup_llama.py
```

**Das Script erkennt automatisch:**
- ✅ NVIDIA GPU → Installiert mit CUDA Support (30-50 tok/s)
- ✅ AMD GPU → Empfiehlt CPU-Version (siehe unten)
- ✅ Keine GPU → Installiert CPU-Version (5-10 tok/s)

**Ausgabe-Beispiel:**
```
╭──────────────────────────────────────────────────────╮
│   JARVIS Core - llama.cpp Setup Script              │
│      Automatic GPU Detection & Install               │
╰──────────────────────────────────────────────────────╯

[INFO] System: Windows AMD64
[INFO] Python: 3.11.5
[INFO] Detecting GPU...
[INFO] NVIDIA GPU detected!

Installing llama-cpp-python with NVIDIA CUDA support

✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅

[SUCCESS] llama-cpp-python installed successfully!
[INFO] GPU Mode: NVIDIA CUDA
[INFO] You can now run: python main.py
```

### Schritt 4: Frontend Dependencies

```bash
cd ../frontend
npm install
cd ..
```

### Schritt 5: JARVIS starten

```bash
python main.py
```

**Das war's!** Das `main.py` Script:
- ✅ Startet automatisch Backend & Frontend
- ✅ Öffnet Browser bei http://localhost:5000
- ✅ Backend läuft auf http://localhost:5050

---

## 🎮 Quick Start Alternative

### One-Liner Installation (Empfohlen)

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git && cd JarvisCore && pip install -r requirements.txt && cd backend && python setup_llama.py && cd ../frontend && npm install && cd .. && python main.py
```

---

## 🌐 Zugriffspunkte

Nach dem Start erreichst du:

- 🎨 **Frontend UI**: http://localhost:5000
- 🔧 **Backend API**: http://localhost:5050
- 📚 **API-Dokumentation**: http://localhost:5050/docs
- 🔌 **WebSocket**: ws://localhost:5050/ws

---

## 🧠 llama.cpp Lokale Inferenz

**NEU in v1.1.0** - Production-ready mit automatischer GPU-Erkennung!

### Features
- 🚀 **GPU-Acceleration** - CUDA automatisch erkannt
- 🎯 **GGUF-Support** - Alle llama.cpp-kompatiblen Modelle
- 💬 **Chat-Modus** - History mit bis zu 32K Context
- ⚡ **Performance** - 30-50 tokens/sec (NVIDIA), 5-10 tokens/sec (CPU)

### GPU Support

| GPU-Typ | Support | Installation | Performance | Empfehlung |
|---------|---------|--------------|-------------|------------|
| **NVIDIA** | ✅ CUDA | Automatisch | ⚡⚡⚡ 30-50 tok/s | ⭐ Empfohlen |
| **AMD** | ⚠️ ROCm | Komplex | ⚡⚡⚡ 25-40 tok/s | 👉 **Nutze CPU-Version** |
| **Intel Arc** | 🔄 oneAPI | Coming Soon | ⚡⚡ 20-35 tok/s | In Entwicklung |
| **CPU** | ✅ Standard | Automatisch | ⚡ 5-10 tok/s | ✅ Funktioniert |

#### 💡 Hinweis für AMD GPU Nutzer:

**ROCm Setup ist komplex und erfordert:**
- Visual Studio Build Tools
- ROCm SDK Installation (~5 GB)
- Spezifische Treiber-Versionen
- Mehrere Neustarts
- Komplizierte Pfad-Konfiguration

**👉 Empfehlung: Nutze die CPU-Version!**
```bash
python setup_llama.py
# Wähle Option 3: CPU-Version
```

**Vorteile CPU-Version:**
- ✅ Sofort einsatzbereit
- ✅ Keine komplexe Konfiguration
- ✅ Stabil und zuverlässig
- ✅ 5-10 tokens/sec (ausreichend für Chat)
- ✅ Kleinere Modelle (3B) laufen flüssig

### Verfügbare Modelle

| Model | Größe | Use Case | CPU Performance |
|-------|-------|----------|----------------|
| **Llama 3.2 3B** | ~2.0 GB | Klein, schnell | ⚡⚡⚡ 8-12 tok/s |
| **Phi-3 Mini** | ~2.3 GB | Kompakt, Chat | ⚡⚡⚡ 7-10 tok/s |
| **Qwen 2.5 7B** | ~5.2 GB | Vielseitig | ⚡⚡ 5-8 tok/s |
| **Mistral 7B Nemo** | ~7.5 GB | Code, technisch | ⚡⚡ 4-7 tok/s |
| **DeepSeek R1 8B** | ~6.9 GB | Analysen | ⚡ 3-6 tok/s |

**👉 Empfehlung für CPU: Nutze Llama 3.2 3B oder Phi-3 Mini für beste Performance!**

---

## 🔧 Manuelle llama.cpp Installation

Falls das automatische Script nicht funktioniert:

### NVIDIA GPU (CUDA)

```bash
cd backend
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir --no-binary llama-cpp-python
```

### CPU Only (Empfohlen für AMD)

```bash
cd backend
pip uninstall llama-cpp-python -y
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### AMD GPU (ROCm) - Nur für Experten

⚠️ **Achtung:** Sehr komplex! Nur für erfahrene Nutzer empfohlen.

1. **ROCm installieren** (~5 GB): https://rocm.docs.amd.com/
2. **Visual Studio Build Tools** installieren
3. **Neustart erforderlich**
4. **Dann:**
```bash
cd backend
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DLLAMA_HIPBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir --no-binary llama-cpp-python
```

---

## 📦 Model-Download-System

JARVIS Core nutzt ein **Ollama-inspiriertes Download-System**:

### Features
- 🔄 **Multi-Registry-Support** - HuggingFace, Ollama, Custom URLs
- 📦 **Resume-Downloads** - Unterbrochene Downloads fortsetzen
- ✅ **SHA256-Verifizierung** - Automatische Integritätsprüfung
- 📊 **Live-Progress** - Speed, ETA, Fortschrittsbalken
- 🔐 **HuggingFace Token** - Support für private Repos

### Models verwalten

1. **JARVIS starten**: `python main.py`
2. **Web-UI öffnen**: http://localhost:5000
3. **Models-Tab**: Navigation zur Model-Verwaltung
4. **Model downloaden**: Klick "Download" → Wähle Quantization
5. **Model laden**: Klick "Load" bei heruntergeladenem Modell
6. **Chat starten**: Gehe zu "Chat" Tab und schreibe

Weitere Infos: [docs/LLM_DOWNLOAD_SYSTEM.md](./docs/LLM_DOWNLOAD_SYSTEM.md)

---

## 🔌 Plugin System

**NEU in v1.1.0** - Erweiterbare Plugin-Architektur!

### Verfügbare Plugins

| Plugin | Beschreibung | API-Key |
|--------|--------------|----------|
| ☀️ **Weather** | OpenWeatherMap Integration | ✅ Erforderlich |
| ⏰ **Timer** | Timer & Erinnerungen | ❌ Nicht nötig |
| 📝 **Notes** | Schnelle Notizen | ❌ Nicht nötig |
| 📰 **News** | RSS News Feeds | ❌ Nicht nötig |

### Plugin aktivieren

1. Öffne **Plugins Tab** in der UI
2. Klicke **"Аktivieren"** beim gewünschten Plugin
3. Falls API-Key nötig → Modal öffnet sich automatisch
4. Gib API-Key ein → Wird sicher in `config/settings.json` gespeichert
5. Plugin ist aktiviert! ✅

---

## 📁 Projektstruktur

```
JarvisCore/
├── main.py                 # 🚀 Unified Launcher
├── requirements.txt        # 📦 Python Dependencies
├── core/                   # 🧠 Core Python Modules
│   ├── llama_inference.py # llama.cpp Engine
│   ├── model_downloader.py
│   └── ...
├── backend/                # 🔧 Python/FastAPI Backend
│   ├── main.py
│   ├── setup_llama.py     # 🆕 Auto GPU Setup
│   ├── plugin_manager.py
│   └── requirements.txt
├── frontend/               # 🎨 Vue 3 Frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── plugins/                # 🔌 Plugin System
│   ├── weather_plugin.py
│   ├── timer_plugin.py
│   └── ...
├── models/llm/             # 📦 GGUF Models
├── config/                 # ⚙️ Configuration
├── data/                   # 🗄️ User Data
├── docs/                   # 📚 Documentation
└── README.md
```

---

## 🐛 Troubleshooting

### Problem: GPU nicht erkannt

```bash
# GPU-Status prüfen
nvidia-smi  # NVIDIA

# llama.cpp neu installieren
cd backend
python setup_llama.py
```

### Problem: Port bereits belegt

```bash
# Windows
netstat -ano | findstr :5000
netstat -ano | findstr :5050

# Linux/Mac
lsof -i :5000
lsof -i :5050
```

### Problem: Module nicht gefunden

```bash
pip install -r requirements.txt
cd frontend && npm install
```

### Problem: AMD GPU - ROCm Installation zu komplex

**Lösung: Nutze CPU-Version!**
```bash
cd backend
python setup_llama.py
# Wähle Option 3
```

Weitere Hilfe: [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)

---

## 🎯 Roadmap

### ✅ v1.1.0 (Current) - Dezember 2025
- ✅ Vue 3 Frontend
- ✅ Production-ready llama.cpp
- ✅ Automatische GPU-Erkennung
- ✅ Plugin System mit API-Key Management
- ✅ Model Download System

### 🔄 v1.2.0 - Q1 2026
- Voice Input (Whisper)
- Voice Output (XTTS v2)
- Desktop App (Wails)
- Enhanced Memory System
- Docker Support

### 📋 v2.0.0 - Q2 2026
- RAG Implementation
- Vector Database
- Multi-User Support
- Cloud Deployment
- Mobile App

---

## 🤝 Contributing

Beiträge sind willkommen! Bitte lies [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

### Quick Start für Contributors

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/amazing-feature`)
3. Commit deine Änderungen (`git commit -m 'feat: Add amazing feature'`)
4. Push zum Branch (`git push origin feature/amazing-feature`)
5. Erstelle einen Pull Request

---

## 📄 Lizenz

**Apache License 2.0** mit zusätzlicher kommerzieller Einschränkung.

Vollständige Lizenz: [LICENSE](./LICENSE)

---

## 🙏 Danksagungen

- Inspiriert von JARVIS aus Iron Man
- Gebaut mit [Vue 3](https://vuejs.org/)
- Backend mit [FastAPI](https://fastapi.tiangolo.com/)
- Lokale Inferenz mit [llama.cpp](https://github.com/ggerganov/llama.cpp)

---

## 📚 Weitere Dokumentation

- [Quick Start Guide](docs/README_QUICKSTART.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [LLM Download System](docs/LLM_DOWNLOAD_SYSTEM.md)
- [Performance Guide](docs/PERFORMANCE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Changelog](docs/CHANGELOG.md)

---

<div align="center">

**Erstellt mit ❤️ von Lautloserspieler**

*"Manchmal muss man rennen, bevor man gehen kann."* - Tony Stark

**Version:** 1.1.0 | **Release:** 02. Januar 2026

[⭐ Star us on GitHub](https://github.com/Lautloserspieler/JarvisCore) | [🐛 Report Bug](https://github.com/Lautloserspieler/JarvisCore/issues) | [💡 Request Feature](https://github.com/Lautloserspieler/JarvisCore/issues)

</div>
