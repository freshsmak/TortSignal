"""Find drugs with increasing SERIOUS adverse events - true mass tort candidates."""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENFDA_API_KEY")

def get_drugs_with_serious_outcomes(reaction_type, start_date, end_date, limit=30):
    """Get drugs associated with specific serious outcomes."""
    date_range = f"[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]"

    params = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND serious:1 AND patient.reaction.reactionmeddrapt:"{reaction_type}"',
        "count": "patient.drug.openfda.brand_name.exact",
        "limit": limit
    }

    response = requests.get("https://api.fda.gov/drug/event.json", params=params, timeout=30)
    if response.status_code != 200:
        return []

    return [(item['term'], item['count']) for item in response.json().get('results', [])]

print("="*70)
print("FINDING DRUGS WITH SEVERE ADVERSE EVENTS")
print("Mass Tort Candidates: Deaths, Cancers, Permanent Injuries")
print("="*70)

# Q4 2024
q4_2024_start = datetime(2024, 10, 1)
q4_2024_end = datetime(2024, 12, 31)

# Q4 2023
q4_2023_start = datetime(2023, 10, 1)
q4_2023_end = datetime(2023, 12, 31)

# High-liability reaction types
severe_reactions = [
    ("DEATH", "Death"),
    ("CARDIAC ARREST", "Cardiac Arrest"),
    ("STROKE", "Stroke"),
    ("MYOCARDIAL INFARCTION", "Heart Attack"),
    ("CANCER", "Cancer (unspecified)"),
    ("BLINDNESS", "Blindness"),
    ("RENAL FAILURE", "Kidney Failure"),
    ("HEPATIC FAILURE", "Liver Failure"),
    ("SUICIDE ATTEMPT", "Suicide Attempt"),
    ("COMPLETED SUICIDE", "Completed Suicide"),
]

all_signals = []

for reaction_key, reaction_label in severe_reactions:
    print(f"\n{'='*70}")
    print(f"Analyzing: {reaction_label}")
    print('='*70)

    try:
        print(f"Fetching Q4 2024 data...")
        drugs_2024 = get_drugs_with_serious_outcomes(reaction_key, q4_2024_start, q4_2024_end, limit=30)

        if len(drugs_2024) == 0:
            print(f"  No data found for Q4 2024")
            continue

        print(f"Fetching Q4 2023 baseline...")
        drugs_2023 = get_drugs_with_serious_outcomes(reaction_key, q4_2023_start, q4_2023_end, limit=30)
        drugs_2023_dict = {drug: count for drug, count in drugs_2023}

        # Find drugs with significant increases
        for drug, count_2024 in drugs_2024:
            count_2023 = drugs_2023_dict.get(drug, 0)

            # Skip if no baseline
            if count_2023 == 0:
                continue

            # Calculate change
            pct_change = ((count_2024 - count_2023) / count_2023) * 100

            # Flag significant increases (>30% and at least 5 additional cases)
            if pct_change > 30 and (count_2024 - count_2023) >= 5:
                all_signals.append({
                    'drug': drug,
                    'reaction': reaction_label,
                    'count_2024': count_2024,
                    'count_2023': count_2023,
                    'change_pct': pct_change,
                    'change_abs': count_2024 - count_2023
                })

        print(f"  ✓ Found {len([s for s in all_signals if s['reaction'] == reaction_label])} signals")

    except Exception as e:
        print(f"  Error: {e}")
        continue

# Sort all signals by severity and percentage change
all_signals.sort(key=lambda x: (x['change_abs'], x['change_pct']), reverse=True)

print("\n" + "="*70)
print(f"🚨 FOUND {len(all_signals)} SEVERE ADVERSE EVENT SIGNALS")
print("="*70)

if len(all_signals) == 0:
    print("\nNo significant spikes in severe adverse events detected.")
    print("This suggests either:")
    print("  - The pharmaceutical market is relatively stable")
    print("  - Need longer time window or different thresholds")
    print("  - Most signals are in less severe reaction categories")
else:
    print(f"\n{'Rank':<5} {'Drug':<25} {'Reaction':<20} {'Q4 2024':<10} {'Q4 2023':<10} {'Change'}")
    print("-"*85)

    for i, signal in enumerate(all_signals[:30], 1):
        drug = signal['drug'][:24]
        reaction = signal['reaction'][:19]
        print(f"{i:<5} {drug:<25} {reaction:<20} {signal['count_2024']:<10} {signal['count_2023']:<10} +{signal['change_pct']:.0f}% (+{signal['change_abs']})")

    # Highlight top candidates
    print("\n" + "="*70)
    print("🎯 TOP MASS TORT CANDIDATES")
    print("="*70)

    for i, signal in enumerate(all_signals[:5], 1):
        print(f"\n{i}. {signal['drug']} - {signal['reaction']}")
        print(f"   Q4 2024: {signal['count_2024']} cases")
        print(f"   Q4 2023: {signal['count_2023']} cases")
        print(f"   Change: +{signal['change_pct']:.1f}% (+{signal['change_abs']} cases)")
        print(f"   💀 HIGH LIABILITY - Investigate immediately")

print("\n" + "="*70)
print("END OF ANALYSIS")
print("="*70)
