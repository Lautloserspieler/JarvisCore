# 🚀 J.A.R.V.I.S. Core - Quickstart

**Schnellstart für lokale Installation (empfohlen)**  
Ziel: Web-UI unter **http://localhost:5050**.

---

## ✅ Voraussetzungen

- **Python 3.11+**
- **Node.js 18+**
- **Git**

---

## ⚡ Schnellstart (Web-UI)

```bash
# 1) Repository klonen
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore

# 2) Virtuelle Umgebung erstellen & aktivieren
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 3) Backend-Abhängigkeiten installieren
pip install -e ".[tts]"

# 4) Frontend installieren
cd frontend
npm install
cd ..

# 5) Start
jarviscore web
```

Danach öffnet sich die Web-UI automatisch: **http://localhost:5050**

---

## 🎮 GPU-Setup (optional)

Für CUDA/ROCm/Metal siehe:  
➡️ **[docs/GPU_SELECTION.md](./docs/GPU_SELECTION.md)**

Für NVIDIA CUDA kannst du zusätzlich:

```bash
pip install -e ".[tts,cuda]"
```

---

## 🧪 Tests (optional)

```bash
pytest
```

---

## 🔧 Troubleshooting

### Port belegt
```bash
# Windows
netstat -ano | findstr :5050

# Linux/Mac
lsof -i :5050
```

### Fehlende Abhängigkeiten
```bash
pip install -e ".[tts]"
```

---

## 📚 Weitere Dokumentation

- **[README.md](README.md)** - Vollständige Projekt-Doku
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Troubleshooting
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Architektur

---

<div align="center">

**Made with ❤️ by [@Lautloserspieler](https://github.com/Lautloserspieler)**

</div>
