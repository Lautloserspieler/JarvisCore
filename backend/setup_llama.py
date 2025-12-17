#!/usr/bin/env python3
"""Automatic llama-cpp-python installation with GPU detection"""

import subprocess
import sys
import platform
import os

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
        print(f"[ERROR] Command failed: {e}")
        return "", 1

def detect_gpu():
    """Detect GPU type (NVIDIA, AMD, or None)"""
    system = platform.system()
    
    print("[INFO] Detecting GPU...")
    
    # Check NVIDIA first
    if system == "Windows":
        output, code = run_command("nvidia-smi", shell=True)
        if code == 0 and "NVIDIA" in output:
            print("[INFO] NVIDIA GPU detected!")
            return "nvidia"
        
        # Check AMD on Windows
        output, code = run_command("wmic path win32_VideoController get name", shell=True)
        if code == 0 and ("AMD" in output or "Radeon" in output):
            print("[INFO] AMD GPU detected!")
            return "amd"
    
    else:  # Linux/Mac
        output, code = run_command("nvidia-smi")
        if code == 0 and "NVIDIA" in output:
            print("[INFO] NVIDIA GPU detected!")
            return "nvidia"
        
        # Check AMD on Linux
        output, code = run_command("lspci")
        if "AMD" in output or "Radeon" in output:
            print("[INFO] AMD GPU detected!")
            return "amd"
    
    print("[INFO] No GPU detected, will use CPU")
    return "cpu"

def check_rocm_installed():
    """Check if ROCm is installed"""
    output, code = run_command("rocm-smi", shell=True)
    return code == 0

def uninstall_llama():
    """Uninstall existing llama-cpp-python"""
    print("[INFO] Removing existing llama-cpp-python...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "llama-cpp-python", "-y"])

def install_llama_cpu():
    """Install llama-cpp-python for CPU"""
    print("\n" + "="*60)
    print("Installing llama-cpp-python for CPU")
    print("="*60 + "\n")
    
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir"
    ])

def install_llama_nvidia():
    """Install llama-cpp-python with CUDA support"""
    print("\n" + "="*60)
    print("Installing llama-cpp-python with NVIDIA CUDA support")
    print("="*60 + "\n")
    
    env = os.environ.copy()
    env["CMAKE_ARGS"] = "-DLLAMA_CUDA=on"
    
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir",
        "--no-binary", "llama-cpp-python"
    ], env=env)

def install_llama_amd():
    """Install llama-cpp-python with ROCm support"""
    print("\n" + "="*60)
    print("Installing llama-cpp-python with AMD ROCm support")
    print("="*60 + "\n")
    
    # Check if ROCm is installed
    if not check_rocm_installed():
        print("[WARNING] ROCm not detected!")
        print("[INFO] Installing for CPU instead...")
        print("[INFO] To use GPU acceleration, install ROCm first:")
        print("       https://rocm.docs.amd.com/en/latest/deploy/linux/quick_start.html")
        install_llama_cpu()
        return
    
    env = os.environ.copy()
    env["CMAKE_ARGS"] = "-DLLAMA_HIPBLAS=on"
    
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir",
        "--no-binary", "llama-cpp-python"
    ], env=env)

def verify_installation():
    """Verify llama-cpp-python is installed correctly"""
    print("\n" + "="*60)
    print("Verifying installation...")
    print("="*60 + "\n")
    
    try:
        import llama_cpp
        print(f"[SUCCESS] llama-cpp-python version: {llama_cpp.__version__}")
        
        # Check backend
        try:
            from llama_cpp import Llama
            print("[SUCCESS] Llama class imported successfully")
        except Exception as e:
            print(f"[ERROR] Failed to import Llama: {e}")
            return False
        
        return True
    except ImportError as e:
        print(f"[ERROR] llama-cpp-python not found: {e}")
        return False

def main():
    print("""
    ╭──────────────────────────────────────────────────────────╮
    │       JARVIS Core - llama.cpp Setup Script            │
    │          Automatic GPU Detection & Install             │
    ╰──────────────────────────────────────────────────────────╯
    """)
    
    print(f"[INFO] System: {platform.system()} {platform.machine()}")
    print(f"[INFO] Python: {sys.version.split()[0]}")
    print()
    
    # Detect GPU
    gpu_type = detect_gpu()
    
    # Uninstall existing
    uninstall_llama()
    
    # Install based on GPU type
    if gpu_type == "nvidia":
        install_llama_nvidia()
    elif gpu_type == "amd":
        install_llama_amd()
    else:
        install_llama_cpu()
    
    # Verify
    if verify_installation():
        print("\n" + "✅"*30)
        print("\n[SUCCESS] llama-cpp-python installed successfully!")
        print(f"[INFO] GPU Mode: {gpu_type.upper()}")
        print("\n[INFO] You can now run: python main.py")
        print("✅"*30 + "\n")
    else:
        print("\n" + "❌"*30)
        print("\n[ERROR] Installation failed!")
        print("[INFO] Please check the error messages above.")
        print("❌"*30 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
