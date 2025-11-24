"""
Helper-Skript fuer Release-Vorbereitung.
Entfernt/ignoriert grosse Modelle, sensible Dateien und erstellt ein Minimal-Setup.
"""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REMOVE_PATHS = [
    "data/settings.json",
    "data/knowledge.db",
    "data/commands.json",
    "logs",
    "LocalWissen",
    "output",
    "reports",
    "backups",
]

MODEL_EXTS = {".gguf", ".bin", ".pt", ".onnx", ".safetensors"}


def remove_file(path: Path) -> None:
    try:
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    except Exception:
        pass


def clean_models(models_dir: Path) -> None:
    if not models_dir.exists():
        return
    for p in models_dir.rglob("*"):
        if p.suffix.lower() in MODEL_EXTS:
            remove_file(p)


def main() -> None:
    for rel in REMOVE_PATHS:
        remove_file(ROOT / rel)
    clean_models(ROOT / "models")
    print("Release-Bereinigung abgeschlossen. Bitte README/LICENCE pruefen und git status kontrollieren.")


if __name__ == "__main__":
    main()
