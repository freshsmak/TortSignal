"""
Step 0 Discovery Pipeline

This is the main orchestration module that:
1. Fetches recent court filings from UniCourt
2. Extracts entities (defendant, product, injury) using LLM
3. Clusters cases into candidate tort clusters
4. Scores and persists candidates to the database

Run with: python -m src.pipeline.discovery
"""

import logging
import sys
from datetime import datetime, timezone

from src.config import get_config
from src.connectors.unicourt import UniCourtConnector
from src.extraction.entity_extractor import EntityExtractor
from src.clustering.candidate_builder import CandidateBuilder, make_candidate_key
from src.scoring.category_router import CategoryRouter
from src.db import (
    get_cursor,
    upsert_source_document,
    upsert_candidate,
    insert_candidate_evidence,
    upsert_candidate_rollup,
    start_ingest_run,
    finish_ingest_run,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_court_discovery(
    days: int = 7,
    limit: int = 100,
    dry_run: bool = False,
) -> dict:
    """
    Run the Step 0 court discovery pipeline.

    Args:
        days: Number of days to look back for cases
        limit: Maximum number of cases to process
        dry_run: If True, don't persist to database

    Returns:
        Dict with pipeline statistics
    """
    config = get_config()
    stats = {
        "cases_fetched": 0,
        "cases_processed": 0,
        "cases_errored": 0,
        "candidates_created": 0,
        "top_candidates": [],
    }

    logger.info(f"Starting court discovery: days={days}, limit={limit}")

    # Initialize components
    connector = UniCourtConnector()
    extractor = EntityExtractor()
    builder = CandidateBuilder()
    router = CategoryRouter()

    # Start ingest tracking
    run_id = None
    if not dry_run:
        with get_cursor() as cur:
            run_id = start_ingest_run(cur, "unicourt_discovery")
            logger.info(f"Started ingest run: {run_id}")

    try:
        # Step 1: Fetch cases
        logger.info("Fetching cases from UniCourt...")
        cases = list(connector.fetch(days=days, limit=limit))
        stats["cases_fetched"] = len(cases)
        logger.info(f"Fetched {len(cases)} cases")

        if not cases:
            logger.warning("No cases fetched. Check UniCourt connector implementation.")
            return stats

        # Step 2: Extract entities and cluster
        logger.info("Extracting entities and clustering...")
        doc_ids = {}  # source_uid -> doc_id mapping

        for i, case in enumerate(cases):
            try:
                # Build text for extraction
                text_parts = [case.title]
                if case.complaint_snippet:
                    text_parts.append(case.complaint_snippet)
                if case.defendant_text:
                    text_parts.append(f"Defendant: {case.defendant_text}")
                extraction_text = "\n".join(text_parts)

                # Extract entities
                entities = extractor.extract(extraction_text)

                if not entities.is_product_liability:
                    logger.debug(f"Skipping non-PL case: {case.source_uid}")
                    continue

                # Add to cluster
                key = builder.add_case(case, entities)
                if key:
                    stats["cases_processed"] += 1

                    # Store document if not dry run
                    if not dry_run:
                        with get_cursor() as cur:
                            doc_id = upsert_source_document(
                                cur,
                                source_type="court_case",
                                source_uid=case.source_uid,
                                title=case.title,
                                published_at=_parse_date(case.filed_date),
                                retrieved_at=datetime.now(timezone.utc),
                                url=case.url,
                                metadata={
                                    "jurisdiction": case.jurisdiction,
                                    "state": case.state,
                                    "plaintiff_firm": case.plaintiff_firm,
                                    "extracted": {
                                        "defendant": entities.defendant,
                                        "product": entities.product,
                                        "injury": entities.injury,
                                        "confidence": entities.confidence,
                                    },
                                },
                                raw_payload=case.raw_data,
                            )
                            doc_ids[case.source_uid] = doc_id

                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(cases)} cases")

            except Exception as e:
                logger.error(f"Error processing case {case.source_uid}: {e}")
                stats["cases_errored"] += 1

        # Step 3: Build and score candidates
        logger.info("Building candidates...")
        candidates = builder.build_candidates()
        stats["candidates_created"] = len(candidates)
        logger.info(f"Created {len(candidates)} candidates")

        # Step 4: Persist candidates
        if not dry_run and candidates:
            logger.info("Persisting candidates to database...")
            now = datetime.now(timezone.utc)

            for candidate in candidates:
                with get_cursor() as cur:
                    # Assign category
                    category = router.assign_category(
                        candidate.defendant,
                        candidate.product,
                        candidate.injury_label,
                    )

                    # Upsert candidate
                    candidate_id = upsert_candidate(
                        cur,
                        candidate_key=make_candidate_key(candidate.defendant, candidate.product),
                        defendant_text=candidate.defendant,
                        product_text=candidate.product,
                        injury_text=candidate.injury_label,
                        first_seen_at=candidate.first_seen or now,
                        last_seen_at=candidate.last_seen or now,
                        metrics={
                            "count": candidate.count,
                            "count_7d": candidate.count,
                            "breadth_states": candidate.breadth_states,
                            "breadth_firms": candidate.breadth_firms,
                            "states": candidate.states,
                            "firms": candidate.firms,
                            "injury_distribution": candidate.injury_counts,
                        },
                        score_total=candidate.score_total,
                        score_components=candidate.score_components,
                        why_now=candidate.why_now,
                        category=category,
                    )

                    # Link evidence
                    for member in candidate.members:
                        case_uid = member.get("case_uid")
                        if case_uid and case_uid in doc_ids:
                            insert_candidate_evidence(
                                cur,
                                candidate_id=candidate_id,
                                doc_id=doc_ids[case_uid],
                                event_type="filing_new",
                                snippet=member.get("title"),
                            )

                    # Upsert rollup
                    upsert_candidate_rollup(
                        cur,
                        candidate_id=candidate_id,
                        as_of_date=now,
                        velocity_7d=candidate.count,
                        velocity_28d=candidate.count,  # Will be updated with historical data
                        accel_ratio=1.0,
                        breadth_states=candidate.breadth_states,
                        breadth_firms=candidate.breadth_firms,
                    )

        # Step 5: Report top candidates
        stats["top_candidates"] = [
            {
                "defendant": c.defendant,
                "product": c.product,
                "injury": c.injury_label,
                "count": c.count,
                "score": c.score_total,
                "states": c.breadth_states,
                "firms": c.breadth_firms,
            }
            for c in candidates[:10]
        ]

        # Finish ingest run
        if not dry_run and run_id:
            with get_cursor() as cur:
                finish_ingest_run(
                    cur,
                    run_id=run_id,
                    status="success",
                    records_fetched=stats["cases_fetched"],
                    records_processed=stats["cases_processed"],
                    records_errored=stats["cases_errored"],
                )

        return stats

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if not dry_run and run_id:
            with get_cursor() as cur:
                finish_ingest_run(
                    cur,
                    run_id=run_id,
                    status="failed",
                    records_fetched=stats["cases_fetched"],
                    records_processed=stats["cases_processed"],
                    records_errored=stats["cases_errored"],
                    error_message=str(e),
                )
        raise


def _parse_date(date_str: str) -> datetime | None:
    """Parse a date string to datetime."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run TortSignal court discovery pipeline")
    parser.add_argument("--days", type=int, default=7, help="Days to look back")
    parser.add_argument("--limit", type=int, default=100, help="Max cases to process")
    parser.add_argument("--dry-run", action="store_true", help="Don't persist to database")
    args = parser.parse_args()

    try:
        stats = run_court_discovery(
            days=args.days,
            limit=args.limit,
            dry_run=args.dry_run,
        )

        print("\n" + "=" * 60)
        print("DISCOVERY PIPELINE COMPLETE")
        print("=" * 60)
        print(f"Cases fetched:    {stats['cases_fetched']}")
        print(f"Cases processed:  {stats['cases_processed']}")
        print(f"Cases errored:    {stats['cases_errored']}")
        print(f"Candidates:       {stats['candidates_created']}")
        print()

        if stats["top_candidates"]:
            print("TOP CANDIDATES:")
            print("-" * 60)
            for i, c in enumerate(stats["top_candidates"], 1):
                print(
                    f"{i:2}. {c['defendant'][:25]:25} | {c['product'][:20]:20} | "
                    f"n={c['count']:3} | score={c['score']:.1f}"
                )
        print()

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
