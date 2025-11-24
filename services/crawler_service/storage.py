"""SQLite storage helpers for the crawler service."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .models import CrawledDocument, CrawlerJob, JobStatus

DB_PATH: Optional[Path] = None
_LOCK = threading.Lock()


def init_db(db_path: Path) -> None:
    """Initialise database and store the global path reference."""
    global DB_PATH
    DB_PATH = Path(db_path)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            start_urls TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            max_pages INTEGER NOT NULL DEFAULT 0,
            max_depth INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            processed_pages INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            text TEXT,
            lang TEXT,
            domain TEXT,
            created_at TEXT NOT NULL,
            synced INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            UNIQUE(job_id, url)
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_synced ON documents (synced, created_at)")
    conn.commit()
    conn.close()


def _get_conn() -> sqlite3.Connection:
    if DB_PATH is None:
        raise RuntimeError("init_db must be called before accessing the crawler database")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_job(topic: str, start_urls: Sequence[str], max_pages: int, max_depth: int) -> CrawlerJob:
    payload = json.dumps([url.strip() for url in start_urls if url])
    created_at = datetime.utcnow().isoformat()
    with _LOCK:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO jobs (topic, start_urls, status, max_pages, max_depth, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (topic, payload, JobStatus.PENDING, max_pages, max_depth, created_at),
        )
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
    job_row = {
        "id": job_id,
        "topic": topic,
        "start_urls": payload,
        "status": JobStatus.PENDING,
        "max_pages": max_pages,
        "max_depth": max_depth,
        "created_at": created_at,
        "processed_pages": 0,
    }
    return CrawlerJob.from_row(job_row)


def update_job_status(job_id: int, *, status: Optional[str] = None, processed_pages: Optional[int] = None) -> None:
    if status is None and processed_pages is None:
        return
    fields = []
    values = []
    if status is not None:
        fields.append("status = ?")
        values.append(status)
    if processed_pages is not None:
        fields.append("processed_pages = ?")
        values.append(processed_pages)
    values.append(job_id)
    with _LOCK:
        conn = _get_conn()
        conn.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        conn.close()


def increment_processed_pages(job_id: int, delta: int = 1) -> int:
    with _LOCK:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET processed_pages = processed_pages + ? WHERE id = ?", (delta, job_id))
        conn.commit()
        cursor.execute("SELECT processed_pages FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
    conn.close()
    if not row:
        return 0
    return int(row["processed_pages"])


def get_job(job_id: int) -> Optional[CrawlerJob]:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return CrawlerJob.from_row(row)


def list_jobs(status: Optional[str] = None) -> List[CrawlerJob]:
    conn = _get_conn()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC", (status,))
    else:
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [CrawlerJob.from_row(dict(row)) for row in rows]


def add_document(
    job_id: int,
    url: str,
    title: str,
    text: str,
    lang: str,
    domain: str,
    created_at: Optional[datetime] = None,
) -> Optional[int]:
    created_ts = (created_at or datetime.utcnow()).isoformat()
    try:
        with _LOCK:
            conn = _get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO documents (job_id, url, title, text, lang, domain, created_at, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (job_id, url, title, text, lang, domain, created_ts),
            )
            doc_id = cursor.lastrowid
            conn.commit()
            conn.close()
        return doc_id or None
    except sqlite3.Error:
        return None


def get_unsynced_documents(since_timestamp: Optional[datetime] = None) -> List[CrawledDocument]:
    conn = _get_conn()
    cursor = conn.cursor()
    query = (
        "SELECT documents.*, jobs.topic FROM documents "
        "JOIN jobs ON documents.job_id = jobs.id "
        "WHERE documents.synced = 0"
    )
    params: List[object] = []
    if since_timestamp is not None:
        query += " AND datetime(documents.created_at) >= datetime(?)"
        params.append(since_timestamp.isoformat())
    query += " ORDER BY documents.created_at ASC LIMIT 500"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [CrawledDocument.from_row(dict(row)) for row in rows]


def mark_documents_synced(doc_ids: Iterable[int]) -> int:
    ids = [int(_id) for _id in doc_ids if int(_id)]
    if not ids:
        return 0
    placeholders = ",".join("?" for _ in ids)
    with _LOCK:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE documents SET synced = 1 WHERE id IN ({placeholders})", ids)
        updated = cursor.rowcount
        conn.commit()
        conn.close()
    return updated
