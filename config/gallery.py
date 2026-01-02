from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib import error, request

from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator


LOGGER = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_GALLERY_PATH = REPO_ROOT / "config" / "models_gallery.json"
CACHE_PATH = REPO_ROOT / "cache" / "gallery_cache.json"
DEFAULT_CACHE_TTL = timedelta(days=1)


class GalleryError(RuntimeError):
    """Base error for gallery loading issues."""


class GalleryValidationError(GalleryError):
    """Raised when gallery data fails validation."""


class GalleryDownloadError(GalleryError):
    """Raised when downloading gallery data fails."""


class GalleryCacheError(GalleryError):
    """Raised when cache data is invalid or unusable."""


class HardwareSpec(BaseModel):
    cpu: str
    gpu: str
    ramGb: int = Field(..., ge=1)
    vramGb: int = Field(..., ge=0)


class ModelMetadata(BaseModel):
    id: str = Field(..., min_length=1)
    name: str
    categories: list[str] = Field(..., min_length=1)
    checksum: str
    downloadUrl: HttpUrl
    languages: list[str] = Field(..., min_length=1)
    recommendedHardware: HardwareSpec
    parameters: str
    sizeGb: float = Field(..., gt=0)
    rating: float = Field(..., ge=0, le=5)
    license: str
    description: str
    tags: list[str] = Field(default_factory=list)
    quantization: str
    contextLength: int = Field(..., ge=1)
    updatedAt: str

    @field_validator("categories", "languages", "tags")
    @classmethod
    def no_empty_strings(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("Listen dürfen keine leeren Strings enthalten.")
        return values


class GalleryPayload(BaseModel):
    version: str
    generatedAt: str
    models: list[ModelMetadata]

    @field_validator("models")
    @classmethod
    def unique_ids(cls, models: list[ModelMetadata]) -> list[ModelMetadata]:
        ids = [model.id for model in models]
        if len(ids) != len(set(ids)):
            raise ValueError("Doppelte Modell-IDs sind nicht erlaubt.")
        return models


@dataclass(frozen=True)
class GalleryCache:
    cached_at: datetime
    payload: dict


def load_gallery(
    *,
    cdn_url: str | None = None,
    use_cache: bool = True,
    cache_ttl: timedelta = DEFAULT_CACHE_TTL,
) -> GalleryPayload:
    if use_cache:
        cached = _load_cache()
        if cached and _is_cache_valid(cached.cached_at, cache_ttl):
            return _parse_payload(cached.payload)

    payload: dict | None = None

    if cdn_url:
        try:
            payload = _load_from_cdn(cdn_url)
        except GalleryDownloadError:
            LOGGER.exception("Fehler beim Laden der Gallery vom CDN: %s", cdn_url)

    if payload is None:
        payload = _load_from_file(LOCAL_GALLERY_PATH)

    gallery = _parse_payload(payload)
    _write_cache(payload)
    return gallery


def search_models(models: Iterable[ModelMetadata], query: str) -> list[ModelMetadata]:
    query_lower = query.strip().lower()
    if not query_lower:
        return list(models)
    results = []
    for model in models:
        haystack = " ".join(
            [model.id, model.name, model.description, " ".join(model.tags)]
        ).lower()
        if query_lower in haystack:
            results.append(model)
    return results


def filter_by_category(
    models: Iterable[ModelMetadata], category: str
) -> list[ModelMetadata]:
    category_lower = category.strip().lower()
    return [
        model
        for model in models
        if any(cat.lower() == category_lower for cat in model.categories)
    ]


def filter_by_language(
    models: Iterable[ModelMetadata], language: str
) -> list[ModelMetadata]:
    language_lower = language.strip().lower()
    return [
        model
        for model in models
        if any(lang.lower() == language_lower for lang in model.languages)
    ]


def filter_by_rating(
    models: Iterable[ModelMetadata], min_rating: float
) -> list[ModelMetadata]:
    return [model for model in models if model.rating >= min_rating]


def filter_by_size(
    models: Iterable[ModelMetadata], *, min_size_gb: float | None = None, max_size_gb: float | None = None
) -> list[ModelMetadata]:
    filtered = []
    for model in models:
        if min_size_gb is not None and model.sizeGb < min_size_gb:
            continue
        if max_size_gb is not None and model.sizeGb > max_size_gb:
            continue
        filtered.append(model)
    return filtered


def query_models(
    gallery: GalleryPayload,
    *,
    query: str | None = None,
    category: str | None = None,
    language: str | None = None,
    min_rating: float | None = None,
    min_size_gb: float | None = None,
    max_size_gb: float | None = None,
) -> list[ModelMetadata]:
    results: Iterable[ModelMetadata] = gallery.models
    if query:
        results = search_models(results, query)
    if category:
        results = filter_by_category(results, category)
    if language:
        results = filter_by_language(results, language)
    if min_rating is not None:
        results = filter_by_rating(results, min_rating)
    if min_size_gb is not None or max_size_gb is not None:
        results = filter_by_size(results, min_size_gb=min_size_gb, max_size_gb=max_size_gb)
    return list(results)


def _load_from_file(path: Path) -> dict:
    if not path.exists():
        raise GalleryError(f"Lokale Gallery-Datei fehlt: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        LOGGER.exception("Ungültiges JSON in %s", path)
        raise GalleryValidationError(f"Ungültiges JSON in {path}: {exc}") from exc


def _load_from_cdn(cdn_url: str) -> dict:
    try:
        with request.urlopen(cdn_url, timeout=10) as response:
            if response.status >= 400:
                raise GalleryDownloadError(
                    f"CDN-Antwortstatus {response.status} für {cdn_url}"
                )
            return json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError) as exc:
        raise GalleryDownloadError(f"CDN konnte nicht geladen werden: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise GalleryValidationError(f"Ungültiges JSON vom CDN: {exc}") from exc


def _parse_payload(payload: dict) -> GalleryPayload:
    try:
        return GalleryPayload.model_validate(payload)
    except ValidationError as exc:
        LOGGER.exception("Gallery-Daten sind ungültig")
        raise GalleryValidationError(str(exc)) from exc


def _load_cache() -> GalleryCache | None:
    if not CACHE_PATH.exists():
        return None
    try:
        raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        cached_at = _parse_datetime(raw.get("cachedAt"))
        payload = raw.get("payload")
        if cached_at is None or not isinstance(payload, dict):
            raise GalleryCacheError("Cache enthält ungültige Felder.")
        return GalleryCache(cached_at=cached_at, payload=payload)
    except (json.JSONDecodeError, GalleryCacheError) as exc:
        LOGGER.warning("Cache ignoriert: %s", exc)
        return None


def _write_cache(payload: dict) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cache_payload = {
            "cachedAt": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        CACHE_PATH.write_text(
            json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        LOGGER.error("Cache konnte nicht geschrieben werden: %s", exc)


def _is_cache_valid(cached_at: datetime, ttl: timedelta) -> bool:
    return datetime.now(timezone.utc) - cached_at <= ttl


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None
