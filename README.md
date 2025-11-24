# 🧠 J.A.R.V.I.S. / JarvisCore – Lokaler KI-Assistent  
🇩🇪 Vollständig lokal · 🇬🇧 English version below  

J.A.R.V.I.S. (JarvisCore) ist ein **modularer, vollständig lokaler Sprach- und Automationsassistent** mit Web- und Desktop-Oberfläche ( momentan Deaktiviert ) , Spracherkennung (Whisper/VOSK), Text-zu-Sprache (XTTS/Coqui), Wissens­datenbank, Plugin-System und GPU-beschleunigten LLMs.  
Entwickelt für Datenschutz, Erweiterbarkeit und echte Offline-Intelligenz.  
**Hinweis:** Sprach-Ein- und -Ausgabe befinden sich noch in aktiver Entwicklung; Funktionsumfang und Stabilität können sich ändern.  

---

## 🚀 Überblick

| Kategorie | Beschreibung |
| ---------- | ------------- |
| **Sprachverarbeitung** | Permanentes Wake-Word („Hey Jarvis“), Sprache-zu-Text (VOSK / Whisper / Faster-Whisper), Text-zu-Sprache (XTTS v2 / Coqui / pyttsx3) |
| **Intelligenz-Kern** | Lokale LLMs (LLaMA 3, Mistral, Hermes, DeepSeek V3/R1) via llama-cpp-python mit GPU-Beschleunigung |
| **Wissen & Gedächtnis** | Hybrid-System aus lokalem Cache + Wikipedia + OpenLibrary + Semantic Scholar + Cross-Encoder (MiniLM L6 v2) |
| **Oberfläche** | Web-Dashboard (AIOHTTP) + Tkinter/Electron-GUI mit Live-Telemetrie, Plugin-Steuerung und Systemmonitor |
| **Sicherheit** | AES-256 / RSA-4096, rollenbasiertes Zugriffssystem, Safe-Mode, Notfall- und Protokollsystem |
| **Erweiterbarkeit** | Plug-in-System, Training- und Debug-Modus, API-Integration, autonomes Task-System |

---

## ⚙️ Highlights

- Komplett **lokale Pipeline** für Spracheingabe und -ausgabe  
- **CUDA-fähiger LLM-Kern** (llama.cpp / Transformers)  
- **Web-Dashboard** mit Live-Telemetrie  
- **System- und Sicherheits-Monitoring** (CPU, RAM, GPU, Logs, Berechtigungen)  
- **Modularer Aufbau** mit klarer Trennung von Modellen, Wissen, Plugins und GUI  

---

## 🧩 Technologiestack

| Komponente | Technologie |
| ----------- | ------------ |
| **Backend** | Python 3.11 + |
| **Frontend** | Tkinter / Electron / AIOHTTP |
| **Spracherkennung** | VOSK / Whisper / Faster-Whisper |
| **Sprachsynthese** | XTTS v2 / Coqui / pyttsx3 |
| **Sprachmodelle** | LLaMA 3 · Mistral · Hermes · DeepSeek |
| **Wissensquellen** | Wikipedia · OpenLibrary · Semantic Scholar · OSM |
| **Datenbank** | SQLite / TinyDB |
| **Verschlüsselung** | AES-256 + RSA-4096 |
| **Plattform** | Windows 10/11 (empfohlen) · Linux/macOS möglich |

---

## ⚡ Schnellstart (Windows / PowerShell)

```powershell
# 1) Repository klonen oder entpacken
cd C:\Users\<du>\Desktop
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2) Automatische Einrichtung + Start
py -3.11 bootstrap.py --run
# oder per Doppelklick:
run_jarvis.bat
```

> Bei Problemen: siehe Abschnitt **Fehlerbehebung** unten.

---

## 🔧 Voraussetzungen

| Komponente | Empfehlung |
| ----------- | ----------- |
| Betriebssystem | Windows 10/11 (getestet), macOS/Linux mit Anpassungen |
| Python | **3.11 x64** (von python.org) |
| Speicher | ≥ 16 GB RAM |
| GPU | NVIDIA, CUDA ≥ 12.0 |
| Git | Für Repository-Klon |

---

## 📦 Installation

### Automatisch (empfohlen)

```powershell
python bootstrap.py --run
```

Erstellt venv, installiert alle Abhängigkeiten, richtet CUDA-Umgebung ein und startet Jarvis.

### Alternativ manuell

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 🎮 Start & Nutzung

```powershell
cd JarvisCore
python main.py
```

Beim ersten Start:
- Erzeugt `data/`, `logs/`, `models/`
- Startet Web-Dashboard auf `http://127.0.0.1:5050`
- Initialisiert Mikrofon und LLMs
- Speichert Einstellungen in `data/settings.json`

Beenden: `Strg + C`

---

## 🌐 Weboberfläche

1. Browser öffnen: [http://127.0.0.1:5050](http://127.0.0.1:5050)  
2. Token: Standard `12345678` (änderbar in `data/settings.json`)  

Tabs:
- **Chat** – Text/Sprachsteuerung, Verlauf, Markdown-Output  
- **System** – Hardware- und Leistungsmonitor  
- **Modelle** – LLM-Verwaltung mit Downloadfortschritt  
- **Plugins / Memory / Training / Logs / Einstellungen**

---

## 🔒 Sicherheit

- AES-256 + RSA-4096  
- Rollenrechte & Zugriffskontrolle  
- Safe-Mode zur Befehlsbegrenzung  
- Sicherheits-Logs unter `logs/security.log`  
- Notfallprotokoll (Sperrung, Shutdown, Alerts)  

---

## 📚 Wissensquellen

- **Wikipedia-API** – Artikel & Kategorien  
- **OpenLibrary / isbnlib** – Buchdaten  
- **Semantic Scholar / DBpedia / SPARQLWrapper** – Fachwissen  
- **Lokaler Cache** – Offline-Abruf, semantisches Ranking mit Cross-Encoder
- **Crawler Bot** - Neue mögliche Wissensammel Plugin ( Muss nicht kann genutst werden für bessere und genaueren antwort Generieung von Jarvis)

---

## 🧠 Eingebundene KI-Modelle

| Komponente | Lizenz | Quelle |
| ----------- | ------- | ------- |
| Meta LLaMA 3 | Meta LLaMA 3 License | Hugging Face – meta-llama |
| Mistral / Mixtral / Hermes | Apache 2.0 | Hugging Face – mistralai |
| DeepSeek V3 / R1 | MIT / Apache 2.0 | Hugging Face – deepseek-ai |
| XTTS v2 (Coqui) | MPL 2.0 | coqui.ai |
| Whisper / Faster-Whisper | MIT | openai/whisper |
| VOSK | Apache 2.0 | alphacep/vosk-api |
| Wissens-APIs | Öffentlich | Wikipedia, OpenLibrary, Semantic Scholar, OSM |

---

## 🧰 Fehlerbehebung

| Problem / Meldung | Lösung |
| ----------------- | ------- |
| `CUDA nicht verfügbar – CPU` | CUDA 12.3 + Treiber installieren |
| `PyAudio Fehler` | Microsoft C++ Build Tools installieren |
| `Ignoring invalid distribution` | Virtuelle Umgebung neu anlegen |
| Modelle laden ewig | Erst-Download = mehrere GB, danach Cache |
| Web-UI leer / 401 | Token prüfen & `jarvis.log` kontrollieren |
| AMD GPU´s werden  zurzeit nich voll Suportet |
---

## 🧩 Entwicklung & Beiträge

1. Repository forken oder Branch erstellen  
2. Änderungen lokal testen (`python main.py`)  
3. Pull Request mit kurzer Erklärung einreichen  

Bitte **PEP-8**-konform entwickeln und keine sensiblen Daten hochladen.  

---

## ⚖️ Lizenz

Copyright © 2025 Lautloserspieler  

Lizenziert unter der **Apache License 2.0**  
mit folgender Zusatzklausel:  

> Kommerzielle Nutzung, Verkauf oder Weiterverbreitung dieses Projekts sind ohne vorherige schriftliche Genehmigung des Urhebers untersagt.  
> Drittanbieter-Komponenten unterliegen ihren jeweiligen Lizenzen (siehe `third_party_licenses`).

---

## 💬 Kontakt & Support

Projektleitung: **Lautloserspieler**  
GitHub: [github.com/Lautloserspieler](https://github.com/Lautloserspieler)  

Wenn dir J.A.R.V.I.S. gefällt, ⭐ **unterstütze das Projekt auf GitHub** oder teile dein Feedback!

---
