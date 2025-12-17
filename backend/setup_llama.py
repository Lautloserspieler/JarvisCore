#!/usr/bin/env python3
"""Automatische llama-cpp-python Installation mit GPU-Erkennung und Build-Tools-Prüfung"""

import subprocess
import sys
import platform
import os
import shutil

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

def check_build_tools():
    """Prüft ob C++ Build-Tools verfügbar sind"""
    system = platform.system()
    
    if system == "Windows":
        # Prüfe auf Visual Studio oder Build Tools
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

def check_rocm_installed():
    """Prüft ob ROCm installiert ist"""
    output, code = run_command("rocm-smi", shell=True)
    return code == 0

def uninstall_llama():
    """Deinstalliert vorhandenes llama-cpp-python"""
    print("\n[INFO] Entferne vorhandenes llama-cpp-python...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "llama-cpp-python", "-y"], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def install_llama_prebuilt():
    """Installiert vorkompiliertes llama-cpp-python (nur CPU, schnell)"""
    print("\n" + "="*60)
    print("Installiere vorkompiliertes llama-cpp-python (nur CPU)")
    print("="*60 + "\n")
    
    result = subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--only-binary", ":all:",
        "--force-reinstall",
        "--no-cache-dir"
    ])
    
    return result.returncode == 0

def install_llama_cpu():
    """Installiert llama-cpp-python für CPU (aus Quellcode)"""
    print("\n" + "="*60)
    print("Installiere llama-cpp-python für CPU (aus Quellcode)")
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
    print("Installiere llama-cpp-python mit NVIDIA CUDA Support")
    print("Dies kann 5-10 Minuten dauern...")
    print("="*60 + "\n")
    
    env = os.environ.copy()
    env["CMAKE_ARGS"] = "-DLLAMA_CUDA=on"
    
    result = subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir",
        "--no-binary", "llama-cpp-python"
    ], env=env)
    
    return result.returncode == 0

def install_llama_amd():
    """Installiert llama-cpp-python mit ROCm-Support"""
    print("\n" + "="*60)
    print("Installiere llama-cpp-python mit AMD ROCm Support")
    print("Dies kann 5-10 Minuten dauern...")
    print("="*60 + "\n")
    
    # Prüfe ob ROCm installiert ist
    if not check_rocm_installed():
        print("[WARNUNG] ⚠️  ROCm nicht erkannt!")
        print("[INFO] ROCm wird für AMD GPU-Beschleunigung benötigt")
        print("[INFO] Installation: https://rocm.docs.amd.com/\n")
        return False
    
    env = os.environ.copy()
    env["CMAKE_ARGS"] = "-DLLAMA_HIPBLAS=on"
    
    result = subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir",
        "--no-binary", "llama-cpp-python"
    ], env=env)
    
    return result.returncode == 0

def verify_installation():
    """Überprüft ob llama-cpp-python korrekt installiert wurde"""
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

def show_build_tools_help():
    """Zeigt Hilfe zur Installation von Build-Tools"""
    system = platform.system()
    
    print("\n" + "⚠️ "*30)
    print("\n[WARNUNG] C++ Build-Tools nicht gefunden!")
    print("\nUm GPU-Beschleunigung zu aktivieren, installiere Build-Tools:\n")
    
    if system == "Windows":
        print("📥 Download: https://visualstudio.microsoft.com/de/visual-cpp-build-tools/")
        print("\n✅ Erforderliche Komponenten:")
        print("   - Desktopentwicklung mit C++")
        print("   - MSVC v143 oder neuer")
        print("   - Windows 10 SDK")
        print("   - CMake-Tools für Windows")
        print("\n⏱️  Installation dauert ca. 5-10 Minuten")
        print("🔄 Neustart erforderlich nach Installation")
    else:
        print("Auf Ubuntu/Debian:")
        print("   sudo apt-get install build-essential cmake")
        print("\nAuf Fedora/RHEL:")
        print("   sudo dnf install gcc gcc-c++ cmake")
        print("\nAuf macOS:")
        print("   xcode-select --install")
        print("   brew install cmake")
    
    print("\n" + "⚠️ "*30 + "\n")

def main():
    print("""
    ╭──────────────────────────────────────────────────────────────╮
    │       JARVIS Core - llama.cpp Setup Script v2.0          │
    │          Automatische GPU-Erkennung & Installation       │
    ╰──────────────────────────────────────────────────────────────╯
    """)
    
    print(f"[INFO] System: {platform.system()} {platform.machine()}")
    print(f"[INFO] Python: {sys.version.split()[0]}")
    print()
    
    # Prüfe Build-Tools
    has_build_tools, missing_tools = check_build_tools()
    
    if not has_build_tools:
        print(f"[WARNUNG] ⚠️  Fehlende Build-Tools: {', '.join(missing_tools)}")
    else:
        print("[INFO] ✅ C++ Build-Tools erkannt")
    
    # Erkenne GPU
    gpu_type = detect_gpu()
    
    # Deinstalliere vorhandenes
    uninstall_llama()
    
    # Bestimme Installationsstrategie
    success = False
    install_mode = "unbekannt"
    
    if gpu_type == "nvidia":
        if has_build_tools:
            print("\n[INFO] 🚀 Installiere mit NVIDIA CUDA Support...")
            success = install_llama_nvidia()
            install_mode = "NVIDIA CUDA"
        else:
            show_build_tools_help()
            print("\n[INFO] Fallback auf vorkompilierte CPU-Version...\n")
            success = install_llama_prebuilt()
            install_mode = "CPU (vorkompiliert)"
    
    elif gpu_type == "amd":
        if has_build_tools:
            print("\n[INFO] 🚀 Installiere mit AMD ROCm Support...")
            success = install_llama_amd()
            if not success:
                print("\n[INFO] ROCm-Installation fehlgeschlagen, versuche CPU-Version...\n")
                success = install_llama_prebuilt()
                install_mode = "CPU (vorkompiliert)"
            else:
                install_mode = "AMD ROCm"
        else:
            show_build_tools_help()
            print("\n[INFO] Fallback auf vorkompilierte CPU-Version...\n")
            success = install_llama_prebuilt()
            install_mode = "CPU (vorkompiliert)"
    
    else:  # CPU
        if has_build_tools:
            print("\n[INFO] Installiere CPU-Version (aus Quellcode)...")
            success = install_llama_cpu()
            install_mode = "CPU (optimiert)"
        else:
            print("\n[INFO] Installiere vorkompilierte CPU-Version...")
            success = install_llama_prebuilt()
            install_mode = "CPU (vorkompiliert)"
    
    # Überprüfe Installation
    if success and verify_installation():
        print("\n" + "✅"*30)
        print("\n[ERFOLG] 🎉 llama-cpp-python erfolgreich installiert!")
        print(f"[INFO] Modus: {install_mode}")
        print(f"[INFO] GPU-Typ: {gpu_type.upper()}")
        
        if not has_build_tools and gpu_type != "cpu":
            print("\n[TIPP] 💡 Um GPU-Beschleunigung zu aktivieren:")
            print("      1. Installiere C++ Build-Tools (siehe Anleitung oben)")
            print("      2. Führe erneut aus: python setup_llama.py")
        
        print("\n[INFO] ▶️  Du kannst jetzt starten: python main.py")
        print("✅"*30 + "\n")
        return 0
    else:
        print("\n" + "❌"*30)
        print("\n[FEHLER] 💥 Installation fehlgeschlagen!")
        print("\n[INFO] Problemlösung:")
        print("      1. Prüfe Fehlermeldungen oben")
        print("      2. Installiere Build-Tools falls fehlend")
        print("      3. Versuche manuelle Installation:")
        print("         pip install llama-cpp-python --only-binary :all:")
        print("\n[INFO] 📚 Vollständige Dokumentation: https://github.com/Lautloserspieler/JarvisCore")
        print("❌"*30 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
