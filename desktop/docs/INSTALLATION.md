# Desktop UI - Installations-Anleitung

## Voraussetzungen

### 1. Go (1.21+)

**Windows:**

```powershell
# Download von https://go.dev/dl/
# Installer ausführen

# Check
go version
```

**Linux:**

```bash
# Ubuntu/Debian
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# Check
go version
```

**macOS:**

```bash
brew install go
go version
```

---

### 2. Node.js (18+)

**Windows:**

```powershell
# Download von https://nodejs.org/
# LTS Version installieren

# Check
node --version
npm --version
```

**Linux:**

```bash
# Mit NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Check
node --version
```

**macOS:**

```bash
brew install node
node --version
```

---

### 3. Wails CLI

```bash
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# Check
wails version

# System-Check
wails doctor
```

**Wails Doctor Output sollte zeigen:**

```
✅ Go version
✅ Node version
✅ npm version
✅ Platform
✅ Dependencies
```

---

### 4. PortAudio (für Voice Recording)

**Windows:**

```powershell
# Option 1: vcpkg (empfohlen)
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg install portaudio:x64-windows

# Option 2: MSYS2
pacman -S mingw-w64-x86_64-portaudio
```

**Linux:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install portaudio19-dev

# Fedora/RHEL
sudo dnf install portaudio-devel

# Arch
sudo pacman -S portaudio
```

**macOS:**

```bash
brew install portaudio
```

---

## Installation

### 1. Repository klonen

```bash
cd ~
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore/desktop
```

### 2. Dependencies installieren

**Mit Makefile (empfohlen):**

```bash
make install
```

**Oder manuell:**

```bash
# Frontend Dependencies
cd frontend
npm install
cd ..

# Go Dependencies
cd backend
go mod download
cd ..
```

### 3. Test

```bash
# Wails Doctor
wails doctor

# Build Test
wails build --clean
```

---

## Development Setup

### 1. JarvisCore Backend starten

```bash
# Terminal 1
cd JarvisCore
python main.py

# Warten bis:
# ✅ J.A.R.V.I.S. Core gestartet
# 🌐 Web-Server läuft auf http://127.0.0.1:5050
```

### 2. Desktop UI starten

```bash
# Terminal 2
cd JarvisCore/desktop
make dev

# ODER:
wails dev
```

**Erwartetes Verhalten:**

1. Vite Dev-Server startet (Port 34115)
2. Go Backend kompiliert
3. Desktop-App öffnet sich automatisch
4. Hot Reload ist aktiv

---

## Production Build

### Build erstellen

```bash
cd desktop

# Mit Makefile
make build

# ODER direkt
wails build --clean
```

**Output:**

```
Windows: ./build/bin/jarvis-desktop.exe (~20-30MB)
Linux:   ./build/bin/jarvis-desktop (~25-35MB)
macOS:   ./build/bin/jarvis-desktop.app (~30-40MB)
```

### Binary testen

```bash
# 1. JarvisCore starten
cd JarvisCore
python main.py

# 2. Binary ausführen (anderes Terminal)
cd desktop/build/bin

# Windows
.\jarvis-desktop.exe

# Linux/macOS
./jarvis-desktop
```

---

## Platform-spezifische Builds

### Windows

```bash
cd desktop
make build-windows

# Output: build/bin/jarvis-desktop.exe
```

### Linux

```bash
cd desktop
make build-linux

# Output: build/bin/jarvis-desktop
```

### macOS

```bash
cd desktop
make build-macos

# Output: build/bin/jarvis-desktop.app
```

---

## Troubleshooting

Siehe [QUICKSTART.md - Troubleshooting](../QUICKSTART.md#troubleshooting) für detaillierte Lösungen.

### Schnell-Checks

```bash
# Go installiert?
go version

# Node installiert?
node --version

# Wails installiert?
wails version

# PortAudio installiert?
# Linux:
ldconfig -p | grep portaudio

# Dependencies OK?
cd desktop/backend
go mod download

cd ../frontend
npm install
```

---

## Nächste Schritte

1. ✅ Installation abgeschlossen
2. 📚 [QUICKSTART.md](../QUICKSTART.md) lesen
3. 🚀 Development starten
4. 🎉 Erste Feature implementieren!
