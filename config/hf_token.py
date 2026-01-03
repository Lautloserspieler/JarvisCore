from __future__ import annotations

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATH = PROJECT_ROOT / "config" / "hf_token.json"


def load_token() -> str | None:
    if not TOKEN_PATH.exists():
        return None
    try:
        with TOKEN_PATH.open("r", encoding="utf-8") as file_handle:
            payload = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        return None
    token = str(payload.get("token", "")).strip()
    return token or None


def save_token(token: str) -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TOKEN_PATH.open("w", encoding="utf-8") as file_handle:
        json.dump({"token": token}, file_handle, indent=2)
    try:
        os.chmod(TOKEN_PATH, 0o600)
    except OSError:
        pass


def delete_token() -> None:
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
