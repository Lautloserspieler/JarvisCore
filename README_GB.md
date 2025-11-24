# ?? J.A.R.V.I.S. / JarvisCore – Local AI Assistant  
???? English Edition · ???? German version above

J.A.R.V.I.S. (JarvisCore) is a **modular, fully local speech and automation assistant** with web and desktop interfaces, speech recognition (Whisper/VOSK), text-to-speech (XTTS/Coqui), a knowledge system, plugin framework, and GPU-accelerated LLMs.  
Designed for **privacy, modularity, and offline intelligence** — inspired by Iron Man’s reactive AI companion.  

---

## ?? Overview

| Category | Description |
| --------- | ------------ |
| **Speech Processing** | Wake-word (“Hey Jarvis”), speech-to-text (VOSK / Whisper / Faster-Whisper), text-to-speech (XTTS v2 / Coqui / pyttsx3) |
| **Core Intelligence** | Local LLMs (LLaMA 3, Mistral, Hermes, DeepSeek V3/R1) via llama-cpp-python with GPU acceleration |
| **Knowledge & Memory** | Hybrid knowledge system (local cache + Wikipedia + OpenLibrary + Semantic Scholar + Cross-Encoder MiniLM L6 v2) |
| **Interface** | Web Dashboard (AIOHTTP) + Tkinter/Electron GUI with live telemetry, plugin control, and performance monitoring |
| **Security** | AES-256 / RSA-4096 encryption, role-based access control, Safe-Mode, emergency and audit logging |
| **Extensibility** | Plugin system, debug & training mode, REST API, autonomous task core |

---

## ?? Highlights

- **Fully local** speech input/output pipeline  
- **CUDA-enabled LLM core** (llama.cpp / Transformers)  
- **Web Dashboard** with live telemetry and plugin management  
- **System & Security monitoring** (CPU, RAM, GPU, access control)  
- **Modular architecture** separating models, knowledge, plugins, and GUI  

---

## ?? Tech Stack

| Component | Technology |
| ---------- | ----------- |
| **Backend** | Python 3.11 + |
| **Frontend** | Tkinter / Electron / AIOHTTP |
| **Speech Recognition** | VOSK / Whisper / Faster-Whisper |
| **Speech Synthesis** | XTTS v2 / Coqui / pyttsx3 |
| **Language Models** | LLaMA 3 · Mistral · Hermes · DeepSeek |
| **Knowledge Sources** | Wikipedia · OpenLibrary · Semantic Scholar · OSM |
| **Database** | SQLite / TinyDB |
| **Encryption** | AES-256 + RSA-4096 |
| **Platform** | Windows 10/11 (recommended), Linux/macOS supported |

---

## ? Quick Start (Windows / PowerShell)

```powershell
# 1) Clone or unpack the repository
cd C:\Users\<you>\Desktop
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2) Automatic setup and launch
py -3.11 bootstrap.py --run
# or simply double-click:
run_jarvis.bat
```

> If something fails, check the **Troubleshooting** section below.

---

## ?? Requirements

| Component | Recommendation |
| ---------- | -------------- |
| OS | Windows 10/11 (tested), Linux/macOS with minor tweaks |
| Python | **3.11 x64** (official python.org installer) |
| Memory | = 16 GB RAM |
| GPU | NVIDIA CUDA = 11.8 |
| Git | Required for repository cloning |

---

## ?? Installation

### Automatic (recommended)

```powershell
python bootstrap.py --run
```

Creates a virtual environment, installs dependencies, sets up CUDA if available, and starts J.A.R.V.I.S.

### Manual (alternative)

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## ?? Running J.A.R.V.I.S.

```powershell
cd JarvisCore
python main.py
```

On first launch:
- Creates `data/`, `logs/`, `models/`
- Starts the web dashboard at [http://127.0.0.1:5050](http://127.0.0.1:5050)
- Initializes microphone + LLMs  
- Saves configuration to `data/settings.json`

Exit anytime with `Ctrl + C`.

---

## ?? Web Interface

1. Open your browser: [http://127.0.0.1:5050](http://127.0.0.1:5050)  
2. Default access token: `12345678` (edit in `data/settings.json`)  

**Main Tabs**
- **Chat:** Commands, markdown output, speech control  
- **System:** Hardware + performance monitoring  
- **Models:** Manage LLMs, download progress  
- **Plugins / Memory / Training / Logs / Settings**

---

## ?? Security

- AES-256 + RSA-4096 encryption  
- Role-based access control  
- Safe-Mode for restricted execution  
- Security logs in `logs/security.log`  
- Emergency protocol (auto-lockdown / alerts / shutdown)  

---

## ?? Knowledge Sources

- **Wikipedia API** – full article and category search  
- **OpenLibrary / isbnlib** – book metadata  
- **Semantic Scholar / DBpedia / SPARQLWrapper** – academic and linked-data queries  
- **Local cache** – offline recall with Cross-Encoder semantic ranking  

---

## ?? Integrated AI Models

| Component | License | Source |
| ---------- | -------- | ------- |
| Meta LLaMA 3 | Meta LLaMA 3 License | Hugging Face – meta-llama |
| Mistral / Mixtral / Hermes | Apache 2.0 | Hugging Face – mistralai |
| DeepSeek V3 / R1 | MIT / Apache 2.0 | Hugging Face – deepseek-ai |
| XTTS v2 (Coqui) | MPL 2.0 | coqui.ai |
| Whisper / Faster-Whisper | MIT | openai/whisper |
| VOSK | Apache 2.0 | alphacep/vosk-api |
| Knowledge APIs | Public | Wikipedia, OpenLibrary, Semantic Scholar, OSM |

---

## ?? Troubleshooting

| Problem / Message | Solution |
| ----------------- | -------- |
| `CUDA not available – using CPU` | Install CUDA 11.8 + latest NVIDIA drivers |
| `PyAudio install error` | Install Microsoft C++ Build Tools and rerun setup |
| `Ignoring invalid distribution` | Recreate the virtual environment |
| Models load slowly | First download may take GBs; cached afterward |
| Web UI blank / 401 error | Verify token and check `jarvis.log` |

---

## ?? Development & Contributions

1. Fork the repository or create a feature branch  
2. Test locally with `python main.py`  
3. Submit a pull request with a short explanation  

Follow **PEP-8** and avoid uploading sensitive data.  

---

## ?? License

Copyright © 2025 Lautloserspieler  

Licensed under the **Apache License 2.0**,  
with the following additional clause:

> Commercial use, resale, or redistribution of this software  
> is prohibited without prior written permission of the author.  
>  
> Third-party components remain under their respective licenses  
> (see `third_party_licenses`).

---

## ?? Contact & Support

Project Lead: **Lautloserspieler**  
GitHub: [github.com/Lautloserspieler](https://github.com/Lautloserspieler)  

If you enjoy J.A.R.V.I.S., ? **give it a star on GitHub** and support future development!

---
