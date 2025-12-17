#!/usr/bin/env python3
"""Automatische llama-cpp-python Installation mit GPU-Erkennung und CUDA Toolkit Support"""

import subprocess
import sys
import platform
import os
import shutil
import webbrowser
from pathlib import Path

def run_command(cmd, shell=False):
    """Führt Befehl aus und gibt Ausgabe zurück"""
    try:
        result = subprocess.run(
            cmd if shell else cmd.split(),
            capture_output=True,
            text=True,
            shell=shell
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return "", 1

def check_cuda_toolkit():
    """Prüft ob CUDA Toolkit installiert ist"""
    # Check common CUDA paths
    cuda_paths = [
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA",
        "C:/Program Files/NVIDIA Corporation/CUDA",
        "/usr/local/cuda",
        "/opt/cuda"
    ]
    
    for cuda_path in cuda_paths:
        if Path(cuda_path).exists():
            # Find version
            versions = [d for d in Path(cuda_path).iterdir() if d.is_dir() and d.name.startswith(('v', '11', '12'))]
            if versions:
                latest = sorted(versions)[-1]
                return True, str(latest)
    
    # Check environment variable
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path and Path(cuda_path).exists():
        return True, cuda_path
    
    # Check nvcc
    nvcc_path = shutil.which("nvcc")
    if nvcc_path:
        return True, nvcc_path
    
    return False, None

def check_build_tools():
    """Prüft ob C++ Build-Tools verfügbar sind"""
    system = platform.system()
    
    if system == "Windows":
        checks = [
            ("cl.exe", "MSVC Compiler"),
            ("cmake", "CMake"),
        ]
        
        missing = []
        for cmd, name in checks:
            if shutil.which(cmd) is None:
                missing.append(name)
        
        return len(missing) == 0, missing
    
    else:  # Linux/Mac
        checks = [
            ("gcc", "GCC"),
            ("g++", "G++"),
            ("cmake", "CMake"),
        ]
        
        missing = []
        for cmd, name in checks:
            if shutil.which(cmd) is None:
                missing.append(name)
        
        return len(missing) == 0, missing

def detect_gpu():
    """Erkennt GPU-Typ (NVIDIA, AMD, oder keine)"""
    system = platform.system()
    
    print("[INFO] Erkenne GPU...")
    
    # Prüfe NVIDIA zuerst
    if system == "Windows":
        output, code = run_command("nvidia-smi", shell=True)
        if code == 0 and "NVIDIA" in output:
            print("[INFO] ✅ NVIDIA GPU erkannt!")
            return "nvidia"
        
        # Prüfe AMD auf Windows
        output, code = run_command("wmic path win32_VideoController get name", shell=True)
        if code == 0 and ("AMD" in output or "Radeon" in output):
            print("[INFO] ✅ AMD GPU erkannt!")
            return "amd"
    
    else:  # Linux/Mac
        output, code = run_command("nvidia-smi")
        if code == 0 and "NVIDIA" in output:
            print("[INFO] ✅ NVIDIA GPU erkannt!")
            return "nvidia"
        
        # Prüfe AMD auf Linux
        output, code = run_command("lspci")
        if "AMD" in output or "Radeon" in output:
            print("[INFO] ✅ AMD GPU erkannt!")
            return "amd"
    
    print("[INFO] ℹ️  Keine GPU erkannt, nutze CPU")
    return "cpu"

def uninstall_llama():
    """Deinstalliert vorhandenes llama-cpp-python"""
    print("\n[INFO] Entferne vorhandenes llama-cpp-python...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "llama-cpp-python", "-y"], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def install_llama_cpu():
    """Installiert llama-cpp-python für CPU"""
    print("\n" + "="*60)
    print("💻 Installiere llama-cpp-python für CPU")
    print("="*60 + "\n")
    
    result = subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir"
    ])
    
    return result.returncode == 0

def install_llama_nvidia():
    """Installiert llama-cpp-python mit CUDA-Support"""
    print("\n" + "="*60)
    print("🚀 Installiere llama-cpp-python mit NVIDIA CUDA Support")
    print("Dies kann 5-10 Minuten dauern...")
    print("="*60 + "\n")
    
    env = os.environ.copy()
    env["CMAKE_ARGS"] = "-DGGML_CUDA=on"
    
    result = subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir",
        "--no-binary", "llama-cpp-python"
    ], env=env)
    
    return result.returncode == 0

def verify_installation():
    """\u00dcberprüft ob llama-cpp-python korrekt installiert wurde"""
    print("\n" + "="*60)
    print("Überprüfe Installation...")
    print("="*60 + "\n")
    
    try:
        import llama_cpp
        print(f"[ERFOLG] ✅ llama-cpp-python Version: {llama_cpp.__version__}")
        
        # Prüfe Backend
        try:
            from llama_cpp import Llama
            print("[ERFOLG] ✅ Llama-Klasse erfolgreich importiert")
        except Exception as e:
            print(f"[FEHLER] ❌ Llama-Import fehlgeschlagen: {e}")
            return False
        
        return True
    except ImportError as e:
        print(f"[FEHLER] ❌ llama-cpp-python nicht gefunden: {e}")
        return False

def show_cuda_installation_guide():
    """Zeigt Anleitung zur CUDA Toolkit Installation"""
    print("\n" + "⚠️ "*30)
    print("\n[WARNUNG] CUDA Toolkit nicht gefunden!\n")
    print("Für NVIDIA GPU-Beschleunigung wird CUDA Toolkit benötigt.\n")
    print("🔧 CUDA Toolkit Installation:\n")
    print("   1️⃣  Download CUDA Toolkit 12.x:")
    print("      https://developer.nvidia.com/cuda-downloads\n")
    print("   2️⃣  Wähle dein System:")
    print("      - Windows -> x86_64 -> 11 -> exe (local)\n")
    print("   3️⃣  Installiere mit Standardeinstellungen")
    print("      - Dauert ca. 5-10 Minuten")
    print("      - Benötigt ca. 3 GB Speicher\n")
    print("   4️⃣  Starte PC neu\n")
    print("   5️⃣  Führe erneut aus: python backend/setup_jarvis.py\n")
    print("ℹ️  Alternative: CPU-Version installieren (Option 2)\n")
    print("⚠️ "*30 + "\n")

def ask_cuda_choice():
    """Fragt Benutzer nach CUDA Installation"""
    print("Wähle Option:\n")
    print("   1️⃣  CUDA Toolkit jetzt installieren (öffnet Browser)")
    print("   2️⃣  CPU-Version installieren (ohne GPU)\n")
    
    while True:
        choice = input("Wähle Option [1/2]: ").strip()
        if choice in ["1", "2"]:
            return choice
        print("[FEHLER] Ungültige Eingabe! Bitte 1 oder 2 eingeben.")

def main():
    print("""
    ╭──────────────────────────────────────────────────────────────╮
    │       JARVIS Core - llama.cpp Setup Script v3.0          │
    │          GPU-Erkennung + CUDA Toolkit Support            │
    ╰──────────────────────────────────────────────────────────────╯
    """)
    
    print(f"[INFO] System: {platform.system()} {platform.machine()}")
    print(f"[INFO] Python: {sys.version.split()[0]}")
    print()
    
    # Prüfe Build-Tools
    has_build_tools, missing_tools = check_build_tools()
    
    if not has_build_tools:
        print(f"[WARNUNG] ⚠️  Fehlende Build-Tools: {', '.join(missing_tools)}")
        print("[INFO] Führe zuerst aus: python backend/setup_buildtools_path.py")
        print("[INFO] Fahre mit CPU-Installation fort...\n")
    else:
        print("[INFO] ✅ C++ Build-Tools erkannt")
    
    # Erkenne GPU
    gpu_type = detect_gpu()
    
    # Prüfe CUDA Toolkit wenn NVIDIA GPU
    has_cuda = False
    cuda_path = None
    
    if gpu_type == "nvidia":
        has_cuda, cuda_path = check_cuda_toolkit()
        if has_cuda:
            print(f"[INFO] ✅ CUDA Toolkit gefunden: {cuda_path}")
        else:
            print("[INFO] ❌ CUDA Toolkit nicht gefunden")
    
    # Entscheidungslogik
    install_mode = "cpu"
    
    if gpu_type == "nvidia" and has_build_tools:
        if has_cuda:
            # Perfekt: GPU + Build Tools + CUDA
            install_mode = "nvidia"
        else:
            # GPU + Build Tools, aber kein CUDA
            show_cuda_installation_guide()
            choice = ask_cuda_choice()
            
            if choice == "1":
                print("\n[INFO] 🌐 Öffne CUDA Toolkit Download...")
                webbrowser.open("https://developer.nvidia.com/cuda-downloads")
                print("\n[INFO] Nach der Installation:\n")
                print("   1. Starte PC neu")
                print("   2. Führe erneut aus: python backend/setup_jarvis.py\n")
                print("[INFO] Installation beendet. Bis gleich! 👋\n")
                return 0
            else:
                install_mode = "cpu"
    elif gpu_type == "nvidia" and not has_build_tools:
        print("\n[INFO] 💡 Tipp: Für GPU-Unterstützung:\n")
        print("   1. Führe aus: python backend/setup_jarvis.py")
        print("   2. Build Tools werden automatisch eingerichtet\n")
        install_mode = "cpu"
    else:
        install_mode = "cpu"
    
    # Deinstalliere vorhandenes
    uninstall_llama()
    
    # Installation
    success = False
    
    if install_mode == "nvidia":
        print("\n[INFO] 🚀 Installiere mit NVIDIA CUDA Support...")
        success = install_llama_nvidia()
    else:
        print("\n[INFO] 💻 Installiere CPU-Version...")
        success = install_llama_cpu()
    
    # Überprüfe Installation
    if success and verify_installation():
        print("\n" + "✅"*30)
        print("\n[ERFOLG] 🎉 llama-cpp-python erfolgreich installiert!")
        print(f"[INFO] Modus: {install_mode.upper()}")
        print(f"[INFO] GPU-Typ: {gpu_type.upper()}")
        
        if install_mode == "cpu" and gpu_type == "nvidia":
            print("\n[TIPP] 💡 Um GPU-Beschleunigung zu aktivieren:")
            print("      1. Installiere CUDA Toolkit")
            print("      2. Führe erneut aus: python backend/setup_jarvis.py")
        
        print("\n[INFO] ▶️  Du kannst jetzt starten: python backend/main.py")
        print("✅"*30 + "\n")
        return 0
    else:
        print("\n" + "❌"*30)
        print("\n[FEHLER] 💥 Installation fehlgeschlagen!")
        print("\n[INFO] Problemlösung:")
        print("      1. Prüfe Fehlermeldungen oben")
        print("      2. Aktualisiere pip: python -m pip install --upgrade pip")
        print("      3. Versuche manuelle Installation:")
        print("         pip install llama-cpp-python")
        print("\n[INFO] 📚 Vollständige Dokumentation: https://github.com/Lautloserspieler/JarvisCore")
        print("❌"*30 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
