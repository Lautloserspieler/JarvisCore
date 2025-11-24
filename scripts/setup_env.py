#!/usr/bin/env python3
"""
Setzt die Python-Umgebung fuer JarvisCore auf.

Schritte:
 1. pip aktualisieren
 2. CUDA 12.1 Wheels fuer Torch/Torchaudio/Torchvision installieren (oder CPU-Fallback)
 3. Binary Wheel fuer llama-cpp-python (cu121) installieren
 4. Binary Wheel fuer TTS installieren (wenn verfuegbar; pyttsx3 bleibt Fallback)
 5. Restliche Pakete aus requirements.txt installieren
 6. pip check

Aufruf:
    python scripts/setup_env.py          # CUDA (Standard)
    python scripts/setup_env.py --cpu    # nur CPU-Builds fuer Torch
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_FILE = REPO_ROOT / "requirements.txt"

# Torch CUDA 12.1 Wheels
TORCH_CUDA_VERSION = "2.1.1+cu121"
TORCHAUDIO_CUDA_VERSION = "2.1.1+cu121"
TORCHVISION_CUDA_VERSION = "0.16.1+cu121"
CUDA_INDEX_URL = "https://download.pytorch.org/whl/cu121"

# CPU Fallback
TORCH_CPU_VERSION = "2.1.1"

# llama-cpp-python Binary Wheels (cu121) from abetlen index
LLAMA_CPP_VERSION = "0.3.4"
LLAMA_CPP_INDEX_URL = "https://abetlen.github.io/llama-cpp-python/whl/cu121"

# TTS Binary Wheel (PyPI provides wheels)
TTS_VERSION = "0.22.0"
TTS_SPEC = f"TTS=={TTS_VERSION}"


def run_pip(args: list[str]) -> None:
    """Fuehrt pip synchron aus."""
    subprocess.check_call([sys.executable, "-m", "pip", *args])


def install_torch(cuda: bool) -> None:
    """Installiert Torch-Stack bevorzugt als CUDA-Wheels, sonst CPU."""
    installed_cuda = False
    if cuda:
        specs = [
            f"torch=={TORCH_CUDA_VERSION}",
            f"torchaudio=={TORCHAUDIO_CUDA_VERSION}",
            f"torchvision=={TORCHVISION_CUDA_VERSION}",
        ]
        print(f"[setup] Installiere Torch CUDA {TORCH_CUDA_VERSION} ...", flush=True)
        try:
            run_pip(["install", "--extra-index-url", CUDA_INDEX_URL, "--only-binary=:all:", *specs])
            installed_cuda = True
        except subprocess.CalledProcessError as exc:
            print(f"[setup] CUDA-Wheels fehlgeschlagen ({exc}); nutze CPU-Fallback.", flush=True)

    if not installed_cuda:
        specs = [
            f"torch=={TORCH_CPU_VERSION}",
            f"torchaudio=={TORCH_CPU_VERSION}",
        ]
        print(f"[setup] Installiere Torch CPU {TORCH_CPU_VERSION} ...", flush=True)
        run_pip(["install", "--only-binary=:all:", *specs])

    # Torch 2.1.x bringt ggf. numpy >=2 mit; downgraden wir auf 1.26.x fuer Kompatibilitaet.
    print("[setup] Erzwinge numpy 1.26.x fuer Kompatibilitaet ...", flush=True)
    run_pip(["install", "--only-binary=:all:", "numpy==1.26.4"])


def install_llama_cpp() -> None:
    """Installiert llama-cpp-python als Binary-Wheel (cu121)."""
    print(f"[setup] Installiere llama-cpp-python {LLAMA_CPP_VERSION} (Binary cu121) ...", flush=True)
    run_pip(
        [
            "install",
            "--extra-index-url",
            LLAMA_CPP_INDEX_URL,
            "--only-binary=:all:",
            f"llama-cpp-python=={LLAMA_CPP_VERSION}",
        ]
    )


def install_tts_binary() -> None:
    """Installiert TTS bevorzugt als Binary-Wheel. Bei Fehlschlag bleibt pyttsx3 als Fallback."""
    print(f"[setup] Installiere TTS {TTS_VERSION} (Binary) ...", flush=True)
    try:
        run_pip(["install", "--only-binary=:all:", TTS_SPEC])
    except subprocess.CalledProcessError as exc:
        print(f"[setup] TTS Binary fehlgeschlagen ({exc}); bitte spaeter manuell installieren. pyttsx3 bleibt aktiv.", flush=True)


def install_requirements(requirements: Path) -> None:
    if not requirements.exists():
        print(f"[setup] Keine requirements.txt unter {requirements} gefunden – ueberspringe.", flush=True)
        return
    print(f"[setup] Installiere restliche Pakete aus {requirements} ...", flush=True)
    run_pip(["install", "--prefer-binary", "--no-build-isolation", "-r", str(requirements)])


def run_health_check() -> None:
    print("[setup] Fuehre pip check aus ...", flush=True)
    run_pip(["check"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Installiert alle Abhaengigkeiten fuer JarvisCore.")
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Nur CPU-Builds von Torch/Torchaudio installieren (kein CUDA).",
    )
    parser.add_argument(
        "--requirements",
        default=str(REQUIREMENTS_FILE),
        help="Pfad zur requirements.txt (Standard: Projektdaten).",
    )
    args = parser.parse_args()

    os.chdir(REPO_ROOT)
    print(f"[setup] Repository-Root: {REPO_ROOT}", flush=True)

    if sys.version_info < (3, 11):
        print("[setup] Warnung: Bitte Python 3.11+ verwenden.", flush=True)

    print("[setup] Aktualisiere pip ...", flush=True)
    run_pip(["install", "--upgrade", "pip"])

    install_torch(cuda=not args.cpu)
    install_llama_cpp()
    install_tts_binary()
    install_requirements(Path(args.requirements))
    run_health_check()

    print("[setup] Installation abgeschlossen.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(f"[setup] Fehler: {error}.", file=sys.stderr)
        sys.exit(error.returncode)
