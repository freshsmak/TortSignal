"""
FDA Discovery Pipeline

Runs broad discovery across both FAERS (drugs) and MAUDE (devices).
This is the "what's happening out there?" scanner that catches signals
you weren't looking for.

Discovery approaches:
- FAERS: Drug anomalies, reaction anomalies, drug+reaction pairs
- MAUDE: Device anomalies, category anomalies, manufacturer anomalies

Run with: python -m src.pipeline.fda_discovery
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from src.config import get_config
from src.connectors.faers import FAERSConnector
from src.connectors.maude import MAUDEConnector
from src.db import (
    get_cursor,
    upsert_source_document,
    upsert_candidate,
    start_ingest_run,
    finish_ingest_run,
)
from src.clustering.candidate_builder import make_candidate_key

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_fda_discovery(
    current_days: int = 30,
    baseline_days: int = 365,
    persist: bool = True,
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    """
    Run comprehensive FDA discovery across FAERS and MAUDE.

    Args:
        current_days: Days in current analysis window
        baseline_days: Days ago for baseline comparison
        persist: If True, save candidates to database
        reference_date: Reference date for queries (defaults to Sept 30, 2025 - latest available FDA data)

    Returns:
        Consolidated discovery results
    """
    # Default to Sept 30, 2025 - the latest date with available FDA data
    if reference_date is None:
        reference_date = datetime(2025, 9, 30, tzinfo=timezone.utc)
    logger.info("=" * 70)
    logger.info("FDA COMPREHENSIVE DISCOVERY SCAN")
    logger.info(f"Parameters: current_days={current_days}, baseline_days={baseline_days}")
    logger.info(f"Reference date: {reference_date.strftime('%Y-%m-%d')}")
    logger.info("=" * 70)

    results = {
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "current_days": current_days,
            "baseline_days": baseline_days,
            "reference_date": reference_date.isoformat(),
        },
        "faers": {},
        "maude": {},
        "cross_source_signals": [],
        "candidates_created": 0,
    }
    
    # Track run if persisting
    run_id = None
    if persist:
        try:
            with get_cursor() as cur:
                run_id = start_ingest_run(cur, "fda_discovery")
        except Exception as e:
            logger.warning(f"Could not start ingest run: {e}")
            persist = False
    
    try:
        # =====================================================================
        # FAERS DISCOVERY (Drugs)
        # =====================================================================
        logger.info("")
        logger.info("PHASE 1: FAERS (Drug Adverse Events)")
        logger.info("-" * 50)

        faers = FAERSConnector(reference_date=reference_date)
        if faers.health_check():
            results["faers"] = faers.run_full_discovery(
                current_days=current_days,
                baseline_days=baseline_days,
            )
            
            # Convert FAERS signals to candidates
            if persist and results["faers"].get("drug_anomalies"):
                candidates_from_faers = _create_candidates_from_faers(
                    results["faers"],
                    current_days,
                )
                results["candidates_created"] += candidates_from_faers
        else:
            logger.error("FAERS health check failed - skipping")
            results["faers"] = {"error": "health_check_failed"}
        
        # =====================================================================
        # MAUDE DISCOVERY (Devices)
        # =====================================================================
        logger.info("")
        logger.info("PHASE 2: MAUDE (Device Adverse Events)")
        logger.info("-" * 50)

        maude = MAUDEConnector(reference_date=reference_date)
        if maude.health_check():
            results["maude"] = maude.run_full_discovery(
                current_days=current_days,
                baseline_days=baseline_days,
            )
            
            # Convert MAUDE signals to candidates
            if persist and results["maude"].get("device_anomalies"):
                candidates_from_maude = _create_candidates_from_maude(
                    results["maude"],
                    current_days,
                )
                results["candidates_created"] += candidates_from_maude
        else:
            logger.error("MAUDE health check failed - skipping")
            results["maude"] = {"error": "health_check_failed"}
        
        # =====================================================================
        # CROSS-SOURCE ANALYSIS
        # =====================================================================
        logger.info("")
        logger.info("PHASE 3: Cross-Source Analysis")
        logger.info("-" * 50)
        
        # Look for signals that appear in both FDA data AND would match
        # known product categories (this is a placeholder for more sophisticated
        # correlation logic)
        cross_signals = _analyze_cross_source(results)
        results["cross_source_signals"] = cross_signals
        
        # =====================================================================
        # SUMMARY
        # =====================================================================
        logger.info("")
        logger.info("=" * 70)
        logger.info("DISCOVERY COMPLETE")
        logger.info("=" * 70)
        
        faers_summary = results.get("faers", {}).get("summary", {})
        maude_summary = results.get("maude", {}).get("summary", {})
        
        logger.info(f"FAERS: {faers_summary.get('drug_anomalies_count', 0)} drug anomalies, "
                   f"{faers_summary.get('reaction_anomalies_count', 0)} reaction anomalies, "
                   f"{faers_summary.get('pair_signals_count', 0)} pair signals")
        logger.info(f"MAUDE: {maude_summary.get('device_anomalies_count', 0)} device anomalies, "
                   f"{maude_summary.get('category_anomalies_count', 0)} category anomalies, "
                   f"{maude_summary.get('manufacturer_anomalies_count', 0)} manufacturer anomalies")
        logger.info(f"Cross-source signals: {len(cross_signals)}")
        logger.info(f"Candidates created: {results['candidates_created']}")
        
        # Finish ingest run
        if persist and run_id:
            try:
                with get_cursor() as cur:
                    finish_ingest_run(
                        cur,
                        run_id=run_id,
                        status="success",
                        records_fetched=0,
                        records_processed=results["candidates_created"],
                        records_errored=0,
                    )
            except Exception as e:
                logger.warning(f"Could not finish ingest run: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"FDA discovery failed: {e}")
        if persist and run_id:
            try:
                with get_cursor() as cur:
                    finish_ingest_run(
                        cur,
                        run_id=run_id,
                        status="failed",
                        records_fetched=0,
                        records_processed=0,
                        records_errored=1,
                        error_message=str(e),
                    )
            except Exception:
                pass
        raise


def _create_candidates_from_faers(faers_results: dict, window_days: int) -> int:
    """Create/update candidates from FAERS discovery results."""
    created = 0
    now = datetime.now(timezone.utc)
    
    # Process drug anomalies
    for anomaly in faers_results.get("drug_anomalies", []):
        try:
            product_name = anomaly["product_name"]
            top_reactions = anomaly.get("top_reactions", [])
            injury_text = top_reactions[0] if top_reactions else "adverse_event"
            
            # For FDA signals, we don't have a defendant yet
            # Use manufacturer if we can infer it, otherwise "unknown"
            defendant_text = "unknown_manufacturer"
            
            candidate_key = make_candidate_key(defendant_text, product_name)
            
            delta_pct = anomaly.get("delta_pct", 0)
            if delta_pct == "new_entrant":
                delta_pct = 999
            
            # Score based on report volume and delta
            score = min(100, (anomaly.get("reports_current", 0) / 100) * (1 + delta_pct / 100))
            
            why_now = (
                f"FAERS signal: {anomaly['reports_current']} adverse event reports "
                f"in last {window_days} days"
            )
            if anomaly.get("is_new_entrant"):
                why_now += " (new entrant - not in baseline)"
            elif delta_pct > 0:
                why_now += f" ({delta_pct:.0f}% increase vs baseline)"
            
            if top_reactions:
                why_now += f". Top reactions: {', '.join(top_reactions[:3])}"
            
            with get_cursor() as cur:
                upsert_candidate(
                    cur,
                    candidate_key=candidate_key,
                    defendant_text=defendant_text,
                    product_text=product_name,
                    injury_text=injury_text,
                    first_seen_at=now,
                    last_seen_at=now,
                    metrics={
                        "source": "faers",
                        "reports_current": anomaly.get("reports_current", 0),
                        "reports_baseline": anomaly.get("reports_baseline", 0),
                        "delta_pct": delta_pct,
                        "top_reactions": top_reactions,
                        "is_new_entrant": anomaly.get("is_new_entrant", False),
                    },
                    score_total=score,
                    score_components={"faers_trend": score},
                    why_now=why_now,
                    category="pharma",
                )
            created += 1
            
        except Exception as e:
            logger.warning(f"Failed to create candidate from FAERS anomaly: {e}")
    
    # Process reaction anomalies (these are higher signal)
    for reaction in faers_results.get("reaction_anomalies", [])[:20]:  # Top 20
        try:
            reaction_name = reaction["reaction"]
            top_drugs = reaction.get("top_drugs", [])
            
            if not top_drugs:
                continue
            
            # Create a candidate for each top drug driving this reaction
            for drug_info in top_drugs[:3]:  # Top 3 drugs per reaction
                product_name = drug_info.get("drug_name", "unknown")
                defendant_text = "unknown_manufacturer"
                
                candidate_key = make_candidate_key(defendant_text, product_name)
                
                delta_pct = reaction.get("delta_pct", 0)
                if delta_pct == "new":
                    delta_pct = 999
                
                score = min(100, (drug_info.get("count", 0) / 50) * (1 + delta_pct / 200))
                
                why_now = (
                    f"Reaction-first signal: '{reaction_name}' is spiking ({reaction['reports_current']} reports). "
                    f"{product_name} is a top associated drug ({drug_info.get('count', 0)} reports for this reaction)."
                )
                
                with get_cursor() as cur:
                    upsert_candidate(
                        cur,
                        candidate_key=candidate_key,
                        defendant_text=defendant_text,
                        product_text=product_name,
                        injury_text=reaction_name,
                        first_seen_at=now,
                        last_seen_at=now,
                        metrics={
                            "source": "faers_reaction",
                            "reaction": reaction_name,
                            "reaction_reports": reaction.get("reports_current", 0),
                            "reaction_delta_pct": delta_pct,
                            "drug_reports_for_reaction": drug_info.get("count", 0),
                        },
                        score_total=score,
                        score_components={"faers_reaction": score},
                        why_now=why_now,
                        category="pharma",
                    )
                created += 1
                
        except Exception as e:
            logger.warning(f"Failed to create candidate from reaction anomaly: {e}")
    
    logger.info(f"Created {created} candidates from FAERS signals")
    return created


def _create_candidates_from_maude(maude_results: dict, window_days: int) -> int:
    """Create/update candidates from MAUDE discovery results."""
    created = 0
    now = datetime.now(timezone.utc)
    
    # Process device anomalies
    for anomaly in maude_results.get("device_anomalies", []):
        try:
            device_name = anomaly["device_name"]
            manufacturer = anomaly.get("manufacturer") or "unknown_manufacturer"
            
            candidate_key = make_candidate_key(manufacturer, device_name)
            
            delta_pct = anomaly.get("delta_pct", 0)
            if delta_pct == "new_entrant":
                delta_pct = 999
            
            score = min(100, (anomaly.get("reports_current", 0) / 50) * (1 + delta_pct / 100))
            
            why_now = (
                f"MAUDE signal: {anomaly['reports_current']} adverse event reports "
                f"in last {window_days} days"
            )
            if anomaly.get("is_new_entrant"):
                why_now += " (new entrant)"
            elif delta_pct > 0:
                why_now += f" ({delta_pct:.0f}% increase vs baseline)"
            
            with get_cursor() as cur:
                upsert_candidate(
                    cur,
                    candidate_key=candidate_key,
                    defendant_text=manufacturer,
                    product_text=device_name,
                    injury_text="device_adverse_event",
                    first_seen_at=now,
                    last_seen_at=now,
                    metrics={
                        "source": "maude",
                        "reports_current": anomaly.get("reports_current", 0),
                        "reports_baseline": anomaly.get("reports_baseline", 0),
                        "delta_pct": delta_pct,
                        "is_new_entrant": anomaly.get("is_new_entrant", False),
                    },
                    score_total=score,
                    score_components={"maude_trend": score},
                    why_now=why_now,
                    category="device",
                )
            created += 1
            
        except Exception as e:
            logger.warning(f"Failed to create candidate from MAUDE anomaly: {e}")
    
    # Process category anomalies (these catch whole device classes)
    for category in maude_results.get("category_anomalies", [])[:20]:
        try:
            product_code = category["product_code"]
            top_brands = category.get("top_brands", [])
            top_manufacturers = category.get("top_manufacturers", [])
            
            if not top_brands:
                continue
            
            # Create candidates for top brands in this category
            for brand_info in top_brands[:3]:
                device_name = brand_info.get("brand_name", "unknown")
                
                # Try to find manufacturer for this brand
                manufacturer = "unknown_manufacturer"
                for mfr in top_manufacturers:
                    manufacturer = mfr.get("manufacturer", "unknown_manufacturer")
                    break
                
                candidate_key = make_candidate_key(manufacturer, device_name)
                
                delta_pct = category.get("delta_pct", 0)
                if delta_pct == "new":
                    delta_pct = 999
                
                score = min(100, (brand_info.get("count", 0) / 30) * (1 + delta_pct / 200))
                
                why_now = (
                    f"Category-first signal: Device category '{product_code}' is spiking "
                    f"({category['reports_current']} total reports). "
                    f"{device_name} is a top brand in this category."
                )
                
                with get_cursor() as cur:
                    upsert_candidate(
                        cur,
                        candidate_key=candidate_key,
                        defendant_text=manufacturer,
                        product_text=device_name,
                        injury_text="device_category_signal",
                        first_seen_at=now,
                        last_seen_at=now,
                        metrics={
                            "source": "maude_category",
                            "product_code": product_code,
                            "category_reports": category.get("reports_current", 0),
                            "category_delta_pct": delta_pct,
                            "brand_reports": brand_info.get("count", 0),
                        },
                        score_total=score,
                        score_components={"maude_category": score},
                        why_now=why_now,
                        category="device",
                    )
                created += 1
                
        except Exception as e:
            logger.warning(f"Failed to create candidate from category anomaly: {e}")
    
    logger.info(f"Created {created} candidates from MAUDE signals")
    return created


def _analyze_cross_source(results: dict) -> list[dict]:
    """
    Analyze for signals that appear across multiple sources.
    
    This is a placeholder for more sophisticated cross-source correlation.
    In a full implementation, you would:
    - Match FAERS drugs to UniCourt filings
    - Match MAUDE devices to court filings
    - Identify products appearing in multiple signal streams
    """
    cross_signals = []
    
    # For now, just flag high-confidence signals from each source
    faers_high = [
        a for a in results.get("faers", {}).get("drug_anomalies", [])
        if a.get("reports_current", 0) > 200 and 
           (a.get("delta_pct") == "new_entrant" or a.get("delta_pct", 0) > 200)
    ]
    
    maude_high = [
        a for a in results.get("maude", {}).get("device_anomalies", [])
        if a.get("reports_current", 0) > 100 and
           (a.get("delta_pct") == "new_entrant" or a.get("delta_pct", 0) > 200)
    ]
    
    for signal in faers_high[:10]:
        cross_signals.append({
            "source": "faers",
            "product_name": signal.get("product_name"),
            "signal_strength": "high",
            "reports": signal.get("reports_current"),
            "delta": signal.get("delta_pct"),
            "note": "High-volume drug with significant increase",
        })
    
    for signal in maude_high[:10]:
        cross_signals.append({
            "source": "maude", 
            "product_name": signal.get("device_name"),
            "signal_strength": "high",
            "reports": signal.get("reports_current"),
            "delta": signal.get("delta_pct"),
            "note": "High-volume device with significant increase",
        })
    
    return cross_signals


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run FDA discovery pipeline")
    parser.add_argument("--current-days", type=int, default=30, help="Current analysis window (days)")
    parser.add_argument("--baseline-days", type=int, default=365, help="Baseline comparison (days ago)")
    parser.add_argument("--no-persist", action="store_true", help="Don't save to database")
    parser.add_argument("--output", type=str, help="Output JSON file for results")
    parser.add_argument("--reference-date", type=str, help="Reference date for queries (YYYY-MM-DD). Defaults to 2025-09-30 (latest available FDA data)")
    args = parser.parse_args()

    # Parse reference date if provided
    reference_date = None
    if args.reference_date:
        try:
            reference_date = datetime.strptime(args.reference_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error(f"Invalid date format: {args.reference_date}. Use YYYY-MM-DD")
            sys.exit(1)

    try:
        results = run_fda_discovery(
            current_days=args.current_days,
            baseline_days=args.baseline_days,
            persist=not args.no_persist,
            reference_date=reference_date,
        )
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results written to {args.output}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("FDA DISCOVERY SUMMARY")
        print("=" * 60)
        
        faers = results.get("faers", {}).get("summary", {})
        maude = results.get("maude", {}).get("summary", {})
        
        print(f"\nFAERS (Drugs):")
        print(f"  Drug anomalies:     {faers.get('drug_anomalies_count', 0)}")
        print(f"  Reaction anomalies: {faers.get('reaction_anomalies_count', 0)}")
        print(f"  Pair signals:       {faers.get('pair_signals_count', 0)}")
        
        print(f"\nMAUDE (Devices):")
        print(f"  Device anomalies:       {maude.get('device_anomalies_count', 0)}")
        print(f"  Category anomalies:     {maude.get('category_anomalies_count', 0)}")
        print(f"  Manufacturer anomalies: {maude.get('manufacturer_anomalies_count', 0)}")
        
        print(f"\nCandidates created: {results.get('candidates_created', 0)}")
        print()

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
