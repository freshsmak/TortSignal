"""
FAERS Timeseries Backfill Pipeline

Populates historical timeseries data for FAERS (drug adverse events) by quarter.
This enables trend analysis: slope, acceleration, consecutive increases, etc.

Run with: python -m src.pipeline.backfill_faers --start-year 2022 --end-year 2025
"""

import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any

import requests

from src.config import get_config
from src.connectors.faers import FAERSConnector
from src.db import get_cursor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_quarter_dates(year: int, quarter: int) -> tuple[datetime, datetime]:
    """Get start and end dates for a quarter."""
    if quarter == 1:
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        end = datetime(year, 3, 31, tzinfo=timezone.utc)
    elif quarter == 2:
        start = datetime(year, 4, 1, tzinfo=timezone.utc)
        end = datetime(year, 6, 30, tzinfo=timezone.utc)
    elif quarter == 3:
        start = datetime(year, 7, 1, tzinfo=timezone.utc)
        end = datetime(year, 9, 30, tzinfo=timezone.utc)
    else:  # quarter == 4
        start = datetime(year, 10, 1, tzinfo=timezone.utc)
        end = datetime(year, 12, 31, tzinfo=timezone.utc)
    return start, end


def fetch_faers_quarter_data(
    connector: FAERSConnector,
    start: datetime,
    end: datetime,
    top_n: int = 500,
    max_retries: int = 3,
) -> list[dict[str, Any]]:
    """
    Fetch top drugs for a specific quarter with retry logic.

    Args:
        connector: FAERS connector instance
        start: Quarter start date
        end: Quarter end date
        top_n: Number of top drugs to fetch
        max_retries: Maximum retry attempts for 500 errors

    Returns:
        List of drug data with counts
    """
    date_range = f"[{start.strftime('%Y%m%d')}+TO+{end.strftime('%Y%m%d')}]"
    url = "https://api.fda.gov/drug/event.json"

    for attempt in range(max_retries):
        try:
            response = connector.session.get(
                url,
                params={
                    "search": f"receivedate:{date_range}",
                    "count": "patient.drug.openfda.brand_name.exact",
                    "limit": min(top_n, 1000),
                },
                timeout=30,
            )

            if response.status_code == 200:
                results = response.json().get("results", [])
                logger.info(f"  Fetched {len(results)} drugs for {start.strftime('%Y-Q%q')}")
                return [
                    {
                        "drug_name": item["term"],
                        "count": item["count"],
                    }
                    for item in results
                ]
            elif response.status_code == 404:
                logger.warning(f"  No data for {start.strftime('%Y-Q%q')}")
                return []
            elif response.status_code == 500:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"  500 error for {start.strftime('%Y-Q%q')}, "
                        f"retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"  Failed after {max_retries} attempts: {response.status_code}")
                    return []
            else:
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"  Request error, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"  Request failed after {max_retries} attempts: {e}")
                return []

    return []


def upsert_timeseries_record(
    cur,
    product_name: str,
    source: str,
    period_start: datetime,
    period_end: datetime,
    report_count: int,
    serious_count: int | None = None,
    top_reactions: list | None = None,
    metadata: dict | None = None,
) -> None:
    """Insert or update a timeseries record."""
    import json

    cur.execute(
        """
        INSERT INTO signal_timeseries
            (product_name, source, period_start, period_end, report_count, serious_count, top_reactions, metadata)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_name, source, period_start)
        DO UPDATE SET
            period_end = EXCLUDED.period_end,
            report_count = EXCLUDED.report_count,
            serious_count = EXCLUDED.serious_count,
            top_reactions = EXCLUDED.top_reactions,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        """,
        (
            product_name,
            source,
            period_start.date(),
            period_end.date(),
            report_count,
            serious_count,
            json.dumps(top_reactions) if top_reactions else None,
            json.dumps(metadata) if metadata else None,
        ),
    )


def backfill_faers_timeseries(
    start_year: int = 2022,
    end_year: int = 2025,
    top_n: int = 500,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Backfill FAERS timeseries data by quarter.

    Args:
        start_year: First year to backfill
        end_year: Last year to backfill (inclusive)
        top_n: Number of top drugs per quarter
        dry_run: If True, don't write to database

    Returns:
        Summary statistics
    """
    logger.info("=" * 70)
    logger.info("FAERS TIMESERIES BACKFILL")
    logger.info(f"Period: {start_year} - {end_year}, Top {top_n} drugs per quarter")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    logger.info("=" * 70)

    connector = FAERSConnector()
    results = {
        "source": "faers",
        "start_year": start_year,
        "end_year": end_year,
        "quarters_processed": 0,
        "total_records": 0,
        "errors": 0,
    }

    cursor_context = None if dry_run else get_cursor()

    try:
        if not dry_run:
            cursor_context.__enter__()
            cur = cursor_context.cursor

        for year in range(start_year, end_year + 1):
            for quarter in range(1, 5):
                quarter_start, quarter_end = get_quarter_dates(year, quarter)

                # Don't try to fetch future data
                if quarter_start > datetime.now(timezone.utc):
                    logger.info(f"Skipping future quarter: {year} Q{quarter}")
                    continue

                logger.info(f"Processing {year} Q{quarter} ({quarter_start.date()} to {quarter_end.date()})")

                # Fetch quarter data with retry logic
                drugs = fetch_faers_quarter_data(connector, quarter_start, quarter_end, top_n)

                if not drugs:
                    results["errors"] += 1
                    continue

                # Store in database
                if not dry_run:
                    for drug_data in drugs:
                        try:
                            upsert_timeseries_record(
                                cur,
                                product_name=drug_data["drug_name"],
                                source="faers",
                                period_start=quarter_start,
                                period_end=quarter_end,
                                report_count=drug_data["count"],
                            )
                        except Exception as e:
                            logger.error(f"Failed to insert {drug_data['drug_name']}: {e}")
                            results["errors"] += 1

                results["quarters_processed"] += 1
                results["total_records"] += len(drugs)

                # Be nice to the API - rate limit between quarters
                time.sleep(1)

        if not dry_run:
            cursor_context.__exit__(None, None, None)

        logger.info("=" * 70)
        logger.info("BACKFILL COMPLETE")
        logger.info(f"Quarters processed: {results['quarters_processed']}")
        logger.info(f"Total records: {results['total_records']}")
        logger.info(f"Errors: {results['errors']}")
        logger.info("=" * 70)

        return results

    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        if cursor_context:
            cursor_context.__exit__(type(e), e, e.__traceback__)
        raise


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Backfill FAERS timeseries data")
    parser.add_argument("--start-year", type=int, default=2022, help="Start year")
    parser.add_argument("--end-year", type=int, default=2025, help="End year (inclusive)")
    parser.add_argument("--top-n", type=int, default=500, help="Top N drugs per quarter")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    args = parser.parse_args()

    try:
        results = backfill_faers_timeseries(
            start_year=args.start_year,
            end_year=args.end_year,
            top_n=args.top_n,
            dry_run=args.dry_run,
        )

        sys.exit(0 if results["errors"] == 0 else 1)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
