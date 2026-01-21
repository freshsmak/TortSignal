"""Database connection and helper functions."""

import json
import hashlib
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from src.config import get_config


def get_connection() -> psycopg.Connection:
    """Get a new database connection."""
    config = get_config()
    return psycopg.connect(config.database.url, row_factory=dict_row)


@contextmanager
def get_cursor() -> Generator[psycopg.Cursor, None, None]:
    """Context manager for database cursor with auto-commit."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def sha256_json(data: dict | list) -> str:
    """Compute SHA256 hash of JSON-serialized data."""
    raw = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# =============================================================================
# SOURCE DOCUMENTS
# =============================================================================


def upsert_source_document(
    cur: psycopg.Cursor,
    source_type: str,
    source_uid: str,
    title: str | None,
    published_at: datetime | None,
    retrieved_at: datetime,
    url: str | None,
    metadata: dict[str, Any],
    raw_payload: dict[str, Any] | None = None,
) -> UUID:
    """Upsert a source document and return its doc_id."""
    raw_hash = sha256_json(raw_payload) if raw_payload else None

    sql = """
    INSERT INTO source_documents
        (source_type, source_uid, title, published_at, retrieved_at, url, 
         raw_hash_sha256, metadata_json, raw_payload_json)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
    ON CONFLICT (source_type, source_uid)
    DO UPDATE SET
        title = COALESCE(EXCLUDED.title, source_documents.title),
        published_at = COALESCE(EXCLUDED.published_at, source_documents.published_at),
        retrieved_at = EXCLUDED.retrieved_at,
        url = COALESCE(EXCLUDED.url, source_documents.url),
        raw_hash_sha256 = COALESCE(EXCLUDED.raw_hash_sha256, source_documents.raw_hash_sha256),
        metadata_json = source_documents.metadata_json || EXCLUDED.metadata_json,
        raw_payload_json = COALESCE(EXCLUDED.raw_payload_json, source_documents.raw_payload_json)
    RETURNING doc_id;
    """
    cur.execute(
        sql,
        (
            source_type,
            source_uid,
            title,
            published_at,
            retrieved_at,
            url,
            raw_hash,
            json.dumps(metadata),
            json.dumps(raw_payload) if raw_payload else None,
        ),
    )
    row = cur.fetchone()
    return row["doc_id"]


# =============================================================================
# CANDIDATES
# =============================================================================


def upsert_candidate(
    cur: psycopg.Cursor,
    candidate_key: str,
    defendant_text: str,
    product_text: str,
    injury_text: str,
    first_seen_at: datetime,
    last_seen_at: datetime,
    metrics: dict[str, Any],
    score_total: float,
    score_components: dict[str, Any],
    why_now: str,
    category: str | None = None,
) -> UUID:
    """Upsert a candidate and return its candidate_id."""
    sql = """
    INSERT INTO candidates
        (candidate_key, defendant_text, product_text, injury_text,
         first_seen_at, last_seen_at, metrics_json, score_total, 
         score_components, why_now, category, status)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s, %s, 'new')
    ON CONFLICT (candidate_key)
    DO UPDATE SET
        last_seen_at = GREATEST(candidates.last_seen_at, EXCLUDED.last_seen_at),
        metrics_json = EXCLUDED.metrics_json,
        score_total = EXCLUDED.score_total,
        score_components = EXCLUDED.score_components,
        why_now = EXCLUDED.why_now,
        category = COALESCE(EXCLUDED.category, candidates.category)
    RETURNING candidate_id;
    """
    cur.execute(
        sql,
        (
            candidate_key,
            defendant_text,
            product_text,
            injury_text,
            first_seen_at,
            last_seen_at,
            json.dumps(metrics),
            float(score_total),
            json.dumps(score_components),
            why_now,
            category,
        ),
    )
    row = cur.fetchone()
    return row["candidate_id"]


def insert_candidate_evidence(
    cur: psycopg.Cursor,
    candidate_id: UUID,
    doc_id: UUID,
    event_type: str,
    snippet: str | None,
) -> None:
    """Insert a candidate evidence link (ignores duplicates)."""
    sql = """
    INSERT INTO candidate_evidence (candidate_id, doc_id, event_type, snippet)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (candidate_id, doc_id) DO NOTHING;
    """
    cur.execute(sql, (str(candidate_id), str(doc_id), event_type, snippet))


def upsert_candidate_rollup(
    cur: psycopg.Cursor,
    candidate_id: UUID,
    as_of_date: datetime,
    velocity_7d: int,
    velocity_28d: int,
    accel_ratio: float,
    breadth_states: int,
    breadth_firms: int,
) -> None:
    """Upsert a candidate daily rollup."""
    sql = """
    INSERT INTO candidate_rollups
        (candidate_id, as_of_date, velocity_7d, velocity_28d, 
         accel_ratio, breadth_states, breadth_firms)
    VALUES
        (%s, %s::date, %s, %s, %s, %s, %s)
    ON CONFLICT (candidate_id, as_of_date)
    DO UPDATE SET
        velocity_7d = EXCLUDED.velocity_7d,
        velocity_28d = EXCLUDED.velocity_28d,
        accel_ratio = EXCLUDED.accel_ratio,
        breadth_states = EXCLUDED.breadth_states,
        breadth_firms = EXCLUDED.breadth_firms;
    """
    cur.execute(
        sql,
        (
            str(candidate_id),
            as_of_date.date() if isinstance(as_of_date, datetime) else as_of_date,
            int(velocity_7d),
            int(velocity_28d),
            float(accel_ratio),
            int(breadth_states),
            int(breadth_firms),
        ),
    )


# =============================================================================
# INGEST TRACKING
# =============================================================================


def start_ingest_run(cur: psycopg.Cursor, connector: str) -> UUID:
    """Start a new ingest run and return its run_id."""
    sql = """
    INSERT INTO ingest_runs (connector, status)
    VALUES (%s, 'running')
    RETURNING run_id;
    """
    cur.execute(sql, (connector,))
    row = cur.fetchone()
    return row["run_id"]


def finish_ingest_run(
    cur: psycopg.Cursor,
    run_id: UUID,
    status: str,
    records_fetched: int,
    records_processed: int,
    records_errored: int,
    error_message: str | None = None,
) -> None:
    """Mark an ingest run as finished."""
    sql = """
    UPDATE ingest_runs
    SET finished_at = now(),
        status = %s,
        records_fetched = %s,
        records_processed = %s,
        records_errored = %s,
        error_message = %s
    WHERE run_id = %s;
    """
    cur.execute(
        sql,
        (status, records_fetched, records_processed, records_errored, error_message, str(run_id)),
    )


# =============================================================================
# QUERIES
# =============================================================================


def get_top_candidates(cur: psycopg.Cursor, limit: int = 20) -> list[dict]:
    """Get top candidates by score."""
    sql = """
    SELECT 
        candidate_id,
        candidate_key,
        defendant_text,
        product_text,
        injury_text,
        category,
        score_total,
        status,
        first_seen_at,
        last_seen_at,
        why_now,
        metrics_json
    FROM candidates
    WHERE status NOT IN ('rejected')
    ORDER BY score_total DESC
    LIMIT %s;
    """
    cur.execute(sql, (limit,))
    return cur.fetchall()


def get_candidate_evidence(cur: psycopg.Cursor, candidate_id: UUID) -> list[dict]:
    """Get all evidence for a candidate."""
    sql = """
    SELECT 
        e.event_type,
        e.snippet,
        e.created_at,
        d.source_type,
        d.source_uid,
        d.title,
        d.url,
        d.published_at
    FROM candidate_evidence e
    JOIN source_documents d ON d.doc_id = e.doc_id
    WHERE e.candidate_id = %s
    ORDER BY d.published_at DESC NULLS LAST;
    """
    cur.execute(sql, (str(candidate_id),))
    return cur.fetchall()
