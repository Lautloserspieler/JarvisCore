"""FastAPI entry point for the crawler service."""

from __future__ import annotations

import atexit
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl, field_validator
import uvicorn

from .config import load_config
from .models import CrawlerJob
from .security_guard import SecurityGuard
from .worker import CrawlerWorker
from . import storage

app = FastAPI(title="Jarvis Crawler Service", version="0.1.0")

CONFIG = load_config()
storage.init_db(CONFIG.db_file)
GUARD = SecurityGuard(CONFIG)
WORKER = CrawlerWorker(CONFIG, GUARD)


@app.on_event("startup")
def _start_workers() -> None:
    WORKER.start()


@app.on_event("shutdown")
def _stop_workers() -> None:
    WORKER.stop()


class JobCreateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=120)
    start_urls: List[HttpUrl] = Field(..., min_length=1, max_length=10)
    max_pages: Optional[int] = Field(default=None, ge=1)
    max_depth: Optional[int] = Field(default=None, ge=0, le=5)

    @field_validator("start_urls")
    @classmethod
    def _normalize_urls(cls, value: List[HttpUrl]) -> List[str]:
        cleaned: List[str] = []
        for url in value or []:
            try:
                cleaned.append(str(url).strip())
            except Exception:
                continue
        return cleaned


class JobResponse(BaseModel):
    job_id: int


class JobStatusResponse(BaseModel):
    job_id: int
    topic: str
    status: str
    processed_pages: int
    max_pages: int
    max_depth: int
    created_at: datetime

    @classmethod
    def from_job(cls, job: CrawlerJob) -> "JobStatusResponse":
        return cls(
            job_id=job.id,
            topic=job.topic,
            status=job.status,
            processed_pages=job.processed_pages,
            max_pages=job.max_pages,
            max_depth=job.max_depth,
            created_at=job.created_at,
        )


class DocumentAckRequest(BaseModel):
    ids: List[int]


def verify_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    """Validates the API key header if a key is configured.

    The header stays optional when no API key is set in the config to keep
    the service usable in trusted local setups.
    """
    if not CONFIG.api_key:
        return
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    if x_api_key != CONFIG.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@app.post("/jobs", response_model=JobResponse)
def create_job(request: JobCreateRequest, _: None = Depends(verify_api_key)):
    max_pages = min(request.max_pages or CONFIG.max_pages_per_job, CONFIG.max_pages_per_job)
    max_depth = min(request.max_depth or CONFIG.max_depth, CONFIG.max_depth)
    job = storage.create_job(request.topic.strip(), request.start_urls, max_pages, max_depth)
    WORKER.enqueue_job(job)
    return JobResponse(job_id=job.id)


@app.get("/jobs", response_model=List[JobStatusResponse])
def list_jobs(status_filter: Optional[str] = Query(default=None, alias="status"), _: None = Depends(verify_api_key)):
    jobs = storage.list_jobs(status_filter)
    return [JobStatusResponse.from_job(job) for job in jobs]


@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: int, _: None = Depends(verify_api_key)):
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse.from_job(job)


@app.get("/results")
def get_results(since: Optional[str] = Query(default=None), _: None = Depends(verify_api_key)):
    since_ts = None
    if since:
        try:
            since_ts = datetime.fromisoformat(since)
        except ValueError:
            try:
                since_ts = datetime.fromtimestamp(float(since))
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid 'since' parameter: {exc}") from exc
    documents = storage.get_unsynced_documents(since_ts)
    return [
        {
            "id": doc.id,
            "job_id": doc.job_id,
            "url": doc.url,
            "title": doc.title,
            "text": doc.text,
            "lang": doc.lang,
            "domain": doc.domain,
            "created_at": int(doc.created_at.timestamp()),
            "crawl_topic": doc.crawl_topic,
        }
        for doc in documents
    ]


@app.post("/results/ack")
def ack_results(request: DocumentAckRequest, _: None = Depends(verify_api_key)):
    updated = storage.mark_documents_synced(request.ids)
    return {"updated": updated}


@app.post("/control/pause")
def pause_workers(_: None = Depends(verify_api_key)):
    WORKER.pause()
    return {"status": "paused"}


@app.post("/control/resume")
def resume_workers(_: None = Depends(verify_api_key)):
    WORKER.resume()
    return {"status": "running"}


@app.get("/health")
def health_check():
    return {"status": "ok", "workers": len(WORKER.threads)}


def _cleanup() -> None:
    WORKER.stop()


atexit.register(_cleanup)


if __name__ == "__main__":
    uvicorn.run(
        "services.crawler_service.main:app",
        host=CONFIG.listen_host,
        port=CONFIG.listen_port,
        reload=False,
        log_level="info",
    )
