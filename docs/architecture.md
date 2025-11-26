\# Architektur



\## Übersicht



JarvisCore besteht aus folgenden Schichten:



\- Eingabe: Mikrofon, Text (Web-UI / API)

\- Sprachverarbeitung: Wake-Word, STT

\- LLM-Kern: lokale, GPU-beschleunigte Sprachmodelle

\- Wissenssystem: lokale Datenbank + externe Wissensquellen

\- Ausgabe: TTS, Web-UI, Logs

\- Verwaltung: Web-Dashboard, Konfiguration, Plugins, Sicherheit



\## Sprachverarbeitung



\- Wake-Word („Hey Jarvis“) für Aktivierung

\- STT-Backends:

&nbsp; - VOSK (leicht, offline)

&nbsp; - Whisper / Faster-Whisper (GPU-optimiert, höhere Qualität)



\## LLM-Kern



\- Unterstützte Modelle:

&nbsp; - Meta LLaMA 3

&nbsp; - Mistral / Mixtral / Hermes

&nbsp; - DeepSeek V3 / R1

\- Ausführung via `llama-cpp-python` mit CUDA-Unterstützung

\- Parametrierbare Einstellungen: Kontextlänge, Temperatur, Sampling-Strategien



\## Wissenssystem



\- Externe Quellen: Wikipedia, OpenLibrary, Semantic Scholar, OSM

\- Lokaler Cache (SQLite / TinyDB) für schnelle Re-Queries

\- Semantisches Ranking mit Cross-Encoder (MiniLM L6 v2)



\## Oberfläche



\- Web-Dashboard basierend auf AIOHTTP mit REST und WebSocket Schnittstellen

\- Optional Desktop-GUI (Tkinter oder Electron)



\## Sicherheit \& Logging



\- Verschlüsselung: AES-256 und RSA-4096

\- Rollenbasiertes Zugriffsmanagement, Safe-Mode

\- Umfangreiche System-, Sicherheits- und Aktionslogs (`logs/` Verzeichnis)

