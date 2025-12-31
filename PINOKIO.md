# Pinokio Integration für JarvisCore

Dieses Dokument erklärt die Pinokio-Integration und wie JarvisCore als Pinokio-App läuft.

## Was ist Pinokio?

[Pinokio](https://pinokio.computer/) ist ein **AI App Browser** – eine Plattform zum Installieren, Verwalten und Ausführen von KI-Anwendungen mit einer einfachen grafischen Oberfläche.

## Installation über Pinokio

### Schnellstart

1. **Pinokio installieren**: https://pinokio.computer/
2. **JarvisCore hinzufügen**:
   - Öffne Pinokio
   - Kopiere diese URL in die Suchleiste oder "+ Add"-Funktion:
     ```
     https://github.com/Lautloserspieler/JarvisCore
     ```
3. **Install klicken** und GPU-Typ wählen
4. **Start klicken** – fertig!

### GPU-Auswahl

Bei der Installation wirst du nach deinem GPU-Backend gefragt:

| Option | Empfohlen für | Geschwindigkeit |
|--------|---------------|------------------|
| 🖥️ **CPU** | Alle Systeme (Fallback) | Langsam |
| 🚀 **NVIDIA CUDA** | NVIDIA RTX/GTX Karten | Schnell |
| 🍎 **Apple Metal** | Mac with Apple Silicon | Schnell |

> **Hinweis**: Metal ist experimentell auf M1/M2/M3. CPU ist der sicherste Standard.

## Architektur

### Pinokio-Dateien

```
JarvisCore/
├── pinokio.js          # Konfiguration & Menü-Logik
├── install.json        # Installationsskript (Dependencies, GPU-Setup)
├── start.json          # Start-Skript (Daemon, Port-Binding, Ready-Event)
├── stop.json           # Stop-Skript (Graceful Shutdown)
├── update.json         # Update-Logik
├── uninstall.json      # Deinstallation
└── PINOKIO.md          # Diese Datei
```

### pinokio.js

Definiert die App-Metadaten und das Menü basierend auf Zustand:

```javascript
version: "2.0"         // Pinokio-API Version
title: "JarvisCore"    // App-Name
description: "..."    // Beschreibung
icon: "icon.png"       // App-Icon
menu: async (kernel, info) => {  // Dynamisches Menü
  if (!info.installed) return [{ Install }];     // Nicht installiert
  if (info.running) return [{ Web UI, Stop }];   // Läuft
  return [{ Start, Update, Uninstall }];         // Bereit
}
```

**Wichtig**: `locals.url` wird auf `http://localhost:5050` gesetzt (nicht mehr 5000).

### install.json

Installiert alle Dependencies und richtet GPU ein:

1. **GPU-Auswahl** (Input-Dialog)
   - 🖥️ CPU only
   - 🚀 NVIDIA CUDA 12.1
   - 🍎 Apple Metal (M1/M2/M3)

2. **Python Setup**
   - `python -m venv venv`
   - `pip install -r requirements.txt`

3. **Frontend Setup**
   - `npm install`
   - `npm run build`

4. **GPU-spezifische Compiler-Flags** (conditional)
   - CUDA: `-DLLAMA_CUDA=1 -DCUDA_ARCHITECTURES=native`
   - Metal: `-DLLAMA_METAL=1`
   - CPU: Standard llama-cpp-python

### start.json

Startet den Backend-Daemon und öffnet die Web-UI:

```json
{
  "daemon": true,              // Läuft im Hintergrund
  "message": "uvicorn ...",    // Kommando (Port 5050)
  "on": [{
    "event": "http",
    "port": 5050,              // ← WICHTIG: Port 5050!
    "handler": async () => true // HTTP-Ready Event
  }],
  "locals": {
    "url": "http://localhost:5050"  // Für Menü-Anzeige
  }
}
```

**Port konsolidiert**: Backend + Pinokio nutzen beide **Port 5050**.

### stop.json

Stoppt den Daemon sauber mit `script.stop`:

```json
{
  "method": "script.stop",
  "params": { "uri": "start.json" }
}
```

Dies sendet SIGTERM zum Prozess. Wichtig: `backend/main.py` reagiert auf Signals.

## Ports

| Service | Port | Host |
|---------|------|------|
| Backend (Pinokio) | 5050 | 127.0.0.1 |
| Web UI | 5050 | localhost |
| API Docs | 5050/docs | localhost |

**Nicht mehr 5000!** Alle Referenzen aktualisiert.

## Troubleshooting

### GPU-Auswahl erscheint nicht

**Lösung**:
1. Pinokio neustarten
2. Im Terminal nachprüfen:
   ```bash
   cd <pinokio-path>/api/JarvisCore
   python -m venv venv
   source venv/bin/activate  # oder: venv\Scripts\activate (Windows)
   pip install -r requirements.txt
   ```

### Install bleibt hängen

**Mögliche Ursachen**:
- CMake oder Build-Tools fehlen
- CUDA/Metal nicht korrekt installiert
- Disk voll

**Lösung**: CPU-Option wählen oder manuell installieren.

### Web UI öffnet sich nicht

**Prüfen**:
1. Läuft der Server? (Check in Pinokio Terminal)
2. Ist Port 5050 frei? (`lsof -i :5050` auf Linux/Mac)
3. Frontend installiert? (`ls frontend/dist`)

**Lösung**: Manuell starten:
```bash
cd <pinokio-path>/api/JarvisCore
source venv/bin/activate
uvicorn backend.main:app --host 127.0.0.1 --port 5050 --reload
```

### Stop funktioniert nicht / Port bleibt besetzt

**Problem**: Prozess reagiert nicht auf SIGTERM.

**Lösung**: `backend/main.py` muss Signal-Handler haben (ist bereits eingebaut).

## Anforderungen

### Für Pinokio

- Pinokio >= 2.0 (https://pinokio.computer/)
- Python 3.10+
- Node.js 18+
- Git

### Für GPU-Support

**NVIDIA CUDA**:
- NVIDIA GPU (RTX/GTX Serie)
- CUDA Toolkit 12.1+

**Apple Metal** (macOS):
- Mac with Apple Silicon (M1, M2, M3, ...)
- macOS 12.0+

## Erweiterte Konfiguration

### Umgebungsvariablen ändern

In `install.json` unter `env`:

```json
"env": {
  "CMAKE_ARGS": "-DLLAMA_CUDA=1",
  "FORCE_CMAKE": "1",
  "CUDA_VISIBLE_DEVICES": "0"
}
```

### Ports ändern

In `backend/main.py`:

```python
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5050)  # Port anpassen
```

Dann in `start.json` + `pinokio.js` anpassen:

```json
"port": 5050,  // start.json
```

```javascript
const url = locals.url || "http://localhost:5050";  // pinokio.js
```

## File-Status (aktuell)

✅ **Repariert**:
- pinokio.js → Port 5050 als Fallback
- start.json → daemon=true + on-Event + locals.url
- install.json → GPU-Auswahl mit CMake-Flags
- PINOKIO.md → Port 5050, GPU-Anleitung
- backend/main.py → CORS Port 5050, Signal-Handler

## Contributing

Fehler in Pinokio-Integration gefunden? Issues willkommen:
- https://github.com/Lautloserspieler/JarvisCore/issues

## Lizenz

Siehe [LICENSE](LICENSE).
