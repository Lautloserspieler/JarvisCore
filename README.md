# J.A.R.V.I.S. / JarvisCore — lokaler KI-Assistent

JarvisCore ist ein modularer, voll lokal laufender Sprach- und Automationsassistent mit Web- und Desktop-Oberflaeche, STT/TTS, Wissensmodul, Plugin-System und GPU-beschleunigten LLMs. Fokus: Datenschutz, Erweiterbarkeit, robuste Sicherheitsmechanismen.

English version: siehe `README_GB.md`.

---

## Ueberblick
- Sprachverarbeitung: Wake-Word, VOSK/Whisper/Faster-Whisper, TTS (XTTS v2 / Coqui / pyttsx3)
- Intelligenz: LLaMA/Mistral/Hermes/DeepSeek via llama-cpp-python (CUDA)
- Wissen & Memory: Lokaler Cache + Wikipedia/OpenLibrary/Semantic Scholar + Cross-Encoder MiniLM L6 v2
- Interfaces: Web-Dashboard (AIOHTTP), Tkinter/Electron-GUI, Headless-Mode
- Sicherheit: Rollenbasierte Kontrolle, Safe-Mode, Audit-Logs, optionale 2FA (TOTP)
- Erweiterbarkeit: Plugins, autonome Tasks, REST-Services (Crawler), Agenten

## Architektur (Kurz)
- Einstieg: `main.py` orchestriert Speech -> CommandProcessor/LLM -> TTS, startet Web-UI, Scheduler und Sicherheits-Subsysteme.
- Kernmodule (`core/`): `speech_recognition`, `command_processor`, `llm_manager` + `llm_router`, Memory (`short_term`, `long_term`, `vector_memory`), Sicherheit (`security_manager`, `security_protocol`), Systemsteuerung (`system_control`, `system_monitor`), Plugins (`plugin_manager`).
- Web: `webapp/server.py` (AIOHTTP Websocket/HTTP) mit Token- und IP-Whitelist, Rate-Limits.
- Services: `services/crawler_service` (FastAPI) fuer wissensbezogenes Crawlen mit SecurityGuard (Domain-/Robots-/Ressourcenlimits) und SQLite-Storage.
- Utilities: Logging, Error-Reporting, Secure Storage (DPAPI), Authenticator (TOTP), Textkuerzer.

## Go-Services (neu)
- Ort: `go/` (Modul `jarviscore/go`).
- `securityd`: HTTP-Service fuer Policy-/Token-Checks (`go run ./cmd/securityd`).
- `gatewayd`: WebSocket-Hub + Broadcast (`go run ./cmd/gatewayd`) mit `/ws` und `/api/events`.
- `memoryd`: Key-Value-/Memory-Service (`go run ./cmd/memoryd`) mit `save/get/search/delete`-Endpoints.
- `systemd`: Systemressourcen/Status (`go run ./cmd/systemd`) mit `/system/resources` und `/system/status`.
- `speechtaskd`: STT-Orchestrator-Stub (`go run ./cmd/speechtaskd`), Python bleibt STT-Hauptpfad.
- `commandd`: Command-Staging (`go run ./cmd/commandd`) mit `/command/execute`.
- gatewayd optional: Forward-Only-Modus per `JARVIS_GATEWAYD_ONLY=1`, ansonsten laeuft der Python-Websocket weiter als Fallback.
- memoryd: unterstützt `ttl_seconds` für Einträge (persistente Ablage unter `data/memoryd`).
- securityd: Token/Rollen via `SECURITYD_TOKENS` (JSON), optional JWT HS256 via `SECURITYD_JWT_SECRET`, Policies via `SECURITYD_POLICY` (JSON Rolle->Permissions).
- Konfig securityd: `SECURITYD_LISTEN` (Standard `:7071`), `JARVIS_SECURITYD_TOKEN` (optional), `JARVIS_SECURITYD_URL` fuer Python-Wrapper.
- Konfig gatewayd: `GATEWAYD_LISTEN` (Standard `:7081`), optional `JARVIS_GATEWAYD_TOKEN`; Python-Spiegelung via `JARVIS_GATEWAYD_URL`, `JARVIS_GATEWAYD_ONLY=1` fuer reinen Forward-Betrieb.
- Konfig memoryd: `MEMORYD_LISTEN` (Standard `:7072`), `MEMORYD_STORE` (Standard `data/memoryd/store.json`), optional `JARVIS_MEMORYD_TOKEN`, Deaktivierung via `JARVIS_MEMORYD_ENABLED=0`.
- Konfig systemd: `SYSTEMD_LISTEN` (Standard `:7073`), optional `JARVIS_SYSTEMD_TOKEN`, Deaktivierung via `JARVIS_SYSTEMD_ENABLED=0`, Python-Wrapper per `JARVIS_SYSTEMD_URL`.

## Anforderungen
- OS: Windows 10/11 empfohlen; Linux/macOS moeglich mit Anpassungen
- Python: 3.11 (64-bit)
- RAM: ab 16 GB empfohlen; GPU: NVIDIA mit CUDA 11.8/12.x fuer LLM/TTS
- Tools: git, PowerShell/Bash

## Installation & Start (Windows / PowerShell)
```powershell
cd C:\Users\<du>\Desktop
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# Optional: Abhaengigkeiten im venv
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Bootstrap + Start
py -3.11 bootstrap.py --run
# oder Doppelklick: run_jarvis.bat
```
Linux/macOS: analog mit `python3.11 -m venv venv && source venv/bin/activate && python bootstrap.py --run`.

## Konfiguration
- Basis-Settings: `data/settings.json` (Template: `data/settings.template.json`). Nicht einchecken; sensible Felder via `.env` oder Umgebung setzen.
- Crawler-Service: `services/crawler_service/config_crawler.json`. API-Key per Env `JARVIS_CRAWLER_API_KEY` setzen; JSON-Key kann leer bleiben.
- Modelle: unter `models/` ablegen (LLM GGUF, Whisper/Faster-Whisper, optional XTTS Stimmen). Pfade in Settings anpassen.

## Sicherheitshinweise
- Keine Klartext-Secrets im Repo belassen. Verwende `.env`/Umgebungsvariablen und DPAPI-Speicher (`utils/secure_storage.py`) fuer lokale Geheimnisse.
- Web-UI: Token setzen, IP-Whitelist und Rate-Limits pruefen (`webapp/server.py`).
- Systemaktionen: Safe-Mode verwenden (`security`-Section in Settings) und nur freigegebene Pfade/Programme erlauben.
- Crawler: Domain-Whitelist, Robots.txt-Respekt und Ressourcengrenzen im Config praeferieren.

## Tests
```bash
python -m pytest
```
Neue Tests decken Crawler-Auth und Config-API-Key-Handling ab.

## Bekannte Baustellen
- FastAPI `@on_event` ist deprecated - Umstellung auf Lifespan empfohlen.
