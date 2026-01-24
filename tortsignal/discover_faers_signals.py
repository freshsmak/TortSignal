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
DRUG_LABEL_API_BASE = "https://api.fda.gov/drug/label.json"

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

# LITIGATION INTELLIGENCE FILTERS
# Based on reverse-engineering major pharma tort MDLs (2014-2025)

# High litigation risk drug classes
WHITELIST_DRUG_CLASSES = [
    'glp-1 agonist', 'glp-1', 'incretin mimetic',
    'sglt2 inhibitor', 'sglt-2', 'gliflozin',
    'h2 blocker', 'h2 antagonist', 'h2-blocker',
    'proton pump inhibitor', 'ppi',
    'anticoagulant', 'blood thinner', 'factor xa inhibitor',
    'weight loss', 'obesity', 'anorectic',
    'phosphodiesterase inhibitor', 'pde5 inhibitor',  # ED drugs
]

# Low litigation risk drug classes (expected high SAEs due to disease severity)
BLACKLIST_DRUG_CLASSES = [
    'chemotherapy', 'antineoplastic', 'cytotoxic',
    'antiretroviral', 'hiv', 'protease inhibitor',
    'immunosuppressant', 'immunosuppressive',
    'antimicrobial', 'antibiotic', 'antibacterial',
]

# Indication severity scores (1=cosmetic/lifestyle, 10=terminal/supplement)
# Supplements at 10 means very low litigation risk UNLESS unexpectedness is extreme
INDICATION_SCORES = {
    'cosmetic': 1, 'beauty': 1, 'aesthetic': 1,
    'weight loss': 2, 'obesity': 2, 'overweight': 2,
    'heartburn': 2, 'gerd': 2, 'reflux': 2,
    'erectile dysfunction': 2, 'impotence': 2,
    'type 2 diabetes': 3, 'diabetes mellitus': 3, 'diabetes': 3,
    'contraception': 3, 'birth control': 3,
    'atrial fibrillation': 4, 'afib': 4, 'a-fib': 4,
    'hypertension': 4, 'high blood pressure': 4, 'cholesterol': 4,
    'inflammation': 5, 'inflammatory': 5, 'arthritis': 5, 'rheumatoid': 5,
    'pain': 4, 'analgesic': 4,
    'deep vein thrombosis': 5, 'dvt': 5, 'thrombosis': 5,
    'schizophrenia': 6, 'psychosis': 6,
    'bipolar': 6, 'bipolar disorder': 6,
    'hiv': 8, 'aids': 8, 'human immunodeficiency': 8,
    'cancer': 9, 'carcinoma': 9, 'tumor': 9, 'malignancy': 9, 'oncology': 9, 'neoplasm': 9,
    'transplant': 9, 'organ rejection': 9,
    'supplement': 10, 'vitamin': 10, 'mineral': 10, 'dietary supplement': 10,
}

# Supplement/vitamin keywords for detection (low litigation unless contaminated)
# Detects via drug name matching
SUPPLEMENT_KEYWORDS = [
    'calcium', 'folic acid', 'folate', 'vitamin', 'multivitamin', 'cholecalciferol',
    'cyanocobalamin', 'ascorbic acid', 'iron', 'zinc', 'magnesium',
    'potassium', 'supplement', 'dietary supplement', 'mineral',
    'thiamine', 'riboflavin', 'niacin', 'pyridoxine', 'biotin',
]

# Expected baseline death rates per 10,000 patients by drug class
BASELINE_DEATH_RATES = {
    'chemotherapy': 500,        # 5% mortality expected
    'immunosuppressant': 200,   # 2% mortality expected
    'antiretroviral': 100,      # 1% mortality expected
    'anticoagulant': 50,        # 0.5% bleeding mortality expected
    'antipsychotic': 30,        # 0.3% sudden cardiac death
    'diabetes': 10,             # 0.1% baseline
    'heartburn': 1,             # 0.01% (essentially zero)
    'weight loss': 1,           # Near zero expected
    'cosmetic': 0.1,            # Near zero expected
    'supplement': 0.01,         # Near zero (unless contaminated - L-Tryptophan pattern)
    'vitamin': 0.01,            # Near zero
}


def get_api_key() -> str:
    """Get OpenFDA API key from config."""
    config = get_config()
    return config.openfda.api_key


def is_supplement(drug_name: str, drug_metadata: Dict) -> bool:
    """
    Detect if a drug is a supplement/vitamin.

    Args:
        drug_name: Name of drug
        drug_metadata: Enriched metadata dict

    Returns:
        True if supplement detected
    """
    drug_name_lower = drug_name.lower()
    drug_class_lower = drug_metadata.get('drug_class', '').lower()

    # Check drug name
    for keyword in SUPPLEMENT_KEYWORDS:
        if keyword in drug_name_lower or keyword in drug_class_lower:
            return True

    return False


def enrich_drug_metadata(drug_name: str) -> Dict:
    """
    Query OpenFDA drug label API to enrich drug metadata.

    Args:
        drug_name: Name of drug to look up

    Returns:
        Dict with drug_class, indication, approval_year, manufacturer
    """
    api_key = get_api_key()

    # Default metadata (used if API fails)
    metadata = {
        'drug_class': 'unknown',
        'indication': 'unknown',
        'approval_year': 2010,  # Default to moderate age
        'manufacturer': 'Unknown',
        'pharmacologic_class': [],
        'indications_text': ''
    }

    try:
        # Search drug label database
        url = f"{DRUG_LABEL_API_BASE}?search=openfda.brand_name:\"{drug_name}\"+openfda.generic_name:\"{drug_name}\"&limit=1&api_key={api_key}"

        response = requests.get(url, timeout=10)
        time.sleep(0.25)  # Rate limiting

        if response.status_code != 200:
            return metadata

        data = response.json()

        if 'results' not in data or len(data['results']) == 0:
            return metadata

        result = data['results'][0]
        openfda = result.get('openfda', {})

        # Extract manufacturer
        if 'manufacturer_name' in openfda:
            metadata['manufacturer'] = openfda['manufacturer_name'][0]

        # Extract pharmacologic class
        if 'pharm_class_epc' in openfda:
            metadata['pharmacologic_class'] = openfda['pharm_class_epc']
            metadata['drug_class'] = openfda['pharm_class_epc'][0].lower()

        # Extract indication from indications_and_usage
        if 'indications_and_usage' in result:
            indication_text = result['indications_and_usage'][0]
            metadata['indications_text'] = indication_text[:500]  # First 500 chars

            # Extract likely indication from text
            indication_lower = indication_text.lower()

            # Try to match indication keywords (sorted by specificity - longest first)
            sorted_indications = sorted(INDICATION_SCORES.keys(), key=len, reverse=True)
            for indication_key in sorted_indications:
                if indication_key in indication_lower:
                    metadata['indication'] = indication_key
                    break

        # Fallback: Try to infer from drug class
        if metadata['indication'] == 'unknown' and metadata['drug_class'] != 'unknown':
            drug_class_lower = metadata['drug_class'].lower()
            if 'anticoagulant' in drug_class_lower or 'factor xa' in drug_class_lower:
                metadata['indication'] = 'atrial fibrillation'
            elif 'corticosteroid' in drug_class_lower:
                metadata['indication'] = 'inflammation'
            elif 'statin' in drug_class_lower or 'hmg-coa reductase' in drug_class_lower:
                metadata['indication'] = 'hypertension'
            elif 'diuretic' in drug_class_lower:
                metadata['indication'] = 'hypertension'

        # Extract approval year from application number (if available)
        # Format: NXXXXXXX where N=type (N=NDA, A=ANDA, B=BLA), XXXXXX=sequential number
        if 'application_number' in openfda:
            app_number = openfda['application_number'][0]
            # Rough heuristic: Lower numbers = older drugs
            # NDAs started in 1938, we can estimate year from number range
            # This is approximate - ideal would be query Drugs@FDA database
            try:
                num_part = int(app_number[1:])
                if num_part < 20000:
                    metadata['approval_year'] = 1990
                elif num_part < 21000:
                    metadata['approval_year'] = 2000
                elif num_part < 22000:
                    metadata['approval_year'] = 2010
                else:
                    metadata['approval_year'] = 2015
            except:
                pass

        # Check if supplement/vitamin (overrides indication)
        # This catches calcium, folic acid, vitamins, etc.
        if is_supplement(drug_name, metadata):
            metadata['indication'] = 'supplement'
            metadata['drug_class'] = 'supplement'

        return metadata

    except Exception as e:
        print(f"  ⚠️  Drug enrichment failed: {e}")
        return metadata


def get_indication_severity(drug_metadata: Dict) -> int:
    """
    Return 1-10 severity score where 1=cosmetic, 10=terminal.
    Lower score = higher litigation risk.
    """
    indication_text = drug_metadata.get('indications_text', '').lower()
    indication = drug_metadata.get('indication', '').lower()

    # Check indication scores
    for key, score in INDICATION_SCORES.items():
        if key in indication or key in indication_text:
            return score

    return 5  # Default: moderate severity


def check_drug_class_filter(drug_metadata: Dict) -> float:
    """
    Return multiplier based on drug class whitelist/blacklist.

    SOFTENED multipliers - use history as guide, not constraint:
        1.2 = whitelisted (gentle boost for known high-risk classes)
        0.7 = blacklisted (gentle penalty, not elimination)
        1.0 = neutral

    This allows discovery of new drug class patterns while still using
    historical MDL data to inform scoring.
    """
    drug_class = drug_metadata.get('drug_class', '').lower()
    pharm_classes = [pc.lower() for pc in drug_metadata.get('pharmacologic_class', [])]

    # Check whitelist (gentle boost)
    for wl_class in WHITELIST_DRUG_CLASSES:
        if wl_class in drug_class or any(wl_class in pc for pc in pharm_classes):
            return 1.2

    # Check blacklist (gentle penalty, not elimination)
    for bl_class in BLACKLIST_DRUG_CLASSES:
        if bl_class in drug_class or any(bl_class in pc for pc in pharm_classes):
            return 0.7

    return 1.0  # Neutral


def get_litigation_window_score(approval_year: int) -> int:
    """
    Return 0-10 score for litigation timing sweet spot.
    Based on pattern: 2-7 years post-approval = highest MDL formation.
    """
    current_year = 2026  # datetime.now().year
    years_since_approval = current_year - approval_year

    if years_since_approval < 2:
        return 2  # Too early
    elif 2 <= years_since_approval <= 7:
        return 10  # SWEET SPOT
    elif 7 < years_since_approval <= 15:
        return 6  # Still viable
    else:
        return 3  # Old drug


def get_unexpectedness_multiplier(drug_metadata: Dict, observed_deaths_per_10k: float) -> float:
    """
    Calculate unexpectedness multiplier based on observed vs expected death rates.

    Returns:
        1.0 = expected rates
        1.5 = 2-10x expected (moderate concern)
        2.0 = 10-100x expected (high concern)
        3.0 = 100x+ expected (extreme concern - contamination pattern)
    """
    drug_class = drug_metadata.get('drug_class', 'unknown').lower()

    # Find matching baseline
    expected = 10  # Default
    for class_name, baseline in BASELINE_DEATH_RATES.items():
        if class_name in drug_class:
            expected = baseline
            break

    if expected == 0 or observed_deaths_per_10k == 0:
        return 1.0

    # Calculate ratio
    ratio = observed_deaths_per_10k / expected

    if ratio > 100:
        # Extreme unexpectedness (L-Tryptophan contamination pattern)
        return 3.0
    elif ratio > 10:
        # High unexpectedness
        return 2.0
    elif ratio > 2:
        # Moderate unexpectedness
        return 1.5
    else:
        # Expected or below expected
        return 1.0


def calculate_litigation_risk_score(
    drug_metadata: Dict,
    faers_metrics: Dict,
    pharma_score: float
) -> float:
    """
    Calculate 0-100 litigation intelligence score.

    Combines:
    - Indication severity (lifestyle drugs = high risk)
    - Drug class filters (whitelist/blacklist)
    - Timeline sweet spot (2-7 years post-approval)
    - Unexpected SAE rate vs baseline
    - FAERS velocity (from pharma score)

    Args:
        drug_metadata: Enriched drug metadata dict
        faers_metrics: FAERS signal metrics
        pharma_score: Raw pharmacovigilance score (0-100)

    Returns:
        Float 0-100 litigation risk score
    """
    # Base score from FAERS velocity (cap at 50)
    base_score = min(pharma_score * 0.6, 50)

    # Indication severity factor (inverse - cosmetic=1.0, cancer=0.0)
    indication_severity = get_indication_severity(drug_metadata)
    indication_factor = (10 - indication_severity) / 10  # 0.0-1.0

    # Drug class multiplier
    class_multiplier = check_drug_class_filter(drug_metadata)

    # Timeline score (0-25 points) - sweet spot drugs get significant boost
    timeline_score = get_litigation_window_score(drug_metadata['approval_year']) * 2.5

    # Unexpected SAE multiplier
    total_count = faers_metrics.get('total_count', 0)
    sae_multiplier = 1.0
    contamination_spike_bonus = 0

    if total_count > 0 and faers_metrics.get('sae_type') == 'Death':
        # Rough estimate: assume 1M prescriptions per year for popular drugs
        observed_rate = (total_count / 100000) * 10000  # Deaths per 10K
        sae_multiplier = get_unexpectedness_multiplier(drug_metadata, observed_rate)

        # Special handling: Contamination detection for supplements
        # Use VELOCITY (sudden spike), not absolute rates, to avoid confounding
        # L-Tryptophan had velocity spike, not just high absolute deaths
        velocity = faers_metrics.get('velocity', 0)
        if indication_severity >= 9 and velocity > 100:  # Supplement with 100%+ spike
            # Sudden spike in supplement deaths = contamination pattern
            contamination_spike_bonus = 50

    # Composite score
    litigation_score = (
        (base_score * indication_factor * class_multiplier * sae_multiplier) +
        timeline_score +
        contamination_spike_bonus
    )

    return min(litigation_score, 100)  # Cap at 100


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
    # drugcharacterization:1 = Primary Suspect (exclude concomitant medications)
    search_query = (
        f"receivedate:[{START_DATE}+TO+{END_DATE}]"
        "+AND+serious:1"
        "+AND+patient.drug.drugcharacterization:1"
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

        # Query for deaths (Primary Suspect only - excludes concomitant meds)
        death_query = (
            f'receivedate:[{start}+TO+{end}]'
            f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
            f'+AND+patient.drug.drugcharacterization:1'
            f'+AND+seriousnessdeath:1'
        )

        death_result = query_faers(death_query, limit=1)
        if death_result and "meta" in death_result:
            counts["Death"] = death_result["meta"]["results"]["total"]

        # Query for hospitalizations (Primary Suspect only)
        hosp_query = (
            f'receivedate:[{start}+TO+{end}]'
            f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
            f'+AND+patient.drug.drugcharacterization:1'
            f'+AND+seriousnesshospitalization:1'
        )

        hosp_result = query_faers(hosp_query, limit=1)
        if hosp_result and "meta" in hosp_result:
            counts["Hospitalization"] = hosp_result["meta"]["results"]["total"]

        # Query for life-threatening (Primary Suspect only)
        life_query = (
            f'receivedate:[{start}+TO+{end}]'
            f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
            f'+AND+patient.drug.drugcharacterization:1'
            f'+AND+seriousnesslifethreatening:1'
        )

        life_result = query_faers(life_query, limit=1)
        if life_result and "meta" in life_result:
            counts["LifeThreatening"] = life_result["meta"]["results"]["total"]

        # Query for disability (Primary Suspect only)
        disability_query = (
            f'receivedate:[{start}+TO+{end}]'
            f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
            f'+AND+patient.drug.drugcharacterization:1'
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
    drug_metadata: Dict,
    sae_type: str,
    metrics: Dict,
    pharma_score: float,
    litigation_score: float,
    stage: str,
    category: str
) -> Optional[int]:
    """
    Insert discovered signal into Safety Intelligence Graph.

    Args:
        drug_name: Name of the drug
        manufacturer: Manufacturer name
        drug_metadata: Enriched drug metadata dict
        sae_type: Type of SAE (Death, Hospitalization, Disability, LifeThreatening)
        metrics: Signal metrics
        pharma_score: Pharmacovigilance score (0-100)
        litigation_score: Litigation intelligence score (0-100)
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

            # 2. Insert/get product (drug) - store enriched metadata
            product_metadata = {
                'drug_class': drug_metadata.get('drug_class', 'unknown'),
                'indication': drug_metadata.get('indication', 'unknown'),
                'approval_year': drug_metadata.get('approval_year', 0),
                'pharmacologic_class': drug_metadata.get('pharmacologic_class', [])
            }

            cur.execute("""
                INSERT INTO products (name, product_type, metadata_json)
                VALUES (%s, 'pharmaceutical', %s)
                ON CONFLICT (name) DO UPDATE
                SET metadata_json = EXCLUDED.metadata_json
                RETURNING product_id
            """, (drug_name, Json(product_metadata)))

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

            # Map to existing schema columns (death_count, serious_count, report_count)
            death_count = metrics["total_count"] if sae_type == "Death" else 0
            serious_count = metrics["total_count"]  # All SAE types are serious by definition

            cur.execute("""
                INSERT INTO product_signals (
                    product_id,
                    injury_id,
                    signal_type,
                    severity_score,
                    death_count,
                    serious_count,
                    report_count,
                    first_detected_at,
                    last_updated_at
                )
                VALUES (%s, %s, 'adverse_event_spike', %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING signal_id
            """, (
                product_id,
                injury_id,
                score,
                death_count,
                serious_count,
                metrics["total_count"]
            ))

            result = cur.fetchone()
            signal_id = result['signal_id']

            # 5. Insert candidate
            # Generate candidate_key for deduplication (normalized defendant|product)
            candidate_key = f"{manufacturer.upper()}|{drug_name.upper()}"

            # Store both pharma_score (in score_total) and litigation_score (in score_components)
            # This maintains backward compatibility while adding litigation intelligence
            cur.execute("""
                INSERT INTO candidates (
                    candidate_key,
                    defendant_id,
                    product_id,
                    injury_id,
                    defendant_text,
                    product_text,
                    injury_text,
                    category,
                    score_total,
                    score_components,
                    metrics_json,
                    first_seen_at,
                    last_seen_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (candidate_key) DO UPDATE
                SET score_total = EXCLUDED.score_total,
                    score_components = EXCLUDED.score_components,
                    metrics_json = EXCLUDED.metrics_json,
                    last_seen_at = CURRENT_TIMESTAMP
                RETURNING candidate_id
            """, (
                candidate_key,
                defendant_id,
                product_id,
                injury_id,
                manufacturer,
                drug_name,
                sae_type,  # Use actual SAE type (Death, Hospitalization, etc.)
                category,
                litigation_score,  # Use litigation score as primary (for law firm customers)
                Json({
                    "pharma_score": pharma_score,
                    "litigation_score": litigation_score
                }),
                Json({
                    "velocity_7d": metrics["velocity"],
                    "breadth_states": 50,  # FAERS is national
                    "signal_metadata": signal_metadata,
                    "drug_metadata": {
                        "drug_class": drug_metadata.get('drug_class', 'unknown'),
                        "indication": drug_metadata.get('indication', 'unknown'),
                        "approval_year": drug_metadata.get('approval_year', 0)
                    }
                })
            ))

            result = cur.fetchone()
            candidate_id = result['candidate_id']

            # Note: signal_events is for tort_clusters (litigation tracking), not product_signals
            # FAERS discovery creates product_signals + candidates, which is sufficient for MVP

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

        # Enrich drug metadata (class, indication, approval year)
        drug_metadata = enrich_drug_metadata(drug_name)
        if drug_metadata['manufacturer'] != 'Unknown':
            print(f"  Manufacturer: {drug_metadata['manufacturer']}")
        if drug_metadata['drug_class'] != 'unknown':
            print(f"  Drug class: {drug_metadata['drug_class']}")
        if drug_metadata['indication'] != 'unknown':
            print(f"  Indication: {drug_metadata['indication']}")

        # Get quarterly breakdown
        quarterly_data = get_quarterly_serious_ae_counts(drug_name)

        # Calculate metrics and score for EACH SAE type
        drug_signals = []
        for sae_type in sae_types:
            metrics = calculate_signal_metrics(quarterly_data, sae_type)

            # Skip if no events reported
            if metrics["total_count"] == 0:
                continue

            # Score this SAE type (pharmacovigilance score)
            pharma_score, stage, category = score_signal(metrics, sae_type)

            # Calculate litigation intelligence score
            litigation_score = calculate_litigation_risk_score(
                drug_metadata,
                {**metrics, 'sae_type': sae_type},
                pharma_score
            )

            print(f"  {sae_type}: {metrics['baseline_count']} → {metrics['recent_count']} "
                  f"({metrics['velocity']:+.1f}%) - Pharma: {pharma_score:.1f}, Lit: {litigation_score:.1f}")

            # Store if EITHER score is above threshold
            # (Pharma score for hospital customers, Litigation score for law firms)
            if pharma_score >= min_score or litigation_score >= min_score:
                drug_signals.append({
                    "drug_name": drug_name,
                    "manufacturer": drug_metadata['manufacturer'],
                    "drug_metadata": drug_metadata,
                    "sae_type": sae_type,
                    "metrics": metrics,
                    "pharma_score": pharma_score,
                    "litigation_score": litigation_score,
                    "stage": stage,
                    "category": category
                })

        # Add all signals for this drug that passed threshold
        if drug_signals:
            discovered_signals.extend(drug_signals)
            print(f"  ✓ {len(drug_signals)} SIGNAL(S) DETECTED - Adding to watchlist")
        else:
            print(f"  ○ No signals above threshold")

    # Sort by litigation score (primary metric for law firm customers)
    discovered_signals.sort(key=lambda x: x["litigation_score"], reverse=True)

    print("\n" + "="*80)
    print(f"STEP 3: Inserting {len(discovered_signals)} signals into database")
    print("="*80)
    print()

    inserted_count = 0

    for i, signal in enumerate(discovered_signals, 1):
        print(f"[{i}/{len(discovered_signals)}] Inserting: {signal['drug_name']} - "
              f"{signal['sae_type']} (Lit: {signal['litigation_score']:.1f}, Pharma: {signal['pharma_score']:.1f})")

        candidate_id = insert_signal_into_database(
            drug_name=signal['drug_name'],
            manufacturer=signal['manufacturer'],
            drug_metadata=signal['drug_metadata'],
            sae_type=signal['sae_type'],
            metrics=signal['metrics'],
            pharma_score=signal['pharma_score'],
            litigation_score=signal['litigation_score'],
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

    # Show top 10 by litigation score
    if discovered_signals:
        print("Top 10 signals by LITIGATION INTELLIGENCE SCORE:")
        print()
        for i, sig in enumerate(discovered_signals[:10], 1):
            print(f"  {i:2d}. {sig['drug_name']:25s} [{sig['sae_type']:15s}] - "
                  f"Lit: {sig['litigation_score']:5.1f}, Pharma: {sig['pharma_score']:5.1f}")
            print(f"      Count: {sig['metrics']['baseline_count']} → "
                  f"{sig['metrics']['recent_count']} ({sig['metrics']['velocity']:+.1f}%) "
                  f"- {sig['drug_metadata'].get('indication', 'unknown')}")


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
