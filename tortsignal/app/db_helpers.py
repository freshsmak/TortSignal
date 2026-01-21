"""
Database Helper Functions for TortSignal Dashboard

Provides data access functions for the Streamlit frontend.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.db import get_cursor
    from src.config import get_config
    DB_AVAILABLE = True
except Exception as e:
    print(f"Database not available: {e}")
    DB_AVAILABLE = False


def get_quick_stats() -> dict:
    """
    Get quick stats for sidebar.

    Returns:
        Dictionary with total, high_conviction, new_7d counts
    """
    if not DB_AVAILABLE:
        return {'total': 0, 'high_conviction': 0, 'new_7d': 0}

    try:
        with get_cursor() as cur:
            # Total active candidates
            cur.execute("""
                SELECT COUNT(*)
                FROM candidates
                WHERE status != 'rejected'
            """)
            total = cur.fetchone()[0]

            # High conviction count
            cur.execute("""
                SELECT COUNT(*)
                FROM candidates
                WHERE status != 'rejected'
                  AND score_total >= 70
            """)
            high_conviction = cur.fetchone()[0]

            # New in last 7 days
            cur.execute("""
                SELECT COUNT(*)
                FROM candidates
                WHERE status != 'rejected'
                  AND created_at >= NOW() - INTERVAL '7 days'
            """)
            new_7d = cur.fetchone()[0]

            return {
                'total': total,
                'high_conviction': high_conviction,
                'new_7d': new_7d
            }

    except Exception as e:
        print(f"Error getting quick stats: {e}")
        return {'total': 0, 'high_conviction': 0, 'new_7d': 0}


def get_watchlist(filters: dict) -> pd.DataFrame:
    """
    Fetch candidates for the watchlist with filters applied.

    Args:
        filters: Dictionary with keys:
            - categories: List of category strings or None
            - stages: List of stage strings or None
            - min_score: Minimum score (int)
            - days: Number of days for date filter

    Returns:
        DataFrame with candidate data
    """
    if not DB_AVAILABLE:
        # Return sample data if DB not available
        return get_sample_watchlist()

    try:
        with get_cursor() as cur:
            # Build WHERE clause
            where_clauses = ["status != 'rejected'"]
            params = []

            if filters.get('categories'):
                where_clauses.append(f"category = ANY(%s)")
                params.append(filters['categories'])

            if filters.get('stages'):
                # Convert stage names to score ranges
                stage_conditions = []
                for stage in filters['stages']:
                    if stage == 'HIGH_CONVICTION':
                        stage_conditions.append("score_total >= 70")
                    elif stage == 'INVESTIGATE':
                        stage_conditions.append("(score_total >= 40 AND score_total < 70)")
                    elif stage == 'AWARENESS':
                        stage_conditions.append("(score_total >= 20 AND score_total < 40)")
                    elif stage == 'QUIET':
                        stage_conditions.append("score_total < 20")

                if stage_conditions:
                    where_clauses.append(f"({' OR '.join(stage_conditions)})")

            if filters.get('min_score', 0) > 0:
                where_clauses.append("score_total >= %s")
                params.append(filters['min_score'])

            if filters.get('days', 9999) < 9999:
                where_clauses.append("updated_at >= NOW() - INTERVAL '%s days'")
                params.append(filters['days'])

            where_sql = " AND ".join(where_clauses)

            # Execute query
            query = f"""
                SELECT
                    cluster_id,
                    defendant_text,
                    product_text,
                    injury_text,
                    score_total,
                    CASE
                        WHEN score_total >= 70 THEN 'HIGH_CONVICTION'
                        WHEN score_total >= 40 THEN 'INVESTIGATE'
                        WHEN score_total >= 20 THEN 'AWARENESS'
                        ELSE 'QUIET'
                    END as stage,
                    category,
                    updated_at as last_updated,
                    metrics->>'velocity_7d' as velocity_7d,
                    metrics->>'breadth_states' as breadth_states
                FROM candidates
                WHERE {where_sql}
                ORDER BY score_total DESC
                LIMIT 100
            """

            cur.execute(query, params)
            rows = cur.fetchall()

            # Convert to DataFrame
            df = pd.DataFrame(
                rows,
                columns=[
                    'cluster_id', 'defendant_text', 'product_text', 'injury_text',
                    'score_total', 'stage', 'category', 'last_updated',
                    'velocity_7d', 'breadth_states'
                ]
            )

            return df

    except Exception as e:
        print(f"Error getting watchlist: {e}")
        return get_sample_watchlist()


def get_dossier(cluster_id: str) -> dict:
    """
    Fetch full dossier data for a single candidate.

    Args:
        cluster_id: UUID of the candidate cluster

    Returns:
        Dictionary with candidate, timeline, evidence, injuries, metrics
    """
    if not DB_AVAILABLE:
        return get_sample_dossier()

    try:
        with get_cursor() as cur:
            # Fetch candidate
            cur.execute("""
                SELECT
                    cluster_id,
                    defendant_text,
                    product_text,
                    injury_text,
                    score_total,
                    score_components,
                    category,
                    status,
                    created_at as first_seen,
                    updated_at as last_updated,
                    metrics
                FROM candidates
                WHERE cluster_id = %s
            """, (cluster_id,))

            row = cur.fetchone()
            if not row:
                return None

            candidate = {
                'cluster_id': row[0],
                'defendant_text': row[1],
                'product_text': row[2],
                'injury_text': row[3],
                'score_total': row[4],
                'score_components': row[5] or {},
                'category': row[6],
                'status': row[7],
                'first_seen': row[8].strftime('%Y-%m-%d') if row[8] else 'N/A',
                'last_updated': row[9].strftime('%Y-%m-%d %H:%M') if row[9] else 'N/A',
                'stage': get_stage_from_score(row[4]),
                'why_now': generate_why_now(row[10] or {})
            }

            # Fetch timeline (signal events)
            cur.execute("""
                SELECT
                    event_id,
                    event_type,
                    detected_at,
                    snippet
                FROM signal_events
                WHERE cluster_id = %s
                ORDER BY detected_at DESC
                LIMIT 50
            """, (cluster_id,))

            timeline = [
                {
                    'event_id': r[0],
                    'event_type': r[1],
                    'detected_at': r[2].strftime('%Y-%m-%d') if r[2] else '',
                    'snippet': r[3] or ''
                }
                for r in cur.fetchall()
            ]

            # Fetch evidence (source documents)
            cur.execute("""
                SELECT
                    document_id,
                    source_type,
                    title,
                    filed_date,
                    external_url,
                    snippet
                FROM source_documents
                WHERE cluster_id = %s
                ORDER BY filed_date DESC
                LIMIT 100
            """, (cluster_id,))

            evidence = [
                {
                    'document_id': r[0],
                    'source_type': r[1],
                    'title': r[2] or 'Untitled',
                    'filed_date': r[3].strftime('%Y-%m-%d') if r[3] else '',
                    'external_url': r[4] or '',
                    'snippet': r[5] or ''
                }
                for r in cur.fetchall()
            ]

            # Fetch injury distribution
            cur.execute("""
                SELECT
                    injury_normalized,
                    COUNT(*) as count
                FROM source_documents
                WHERE cluster_id = %s
                  AND injury_normalized IS NOT NULL
                GROUP BY injury_normalized
                ORDER BY count DESC
                LIMIT 10
            """, (cluster_id,))

            injury_rows = cur.fetchall()
            total_injuries = sum(r[1] for r in injury_rows)
            injuries = [
                {
                    'injury': r[0],
                    'count': r[1],
                    'pct': r[1] / total_injuries if total_injuries > 0 else 0
                }
                for r in injury_rows
            ]

            # Extract metrics
            metrics_data = candidate.get('metrics', {}) or {}
            metrics = {
                'velocity_7d': int(metrics_data.get('velocity_7d', 0)),
                'velocity_28d': int(metrics_data.get('velocity_28d', 0)),
                'accel_ratio': float(metrics_data.get('accel_ratio', 0)),
                'breadth_states': int(metrics_data.get('breadth_states', 0)),
                'breadth_firms': int(metrics_data.get('breadth_firms', 0))
            }

            return {
                'candidate': candidate,
                'timeline': timeline,
                'evidence': evidence,
                'injuries': injuries,
                'metrics': metrics
            }

    except Exception as e:
        print(f"Error getting dossier: {e}")
        import traceback
        traceback.print_exc()
        return get_sample_dossier()


def get_stage_from_score(score: int) -> str:
    """Determine stage from score."""
    if score >= 70:
        return 'HIGH_CONVICTION'
    elif score >= 40:
        return 'INVESTIGATE'
    elif score >= 20:
        return 'AWARENESS'
    else:
        return 'QUIET'


def generate_why_now(metrics: dict) -> str:
    """Generate a why now narrative from metrics."""
    parts = []

    velocity_7d = int(metrics.get('velocity_7d', 0))
    breadth_states = int(metrics.get('breadth_states', 0))
    breadth_firms = int(metrics.get('breadth_firms', 0))

    if velocity_7d > 0:
        parts.append(f"{velocity_7d} new filings in last 7 days")

    if breadth_states > 0 or breadth_firms > 0:
        parts.append(f"across {breadth_states} states and {breadth_firms} plaintiff firms")

    if not parts:
        return "Signal detected based on available evidence"

    return ". ".join(parts) + "."


def get_sample_watchlist() -> pd.DataFrame:
    """Return sample watchlist data for demo."""
    return pd.DataFrame([
        {
            'cluster_id': '1',
            'defendant_text': 'Bayer AG',
            'product_text': 'Roundup',
            'injury_text': 'Non-Hodgkin Lymphoma',
            'score_total': 92,
            'stage': 'HIGH_CONVICTION',
            'category': 'chemical',
            'last_updated': datetime.now() - timedelta(hours=2),
            'velocity_7d': 47,
            'breadth_states': 12
        },
        {
            'cluster_id': '2',
            'defendant_text': 'Johnson & Johnson',
            'product_text': 'Talcum Powder',
            'injury_text': 'Ovarian Cancer',
            'score_total': 78,
            'stage': 'HIGH_CONVICTION',
            'category': 'consumer',
            'last_updated': datetime.now() - timedelta(days=1),
            'velocity_7d': 32,
            'breadth_states': 9
        },
    ])


def get_sample_dossier() -> dict:
    """Return sample dossier for demo."""
    return {
        'candidate': {
            'cluster_id': '1',
            'defendant_text': 'Bayer AG',
            'product_text': 'Roundup',
            'injury_text': 'Non-Hodgkin Lymphoma',
            'score_total': 92,
            'score_components': {
                'literature': 92,
                'court_velocity': 85,
                'court_breadth': 70
            },
            'stage': 'HIGH_CONVICTION',
            'category': 'chemical',
            'first_seen': '2019-03-15',
            'last_updated': '2025-01-20 14:30',
            'why_now': '47 new filings in last 7 days across 12 states and 9 plaintiff firms.'
        },
        'timeline': [],
        'evidence': [],
        'injuries': [],
        'metrics': {
            'velocity_7d': 47,
            'velocity_28d': 183,
            'accel_ratio': 2.3,
            'breadth_states': 12,
            'breadth_firms': 9
        }
    }
