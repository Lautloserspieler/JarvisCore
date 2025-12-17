#!/usr/bin/env python3
"""Findet und aktiviert Visual Studio Build Tools im aktuellen Prozess"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def find_vswhere():
    """Findet vswhere.exe Tool von Visual Studio"""
    vswhere_path = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if vswhere_path.exists():
        return vswhere_path
    return None

def find_buildtools_with_vswhere():
    """Nutzt vswhere um Build Tools zu finden - gibt ALLE gefundenen Installationen zurück"""
    vswhere = find_vswhere()
    if not vswhere:
        return []
    
    installations = []
    
    try:
        # Finde alle Installationen mit VC Tools
        result = subprocess.run(
            [str(vswhere), "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    installations.append(Path(line.strip()))
    except Exception as e:
        print(f"[DEBUG] vswhere error: {e}")
    
    return installations

def find_buildtools_manual():
    """Sucht manuell nach Build Tools Installation"""
    base_paths = [
        Path("C:/Program Files (x86)/Microsoft Visual Studio"),
        Path("C:/Program Files/Microsoft Visual Studio")
    ]
    
    versions = ["2022", "2019", "2017"]
    editions = ["BuildTools", "Community", "Professional", "Enterprise"]
    
    found = []
    
    for base in base_paths:
        if not base.exists():
            continue
        for version in versions:
            for edition in editions:
                path = base / version / edition
                if path.exists():
                    # Prüfe ob VC Tools vorhanden sind
                    vc_tools = path / "VC" / "Tools" / "MSVC"
                    if vc_tools.exists() and any(vc_tools.iterdir()):
                        found.append(path)
    
    return found

def get_latest_msvc_version(buildtools_path):
    """Findet die neueste MSVC Version"""
    msvc_path = buildtools_path / "VC" / "Tools" / "MSVC"
    if not msvc_path.exists():
        return None
    
    versions = [d for d in msvc_path.iterdir() if d.is_dir()]
    if not versions:
        return None
    
    # Sortiere nach Version (neueste zuerst)
    versions.sort(reverse=True)
    return versions[0]

def get_windows_sdk_version(buildtools_path):
    """Findet die neueste Windows SDK Version"""
    sdk_path = Path("C:/Program Files (x86)/Windows Kits/10/bin")
    if not sdk_path.exists():
        return None
    
    versions = [d for d in sdk_path.iterdir() if d.is_dir() and d.name.startswith("10.")]
    if not versions:
        return None
    
    versions.sort(reverse=True)
    return versions[0]

def select_best_installation(installations):
    """Wählt die beste Installation aus (präferiert BuildTools, dann Community)"""
    if not installations:
        return None
    
    # Präferiere BuildTools
    for inst in installations:
        if "BuildTools" in str(inst):
            return inst
    
    # Dann Community
    for inst in installations:
        if "Community" in str(inst):
            return inst
    
    # Sonst die erste
    return installations[0]

def setup_build_environment():
    """Richtet Build-Umgebung ein und gibt PATH-Liste zurück"""
    if platform.system() != "Windows":
        print("[INFO] Dieses Script ist nur für Windows")
        return None
    
    print("[INFO] 🔍 Suche nach Visual Studio Build Tools...\n")
    
    # Versuche vswhere zuerst (findet alle)
    installations = find_buildtools_with_vswhere()
    if not installations:
        # Manuelle Suche
        installations = find_buildtools_manual()
    
    if not installations:
        print("[FEHLER] ❌ Build Tools nicht gefunden!")
        print("[INFO] Installiere zuerst Build Tools mit: python setup_llama.py")
        return None
    
    # Zeige alle gefundenen Installationen
    print(f"[INFO] ✅ {len(installations)} Installation(en) gefunden:")
    for inst in installations:
        print(f"       - {inst}")
    
    # Wähle beste Installation
    buildtools_path = select_best_installation(installations)
    print(f"\n[INFO] 🎯 Nutze: {buildtools_path}\n")
    
    # Finde MSVC Version
    msvc_version = get_latest_msvc_version(buildtools_path)
    if not msvc_version:
        print("[FEHLER] ❌ MSVC Compiler nicht gefunden!")
        print(f"[DEBUG] Gesucht in: {buildtools_path / 'VC' / 'Tools' / 'MSVC'}")
        return None
    
    print(f"[INFO] ✅ MSVC Version: {msvc_version.name}")
    
    # Finde Windows SDK
    sdk_version = get_windows_sdk_version(buildtools_path)
    if sdk_version:
        print(f"[INFO] ✅ Windows SDK: {sdk_version.name}")
    else:
        print("[WARNUNG] ⚠️  Windows SDK nicht gefunden (optional)")
    
    # Baue PATH Liste
    new_paths = []
    
    # MSVC Compiler (cl.exe)
    msvc_bin = msvc_version / "bin" / "Hostx64" / "x64"
    if msvc_bin.exists():
        new_paths.append(str(msvc_bin))
        print(f"[INFO] ✅ MSVC Compiler: {msvc_bin}")
    
    # MSBuild
    msbuild_path = buildtools_path / "MSBuild" / "Current" / "Bin"
    if msbuild_path.exists():
        new_paths.append(str(msbuild_path))
    
    # CMake
    cmake_path = buildtools_path / "Common7" / "IDE" / "CommonExtensions" / "Microsoft" / "CMake" / "CMake" / "bin"
    if cmake_path.exists():
        new_paths.append(str(cmake_path))
    
    # Windows SDK
    if sdk_version:
        sdk_bin = sdk_version / "x64"
        if sdk_bin.exists():
            new_paths.append(str(sdk_bin))
    
    # INCLUDE und LIB Pfade
    include_paths = []
    lib_paths = []
    
    # MSVC Include
    msvc_include = msvc_version / "include"
    if msvc_include.exists():
        include_paths.append(str(msvc_include))
    
    # MSVC Lib
    msvc_lib = msvc_version / "lib" / "x64"
    if msvc_lib.exists():
        lib_paths.append(str(msvc_lib))
    
    # Windows SDK Include
    if sdk_version:
        sdk_include_base = Path("C:/Program Files (x86)/Windows Kits/10/Include") / sdk_version.name
        for subdir in ["ucrt", "um", "shared"]:
            sdk_inc = sdk_include_base / subdir
            if sdk_inc.exists():
                include_paths.append(str(sdk_inc))
    
    # Windows SDK Lib
    if sdk_version:
        sdk_lib_base = Path("C:/Program Files (x86)/Windows Kits/10/Lib") / sdk_version.name
        for subdir in ["ucrt/x64", "um/x64"]:
            sdk_lib = sdk_lib_base / subdir
            if sdk_lib.exists():
                lib_paths.append(str(sdk_lib))
    
    return {
        "PATH": new_paths,
        "INCLUDE": include_paths,
        "LIB": lib_paths
    }

def apply_environment(env_vars):
    """Wendet Umgebungsvariablen auf aktuellen Prozess an"""
    if not env_vars:
        return False
    
    print("\n[INFO] ⚙️  Setze Umgebungsvariablen...\n")
    
    # PATH
    current_path = os.environ.get("PATH", "")
    new_path = os.pathsep.join(env_vars["PATH"]) + os.pathsep + current_path
    os.environ["PATH"] = new_path
    print(f"[INFO] ✅ PATH erweitert ({len(env_vars['PATH'])} neue Pfade)")
    
    # INCLUDE
    if env_vars["INCLUDE"]:
        os.environ["INCLUDE"] = os.pathsep.join(env_vars["INCLUDE"])
        print(f"[INFO] ✅ INCLUDE gesetzt ({len(env_vars['INCLUDE'])} Pfade)")
    
    # LIB
    if env_vars["LIB"]:
        os.environ["LIB"] = os.pathsep.join(env_vars["LIB"])
        print(f"[INFO] ✅ LIB gesetzt ({len(env_vars['LIB'])} Pfade)")
    
    return True

def verify_tools():
    """Verifiziert dass Tools jetzt verfügbar sind"""
    print("\n[INFO] 🔍 Verifiziere Tools...\n")
    
    tools = [
        ("cl.exe", "MSVC Compiler"),
        ("cmake.exe", "CMake"),
        ("msbuild.exe", "MSBuild")
    ]
    
    all_found = True
    for tool, name in tools:
        result = subprocess.run(["where", tool], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            path = result.stdout.strip().split('\n')[0]
            print(f"[INFO] ✅ {name}: {path}")
        else:
            print(f"[WARNUNG] ⚠️  {name} nicht gefunden")
            all_found = False
    
    return all_found

def main():
    print("""
    ╭──────────────────────────────────────────────────────────╮
    │       Build Tools PATH Setup                            │
    │       Automatische Umgebungskonfiguration               │
    ╰──────────────────────────────────────────────────────────╯
    """)
    
    # Finde und konfiguriere Build Tools
    env_vars = setup_build_environment()
    
    if not env_vars:
        print("\n❌ Build Tools Setup fehlgeschlagen!\n")
        return 1
    
    # Wende Umgebungsvariablen an
    if not apply_environment(env_vars):
        print("\n❌ Fehler beim Setzen der Umgebungsvariablen!\n")
        return 1
    
    # Verifiziere
    if verify_tools():
        print("\n" + "✅"*30)
        print("\n[ERFOLG] 🎉 Build Tools erfolgreich aktiviert!")
        print("\n[INFO] 💡 Jetzt kannst du ausführen:")
        print("       python setup_llama.py")
        print("\n[INFO] Die Tools sind NUR in diesem Terminal-Fenster aktiv.")
        print("       Für permanente Aktivierung starte Windows neu.")
        print("\n" + "✅"*30 + "\n")
        return 0
    else:
        print("\n⚠️  Einige Tools wurden nicht gefunden.")
        print("[INFO] Versuche trotzdem: python setup_llama.py\n")
        return 0

if __name__ == "__main__":
    sys.exit(main())