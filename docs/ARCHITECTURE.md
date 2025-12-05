# JarvisCore Architektur (Kurzüberblick)

## Datenfluss
Audio → STT (Whisper/Faster-Whisper) → Intent/Command Parsing → LLM-Router → Antwort → TTS (pyttsx3/XTTS) → Audioausgabe. Optional: Plugins/Wissenssuche, Sicherheitsprüfungen und Kontextmanager.

## Kernmodule (core/)
- `command_processor.py`: Intent-Erkennung, Routing zu Aktionen/Plugins, Sicherheitsprüfung.
- `llm_manager.py` + `llm_router.py`: Modellwahl (Konversation/Code/Analyse), Laden/Cache, Chat-Kontext.
- `speech_recognition.py`: Wake-Word/Hotword, STT.
- `text_to_speech.py`: TTS-Backends, Voice-Latents, Playback.
- `knowledge_manager.py`, `local_knowledge_*`: Lokale Wissensbasis/Import/Scanner.
- `plugin_manager.py` + `plugins/`: Externe Quellen (Wikipedia, OSM, PubMed, Wikidata, Semanticscholar, OpenLibrary).
- `security_protocol.py` + `security_manager.py`: Safe-Mode, Sensitivität, Logging/Findings.
- `system_control.py`, `system_monitor.py`: Systemstatus, Ressourcenmonitor, optionale Aktionen.
- `websocket_gateway.py`, `webapp/`: Web-UI/Headless-Interaktion.

## Konfiguration
- Templates: `data/settings.template.json`; lokal kopieren nach `data/settings.json` (nicht versionieren).
- Weitere Konfigs in `config/` (Intents, Plugins, Persona).
- Env: `.env` für Schlüssel/Tokens (nicht versionieren).

## Modelle
- Nicht gebundled. Erwartete Pfade unter `models/` (LLM-GGUF, STT, optional XTTS/Voices).
- Download-Anleitungen im README.

## Sicherheit
- Sensible Dateien bleiben lokal (LocalWissen, Logs, Datenbanken).
- Optionaler Safe-Mode/Plugin-Blockierung bei sensiblen Inhalten.
- Logging/Audit konfigurierbar in `data/settings.json`.

## Erweiterbarkeit
- Plugins: einfache Schnittstelle über `plugins/`; Beispielplugin als Vorlage nutzen.
- Services/Agenten: `services/`, `core/*_agent.py` für Hintergrundjobs (z. B. Knowledge Expansion).

## Deployment-Hinweis
- Keine absoluten Pfade fest verdrahtet; Pfade über Settings steuerbar.
- Modelle und persönliche Daten immer lokal halten; Repo nur Code/Configs/Templates.
