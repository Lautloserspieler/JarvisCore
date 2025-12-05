#!/usr/bin/env python3
"""
Automatische CUDA Erkennung und llama-cpp-python Installation
Wird automatisch von setup.py aufgerufen
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class CUDASetup:
    """CUDA Detection und llama-cpp-python Installation"""

    def __init__(self):
        self.cuda_available = False
        self.cuda_version = None
        self.cuda_home = None
        self.nvcc_path = None

    def detect_cuda(self) -> bool:
        """Erkennt ob CUDA installiert ist"""
        print("\n🔍 Prüfe CUDA Installation...")

        # 1. CUDA_HOME / CUDA_PATH Environment Variable
        self.cuda_home = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
        if self.cuda_home:
            print(f"✅ CUDA_HOME gefunden: {self.cuda_home}")

        # 2. nvcc Compiler suchen
        self.nvcc_path = self._find_nvcc()
        if self.nvcc_path:
            print(f"✅ nvcc gefunden: {self.nvcc_path}")
            self.cuda_version = self._get_cuda_version()
            if self.cuda_version:
                print(f"✅ CUDA Version: {self.cuda_version}")
                self.cuda_available = True
                return True

        # 3. PyTorch CUDA Check (falls bereits installiert)
        if self._check_torch_cuda():
            print("✅ PyTorch mit CUDA Support gefunden")
            self.cuda_available = True
            return True

        print("⚠️  CUDA nicht gefunden - Installation läuft im CPU-Modus")
        return False

    def _find_nvcc(self) -> str:
        """Sucht nvcc Compiler"""
        # Standard-Pfade je nach OS
        if platform.system() == "Windows":
            possible_paths = [
                r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*\bin\nvcc.exe",
                r"C:\Program Files\NVIDIA Corporation\CUDA\v*\bin\nvcc.exe",
            ]
        else:
            possible_paths = [
                "/usr/local/cuda/bin/nvcc",
                "/usr/bin/nvcc",
                "/opt/cuda/bin/nvcc",
            ]

        # 1. Prüfe CUDA_HOME
        if self.cuda_home:
            nvcc = os.path.join(self.cuda_home, "bin", "nvcc")
            if os.path.exists(nvcc):
                return nvcc

        # 2. Prüfe Standard-Pfade
        import glob
        for pattern in possible_paths:
            for path in glob.glob(pattern):
                if os.path.exists(path):
                    return path

        # 3. which/where Befehl
        try:
            cmd = "where" if platform.system() == "Windows" else "which"
            result = subprocess.run(
                [cmd, "nvcc"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]
        except Exception:
            pass

        return None

    def _get_cuda_version(self) -> str:
        """Ermittelt CUDA Version aus nvcc"""
        if not self.nvcc_path:
            return None

        try:
            result = subprocess.run(
                [self.nvcc_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Parse: "release 12.1, V12.1.105"
                for line in result.stdout.split("\n"):
                    if "release" in line.lower():
                        parts = line.split("release")
                        if len(parts) > 1:
                            version = parts[1].strip().split(",")[0].strip()
                            return version
        except Exception as e:
            print(f"⚠️  Fehler beim Ermitteln der CUDA Version: {e}")

        return None

    def _check_torch_cuda(self) -> bool:
        """Prüft ob PyTorch mit CUDA verfügbar ist"""
        try:
            import torch
            if torch.cuda.is_available():
                self.cuda_version = torch.version.cuda
                return True
        except ImportError:
            pass
        return False

    def install_llama_cpp(self) -> bool:
        """Installiert llama-cpp-python mit oder ohne CUDA"""
        print("\n📦 Installiere llama-cpp-python...")

        # Basis-Command
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade"]

        if self.cuda_available and self.cuda_version:
            print(f"🚀 Baue mit CUDA {self.cuda_version} Support...")

            # CMAKE Args für CUDA
            cuda_major = int(self.cuda_version.split(".")[0])

            if cuda_major >= 12:
                cmake_args = "-DLLAMA_CUDA=on"
            elif cuda_major == 11:
                cmake_args = "-DLLAMA_CUBLAS=on"
            else:
                print(f"⚠️  CUDA {self.cuda_version} wird möglicherweise nicht unterstützt")
                cmake_args = "-DLLAMA_CUBLAS=on"

            # Environment Variable setzen
            env = os.environ.copy()
            env["CMAKE_ARGS"] = cmake_args

            # CUDA Pfad hinzufügen falls vorhanden
            if self.cuda_home:
                env["CUDA_HOME"] = self.cuda_home
                env["CUDA_PATH"] = self.cuda_home

            cmd.extend(["llama-cpp-python", "--force-reinstall", "--no-cache-dir"])

            try:
                print(f"   CMAKE_ARGS={cmake_args}")
                print(f"   Command: {' '.join(cmd)}")
                print("   (Das kann 5-15 Minuten dauern...)\n")

                result = subprocess.run(
                    cmd,
                    env=env,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                # Erfolgs-Check
                if "Successfully installed" in result.stdout:
                    print("✅ llama-cpp-python mit CUDA Support installiert!")
                    return True
                else:
                    print("⚠️  Installation abgeschlossen, aber Status unklar")
                    print("   Prüfe Installation mit: python -c 'from llama_cpp import Llama'")
                    return True

            except subprocess.CalledProcessError as e:
                print(f"❌ CUDA Build fehlgeschlagen: {e}")
                print("   Ausgabe:")
                print(e.stdout if hasattr(e, 'stdout') else '')
                print("\n⚠️  Versuche CPU-Installation als Fallback...")
                # Fallback zu CPU
                return self._install_cpu_version()

        else:
            # CPU-Version installieren
            return self._install_cpu_version()

    def _install_cpu_version(self) -> bool:
        """Installiert llama-cpp-python CPU-Version"""
        print("🔧 Installiere CPU-Version von llama-cpp-python...")

        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "llama-cpp-python",
        ]

        try:
            subprocess.run(cmd, check=True)
            print("✅ llama-cpp-python (CPU) installiert")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ CPU Installation fehlgeschlagen: {e}")
            return False

    def verify_installation(self) -> bool:
        """Verifiziert dass llama-cpp-python funktioniert"""
        print("\n🔍 Verifiziere Installation...")

        try:
            from llama_cpp import Llama

            print("✅ llama-cpp-python erfolgreich importiert")

            # Prüfe CUDA Support
            if self.cuda_available:
                try:
                    # Test ob CUDA-Build funktioniert
                    import torch
                    if torch.cuda.is_available():
                        gpu_count = torch.cuda.device_count()
                        print(f"✅ CUDA Support aktiv ({gpu_count} GPU(s) verfügbar)")
                        for i in range(gpu_count):
                            gpu_name = torch.cuda.get_device_name(i)
                            print(f"   GPU {i}: {gpu_name}")
                    else:
                        print("⚠️  PyTorch findet keine CUDA GPUs")
                except Exception as e:
                    print(f"⚠️  CUDA Check fehlgeschlagen: {e}")

            return True

        except ImportError as e:
            print(f"❌ Import fehlgeschlagen: {e}")
            return False

    def print_summary(self):
        """Gibt Setup-Zusammenfassung aus"""
        print("\n" + "=" * 60)
        print("📊 CUDA Setup Zusammenfassung")
        print("=" * 60)
        print(f"CUDA verfügbar:    {'✅ Ja' if self.cuda_available else '❌ Nein'}")
        if self.cuda_version:
            print(f"CUDA Version:      {self.cuda_version}")
        if self.cuda_home:
            print(f"CUDA_HOME:         {self.cuda_home}")
        if self.nvcc_path:
            print(f"nvcc Pfad:         {self.nvcc_path}")
        print(f"llama-cpp Modus:   {'🚀 GPU' if self.cuda_available else '🔧 CPU'}")
        print("=" * 60)

        if not self.cuda_available:
            print("\n💡 CUDA Installation (optional für bessere Performance):")
            print("   1. NVIDIA GPU Treiber: https://www.nvidia.com/drivers")
            print("   2. CUDA Toolkit: https://developer.nvidia.com/cuda-downloads")
            print("   3. Setup erneut ausführen: python scripts/setup_cuda.py")
            print()


def main():
    """Hauptfunktion"""
    print("\n" + "=" * 60)
    print("🚀 JarvisCore - Automatisches CUDA Setup")
    print("=" * 60)

    setup = CUDASetup()

    # 1. CUDA erkennen
    setup.detect_cuda()

    # 2. llama-cpp-python installieren
    success = setup.install_llama_cpp()

    if success:
        # 3. Verifizieren
        setup.verify_installation()

    # 4. Zusammenfassung
    setup.print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
