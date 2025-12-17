#!/usr/bin/env python3
"""Automatische llama-cpp-python Installation mit GPU-Erkennung und Build-Tools-Installation"""

import subprocess
import sys
import platform
import os
import shutil
import urllib.request
import tempfile
import webbrowser

# Build Tools Download URLs
VS_BUILDTOOLS_URL = "https://aka.ms/vs/17/release/vs_BuildTools.exe"

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

def download_build_tools():
    """Lädt Visual Studio Build Tools herunter"""
    print("\n[INFO] 📥 Lade Visual Studio Build Tools herunter...")
    print("[INFO] Größe: ~3 GB, dies kann einige Minuten dauern...\n")
    
    try:
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "vs_BuildTools.exe")
        
        # Download mit Progress
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                print(f"\r[INFO] Download: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)", end="")
        
        urllib.request.urlretrieve(VS_BUILDTOOLS_URL, installer_path, download_progress)
        print("\n[INFO] ✅ Download abgeschlossen!")
        return installer_path
    
    except Exception as e:
        print(f"\n[FEHLER] Download fehlgeschlagen: {e}")
        return None

def install_build_tools_windows(installer_path):
    """Installiert Visual Studio Build Tools auf Windows"""
    print("\n[INFO] 🛠️  Starte Build Tools Installation...")
    print("[INFO] Dies erfordert Administrator-Rechte!")
    print("[INFO] Installation dauert ca. 5-15 Minuten...\n")
    
    # Installationsbefehl mit den benötigten Komponenten
    install_cmd = [
        installer_path,
        "--quiet",
        "--wait",
        "--norestart",
        "--add", "Microsoft.VisualStudio.Workload.VCTools",
        "--add", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
        "--add", "Microsoft.VisualStudio.Component.Windows11SDK.22621",
        "--add", "Microsoft.VisualStudio.Component.VC.CMake.Project"
    ]
    
    try:
        result = subprocess.run(install_cmd, check=False)
        if result.returncode == 0 or result.returncode == 3010:  # 3010 = Neustart erforderlich
            print("\n[INFO] ✅ Build Tools erfolgreich installiert!")
            if result.returncode == 3010:
                print("[INFO] 🔄 Ein Neustart wird empfohlen")
            return True
        else:
            print(f"\n[FEHLER] Installation fehlgeschlagen (Code: {result.returncode})")
            return False
    except Exception as e:
        print(f"\n[FEHLER] Installation fehlgeschlagen: {e}")
        return False

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
    print("\nFür GPU-Beschleunigung werden Build-Tools benötigt.\n")
    
    if system == "Windows":
        print("🔧 Build-Tools Optionen:\n")
        print("   1️⃣  Automatische Installation (empfohlen)")
        print("      - Download + Installation automatisch")
        print("      - Dauert ca. 15-20 Minuten")
        print("      - Erfordert Administrator-Rechte\n")
        print("   2️⃣  Manuelle Installation")
        print("      - Download: https://visualstudio.microsoft.com/de/visual-cpp-build-tools/")
        print("      - Installiere: Desktopentwicklung mit C++\n")
        print("   3️⃣  CPU-Version ohne GPU (schnell)")
        print("      - Vorkompiliertes Paket")
        print("      - Keine GPU-Beschleunigung")
    else:
        print("Auf Ubuntu/Debian:")
        print("   sudo apt-get install build-essential cmake")
        print("\nAuf Fedora/RHEL:")
        print("   sudo dnf install gcc gcc-c++ cmake")
        print("\nAuf macOS:")
        print("   xcode-select --install")
        print("   brew install cmake")
    
    print("\n" + "⚠️ "*30 + "\n")

def ask_user_choice():
    """Fragt Benutzer nach bevorzugter Installation"""
    while True:
        choice = input("Wähle Option [1/2/3]: ").strip()
        if choice in ["1", "2", "3"]:
            return choice
        print("[FEHLER] Ungültige Eingabe! Bitte 1, 2 oder 3 eingeben.")

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
    
    # Wenn GPU erkannt aber keine Build-Tools: Frage Benutzer
    if gpu_type != "cpu" and not has_build_tools and platform.system() == "Windows":
        show_build_tools_help()
        choice = ask_user_choice()
        
        if choice == "1":  # Automatische Installation
            installer_path = download_build_tools()
            if installer_path:
                if install_build_tools_windows(installer_path):
                    print("\n[INFO] ✅ Build-Tools installiert!")
                    print("[INFO] Bitte starte deinen Computer neu.")
                    print("[INFO] Nach dem Neustart führe erneut aus: python setup_llama.py\n")
                    return 0
                else:
                    print("\n[INFO] Installation fehlgeschlagen, fahre mit CPU-Version fort...\n")
            else:
                print("\n[INFO] Download fehlgeschlagen, fahre mit CPU-Version fort...\n")
        
        elif choice == "2":  # Manuelle Installation
            print("\n[INFO] Öffne Download-Seite im Browser...")
            webbrowser.open("https://visualstudio.microsoft.com/de/visual-cpp-build-tools/")
            print("[INFO] Nach der Installation führe erneut aus: python setup_llama.py")
            print("[INFO] Fahre jetzt mit CPU-Version fort...\n")
        
        # Choice 3 oder Fallback: CPU-Version
    
    # Deinstalliere vorhandenes
    uninstall_llama()
    
    # Bestimme Installationsstrategie
    success = False
    install_mode = "unbekannt"
    
    if gpu_type == "nvidia" and has_build_tools:
        print("\n[INFO] 🚀 Installiere mit NVIDIA CUDA Support...")
        success = install_llama_nvidia()
        install_mode = "NVIDIA CUDA"
    elif gpu_type == "amd" and has_build_tools:
        print("\n[INFO] 🚀 Installiere mit AMD ROCm Support...")
        success = install_llama_amd()
        if not success:
            print("\n[INFO] ROCm-Installation fehlgeschlagen, versuche CPU-Version...\n")
            success = install_llama_prebuilt()
            install_mode = "CPU (vorkompiliert)"
        else:
            install_mode = "AMD ROCm"
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
            print("      Führe erneut aus: python setup_llama.py")
            print("      Und wähle Option 1 für automatische Build-Tools Installation")
        
        print("\n[INFO] ▶️  Du kannst jetzt starten: python main.py")
        print("✅"*30 + "\n")
        return 0
    else:
        print("\n" + "❌"*30)
        print("\n[FEHLER] 💥 Installation fehlgeschlagen!")
        print("\n[INFO] Problemlösung:")
        print("      1. Prüfe Fehlermeldungen oben")
        print("      2. Führe Script erneut aus: python setup_llama.py")
        print("      3. Versuche manuelle Installation:")
        print("         pip install llama-cpp-python --only-binary :all:")
        print("\n[INFO] 📚 Vollständige Dokumentation: https://github.com/Lautloserspieler/JarvisCore")
        print("❌"*30 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
