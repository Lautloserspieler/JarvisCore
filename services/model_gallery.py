from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Iterable, Protocol
from urllib.parse import urlsplit

import aiohttp

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.gallery import (
    GalleryPayload,
    ModelMetadata,
    load_gallery,
    query_models,
)

MODELS_DIR = PROJECT_ROOT / "models" / "llm"
REGISTRY_PATH = PROJECT_ROOT / "config" / "models.json"
CHUNK_SIZE_BYTES = 8192
DOWNLOAD_TIMEOUT_SECONDS = 3600

logger = logging.getLogger(__name__)


class ProgressCallback(Protocol):
    async def __call__(
        self,
        model_id: str,
        progress: float | None,
        downloaded: int,
        total: int | None,
        *,
        status: str | None = None,
        error_message: str | None = None,
    ) -> None: ...


def fetch_gallery(*, cdn_url: str | None = None, use_cache: bool = True) -> GalleryPayload:
    return load_gallery(cdn_url=cdn_url, use_cache=use_cache)


def search_models(
    gallery: GalleryPayload,
    *,
    query: str | None = None,
    category: str | None = None,
    language: str | None = None,
    min_rating: float | None = None,
    min_size_gb: float | None = None,
    max_size_gb: float | None = None,
) -> list[ModelMetadata]:
    return query_models(
        gallery,
        query=query,
        category=category,
        language=language,
        min_rating=min_rating,
        min_size_gb=min_size_gb,
        max_size_gb=max_size_gb,
    )


async def download_model(
    model_id: str,
    *,
    gallery: GalleryPayload,
    progress_callback: ProgressCallback | None = None,
    destination_dir: Path | None = None,
) -> dict:
    model = _get_model_metadata(gallery.models, model_id)
    if model is None:
        raise ValueError(f"Unbekanntes Modell: {model_id}")

    destination_dir = destination_dir or MODELS_DIR
    destination_dir.mkdir(parents=True, exist_ok=True)

    filename = _filename_from_url(str(model.downloadUrl), model_id)
    output_path = destination_dir / filename
    temp_path = output_path.with_suffix(output_path.suffix + ".part")

    if output_path.exists() and _verify_checksum(output_path, model.checksum):
        return register_model(model_id, output_path, model)

    if output_path.exists():
        output_path.unlink()

    if temp_path.exists():
        temp_path.unlink()

    if progress_callback:
        await progress_callback(model_id, 0.0, 0, None)

    timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(str(model.downloadUrl)) as response:
            response.raise_for_status()
            total = response.headers.get("Content-Length")
            total_bytes = int(total) if total and total.isdigit() else None
            downloaded = 0

            with temp_path.open("wb") as file_handle:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE_BYTES):
                    if not chunk:
                        continue
                    file_handle.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress = (
                            (downloaded / total_bytes) * 100
                            if total_bytes and total_bytes > 0
                            else None
                        )
                        await progress_callback(model_id, progress, downloaded, total_bytes)

    if not _verify_checksum(temp_path, model.checksum):
        temp_path.unlink(missing_ok=True)
        raise ValueError(f"Checksum-Prüfung fehlgeschlagen für {model_id}")

    temp_path.rename(output_path)
    result = register_model(model_id, output_path, model)
    if progress_callback:
        total_final = output_path.stat().st_size
        await progress_callback(model_id, 100.0, total_final, total_final)
    return result


def _verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    normalized_expected = expected_checksum.strip()
    if normalized_expected.lower().startswith("sha256:"):
        normalized_expected = normalized_expected[len("sha256:") :].strip()
    hasher = hashlib.sha256()
    with file_path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(CHUNK_SIZE_BYTES), b""):
            hasher.update(chunk)
    return hasher.hexdigest().lower() == normalized_expected.lower()


def register_model(model_id: str, file_path: Path, metadata: ModelMetadata) -> dict:
    registry = _load_registry()
    registry_entry = {
        "id": model_id,
        "name": metadata.name,
        "path": str(file_path),
        "size": file_path.stat().st_size,
        "installedAt": datetime.now(timezone.utc).isoformat(),
        "backend": "gallery",
        "active": False,
    }
    registry.setdefault("models", {})[model_id] = registry_entry
    _save_registry(registry)
    return registry_entry


def get_installed_models() -> list[dict]:
    registry = _load_registry()
    registry_models = registry.get("models", {})

    installed: list[dict] = []
    tracked_files = set()

    for model_id, entry in registry_models.items():
        file_path = Path(entry.get("path", ""))
        status = "installed" if file_path.exists() else "missing"
        entry_with_status = {**entry, "status": status}
        installed.append(entry_with_status)
        if file_path.exists():
            tracked_files.add(file_path.resolve())

    if MODELS_DIR.exists():
        for file_path in MODELS_DIR.iterdir():
            if not file_path.is_file():
                continue
            resolved = file_path.resolve()
            if resolved in tracked_files:
                continue
            installed.append(
                {
                    "id": file_path.stem,
                    "name": file_path.stem,
                    "path": str(file_path),
                    "status": "unregistered",
                    "size": file_path.stat().st_size,
                    "backend": "gallery",
                    "active": False,
                }
            )

    return installed


def _filename_from_url(url: str, fallback: str) -> str:
    name = Path(urlsplit(url).path).name
    return name or f"{fallback}.bin"


def _get_model_metadata(models: Iterable[ModelMetadata], model_id: str) -> ModelMetadata | None:
    for model in models:
        if model.id == model_id:
            return model
    return None


def _load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {"models": {}}
    with REGISTRY_PATH.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _save_registry(registry: dict) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("w", encoding="utf-8") as file_handle:
        json.dump(registry, file_handle, indent=2, ensure_ascii=False)


def remove_registered_model(model_id: str) -> dict | None:
    registry = _load_registry()
    models = registry.get("models", {})
    entry = models.pop(model_id, None)
    if entry is None:
        return None
    _save_registry(registry)
    return entry


def get_registered_model(model_id: str) -> dict | None:
    registry = _load_registry()
    return registry.get("models", {}).get(model_id)


def resolve_model_path(model_id: str) -> Path | None:
    entry = get_registered_model(model_id)
    if entry and entry.get("path"):
        return Path(entry["path"])
    candidate = MODELS_DIR / f"{model_id}.gguf"
    if candidate.exists():
        return candidate
    return None


def delete_model_file(model_id: str) -> bool:
    path = resolve_model_path(model_id)
    if path and path.exists():
        path.unlink()
        return True
    return False


def schedule_download(
    model_id: str,
    *,
    gallery: GalleryPayload,
    progress_callback: ProgressCallback | None = None,
) -> asyncio.Task:
    async def _task_wrapper() -> dict:
        try:
            return await download_model(
                model_id, gallery=gallery, progress_callback=progress_callback
            )
        except Exception as exc:
            logger.exception("Download fehlgeschlagen für %s: %s", model_id, exc)
            if progress_callback:
                try:
                    await progress_callback(
                        model_id,
                        None,
                        0,
                        None,
                        status="error",
                        error_message=str(exc),
                    )
                except Exception:
                    logger.exception(
                        "Fehler beim Melden des Download-Fehlers für %s", model_id
                    )
            return {
                "status": "error",
                "model_id": model_id,
                "error": str(exc),
            }

    return asyncio.create_task(_task_wrapper())
