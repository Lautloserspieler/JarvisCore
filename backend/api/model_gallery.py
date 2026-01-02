from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from services import model_gallery

router = APIRouter(prefix="/api/models", tags=["models"])


class ProgressBroadcaster:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            connections = list(self._connections)
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except WebSocketDisconnect:
                await self.disconnect(websocket)
            except RuntimeError:
                await self.disconnect(websocket)


progress_broadcaster = ProgressBroadcaster()


def _serialize_model(model: Any) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


async def _progress_callback(
    model_id: str, progress: float | None, downloaded: int, total: int | None
) -> None:
    await progress_broadcaster.broadcast(
        {
            "model_id": model_id,
            "progress": progress,
            "downloaded": downloaded,
            "total": total,
        }
    )


@router.get("/gallery")
async def get_gallery() -> dict:
    gallery = model_gallery.fetch_gallery()
    return _serialize_model(gallery)


@router.get("/gallery/search")
async def search_gallery(
    query: str | None = None,
    category: str | None = None,
    language: str | None = None,
    min_rating: float | None = None,
    min_size_gb: float | None = None,
    max_size_gb: float | None = None,
) -> list[dict]:
    gallery = model_gallery.fetch_gallery()
    results = model_gallery.search_models(
        gallery,
        query=query,
        category=category,
        language=language,
        min_rating=min_rating,
        min_size_gb=min_size_gb,
        max_size_gb=max_size_gb,
    )
    return [_serialize_model(model) for model in results]


@router.post("/gallery/{model_id}/install")
async def install_model(model_id: str) -> dict:
    gallery = model_gallery.fetch_gallery()
    if not any(model.id == model_id for model in gallery.models):
        raise HTTPException(status_code=404, detail="Modell nicht gefunden")
    model_gallery.schedule_download(
        model_id, gallery=gallery, progress_callback=_progress_callback
    )
    return {"status": "started", "model_id": model_id}


@router.get("/installed")
async def get_installed_models() -> list[dict]:
    return model_gallery.get_installed_models()


@router.delete("/{model_id}")
async def delete_model(model_id: str) -> dict:
    registry_entry = model_gallery.get_registered_model(model_id)
    removed = model_gallery.remove_registered_model(model_id)
    deleted = model_gallery.delete_model_file(model_id)
    if not registry_entry and not deleted:
        raise HTTPException(status_code=404, detail="Modell nicht gefunden")
    return {
        "model_id": model_id,
        "registry_removed": removed is not None,
        "file_deleted": deleted,
    }


@router.websocket("/ws/progress")
async def progress_ws(websocket: WebSocket) -> None:
    await progress_broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await progress_broadcaster.disconnect(websocket)
