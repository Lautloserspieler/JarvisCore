#!/usr/bin/env python3
"""Automatische llama-cpp-python Installation mit GPU-Erkennung und CUDA Toolkit Support"""

import subprocess
import sys
import platform
import os
import shutil
import webbrowser
from pathlib import Path
import glob

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

def find_vs_installation():
    """Sucht nach Visual Studio Build Tools Installation"""
    system = platform.system()
    if system != "Windows":
        return None, []
    
    # Suche nach VS Installationen
    vs_paths = [
        "C:/Program Files (x86)/Microsoft Visual Studio",
        "C:/Program Files/Microsoft Visual Studio",
    ]
    
    found_installations = []
    
    for base_path in vs_paths:
        if not Path(base_path).exists():
            continue
        
        # Suche nach Jahren (2022, 2026, etc.) und Versionen (18, 17, etc.)
        for year_path in Path(base_path).iterdir():
            if not year_path.is_dir():
                continue
            
            # Suche nach Editionen (BuildTools, Community, Professional, Enterprise)
            for edition_path in year_path.iterdir():
                if not edition_path.is_dir():
                    continue
                
                # Prüfe ob cl.exe existiert
                msvc_path = edition_path / "VC" / "Tools" / "MSVC"
                if msvc_path.exists():
                    # Finde neueste MSVC Version
                    msvc_versions = sorted([d for d in msvc_path.iterdir() if d.is_dir()], reverse=True)
                    if msvc_versions:
                        compiler_path = msvc_versions[0] / "bin" / "Hostx64" / "x64" / "cl.exe"
                        if compiler_path.exists():
                            found_installations.append({
                                "year": year_path.name,
                                "edition": edition_path.name,
                                "path": str(edition_path),
                                "compiler": str(compiler_path),
                                "msvc_version": msvc_versions[0].name
                            })
    
    if found_installations:
        # Wähle neueste Installation
        latest = sorted(found_installations, key=lambda x: x["year"], reverse=True)[0]
        return latest, found_installations
    
    return None, []

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
        
        # Wenn cl.exe fehlt, prüfe ob VS installiert ist (nicht im PATH)
        if "MSVC Compiler" in missing:
            vs_install, all_installs = find_vs_installation()
            if vs_install:
                return False, missing, vs_install
        
        return len(missing) == 0, missing, None
    
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
        
        return len(missing) == 0, missing, None

def show_path_fix_guide(vs_install):
    """Zeigt Anleitung zum PATH-Fix"""
    print("\n" + "🔧"*30)
    print("\n[INFO] Visual Studio Build Tools gefunden!\n")
    print(f"   Version: {vs_install['year']} {vs_install['edition']}")
    print(f"   Pfad: {vs_install['path']}\n")
    print("Build-Tools sind nicht im PATH. Verwende den Developer Command Prompt.\n")
    print("Option 1: Developer Command Prompt\n")
    print("   1. Windows-Taste drücken")
    print("   2. 'Developer Command Prompt' tippen")
    print(f"   3. 'Developer Command Prompt for VS {vs_install['year']}' öffnen")
    print("   4. In dein JarvisCore-Verzeichnis wechseln, z.B.:")
    print("      cd C:\\Users\\User\\Desktop\\jarvis\\JarvisCore")
    print("   5. Script ausführen:")
    print("      python backend/setup_llama.py\n")
    print("Option 2: Developer PowerShell\n")
    print("   1. Windows-Taste drücken")
    print("   2. 'Developer PowerShell' tippen")
    print(f"   3. 'Developer PowerShell for VS {vs_install['year']}' öffnen")
    print("   4. In dein JarvisCore-Verzeichnis wechseln, z.B.:")
    print("      cd C:\\Users\\User\\Desktop\\jarvis\\JarvisCore")
    print("   5. Script ausführen:")
    print("      python backend/setup_llama.py\n")
    print("Option 3: vcvarsall.bat manuell\n")
    print("   In einer eigenen Shell:")
    vcvars_path = Path(vs_install['path']) / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
    print(f"   \"{vcvars_path}\" x64")
    print("   cd C:\\Users\\User\\Desktop\\jarvis\\JarvisCore")
    print("   python backend/setup_llama.py\n")
    print("Hinweis: Normales CMD/PowerShell ohne VS-Umgebung funktioniert oft nicht.\n")
    print("🔧"*30 + "\n")

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
            versions = [d for d in Path(cuda_path).iterdir() if d.is_dir() and d.name.startswith(('v', '11', '12', '13'))]
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

def detect_gpu():
    """Erkennt GPU-Typ (NVIDIA, AMD, oder keine)"""
    system = platform.system()
    
    print("[INFO] Erkenne GPU...")
    
    # Prüfe NVIDIA zuerst
    if system == "Windows":
        output, code = run_command("nvidia-smi", shell=True)
        if code == 0 and "NVIDIA" in output:
            print("[INFO] NVIDIA GPU erkannt")
            return "nvidia"
        
        # Prüfe AMD auf Windows
        output, code = run_command("wmic path win32_VideoController get name", shell=True)
        if code == 0 and ("AMD" in output or "Radeon" in output):
            print("[INFO] AMD GPU erkannt")
            return "amd"
    
    else:  # Linux/Mac
        output, code = run_command("nvidia-smi")
        if code == 0 and "NVIDIA" in output:
            print("[INFO] NVIDIA GPU erkannt")
            return "nvidia"
        
        # Prüfe AMD auf Linux
        output, code = run_command("lspci")
        if "AMD" in output or "Radeon" in output:
            print("[INFO] AMD GPU erkannt")
            return "amd"
    
    print("[INFO] Keine GPU erkannt, nutze CPU")
    return "cpu"

def show_build_tools_guide():
    """Zeigt Anleitung zur Build-Tools Installation"""
    system = platform.system()
    
    print("\n" + "-"*60)
    print("C++ Build-Tools nicht gefunden\n")
    print("Für llama-cpp-python werden C++ Build-Tools benötigt.\n")
    
    if system == "Windows":
        print("Windows Build-Tools Installation:\n")
        print("1. Visual Studio Build Tools herunterladen:")
        print("   https://visualstudio.microsoft.com/downloads/")
        print("   -> 'Tools for Visual Studio 2026'")
        print("   -> 'Build Tools für Visual Studio 2026'\n")
        print("2. Komponenten auswählen:")
        print("   - Desktopentwicklung mit C++")
        print("   - MSVC v145 - VS 2026 C++ x64/x86-Buildtools")
        print("   - Windows 11 SDK (neueste Version)")
        print("   - CMake-Tools für Windows\n")
        print("3. Nach der Installation:")
        print("   - Developer Command Prompt öffnen")
        print("   - In dein JarvisCore-Verzeichnis wechseln")
        print("   - python backend/setup_llama.py ausführen\n")
        print("Alternative: VS 2022 Build Tools können ebenfalls verwendet werden.\n")
    
    elif system == "Linux":
        print("Linux Build-Tools Installation:\n")
        print("Debian/Ubuntu:")
        print("   sudo apt update")
        print("   sudo apt install build-essential cmake\n")
        print("Fedora/RHEL:")
        print("   sudo dnf groupinstall 'Development Tools'")
        print("   sudo dnf install cmake\n")
        print("Arch Linux:")
        print("   sudo pacman -S base-devel cmake\n")
    
    elif system == "Darwin":  # macOS
        print("macOS Build-Tools Installation:\n")
        print("1. Xcode Command Line Tools installieren:")
        print("   xcode-select --install\n")
        print("2. Homebrew installieren (falls nötig):")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n")
        print("3. CMake installieren:")
        print("   brew install cmake\n")
    
    print("Du kannst alternativ die CPU-Version ohne Build-Tools installieren (Option 2).\n")
    print("-"*60 + "\n")

def show_cuda_installation_guide():
    """Zeigt Anleitung zur CUDA Toolkit Installation"""
    print("\n" + "-"*60)
    print("CUDA Toolkit nicht gefunden\n")
    print("Für NVIDIA GPU-Beschleunigung wird CUDA Toolkit benötigt.\n")
    print("1. CUDA Toolkit herunterladen (12.x oder 13.x):")
    print("   https://developer.nvidia.com/cuda-downloads\n")
    print("2. System auswählen:")
    print("   - Windows -> x86_64 -> 11 -> exe (local)")
    print("   - Linux -> x86_64 -> Distribution -> Version\n")
    print("3. Installation mit Standardeinstellungen durchführen")
    print("4. PC neu starten")
    print("5. Script erneut ausführen: python backend/setup_llama.py\n")
    print("Hinweis: CUDA 12.x und 13.x werden unterstützt.\n")
    print("Du kannst auch ohne CUDA im CPU-Modus weiterarbeiten.\n")
    print("-"*60 + "\n")

def ask_build_tools_choice():
    """Fragt Benutzer nach Build-Tools Installation"""
    print("Wähle Option:\n")
    print("  1) Anleitung für Build-Tools anzeigen")
    print("  2) CPU-Version installieren (ohne Kompilierung)")
    
    while True:
        choice = input("Option [1/2]: ").strip()
        if choice in ["1", "2"]:
            return choice
        print("Ungültige Eingabe, bitte 1 oder 2 eingeben.")

def ask_cuda_choice():
    """Fragt Benutzer nach CUDA Installation"""
    print("Wähle Option:\n")
    print("  1) CUDA Toolkit jetzt installieren (Browser wird geöffnet)")
    print("  2) CPU-Version ohne GPU verwenden")
    
    while True:
        choice = input("Option [1/2]: ").strip()
        if choice in ["1", "2"]:
            return choice
        print("Ungültige Eingabe, bitte 1 oder 2 eingeben.")

def uninstall_llama():
    """Deinstalliert vorhandenes llama-cpp-python"""
    print("\n[INFO] Entferne vorhandenes llama-cpp-python...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "llama-cpp-python", "-y"], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def install_llama_cpu():
    """Installiert llama-cpp-python für CPU"""
    print("\n" + "="*60)
    print("Installiere llama-cpp-python (CPU-Modus)")
    print("="*60 + "\n")
    
    # 64-bit Build erzwingen
    env = os.environ.copy()
    env["CMAKE_ARGS"] = "-DLLAMA_NATIVE=OFF -DCMAKE_GENERATOR_PLATFORM=x64"
    
    result = subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir",
        "--no-binary", "llama-cpp-python"
    ], env=env)
    
    return result.returncode == 0

def install_llama_nvidia():
    """Installiert llama-cpp-python mit CUDA-Support"""
    print("\n" + "="*60)
    print("Installiere llama-cpp-python mit NVIDIA CUDA Support")
    print("Dies kann einige Minuten dauern...")
    print("="*60 + "\n")
    
    env = os.environ.copy()
    env["CMAKE_ARGS"] = "-DGGML_CUDA=on -DCMAKE_GENERATOR_PLATFORM=x64"
    
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
        print(f"llama-cpp-python Version: {llama_cpp.__version__}")
        
        try:
            from llama_cpp import Llama
            print("Llama-Klasse erfolgreich importiert")
        except Exception as e:
            print(f"Fehler beim Import von Llama: {e}")
            return False
        
        return True
    except ImportError as e:
        print(f"llama-cpp-python nicht gefunden: {e}")
        return False

def main():
    print("""
    JARVIS Core - llama.cpp Setup Script
    VS 2026 + CUDA 13.x + GPU-Erkennung
    """)
    
    print(f"System: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Python Architektur: {platform.architecture()[0]}")
    print()
    
    # Prüfe Build-Tools
    has_build_tools, missing_tools, vs_install = check_build_tools()
    
    if not has_build_tools:
        print(f"Fehlende Build-Tools: {', '.join(missing_tools)}\n")
        
        if vs_install:
            show_path_fix_guide(vs_install)
            return 0
        
        show_build_tools_guide()
        choice = ask_build_tools_choice()
        
        if choice == "1":
            print("\nBitte führe die obenstehende Anleitung aus und starte das Script danach erneut.\n")
            return 0
        else:
            print("\nCPU-Installation ohne Build-Tools wird versucht (nicht empfohlen)...")
            uninstall_llama()
            success = install_llama_cpu()
            
            if success and verify_installation():
                print("\nInstallation erfolgreich.")
                print("JarvisCore kann jetzt mit 'python main.py' im Projekt-Root gestartet werden.")
                return 0
            else:
                print("\nInstallation fehlgeschlagen.")
                print("Bitte Build-Tools installieren und Script erneut ausführen.")
                return 1
    else:
        print("Build-Tools erkannt.")
    
    # Erkenne GPU
    gpu_type = detect_gpu()
    
    # Prüfe CUDA Toolkit wenn NVIDIA GPU
    has_cuda = False
    cuda_path = None
    
    if gpu_type == "nvidia":
        has_cuda, cuda_path = check_cuda_toolkit()
        if has_cuda:
            print(f"CUDA Toolkit gefunden: {cuda_path}")
        else:
            print("CUDA Toolkit nicht gefunden.")
    
    install_mode = "cpu"
    
    if gpu_type == "nvidia" and has_build_tools:
        if has_cuda:
            install_mode = "nvidia"
        else:
            show_cuda_installation_guide()
            choice = ask_cuda_choice()
            
            if choice == "1":
                webbrowser.open("https://developer.nvidia.com/cuda-downloads")
                print("Bitte nach der CUDA-Installation das Script erneut ausführen.")
                return 0
            else:
                install_mode = "cpu"
    else:
        install_mode = "cpu"
    
    uninstall_llama()
    
    if install_mode == "nvidia":
        print("\nInstallation im NVIDIA CUDA Modus...")
        success = install_llama_nvidia()
    else:
        print("\nInstallation im CPU-Modus...")
        success = install_llama_cpu()
    
    if success and verify_installation():
        print("\nInstallation erfolgreich.")
        print("JarvisCore kann jetzt mit 'python main.py' im Projekt-Root gestartet werden.")
        return 0
    else:
        print("\nInstallation fehlgeschlagen.")
        print("Bitte Fehlermeldungen prüfen und erneut versuchen.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
