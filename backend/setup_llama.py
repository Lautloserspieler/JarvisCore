#!/usr/bin/env python3
"""Automatic llama-cpp-python installation with GPU detection and build tools check"""

import subprocess
import sys
import platform
import os
import shutil

def run_command(cmd, shell=False):
    """Run command and return output"""
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
    """Check if C++ build tools are available"""
    system = platform.system()
    
    if system == "Windows":
        # Check for Visual Studio or Build Tools
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
    """Detect GPU type (NVIDIA, AMD, or None)"""
    system = platform.system()
    
    print("[INFO] Detecting GPU...")
    
    # Check NVIDIA first
    if system == "Windows":
        output, code = run_command("nvidia-smi", shell=True)
        if code == 0 and "NVIDIA" in output:
            print("[INFO] ✅ NVIDIA GPU detected!")
            return "nvidia"
        
        # Check AMD on Windows
        output, code = run_command("wmic path win32_VideoController get name", shell=True)
        if code == 0 and ("AMD" in output or "Radeon" in output):
            print("[INFO] ✅ AMD GPU detected!")
            return "amd"
    
    else:  # Linux/Mac
        output, code = run_command("nvidia-smi")
        if code == 0 and "NVIDIA" in output:
            print("[INFO] ✅ NVIDIA GPU detected!")
            return "nvidia"
        
        # Check AMD on Linux
        output, code = run_command("lspci")
        if "AMD" in output or "Radeon" in output:
            print("[INFO] ✅ AMD GPU detected!")
            return "amd"
    
    print("[INFO] ℹ️  No GPU detected, will use CPU")
    return "cpu"

def check_rocm_installed():
    """Check if ROCm is installed"""
    output, code = run_command("rocm-smi", shell=True)
    return code == 0

def uninstall_llama():
    """Uninstall existing llama-cpp-python"""
    print("\n[INFO] Removing existing llama-cpp-python...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "llama-cpp-python", "-y"], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def install_llama_prebuilt():
    """Install pre-built llama-cpp-python wheel (CPU-only, fast)"""
    print("\n" + "="*60)
    print("Installing pre-built llama-cpp-python (CPU-only)")
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
    """Install llama-cpp-python for CPU (build from source)"""
    print("\n" + "="*60)
    print("Installing llama-cpp-python for CPU (from source)")
    print("="*60 + "\n")
    
    result = subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir"
    ])
    
    return result.returncode == 0

def install_llama_nvidia():
    """Install llama-cpp-python with CUDA support"""
    print("\n" + "="*60)
    print("Installing llama-cpp-python with NVIDIA CUDA support")
    print("This may take 5-10 minutes...")
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
    """Install llama-cpp-python with ROCm support"""
    print("\n" + "="*60)
    print("Installing llama-cpp-python with AMD ROCm support")
    print("This may take 5-10 minutes...")
    print("="*60 + "\n")
    
    # Check if ROCm is installed
    if not check_rocm_installed():
        print("[WARNING] ⚠️  ROCm not detected!")
        print("[INFO] ROCm is required for AMD GPU acceleration")
        print("[INFO] Install from: https://rocm.docs.amd.com/\n")
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
    """Verify llama-cpp-python is installed correctly"""
    print("\n" + "="*60)
    print("Verifying installation...")
    print("="*60 + "\n")
    
    try:
        import llama_cpp
        print(f"[SUCCESS] ✅ llama-cpp-python version: {llama_cpp.__version__}")
        
        # Check backend
        try:
            from llama_cpp import Llama
            print("[SUCCESS] ✅ Llama class imported successfully")
        except Exception as e:
            print(f"[ERROR] ❌ Failed to import Llama: {e}")
            return False
        
        return True
    except ImportError as e:
        print(f"[ERROR] ❌ llama-cpp-python not found: {e}")
        return False

def show_build_tools_help():
    """Show help for installing build tools"""
    system = platform.system()
    
    print("\n" + "⚠️ "*30)
    print("\n[WARNING] C++ Build Tools not found!")
    print("\nTo enable GPU acceleration, install build tools:\n")
    
    if system == "Windows":
        print("📥 Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        print("\n✅ Required components:")
        print("   - Desktop development with C++")
        print("   - MSVC v143 or newer")
        print("   - Windows 10 SDK")
        print("   - CMake tools for Windows")
        print("\n⏱️  Installation takes ~5-10 minutes")
        print("🔄 Restart required after installation")
    else:
        print("On Ubuntu/Debian:")
        print("   sudo apt-get install build-essential cmake")
        print("\nOn Fedora/RHEL:")
        print("   sudo dnf install gcc gcc-c++ cmake")
        print("\nOn macOS:")
        print("   xcode-select --install")
        print("   brew install cmake")
    
    print("\n" + "⚠️ "*30 + "\n")

def main():
    print("""
    ╭──────────────────────────────────────────────────────────────╮
    │       JARVIS Core - llama.cpp Setup Script v2.0          │
    │          Automatic GPU Detection & Install               │
    ╰──────────────────────────────────────────────────────────────╯
    """)
    
    print(f"[INFO] System: {platform.system()} {platform.machine()}")
    print(f"[INFO] Python: {sys.version.split()[0]}")
    print()
    
    # Check build tools
    has_build_tools, missing_tools = check_build_tools()
    
    if not has_build_tools:
        print(f"[WARNING] ⚠️  Missing build tools: {', '.join(missing_tools)}")
    else:
        print("[INFO] ✅ C++ build tools detected")
    
    # Detect GPU
    gpu_type = detect_gpu()
    
    # Uninstall existing
    uninstall_llama()
    
    # Determine installation strategy
    success = False
    install_mode = "unknown"
    
    if gpu_type == "nvidia":
        if has_build_tools:
            print("\n[INFO] 🚀 Installing with NVIDIA CUDA support...")
            success = install_llama_nvidia()
            install_mode = "NVIDIA CUDA"
        else:
            show_build_tools_help()
            print("\n[INFO] Falling back to pre-built CPU-only version...\n")
            success = install_llama_prebuilt()
            install_mode = "CPU (pre-built)"
    
    elif gpu_type == "amd":
        if has_build_tools:
            print("\n[INFO] 🚀 Installing with AMD ROCm support...")
            success = install_llama_amd()
            if not success:
                print("\n[INFO] ROCm installation failed, trying CPU version...\n")
                success = install_llama_prebuilt()
                install_mode = "CPU (pre-built)"
            else:
                install_mode = "AMD ROCm"
        else:
            show_build_tools_help()
            print("\n[INFO] Falling back to pre-built CPU-only version...\n")
            success = install_llama_prebuilt()
            install_mode = "CPU (pre-built)"
    
    else:  # CPU
        if has_build_tools:
            print("\n[INFO] Installing CPU version (from source)...")
            success = install_llama_cpu()
            install_mode = "CPU (optimized)"
        else:
            print("\n[INFO] Installing pre-built CPU version...")
            success = install_llama_prebuilt()
            install_mode = "CPU (pre-built)"
    
    # Verify
    if success and verify_installation():
        print("\n" + "✅"*30)
        print("\n[SUCCESS] 🎉 llama-cpp-python installed successfully!")
        print(f"[INFO] Mode: {install_mode}")
        print(f"[INFO] GPU Type: {gpu_type.upper()}")
        
        if not has_build_tools and gpu_type != "cpu":
            print("\n[TIP] 💡 To enable GPU acceleration:")
            print("      1. Install C++ build tools (see instructions above)")
            print("      2. Re-run: python setup_llama.py")
        
        print("\n[INFO] ▶️  You can now run: python main.py")
        print("✅"*30 + "\n")
        return 0
    else:
        print("\n" + "❌"*30)
        print("\n[ERROR] 💥 Installation failed!")
        print("\n[INFO] Troubleshooting:")
        print("      1. Check error messages above")
        print("      2. Install build tools if missing")
        print("      3. Try manual installation:")
        print("         pip install llama-cpp-python --only-binary :all:")
        print("\n[INFO] 📚 Full docs: https://github.com/Lautloserspieler/JarvisCore")
        print("❌"*30 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
