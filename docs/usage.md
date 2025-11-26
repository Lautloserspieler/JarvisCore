\# Nutzung



\## Start



cd JarvisCore

python main.py



text



Beim ersten Start:



\- werden `data/`, `logs/`, `models/` angelegt,

\- `data/settings.json` wird erzeugt,

\- Modelle, Wake-Word, STT und TTS werden initialisiert.



Beenden mit `Strg + C`.



\## Weboberfläche



\- URL: http://127.0.0.1:5050

\- Standard-Token: `12345678` (anpassbar in `data/settings.json`)



\### Verfügbare Tabs



\- \*\*Chat:\*\* Text- und Sprach-Chat mit Verlauf und Markdown-Ausgabe

\- \*\*System:\*\* CPU-, RAM- und GPU-Nutzung, Latenzen und Logs

\- \*\*Modelle:\*\* Auswahl und Verwaltung der LLM-Modelle

\- \*\*Plugins:\*\* Aktivierung und Konfiguration von Plugins

\- \*\*Memory:\*\* Einsicht in den gespeicherten Wissensspeicher

\- \*\*Training:\*\* Training und Feintuning (optional)

\- \*\*Logs:\*\* System- und Fehlerprotokolle

\- \*\*Einstellungen:\*\* Sprache, Backend-Auswahl, Ports, Sicherheit und mehr



\## Sprachein- und -ausgabe



\- \*\*STT-Backends:\*\* VOSK, Whisper, Faster-Whisper (konfigurierbar)

\- \*\*TTS-Backends:\*\* XTTS v2, Coqui, pyttsx3 (konfigurierbar)

\- Wake-Word „Hey Jarvis“ aktiviert das Zuhören



\## Typische Workflows



\- Fragen an Jarvis stellen (lokales Wissen + Web-APIs)

\- Systemstatus per Sprache abfragen (CPU, RAM, Temperaturen)

\- Plugins zur Automatisierung und Tools nutzen

