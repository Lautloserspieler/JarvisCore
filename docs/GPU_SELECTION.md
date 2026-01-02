# 🎮 GPU-Auswahl für JarvisCore + Pinokio

> **Automatische GPU-Erkennung während der Pinokio-Installation**

---

## 📊 Installations-Flow mit GPU-Auswahl

```
┌─────────────────────────────────────────────────────────────────┐
│           PINOKIO INSTALLATION MIT GPU-AUSWAHL              │
└─────────────────────────────────────────────────────────────────┘

      USER KLICKT "INSTALL"
              │
              ▼
┌──────────────────────────────────────────────────────────────────┐
│ STEP 1: Git Clone                                                │
├──────────────────────────────────────────────────────────────────┤
│ git clone https://github.com/Lautloserspieler/JarvisCore         │
│ Status: [████████████████████] Done ✓                           │
└──────────────────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────────────┐
│ STEP 2: GPU Selection Prompt 🎮                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │          🎮 GPU ACCELERATION AUSWAHL                   │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │                                                          │  │
│ │  Wähle deine GPU-Beschleunigung für llama.cpp:          │  │
│ │                                                          │  │
│ │  ◉ 🟢 NVIDIA GPU (CUDA)                                 │  │
│ │    Empfohlen für NVIDIA RTX/GTX Karten                    │  │
│ │    Performance: ⚡⚡⚡ 30-50 tokens/sec                     │  │
│ │    Requirements: CUDA Toolkit (automatisch)             │  │
│ │                                                          │  │
│ │  ○ 🟠 AMD GPU (ROCm)                                     │  │
│ │    Für AMD Radeon RX 5000+/7000+ (Experimentell)         │  │
│ │    Performance: ⚡⚡⚡ 25-40 tokens/sec                     │  │
│ │    ⚠️  Komplex, erfordert ROCm SDK                       │  │
│ │                                                          │  │
│ │  ○ 🔵 CPU Only                                          │  │
│ │    Keine GPU (Funktioniert auf allen Computern)         │  │
│ │    Performance: ⚡ 5-10 tokens/sec                        │  │
│ │    ✅ Empfohlen für schwache PCs                           │  │
│ │                                                          │  │
│ │           [ Bestätigen ]   [ Abbrechen ]                  │  │
│ │                                                          │  │
│ └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
              │
              ▼
       USER WÄHLT OPTION
              │
    ┌───────────┬─────────────┬────────────┐
    │            │              │            │
    ▼            ▼              ▼            ▼
 🟢 CUDA      🟠 ROCm      🔵 CPU
    │            │              │
    │            │              │
    ▼            ▼              ▼
```

---

## 🔀 Installations-Pfade nach GPU-Auswahl

### 🟢 Option 1: NVIDIA CUDA (Empfohlen)

```
┌──────────────────────────────────────────────────────────────────┐
│              🟢 NVIDIA CUDA INSTALLATION                     │
└──────────────────────────────────────────────────────────────────┘

Phase 3a: Standard Dependencies
├─ pip install -e ".[tts]"
└─ Status: [████████████████████] Done

Phase 3b: CUDA-Optimized llama.cpp
├─ pip uninstall llama-cpp-python -y
├─ set CMAKE_ARGS=-DLLAMA_CUDA=on
├─ pip install llama-cpp-python --force-reinstall
│  ├─ Detecting NVIDIA GPU...
│  ├─ CUDA Toolkit: Found ✓
│  ├─ Compiling with CUDA support...
│  └─ Build: [████████████████████] Done ✅
└─ Time: ~5-10 Minuten (Compilation)

Phase 4: Frontend
└─ npm install

Result:
✅ CUDA-beschleunigtes llama.cpp
✅ Performance: 30-50 tokens/sec
✅ GPU Memory: Nutzt VRAM effizient
```

---

### 🟠 Option 2: AMD ROCm (Experimentell)

```
┌──────────────────────────────────────────────────────────────────┐
│               🟠 AMD ROCm INSTALLATION                       │
└──────────────────────────────────────────────────────────────────┘

⚠️  WARNUNG: ROCm Setup ist komplex!

Phase 3a: Standard Dependencies
├─ pip install -e ".[tts]"
└─ Status: [████████████████████] Done

Phase 3b: ROCm-Optimized llama.cpp
├─ pip uninstall llama-cpp-python -y
├─ set CMAKE_ARGS=-DLLAMA_HIPBLAS=on
├─ pip install llama-cpp-python --force-reinstall
│  ├─ Detecting AMD GPU...
│  ├─ ROCm SDK: Checking...
│  │  ⚠️  Falls nicht gefunden:
│  │     1. Installiere ROCm SDK manuell
│  │     2. Starte System neu
│  │     3. Wiederhole Installation
│  ├─ Compiling with ROCm support...
│  └─ Build: [████████████████████] Done (⚠️  kann fehlschlagen)
└─ Time: ~10-15 Minuten (Compilation + Setup)

Phase 4: Frontend
└─ npm install

Result:
⚠️  ROCm-beschleunigtes llama.cpp (falls erfolgreich)
⚠️  Performance: 25-40 tokens/sec (bei Erfolg)
⚠️  Fallback: Bei Fehler → CPU-Version nutzen

💡 EMPFEHLUNG: Wähle "CPU Only" falls ROCm fehlschlägt!
```

---

### 🔵 Option 3: CPU Only (Zuverlässig)

```
┌──────────────────────────────────────────────────────────────────┐
│                 🔵 CPU-ONLY INSTALLATION                     │
└──────────────────────────────────────────────────────────────────┘

Phase 3a: Standard Dependencies
├─ pip install -e ".[tts]"
│  ├─ llama-cpp-python: Standard (CPU)
│  └─ Keine GPU-Compilation nötig
└─ Status: [████████████████████] Done ✅

Phase 3b: SKIP (Keine GPU-Optimierung)
└─ Verwendet pre-built CPU-Version

Phase 4: Frontend
└─ npm install

Result:
✅ CPU-basiertes llama.cpp
✅ Performance: 5-10 tokens/sec
✅ Funktioniert auf ALLEN Computern
✅ Schnellste Installation (keine Compilation)
✅ Keine CUDA/ROCm Abhängigkeiten

💡 Perfekt für:
   • Schwache PCs / Laptops
   • Testing & Development
   • Keine GPU verfügbar
   • Zuverlässige Installation
```

---

## 📊 Performance-Vergleich

```
┌─────────────────────────────────────────────────────────────────┐
│                  PERFORMANCE BENCHMARKS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                             │
│ Model: Llama 3.2 3B (Q4_K_M)                                │
│                                                             │
│ 🟢 NVIDIA RTX 4070:                                         │
│    ├─ Tokens/sec: 45-50 ⚡⚡⚡                               │
│    ├─ VRAM Usage: ~2.5 GB                                   │
│    ├─ Installation: ~8 Min (Compilation)                   │
│    └─ Rating: ⭐⭐⭐⭐⭐ (Best Performance)                  │
│                                                             │
│ 🟠 AMD RX 7900 XT (ROCm):                                   │
│    ├─ Tokens/sec: 35-40 ⚡⚡⚡ (falls ROCm funktioniert)     │
│    ├─ VRAM Usage: ~3.0 GB                                   │
│    ├─ Installation: ~15 Min (Complex Setup)                │
│    └─ Rating: ⭐⭐⭐ (Experimentell, kann fehlschlagen)        │
│                                                             │
│ 🔵 CPU: Intel i7-13700K / AMD Ryzen 7 7700X:                │
│    ├─ Tokens/sec: 8-12 ⚡ (ausreichend für Chat)             │
│    ├─ RAM Usage: ~4 GB                                      │
│    ├─ Installation: ~5 Min (Schnell)                       │
│    └─ Rating: ⭐⭐⭐⭐ (Zuverlässig, funktioniert immer)      │
│                                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## ❓ Häufige Fragen

### Q: Kann ich später zwischen GPU-Modi wechseln?
**A:** Ja! Einfach:
1. "Stop" klicken (falls laufend)
2. "Uninstall" klicken
3. "Install" klicken und andere Option wählen

### Q: Was wenn CUDA-Installation fehlschlägt?
**A:** Pinokio fällt automatisch zurück auf CPU-Version. Die App funktioniert weiterhin!

### Q: Brauche ich ROCm SDK vorab?
**A:** Nein, aber ROCm ist komplex. Falls du AMD hast, empfehle ich **CPU Only** für zuverlässige Installation.

### Q: Wie sehe ich meine GPU-Auswahl nach Installation?
**A:** Im Log bei "Install complete!" siehst du:
```
GPU Type: NVIDIA CUDA 🟢
```

### Q: Performance mit kleinen Modellen auf CPU?
**A:** Llama 3.2 3B und Phi-3 Mini laufen flüssig mit 8-12 tok/s auf modernen CPUs!

---

## 👀 Visuelle Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│              WELCHE GPU-OPTION WÄHLEN?                       │
├─────────────────────────────────────────────────────────────────┤
│                                                             │
│ Du hast NVIDIA RTX/GTX Karte?                               │
│ └─► Wähle: 🟢 NVIDIA GPU (CUDA)                          │
│                                                             │
│ Du hast AMD RX 5000+/7000+ Karte UND bist erfahren?        │
│ └─► Wähle: 🟠 AMD GPU (ROCm) - aber bereit für Probleme   │
│                                                             │
│ Du hast AMD Karte ABER keine Lust auf Komplikationen?      │
│ └─► Wähle: 🔵 CPU Only - funktioniert garantiert!         │
│                                                             │
│ Du hast schwachen PC / Laptop?                              │
│ └─► Wähle: 🔵 CPU Only - 8-12 tok/s ausreichend für Chat   │
│                                                             │
│ Du willst schnellste Installation ohne Komplikationen?      │
│ └─► Wähle: 🔵 CPU Only - ready in 5 Minuten             │
│                                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Links

- 📚 [Haupt-README](../README.md)
- 🎯 [Pinokio Documentation](../PINOKIO.md)
- ❓ [FAQ](./FAQ.md)
- 🐛 [Troubleshooting](./TROUBLESHOOTING.md)

---

<div align="center">

**Optimale Performance für jede Hardware**

*"The right GPU for the right job"* - JarvisCore Team

</div>