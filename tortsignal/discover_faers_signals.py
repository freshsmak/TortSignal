#!/usr/bin/env python3
"""
FAERS Mass Signal Discovery Pipeline

Queries FDA FAERS database for all drugs with serious adverse events in the last 24 months,
detects statistical spikes, scores by litigation potential, and populates the watchlist.

Focus: Pre-litigation signal detection (drugs NOT yet in MDLs)
"""

import os
import sys
import requests
import time
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import statistics
from psycopg.types.json import Json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db import get_cursor
from config import get_config

# FAERS API endpoint
FAERS_API_BASE = "https://api.fda.gov/drug/event.json"

# Serious outcome categories (litigation-worthy)
SERIOUS_OUTCOMES = {
    "1": "Death",
    "2": "Life-Threatening",
    "3": "Hospitalization",
    "4": "Disability",
    "5": "Congenital Anomaly",
    "6": "Required Intervention"
}

# Date range: Last 24 months (Q1 2024 - Q4 2025)
# Current date: Q1 2026
END_DATE = "20251231"  # End of Q4 2025
START_DATE = "20240101"  # Start of Q1 2024


def get_api_key() -> str:
    """Get OpenFDA API key from config."""
    config = get_config()
    return config.openfda.api_key


def query_faers(search_query: str, limit: int = 100) -> Optional[Dict]:
    """
    Query FAERS API with rate limiting and error handling.

    Args:
        search_query: FDA search query string
        limit: Max results to return

    Returns:
        API response dict or None if error
    """
    api_key = get_api_key()

    url = f"{FAERS_API_BASE}?search={search_query}&limit={limit}&api_key={api_key}"

    try:
        response = requests.get(url, timeout=30)

        # Rate limiting: 240 requests/minute with API key
        time.sleep(0.25)  # 4 requests/second = 240/minute

        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  API error: {response.status_code} - {response.text[:200]}")
            return None

    except Exception as e:
        print(f"⚠️  Query failed: {e}")
        return None


def get_top_drugs_by_serious_aes(limit: int = 500) -> List[Tuple[str, int]]:
    """
    Get top drugs by serious adverse event count in last 24 months.

    Returns:
        List of (drug_name, serious_ae_count) tuples
    """
    print("\n" + "="*80)
    print("STEP 1: Querying FAERS for top drugs with serious adverse events")
    print("="*80)
    print(f"Date range: {START_DATE} - {END_DATE} (24 months)")
    print(f"Outcomes: {', '.join(SERIOUS_OUTCOMES.values())}")
    print()

    # Query for drugs with serious outcomes in date range
    # Serious codes: 1=Death, 2=Life-threatening, 3=Hospitalization
    search_query = (
        f"receivedate:[{START_DATE}+TO+{END_DATE}]"
        "+AND+serious:1"
        "+AND+(seriousnessdeath:1+OR+seriousnesshospitalization:1+OR+seriousnesslifethreatening:1)"
    )

    # Get count by drug substance name
    count_url = (
        f"{FAERS_API_BASE}?search={search_query}"
        f"&count=patient.drug.medicinalproduct.exact"
        f"&limit={limit}"
        f"&api_key={get_api_key()}"
    )

    print(f"Fetching top {limit} drugs...")

    try:
        response = requests.get(count_url, timeout=60)
        time.sleep(0.5)  # Rate limit

        if response.status_code != 200:
            print(f"❌ API error: {response.status_code}")
            return []

        data = response.json()
        results = data.get("results", [])

        drugs = [(r["term"], r["count"]) for r in results]

        print(f"✓ Found {len(drugs)} drugs with serious AEs")

        # Show preview of drugs (up to 10)
        preview_count = min(10, len(drugs))
        if len(drugs) <= 10:
            print(f"\n📋 All {len(drugs)} drugs to be analyzed:")
        else:
            print(f"\n📋 Top {preview_count} of {len(drugs)} drugs to be analyzed:")

        for i, (drug, count) in enumerate(drugs[:preview_count], 1):
            print(f"  {i:2d}. {drug:30s} - {count:6,d} serious AEs")

        return drugs

    except Exception as e:
        print(f"❌ Failed to get drug counts: {e}")
        return []


def get_quarterly_serious_ae_counts(drug_name: str) -> Dict[str, Dict[str, int]]:
    """
    Get quarterly breakdown of serious AE counts for a drug.

    Returns:
        Dict of quarter -> outcome type -> count
        e.g., {"2024Q1": {"Death": 50, "Hospitalization": 120}, ...}
    """
    quarters = {
        "2024Q1": ("20240101", "20240331"),
        "2024Q2": ("20240401", "20240630"),
        "2024Q3": ("20240701", "20240930"),
        "2024Q4": ("20241001", "20241231"),
        "2025Q1": ("20250101", "20250331"),
        "2025Q2": ("20250401", "20250630"),
        "2025Q3": ("20250701", "20250930"),
        "2025Q4": ("20251001", "20251231"),
    }

    quarterly_data = {}

    # Escape drug name for API query
    drug_escaped = drug_name.replace('"', '\\"')

    for quarter, (start, end) in quarters.items():
        counts = {
            "Death": 0,
            "Hospitalization": 0,
            "LifeThreatening": 0,
            "Disability": 0,
        }

        # Query for deaths
        death_query = (
            f'receivedate:[{start}+TO+{end}]'
            f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
            f'+AND+seriousnessdeath:1'
        )

        death_result = query_faers(death_query, limit=1)
        if death_result and "meta" in death_result:
            counts["Death"] = death_result["meta"]["results"]["total"]

        # Query for hospitalizations
        hosp_query = (
            f'receivedate:[{start}+TO+{end}]'
            f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
            f'+AND+seriousnesshospitalization:1'
        )

        hosp_result = query_faers(hosp_query, limit=1)
        if hosp_result and "meta" in hosp_result:
            counts["Hospitalization"] = hosp_result["meta"]["results"]["total"]

        # Query for life-threatening
        life_query = (
            f'receivedate:[{start}+TO+{end}]'
            f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
            f'+AND+seriousnesslifethreatening:1'
        )

        life_result = query_faers(life_query, limit=1)
        if life_result and "meta" in life_result:
            counts["LifeThreatening"] = life_result["meta"]["results"]["total"]

        # Query for disability
        disability_query = (
            f'receivedate:[{start}+TO+{end}]'
            f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
            f'+AND+seriousnessdisabling:1'
        )

        disability_result = query_faers(disability_query, limit=1)
        if disability_result and "meta" in disability_result:
            counts["Disability"] = disability_result["meta"]["results"]["total"]

        quarterly_data[quarter] = counts

    return quarterly_data


def calculate_signal_metrics(quarterly_data: Dict[str, Dict[str, int]], sae_type: str) -> Dict:
    """
    Calculate velocity, acceleration, and severity scores from quarterly data for a specific SAE type.

    Args:
        quarterly_data: Dict of quarter -> SAE counts
        sae_type: "Death", "Hospitalization", "LifeThreatening", or "Disability"

    Returns:
        Dict with metrics: velocity, acceleration, severity, total_count, etc.
    """
    quarters = sorted(quarterly_data.keys())

    # Extract counts for this SAE type by quarter
    counts = [quarterly_data[q].get(sae_type, 0) for q in quarters]
    total_count = sum(counts)

    # Calculate velocity (% change from baseline to most recent COMPLETE quarters)
    # Exclude most recent 2 quarters due to FAERS reporting lag (2-3 month delay)
    # Compare: Q1-Q4 2024 (baseline) vs Q1-Q2 2025 (recent complete)
    if len(counts) >= 6:
        baseline = statistics.mean(counts[:4])    # Q1-Q4 2024 (baseline year)
        recent = statistics.mean(counts[4:6])     # Q1-Q2 2025 (most recent COMPLETE quarters)

        if baseline > 0:
            velocity = ((recent - baseline) / baseline) * 100
        else:
            velocity = 0 if recent == 0 else 999  # Spike from zero
    else:
        velocity = 0

    # Calculate acceleration (quarter-over-quarter change)
    qoq_changes = []
    for i in range(1, len(counts)):
        if counts[i-1] > 0:
            change = ((counts[i] - counts[i-1]) / counts[i-1]) * 100
            qoq_changes.append(change)

    acceleration = statistics.mean(qoq_changes) if qoq_changes else 0

    # Recent spike (Q1-Q2 2025 vs Q3-Q4 2024)
    # Compare most recent complete quarters vs previous 2 quarters
    if len(counts) >= 6:
        prev_avg = statistics.mean(counts[2:4])   # Q3-Q4 2024
        recent_avg = statistics.mean(counts[4:6]) # Q1-Q2 2025 (complete)

        if prev_avg > 0:
            recent_spike = ((recent_avg - prev_avg) / prev_avg) * 100
        else:
            recent_spike = 0 if recent_avg == 0 else 999
    else:
        recent_spike = 0

    return {
        "sae_type": sae_type,
        "velocity": round(velocity, 1),
        "acceleration": round(acceleration, 1),
        "recent_spike": round(recent_spike, 1),
        "total_count": total_count,
        "baseline_count": int(statistics.mean(counts[:4])) if len(counts) >= 4 else 0,
        "recent_count": int(statistics.mean(counts[4:6])) if len(counts) >= 6 else 0,  # Q1-Q2 2025 only
    }


def score_signal(metrics: Dict, sae_type: str) -> Tuple[float, str, str]:
    """
    Score signal 0-100 based on litigation potential.

    Args:
        metrics: Signal metrics dict
        sae_type: Type of SAE (Death, Hospitalization, Disability, LifeThreatening)

    Returns:
        (score, stage, category)
    """
    score = 0
    total_count = metrics["total_count"]

    # Severity thresholds vary by SAE type
    # Deaths are rarer but more severe; Hospitalizations are more common
    if sae_type == "Death":
        thresholds = {500: 40, 200: 30, 100: 20, 50: 10}
    elif sae_type == "Hospitalization":
        thresholds = {2000: 40, 1000: 30, 500: 20, 200: 10}  # Higher volume expected
    elif sae_type == "Disability":
        thresholds = {1000: 40, 500: 30, 200: 20, 100: 10}
    else:  # LifeThreatening
        thresholds = {500: 40, 200: 30, 100: 20, 50: 10}

    # Severity component (0-40 points): Based on absolute count
    # This applies regardless of trend (even declining counts matter if absolute is high)
    for threshold, points in sorted(thresholds.items(), reverse=True):
        if total_count >= threshold:
            score += points
            break

    # Velocity component (0-30 points): % increase baseline to recent
    # Only RISING trends get points (declining = 0, not penalty)
    velocity = metrics["velocity"]
    if velocity >= 100:  # 100%+ increase
        score += 30
    elif velocity >= 50:
        score += 25
    elif velocity >= 25:
        score += 20
    elif velocity >= 10:
        score += 10
    elif velocity > 0:
        score += 5
    # Note: velocity <= 0 adds 0 points (no penalty, no reward)

    # Recent spike component (0-20 points): Recent acceleration
    # Only POSITIVE spikes get points
    recent_spike = metrics["recent_spike"]
    if recent_spike >= 50:
        score += 20
    elif recent_spike >= 25:
        score += 15
    elif recent_spike >= 10:
        score += 10
    elif recent_spike > 0:
        score += 5
    # Note: negative recent_spike adds 0 points

    # Acceleration component (0-10 points): Sustained growth
    # Only POSITIVE acceleration gets points
    if metrics["acceleration"] >= 20:
        score += 10
    elif metrics["acceleration"] >= 10:
        score += 7
    elif metrics["acceleration"] >= 5:
        score += 5
    elif metrics["acceleration"] > 0:
        score += 3
    # Note: negative acceleration adds 0 points

    # Penalty for steep declines (suggests resolved/disclosed issue)
    # If deaths declining >40%, apply small penalty
    if velocity < -40:
        score = max(0, score - 10)  # -10 points, but never below 0

    # Determine stage and category based on score and SAE type
    category_map = {
        "Death": "drug_death",
        "Hospitalization": "drug_hospitalization",
        "Disability": "drug_disability",
        "LifeThreatening": "drug_life_threatening"
    }

    if score >= 70:
        stage = "HIGH_CONVICTION"
        category = category_map.get(sae_type, "drug_serious_ae") + "_spike"
    elif score >= 40:
        stage = "INVESTIGATE"
        category = category_map.get(sae_type, "drug_serious_ae")
    elif score >= 20:
        stage = "AWARENESS"
        category = category_map.get(sae_type, "drug_emerging")
    else:
        stage = "QUIET"
        category = "drug_monitoring"

    return (round(score, 1), stage, category)


def insert_signal_into_database(
    drug_name: str,
    manufacturer: str,
    sae_type: str,
    metrics: Dict,
    score: float,
    stage: str,
    category: str
) -> Optional[int]:
    """
    Insert discovered signal into Safety Intelligence Graph.

    Args:
        drug_name: Name of the drug
        manufacturer: Manufacturer name
        sae_type: Type of SAE (Death, Hospitalization, Disability, LifeThreatening)
        metrics: Signal metrics
        score: Calculated score
        stage: Stage (HIGH_CONVICTION, INVESTIGATE, etc.)
        category: Category string

    Returns:
        candidate_id if successful, None otherwise
    """
    try:
        with get_cursor() as cur:
            # 1. Insert/get defendant (manufacturer) - for future use
            cur.execute("""
                INSERT INTO defendants (name, defendant_type, metadata_json)
                VALUES (%s, 'pharmaceutical', %s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING defendant_id
            """, (manufacturer, Json({})))

            result = cur.fetchone()
            defendant_id = result['defendant_id']

            # 2. Insert/get product (drug) - without defendant_id (simplified schema)
            cur.execute("""
                INSERT INTO products (name, product_type, metadata_json)
                VALUES (%s, 'pharmaceutical', %s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING product_id
            """, (drug_name, Json({})))

            result = cur.fetchone()
            product_id = result['product_id']

            # 3. Insert/get injury based on SAE type
            cur.execute("""
                INSERT INTO injuries (name, metadata_json)
                VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING injury_id
            """, (sae_type, Json({})))

            result = cur.fetchone()
            injury_id = result['injury_id']

            # 4. Insert product signal
            signal_metadata = {
                "sae_type": sae_type,
                "velocity": metrics["velocity"],
                "acceleration": metrics["acceleration"],
                "recent_spike": metrics["recent_spike"],
                "baseline_count": metrics["baseline_count"],
                "recent_count": metrics["recent_count"],
                "total_count": metrics["total_count"],
                "source": "FAERS",
                "date_range": f"{START_DATE}-{END_DATE}"
            }

            # Set death_count or hospitalization_count based on SAE type
            death_count = metrics["total_count"] if sae_type == "Death" else 0
            hosp_count = metrics["total_count"] if sae_type == "Hospitalization" else 0

            cur.execute("""
                INSERT INTO product_signals (
                    product_id,
                    injury_id,
                    signal_type,
                    severity_score,
                    death_count,
                    hospitalization_count,
                    first_detected_at,
                    last_updated_at,
                    metadata_json
                )
                VALUES (%s, %s, 'adverse_event_spike', %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s)
                RETURNING signal_id
            """, (
                product_id,
                injury_id,
                score,
                death_count,
                hosp_count,
                Json(signal_metadata)
            ))

            result = cur.fetchone()
            signal_id = result['signal_id']

            # 5. Insert candidate
            cur.execute("""
                INSERT INTO candidates (
                    defendant_id,
                    product_id,
                    injury_id,
                    defendant_text,
                    product_text,
                    injury_text,
                    category,
                    score_total,
                    metrics_json,
                    first_seen_at,
                    last_seen_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING candidate_id
            """, (
                defendant_id,
                product_id,
                injury_id,
                manufacturer,
                drug_name,
                sae_type,  # Use actual SAE type (Death, Hospitalization, etc.)
                category,
                score,
                Json({
                    "velocity_7d": metrics["velocity"],
                    "breadth_states": 50,  # FAERS is national
                    "signal_metadata": signal_metadata
                })
            ))

            result = cur.fetchone()
            candidate_id = result['candidate_id']

            # 6. Insert signal event
            cur.execute("""
                INSERT INTO signal_events (
                    signal_id,
                    event_type,
                    severity,
                    count,
                    recorded_at,
                    metadata_json
                )
                VALUES (%s, 'adverse_event', %s, %s, CURRENT_TIMESTAMP, %s)
            """, (
                signal_id,
                score,
                metrics["total_count"],  # Use total_count instead of total_deaths
                Json({"source": "FAERS_discovery", "sae_type": sae_type})
            ))

            return candidate_id

    except Exception as e:
        print(f"❌ Database insert failed: {e}")
        return None


def discover_and_populate_signals(max_drugs: int = 100, min_score: int = 20):
    """
    Main pipeline: Discover FAERS signals and populate watchlist.

    Args:
        max_drugs: Maximum number of drugs to analyze
        min_score: Minimum score threshold for insertion (default: 20 = AWARENESS)
    """
    print("\n" + "="*80)
    print("FAERS MASS SIGNAL DISCOVERY PIPELINE")
    print("="*80)

    # Show TEST MODE banner if limiting to small number
    if max_drugs <= 20:
        print(f"\n🧪 TEST MODE: Analyzing {max_drugs} drugs only")
        print(f"   (Change max_drugs parameter to analyze more)")

    print(f"\nTarget: {max_drugs} drugs")
    print(f"Threshold: Score >= {min_score}")
    print(f"Date range: {START_DATE} - {END_DATE} (24 months)")
    print()

    # Get top drugs
    top_drugs = get_top_drugs_by_serious_aes(limit=max_drugs)

    if not top_drugs:
        print("❌ No drugs found. Exiting.")
        return

    print("\n" + "="*80)
    print(f"STEP 2: Analyzing {len(top_drugs)} drugs for statistical spikes")
    print("="*80)

    if len(top_drugs) <= 20:
        print(f"🔍 Processing {len(top_drugs)} drugs (this should be quick...)")
    else:
        print(f"🔍 Processing {len(top_drugs)} drugs (this may take several minutes...)")

    print()

    discovered_signals = []

    # SAE types to track
    sae_types = ["Death", "Hospitalization", "Disability", "LifeThreatening"]

    for i, (drug_name, ae_count) in enumerate(top_drugs, 1):
        print(f"\n[{i}/{len(top_drugs)}] Analyzing: {drug_name}")
        print(f"  Total serious AEs: {ae_count:,}")

        # Get quarterly breakdown
        quarterly_data = get_quarterly_serious_ae_counts(drug_name)

        # Calculate metrics and score for EACH SAE type
        drug_signals = []
        for sae_type in sae_types:
            metrics = calculate_signal_metrics(quarterly_data, sae_type)

            # Skip if no events reported
            if metrics["total_count"] == 0:
                continue

            # Score this SAE type
            score, stage, category = score_signal(metrics, sae_type)

            print(f"  {sae_type}: {metrics['baseline_count']} → {metrics['recent_count']} "
                  f"({metrics['velocity']:+.1f}%) - Score: {score:.1f}")

            # Store if above threshold
            if score >= min_score:
                drug_signals.append({
                    "drug_name": drug_name,
                    "manufacturer": "Unknown",  # TODO: Look up from drug database
                    "sae_type": sae_type,
                    "metrics": metrics,
                    "score": score,
                    "stage": stage,
                    "category": category
                })

        # Add all signals for this drug that passed threshold
        if drug_signals:
            discovered_signals.extend(drug_signals)
            print(f"  ✓ {len(drug_signals)} SIGNAL(S) DETECTED - Adding to watchlist")
        else:
            print(f"  ○ No signals above threshold")

    # Sort by score
    discovered_signals.sort(key=lambda x: x["score"], reverse=True)

    print("\n" + "="*80)
    print(f"STEP 3: Inserting {len(discovered_signals)} signals into database")
    print("="*80)
    print()

    inserted_count = 0

    for i, signal in enumerate(discovered_signals, 1):
        print(f"[{i}/{len(discovered_signals)}] Inserting: {signal['drug_name']} - "
              f"{signal['sae_type']} (Score: {signal['score']:.1f})")

        candidate_id = insert_signal_into_database(
            drug_name=signal['drug_name'],
            manufacturer=signal['manufacturer'],
            sae_type=signal['sae_type'],
            metrics=signal['metrics'],
            score=signal['score'],
            stage=signal['stage'],
            category=signal['category']
        )

        if candidate_id:
            print(f"  ✓ Candidate ID: {candidate_id}")
            inserted_count += 1
        else:
            print(f"  ✗ Failed to insert")

    print("\n" + "="*80)
    print("DISCOVERY COMPLETE")
    print("="*80)
    print(f"\nResults:")
    print(f"  Drugs analyzed: {len(top_drugs)}")
    print(f"  Signals detected: {len(discovered_signals)}")
    print(f"  Inserted to database: {inserted_count}")
    print()
    print("📊 Refresh your dashboard to see the watchlist")
    print()

    # Show top 10
    if discovered_signals:
        print("Top 10 signals by score:")
        print()
        for i, sig in enumerate(discovered_signals[:10], 1):
            print(f"  {i:2d}. {sig['drug_name']:25s} [{sig['sae_type']:15s}] - Score: {sig['score']:5.1f} ({sig['stage']})")
            print(f"      Count: {sig['metrics']['baseline_count']} → "
                  f"{sig['metrics']['recent_count']} ({sig['metrics']['velocity']:+.1f}%)")


if __name__ == "__main__":
    # Ensure database constraints exist
    print("Ensuring database constraints...")
    try:
        with get_cursor() as cur:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_defendants_name ON defendants(name)")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_products_defendant_name ON products(defendant_id, name)")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_injuries_name ON injuries(name)")
        print("✓ Constraints verified\n")
    except Exception as e:
        print(f"⚠️  Constraint creation failed: {e}\n")

    # Run discovery pipeline
    # TEST MODE: Start with 10 drugs to validate schema compatibility
    discover_and_populate_signals(
        max_drugs=10,       # TEST: Analyze top 10 drugs first
        min_score=20        # AWARENESS threshold or higher
    )
