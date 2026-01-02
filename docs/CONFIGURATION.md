# ⚙️ Konfiguration (.env)

Diese Übersicht erklärt die wichtigsten Umgebungsvariablen und verweist auf weiterführende Dokumentation.
Die vollständige Liste aller Optionen findest du in der Vorlage: [`.env.example`](../.env.example).

## 🤖 LLM (Large Language Model)

* **`LLM_DEFAULT_MODEL`** – Standardmodell (z. B. `llama32-3b`).
* **`LLM_CONTEXT_SIZE`** – Kontextfenster in Tokens.
* **`LLM_GPU_LAYERS`** – GPU-Layer (`-1` auto, `0` CPU-only).
* **`LLM_DEVICE`** – `cuda`, `cpu` oder `mps`.
* **`LLM_TEMPERATURE`** – Kreativität/Randomness (0.0–2.0).
* **`LLM_MAX_TOKENS`** – Maximal erzeugte Tokens.
* **`LLM_MAX_CACHED_MODELS`** – Anzahl gecachter Modelle.
* **`LLM_CACHE_TTL`** – Cache-TTL in Sekunden.

Weiterführend:
* [LLM Download-System](LLM_DOWNLOAD_SYSTEM.md)

## 🔊 Text-to-Speech (TTS)

* **`TTS_ENGINE`** – TTS-Engine (`xtts`, `pyttsx3`).
* **`TTS_DEVICE`** – `cuda` oder `cpu`.
* **`TTS_LANGUAGE`** – Standard-Sprache (`de`, `en`).
* **`TTS_ENABLED`** – TTS global aktivieren/deaktivieren.
* **`TTS_VOLUME`** – Lautstärke (0.0–1.0).
* **`JARVIS_XTTS_MODEL`** – Optionaler Modell-Override für XTTS.
* **`JARVIS_XTTS_DEFAULT_SPEAKER`** – Optionaler Standardsprecher.

Weiterführend:
* [TTS Integration Guide](./TTS_INTEGRATION_GUIDE.md)
* [Voice Setup Guide](./VOICE_SETUP_GUIDE.md)

## 🧩 Plugins & API-Keys

* **`OPENWEATHER_API_KEY`** – OpenWeatherMap (Wetter).
* **`NEWS_API_KEY`** – NewsAPI (Nachrichten).
* **`GOOGLE_API_KEY`** – Google APIs (je nach Plugin).
* **`DEEPL_API_KEY`** – DeepL API (Übersetzungen).
* **`WEATHER_DEFAULT_CITY`** / **`WEATHER_DEFAULT_COUNTRY`** – Default-Standort.

## 🎛️ Feature Flags

* **`ENABLE_VOICE_CONTROL`** – Sprachsteuerung.
* **`ENABLE_DESKTOP_NOTIFICATIONS`** – Desktop-Notifications.
* **`ENABLE_SYSTEM_TRAY`** – Systemtray-Icon.
* **`ENABLE_TELEMETRY`** – Telemetrie.
* **`ENABLE_PLUGIN_HOTRELOAD`** – Plugin-Hot-Reload.
* **`DEBUG`** – Debug-Modus.

## ✅ Validierung beim Start

Beim Start prüft der Launcher die wichtigsten Werte (z. B. erlaubte Werte für `LLM_DEVICE` oder `TTS_ENGINE`).
Ungültige Werte werden mit klaren Fehlermeldungen ausgegeben, damit du Konfigurationen schnell korrigieren kannst.
