from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Awaitable, Iterable, Protocol
from urllib import parse, request
from urllib.parse import urlsplit, urlunsplit

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
from config.hf_token import load_token as load_hf_token

MODELS_DIR = PROJECT_ROOT / "models" / "llm"
REGISTRY_PATH = PROJECT_ROOT / "config" / "models.json"
GALLERY_PATH = PROJECT_ROOT / "config" / "models_gallery.json"
CACHE_PATH = PROJECT_ROOT / "cache" / "gallery_cache.json"
CHUNK_SIZE_BYTES = 8192
DOWNLOAD_TIMEOUT_SECONDS = 3600

logger = logging.getLogger(__name__)
_ACTIVE_DOWNLOADS: dict[str, asyncio.Task] = {}
_ACTIVE_DOWNLOADS_LOCK = Lock()


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


def preflight_check_model(model_id: str, *, gallery: GalleryPayload) -> dict:
    model = _get_model_metadata(gallery.models, model_id)
    if model is None:
        return {"error": f"Modell {model_id} nicht in Gallery gefunden"}

    download_url = _resolve_download_url(model)
    gallery_checksum = _normalize_checksum(model.checksum)
    header_checksum = _fetch_header_checksum(download_url)
    hf_checksum = _fetch_hf_checksum(model, download_url)
    match = (
        hf_checksum is not None
        and gallery_checksum.lower() == hf_checksum.lower()
    )

    if not match:
        logger.warning(
            "Checksummen-Warnung für %s: Gallery=%s, Header=%s, HF=%s",
            model_id,
            gallery_checksum,
            header_checksum,
            hf_checksum,
        )

    return {
        "model_id": model_id,
        "download_url": download_url,
        "gallery_checksum": gallery_checksum,
        "header_checksum": header_checksum,
        "hf_checksum": hf_checksum,
        "match": match,
    }


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

    download_url = _resolve_download_url(model)
    fallback_url = _resolve_hf_fallback_url(model, download_url)
    url_candidates = [download_url]
    if fallback_url and fallback_url != download_url:
        url_candidates.append(fallback_url)
    active_url = url_candidates[0]
    filename = _filename_from_url(active_url, model_id)
    output_path = destination_dir / filename
    temp_path = output_path.with_suffix(output_path.suffix + ".part")

    if output_path.exists() and _verify_checksum(output_path, model.checksum):
        return register_model(model_id, output_path, model)

    if output_path.exists():
        output_path.unlink()

    if temp_path.exists():
        try:
            temp_path.unlink()
        except OSError:
            temp_path = output_path.with_suffix(
                f"{output_path.suffix}.{uuid.uuid4().hex}.part"
            )

    if progress_callback:
        await progress_callback(
            model_id,
            0.0,
            0,
            None,
            status="downloading",
        )

    timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_SECONDS)
    headers = _build_download_headers()
    async with aiohttp.ClientSession(timeout=timeout, auto_decompress=False) as session:
        response = None
        for index, candidate_url in enumerate(url_candidates):
            if index > 0:
                active_url = candidate_url
            response = await session.get(active_url, headers=headers)
            if response.status == 404 and index == 0 and len(url_candidates) > 1:
                await response.release()
                continue
            break

        if response is None:
            raise ValueError("Download-URL konnte nicht aufgelöst werden.")

        if response.status == 401:
            await response.release()
            raise ValueError(
                "Download erfordert einen HuggingFace-Token. "
                "Bitte Token in der Oberfläche speichern oder "
                "HF_TOKEN/HUGGING_FACE_HUB_TOKEN setzen."
            )

        if response.status == 404:
            await response.release()
            raise ValueError(
                "Download-Datei nicht gefunden (404). "
                "Bitte prüfe die Datei-URL in config/models_gallery.json."
            )

        response.raise_for_status()
        total = response.headers.get("Content-Length")
        total_bytes = int(total) if total and total.isdigit() else None
        downloaded = 0
        header_hash = _extract_header_hash(response.headers)

        hasher = hashlib.sha256()
        with temp_path.open("wb") as file_handle:
            async for chunk in response.content.iter_chunked(CHUNK_SIZE_BYTES):
                if not chunk:
                    continue
                file_handle.write(chunk)
                hasher.update(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress = (
                        (downloaded / total_bytes) * 100
                        if total_bytes and total_bytes > 0
                        else None
                    )
                    await progress_callback(
                        model_id,
                        progress,
                        downloaded,
                        total_bytes,
                        status="downloading",
                    )
        response.release()

    if total_bytes is not None and downloaded != total_bytes:
        temp_path.unlink(missing_ok=True)
        raise ValueError(
            "Download unvollständig für "
            f"{model_id} (erwartet {total_bytes} Bytes, erhalten {downloaded})"
        )

    normalized_expected = _normalize_checksum(model.checksum)
    downloaded_hash = hasher.hexdigest().lower()

    if downloaded_hash != normalized_expected.lower():
        hf_checksum = _fetch_hf_checksum(model, active_url)
        mismatch_details = []
        if header_hash:
            mismatch_details.append(f"Header={header_hash}")
        if hf_checksum:
            mismatch_details.append(f"HF={hf_checksum}")
        detail = (
            "Checksum-Prüfung fehlgeschlagen für "
            f"{model_id} (erwartet {normalized_expected}, erhalten {downloaded_hash})"
        )
        if mismatch_details:
            detail = f"{detail}. Weitere Quellen: {', '.join(mismatch_details)}"
        temp_path.unlink(missing_ok=True)
        raise ValueError(detail)

    temp_path.rename(output_path)
    result = register_model(model_id, output_path, model)
    if progress_callback:
        total_final = output_path.stat().st_size
        await progress_callback(
            model_id,
            100.0,
            total_final,
            total_final,
            status="completed",
        )
    return result


def _verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    normalized_expected = _normalize_checksum(expected_checksum)
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


def _resolve_download_url(model: ModelMetadata) -> str:
    url = str(model.downloadUrl)
    override_base = os.environ.get("JARVIS_GALLERY_CDN_BASE_URL")
    if override_base:
        override_parts = urlsplit(override_base)
        if not override_parts.scheme or not override_parts.netloc:
            raise ValueError(
                "JARVIS_GALLERY_CDN_BASE_URL muss ein vollstaendiger URL sein."
            )
        url_parts = urlsplit(url)
        url = urlunsplit(
            (
                override_parts.scheme,
                override_parts.netloc,
                url_parts.path,
                url_parts.query,
                url_parts.fragment,
            )
        )
    elif "cdn.jarviscore.example" in url:
        url = _resolve_bartowski_url(model)
        if url is None:
            raise ValueError(
                "Download-URL zeigt auf den Platzhalter cdn.jarviscore.example und "
                "kein passendes bartowski-Modell konnte ermittelt werden. "
                "Bitte setze echte URLs in config/models_gallery.json oder "
                "verwende JARVIS_GALLERY_CDN_BASE_URL."
            )
    return url


def _resolve_bartowski_url(model: ModelMetadata) -> str | None:
    query = model.name.strip()
    if not query:
        return None
    search_params = {
        "search": query,
        "author": "bartowski",
        "limit": "5",
    }
    search_url = f"https://huggingface.co/api/models?{parse.urlencode(search_params)}"
    try:
        with request.urlopen(search_url, timeout=10) as response:
            results = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("Bartowski-Suche fehlgeschlagen: %s", exc)
        return None

    if not results:
        return None

    repo_id = results[0].get("modelId")
    if not repo_id:
        return None

    repo_url = f"https://huggingface.co/api/models/{repo_id}"
    try:
        with request.urlopen(repo_url, timeout=10) as response:
            repo_payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("Bartowski-Repo konnte nicht geladen werden: %s", exc)
        return None

    siblings = repo_payload.get("siblings", [])
    gguf_files = [
        entry.get("rfilename")
        for entry in siblings
        if isinstance(entry, dict) and str(entry.get("rfilename", "")).endswith(".gguf")
    ]
    gguf_files = [name for name in gguf_files if name]
    if not gguf_files:
        return None

    quant_hint = model.quantization.replace("_", "").upper()
    param_hint = model.parameters.replace(" ", "").upper()
    preferred = []
    for name in gguf_files:
        upper_name = name.upper().replace("_", "")
        if quant_hint and quant_hint in upper_name:
            preferred.append(name)
        elif param_hint and param_hint in upper_name:
            preferred.append(name)

    chosen = preferred[0] if preferred else gguf_files[0]
    logger.info("Nutze bartowski-Download %s (%s)", repo_id, chosen)
    return f"https://huggingface.co/{repo_id}/resolve/main/{chosen}"


def _resolve_hf_fallback_url(model: ModelMetadata, download_url: str) -> str | None:
    if "huggingface.co" not in download_url or "/resolve/" not in download_url:
        return None

    parts = urlsplit(download_url).path.strip("/").split("/")
    if len(parts) < 3:
        return None
    repo_id = "/".join(parts[:2])
    filename = parts[-1]

    repo_url = f"https://huggingface.co/api/models/{repo_id}"
    try:
        with request.urlopen(repo_url, timeout=10) as response:
            repo_payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("HF-Repo konnte nicht geladen werden: %s", exc)
        return None

    siblings = repo_payload.get("siblings", [])
    gguf_files = [
        entry.get("rfilename")
        for entry in siblings
        if isinstance(entry, dict) and str(entry.get("rfilename", "")).endswith(".gguf")
    ]
    gguf_files = [name for name in gguf_files if name]
    if not gguf_files:
        return None

    if filename in gguf_files:
        return download_url

    quant_hint = model.quantization.replace("_", "").upper()
    param_hint = model.parameters.replace(" ", "").upper()
    preferred = []
    for name in gguf_files:
        upper_name = name.upper().replace("_", "")
        if quant_hint and quant_hint in upper_name:
            preferred.append(name)
        elif param_hint and param_hint in upper_name:
            preferred.append(name)

    chosen = preferred[0] if preferred else gguf_files[0]
    logger.info("HF-Fallback nutzt %s (%s)", repo_id, chosen)
    return f"https://huggingface.co/{repo_id}/resolve/main/{chosen}"


def _build_download_headers() -> dict[str, str]:
    hf_token = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        or load_hf_token()
    )
    if not hf_token:
        return {}
    return {"Authorization": f"Bearer {hf_token}"}


def _fetch_hf_checksum(model: ModelMetadata, download_url: str) -> str | None:
    if "huggingface.co" not in download_url:
        return None
    parts = urlsplit(download_url).path.strip("/").split("/")
    if len(parts) < 3:
        return None
    repo_id = "/".join(parts[:2])
    filename = parts[-1]
    params = parse.urlencode({"files_metadata": "1"})
    api_url = f"https://huggingface.co/api/models/{repo_id}?{params}"
    headers = {"User-Agent": "JarvisCore/1.0", **_build_download_headers()}
    try:
        req = request.Request(api_url, headers=headers)
        with request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("HF-Metadaten konnten nicht geladen werden: %s", exc)
        return None

    siblings = payload.get("siblings", [])
    match = next(
        (entry for entry in siblings if entry.get("rfilename") == filename), None
    )
    if not match:
        return None
    lfs = match.get("lfs") or {}
    oid = lfs.get("oid")
    if oid:
        return oid
    return None


def _fetch_header_checksum(download_url: str) -> str | None:
    if "huggingface.co" not in download_url:
        return None
    headers = {"User-Agent": "JarvisCore/1.0", **_build_download_headers()}
    try:
        req = request.Request(download_url, headers=headers, method="HEAD")
        with request.urlopen(req, timeout=20) as response:
            return _extract_header_hash(response.headers)
    except Exception as exc:
        logger.warning("Header-Checksumme konnte nicht geladen werden: %s", exc)
        return None


def _normalize_checksum(checksum: str) -> str:
    normalized = checksum.strip()
    if normalized.lower().startswith("sha256:"):
        normalized = normalized.split(":", 1)[1].strip()
    return normalized


def _extract_header_hash(headers: "aiohttp.typedefs.LooseHeaders") -> str | None:
    for key in ("X-Linked-ETag", "X-Checksum-Sha256", "ETag"):
        value = headers.get(key)
        if value:
            return str(value).strip('"')
    return None


def _update_gallery_checksum(model_id: str, sha256_hex: str) -> None:
    if not GALLERY_PATH.exists():
        return
    updated = False
    try:
        payload = json.loads(GALLERY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    models = payload.get("models")
    if isinstance(models, list):
        for entry in models:
            if isinstance(entry, dict) and entry.get("id") == model_id:
                entry["checksum"] = f"sha256:{sha256_hex}"
                updated = True
                break
    if updated:
        GALLERY_PATH.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        _update_cache_checksum(model_id, sha256_hex)


def _update_cache_checksum(model_id: str, sha256_hex: str) -> None:
    if not CACHE_PATH.exists():
        return
    try:
        cache_payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    payload = cache_payload.get("payload")
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return
    updated = False
    for entry in models:
        if isinstance(entry, dict) and entry.get("id") == model_id:
            entry["checksum"] = f"sha256:{sha256_hex}"
            updated = True
            break
    if updated:
        CACHE_PATH.write_text(
            json.dumps(cache_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


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
    with _ACTIVE_DOWNLOADS_LOCK:
        if model_id in _ACTIVE_DOWNLOADS:
            return _ACTIVE_DOWNLOADS[model_id]

    async def _task_wrapper() -> dict:
        try:
            return await download_model(
                model_id, gallery=gallery, progress_callback=progress_callback
            )
        except Exception as exc:
            logger.exception("Download fehlgeschlagen für %s", model_id)
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
            return {"error": str(exc), "model_id": model_id}
        finally:
            with _ACTIVE_DOWNLOADS_LOCK:
                _ACTIVE_DOWNLOADS.pop(model_id, None)

    task = asyncio.create_task(_task_wrapper())
    with _ACTIVE_DOWNLOADS_LOCK:
        _ACTIVE_DOWNLOADS[model_id] = task
    return task
