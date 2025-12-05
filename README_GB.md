# J.A.R.V.I.S. / JarvisCore — Local AI Assistant

JarvisCore is a modular, fully local speech and automation assistant with web/desktop UI, STT/TTS, knowledge system, plugin framework, and GPU-accelerated LLMs. Focus: privacy, extensibility, and robust safety.

German version: see `README.md`.

---

## Overview
- Speech: wake word, VOSK/Whisper/Faster-Whisper, TTS (XTTS v2 / Coqui / pyttsx3)
- Intelligence: LLaMA/Mistral/Hermes/DeepSeek via llama-cpp-python (CUDA)
- Knowledge & Memory: local cache + Wikipedia/OpenLibrary/Semantic Scholar + cross-encoder MiniLM L6 v2
- Interfaces: Web dashboard (AIOHTTP), Tkinter/Electron GUI, headless mode
- Security: role-based control, Safe-Mode, audit logs, optional TOTP 2FA
- Extensibility: plugins, autonomous tasks, REST services (crawler), agents

## Architecture (brief)
- Entry: `main.py` orchestrates Speech -> CommandProcessor/LLM -> TTS, starts Web UI, scheduler, and safety subsystems.
- Core (`core/`): speech recognition, command processing, LLM manager/router, memory layers, security protocol/manager, system control/monitor, plugin manager.
- Web: `webapp/server.py` (AIOHTTP Websocket/HTTP) with token, IP whitelist, and rate limits.
- Services: `services/crawler_service` (FastAPI) for knowledge crawling with SecurityGuard (domains/robots/resources) and SQLite storage.
- Utilities: logging, error reporting, secure storage (DPAPI), authenticator (TOTP), text shortener.

## Requirements
- OS: Windows 10/11 recommended; Linux/macOS with adjustments
- Python: 3.11 (64-bit)
- RAM: 16 GB+ recommended; GPU: NVIDIA CUDA 11.8/12.x for LLM/TTS
- Tools: git, PowerShell/Bash

## Setup & Run (Windows / PowerShell)
```powershell
cd C:\Users\<you>\Desktop
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

py -3.11 bootstrap.py --run
# or double-click run_jarvis.bat
```
Linux/macOS: `python3.11 -m venv venv && source venv/bin/activate && python bootstrap.py --run`.

## Configuration
- Base settings: `data/settings.json` (template: `data/settings.template.json`). Do not commit secrets; use `.env`/environment overrides.
- Crawler service: `services/crawler_service/config_crawler.json`. Provide API key via env var `JARVIS_CRAWLER_API_KEY`; JSON key may stay empty.
- Models: place under `models/` (LLM GGUF, Whisper/Faster-Whisper, optional XTTS voices) and adjust paths.

## Security Notes
- Keep secrets out of the repo; use environment variables and DPAPI-backed storage (`utils/secure_storage.py`).
- Web UI: set a token, enable IP whitelist and rate limits (`webapp/server.py`).
- System actions: Safe-Mode (`security` settings) and whitelisted paths/programs.
- Crawler: prefer domain allowlist, respect robots.txt, configure CPU/RAM limits.

## Tests
```bash
python -m pytest
```
Includes coverage for crawler auth and config API key handling.

## Known Items
- FastAPI `@on_event` is deprecated; migrating to lifespan events is recommended.
