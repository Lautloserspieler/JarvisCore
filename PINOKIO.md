# Pinokio Integration für JarvisCore

Dieses Dokument erklärt die Pinokio-Integration und wie JarvisCore als Pinokio-App läuft.

## Was ist Pinokio?

[Pinokio](https://pinokio.computer/) ist ein **AI App Browser** – eine Plattform zum Installieren, Verwalten und Ausführen von KI-Anwendungen mit einer einfachen grafischen Oberfläche.

## Installation über Pinokio

### Schnellstart

1. **Pinokio installieren**: https://pinokio.computer/
2. **JarvisCore hinzufügen**:
   - Öffne Pinokio
   - Kopiere diese URL in die Suchleiste oder "+ Add"-Funktion:
     ```
     https://github.com/Lautloserspieler/JarvisCore
     ```
3. **Install klicken** und GPU-Typ wählen
4. **Start klicken** – fertig!

### GPU-Auswahl

Bei der Installation wirst du nach deinem GPU-Backend gefragt:

| Option | Empfohlen für | Geschwindigkeit |
|--------|---------------|-----------------|
| 🔵 **CPU** | Alle Systeme (Fallback) | Langsam |
| 🟢 **NVIDIA CUDA** | NVIDIA RTX/GTX Karten | Schnell |
| 🟠 **AMD ROCm** | AMD Radeon RX 5000+/7000+ (Linux) | Schnell |
| 🍎 **Apple Metal** | Mac with Apple Silicon | Schnell |

> **Hinweis**: ROCm und Metal sind experimentell. CPU ist der sicherste Standard.

## Architektur

### Pinokio-Dateien

```
JarvisCore/
├── pinokio.js          # Konfiguration & Menü-Logik
├── install.json        # Installationsskript (Dependencies, GPU-Setup)
├── start.json          # Start-Skript (Daemon, Port-Binding)
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
  if (!info.installed) return [{ Install }];   // Nicht installiert
  if (info.running) return [{ Web UI, Stop }]; // Läuft
  return [{ Start, Update, Uninstall }];       // Bereit
}
```

### install.json

Installiert alle Dependencies und richtet GPU ein:

1. **GPU-Auswahl** (Input)
2. **Python Setup** (pip install -e ".[tts]")
3. **Frontend Setup** (npm install)
4. **GPU-spezifische Installation** (conditional based on GPU-Typ)
   - CUDA: `-DGGML_CUDA=on`
   - ROCm: `-DGGML_HIPBLAS=on`
   - Metal: `-DGGML_METAL=on`
   - CPU: Standard llama-cpp-python

**Wichtig**: Verwendet moderne **GGML-Flags** (nicht legacy LLAMA-Flags).

### start.json

Startet den Backend-Daemon und öffnet die Web-UI:

```json
{
  "daemon": true,              // Läuft im Hintergrund
  "message": "jarviscore web", // Kommando
  "on": [{                      // Event-Handler
    "event": "http://localhost:5000",
    "done": true               // Fertig, wenn URL antwortet
  }]
}
```

### stop.json

Stoppt den Daemon sauber mit `script.stop`:

```json
{
  "method": "script.stop",
  "params": { "uri": "start.json" }
}
```

Dies sendet SIGTERM zum Prozess. Wichtig: `main.py` muss Signal-Handler implementieren.

## Troubleshooting

### GPU-Auswahl erscheint nicht

**Lösung**:
1. Pinokio neustarten
2. Im Terminal nachprüfen:
   ```bash
   cd <pinokio-path>/api/JarvisCore
   python -m venv venv
   source venv/bin/activate  # oder: venv\Scripts\activate (Windows)
   pip install -e ".[tts]"
   ```

### Install bleibt hängen

**Mögliche Ursachen**:
- CMake oder Build-Tools fehlen
- CUDA/ROCm nicht korrekt installiert
- Disk voll

**Lösung**: CPU-Option wählen oder manuell installieren.

### Web UI öffnet sich nicht

**Prüfen**:
1. Läuft der Server? (Check in Pinokio Terminal)
2. Ist Port 5000 frei? (`lsof -i :5000` auf Linux/Mac)
3. Frontend installiert? (`ls frontend/node_modules`)

**Lösung**: Manuell starten:
```bash
cd <pinokio-path>/api/JarvisCore
source venv/bin/activate
jarviscore web
```

### Stop funktioniert nicht / Port bleibt besetzt

**Problem**: Prozess reagiert nicht auf SIGTERM.

**Lösung**: `main.py` muss Signal-Handler haben:

```python
import signal
import sys

def signal_handler(sig, frame):
    print("Shutting down gracefully...")
    # Cleanup code hier
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

## Anforderungen

### Für Pinokio

- Pinokio >= 1.0 (https://pinokio.computer/)
- Python 3.10+
- Node.js 18+
- Git

### Für GPU-Support

**NVIDIA CUDA**:
- NVIDIA GPU (RTX/GTX Serie)
- CUDA Toolkit 11.8+
- cuDNN 8.0+

**AMD ROCm** (Linux):
- AMD GPU (RX 5000+/7000+)
- ROCm 5.4+

**Apple Metal** (macOS):
- Mac with Apple Silicon (M1, M2, M3, ...)
- macOS 12.0+

## Erweiterte Konfiguration

### Umgebungsvariablen (in Pinokio)

Setzen in `install.json` unter `env`:

```json
"env": {
  "CMAKE_ARGS": "-DGGML_CUDA=on",
  "FORCE_CMAKE": "1",
  "CUDA_VISIBLE_DEVICES": "0"
}
```

### Ports ändern

In `main.py`:

```python
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)  # Port hier anpassen
```

Dann in `start.json` anpassen:

```json
"event": "/http:\\/\\/localhost:YOUR_PORT/"
```

## Contributing

Fehler in Pinokio-Integration gefunden? Issues willkommen:
- https://github.com/Lautloserspieler/JarvisCore/issues

## Lizenz

Siehe [LICENSE](LICENSE).
