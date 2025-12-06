#!/usr/bin/env python3
"""
Bootstrap-Skript für JarvisCore.

Automatisiert:
    - Erzeugt bei Bedarf die virtuelle Umgebung.
    - Führt scripts/setup_env.py (inkl. CUDA/CPU-Option) aus.
    - Startet JarvisCore optional direkt.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = REPO_ROOT / "venv"
SETUP_SCRIPT = REPO_ROOT / "scripts" / "setup_env.py"
MAIN_SCRIPT = REPO_ROOT / "main.py"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _run(cmd: list[str | Path], *, cwd: Path | None = None) -> None:
    display = " ".join(str(part) for part in cmd)
    print(f"[bootstrap] > {display}")
    subprocess.check_call([str(part) for part in cmd], cwd=str(cwd) if cwd else None)


def ensure_python_version() -> None:
    if sys.version_info < (3, 11):
        raise SystemExit(
            "[bootstrap] Fehler: Python 3.11+ wird benötigt. "
            "Bitte installiere eine aktuelle 64-bit Version."
        )


def create_or_reset_venv(recreate: bool) -> None:
    if recreate and VENV_DIR.exists():
        print("[bootstrap] Entferne bestehende virtuelle Umgebung …")
        shutil.rmtree(VENV_DIR)
    if not VENV_DIR.exists():
        print("[bootstrap] Erzeuge virtuelle Umgebung …")
        _run([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print("[bootstrap] Virtuelle Umgebung bereits vorhanden – überspringe.")


def run_setup(venv_python: Path, cpu_only: bool) -> None:
    if not SETUP_SCRIPT.exists():
        raise SystemExit(f"[bootstrap] Fehler: {SETUP_SCRIPT} nicht gefunden.")
    cmd = [venv_python, str(SETUP_SCRIPT)]
    if cpu_only:
        cmd.append("--cpu")
    _run(cmd)


def launch_jarvis(venv_python: Path) -> None:
    if not MAIN_SCRIPT.exists():
        raise SystemExit(f"[bootstrap] Fehler: {MAIN_SCRIPT} nicht gefunden.")
    _run([venv_python, str(MAIN_SCRIPT)])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap JarvisCore mit einer Aktion.")
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Nur CPU-Builds von Torch/Torchaudio installieren (kein CUDA).",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="JarvisCore nach erfolgreicher Installation direkt starten.",
    )
    parser.add_argument(
        "--recreate-venv",
        action="store_true",
        help="Existierende virtuelle Umgebung vorher löschen und neu anlegen.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_python_version()
    create_or_reset_venv(recreate=args.recreate_venv)

    venv_python = _venv_python()
    if not venv_python.exists():
        raise SystemExit("[bootstrap] Fehler: Konnte Interpreter in der virtuellen Umgebung nicht finden.")

    run_setup(venv_python, cpu_only=args.cpu)

    if args.run:
        launch_jarvis(venv_python)
    else:
        print("[bootstrap] Fertig. Verwende 'venv\\Scripts\\activate' (Windows) oder 'source venv/bin/activate' (Unix),")
        print("[bootstrap] um JarvisCore manuell zu starten: python main.py")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"[bootstrap] Unterprozess schlug fehl (Exitcode {exc.returncode}).") from exc
