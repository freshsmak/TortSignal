"""Quick script to find real emerging signals in 2024 FDA data."""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENFDA_API_KEY")

def get_top_drugs(start_date, end_date, limit=50):
    """Get top drugs for a date range."""
    date_range = f"[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]"

    params = {
        "api_key": api_key,
        "search": f"receivedate:{date_range}",
        "count": "patient.drug.openfda.brand_name.exact",
        "limit": limit
    }

    response = requests.get("https://api.fda.gov/drug/event.json", params=params, timeout=30)
    response.raise_for_status()

    return {item['term']: item['count'] for item in response.json().get('results', [])}

print("="*70)
print("FINDING EMERGING DRUG SIGNALS IN 2024")
print("="*70)

# Q4 2024 (most recent)
q4_2024_start = datetime(2024, 10, 1)
q4_2024_end = datetime(2024, 12, 31)

# Q4 2023 (baseline for comparison)
q4_2023_start = datetime(2023, 10, 1)
q4_2023_end = datetime(2023, 12, 31)

print(f"\nFetching Q4 2024 data ({q4_2024_start.date()} to {q4_2024_end.date()})...")
q4_2024_drugs = get_top_drugs(q4_2024_start, q4_2024_end, limit=100)
print(f"Got {len(q4_2024_drugs)} drugs")

print(f"\nFetching Q4 2023 baseline ({q4_2023_start.date()} to {q4_2023_end.date()})...")
q4_2023_drugs = get_top_drugs(q4_2023_start, q4_2023_end, limit=100)
print(f"Got {len(q4_2023_drugs)} drugs")

# Find drugs with biggest increases
signals = []

for drug, q4_2024_count in q4_2024_drugs.items():
    q4_2023_count = q4_2023_drugs.get(drug, 0)

    # Skip if no baseline (likely new drug or renamed)
    if q4_2023_count == 0:
        continue

    # Calculate percentage increase
    pct_change = ((q4_2024_count - q4_2023_count) / q4_2023_count) * 100

    # Only flag significant increases
    if pct_change > 50 and q4_2024_count > 100:  # At least 50% increase and 100+ reports
        signals.append({
            'drug': drug,
            'q4_2024': q4_2024_count,
            'q4_2023': q4_2023_count,
            'change_pct': pct_change,
            'change_abs': q4_2024_count - q4_2023_count
        })

# Sort by percentage change
signals.sort(key=lambda x: x['change_pct'], reverse=True)

print("\n" + "="*70)
print(f"🚨 FOUND {len(signals)} EMERGING SIGNALS (>50% increase, >100 reports)")
print("="*70)

if len(signals) == 0:
    print("\nNo significant spikes detected with current criteria.")
    print("This could mean:")
    print("  - The market is stable")
    print("  - Need to adjust thresholds")
    print("  - Need longer time window")
else:
    print(f"\n{'Rank':<5} {'Drug Name':<35} {'Q4 2024':<10} {'Q4 2023':<10} {'Change':<10}")
    print("-"*70)

    for i, signal in enumerate(signals[:25], 1):
        drug = signal['drug'][:34]
        q4_2024 = f"{signal['q4_2024']:,}"
        q4_2023 = f"{signal['q4_2023']:,}"
        change = f"+{signal['change_pct']:.0f}%"

        print(f"{i:<5} {drug:<35} {q4_2024:<10} {q4_2023:<10} {change:<10}")

    # Highlight top 5
    print("\n" + "="*70)
    print("TOP 5 SIGNALS TO INVESTIGATE:")
    print("="*70)

    for i, signal in enumerate(signals[:5], 1):
        print(f"\n{i}. {signal['drug']}")
        print(f"   Q4 2024: {signal['q4_2024']:,} reports")
        print(f"   Q4 2023: {signal['q4_2023']:,} reports")
        print(f"   Change: +{signal['change_pct']:.1f}% ({signal['change_abs']:+,} reports)")
        print(f"   🎯 EMERGING SIGNAL - Investigate for product liability")

print("\n" + "="*70)
