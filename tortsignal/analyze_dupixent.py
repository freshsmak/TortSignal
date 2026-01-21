"""Deep dive analysis of DUPIXENT adverse events."""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENFDA_API_KEY")

def get_reactions_for_drug(drug_name, start_date, end_date, limit=50):
    """Get top adverse reactions for a specific drug."""
    date_range = f"[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]"

    params = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}"',
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": limit
    }

    response = requests.get("https://api.fda.gov/drug/event.json", params=params, timeout=30)
    response.raise_for_status()

    return [(item['term'], item['count']) for item in response.json().get('results', [])]

def get_serious_events(drug_name, start_date, end_date):
    """Count serious adverse events."""
    date_range = f"[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]"

    # Get total reports
    params_total = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}"',
        "limit": 1
    }

    response_total = requests.get("https://api.fda.gov/drug/event.json", params=params_total, timeout=30)
    response_total.raise_for_status()
    total = response_total.json().get('meta', {}).get('results', {}).get('total', 0)

    # Get serious reports
    params_serious = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}" AND serious:1',
        "limit": 1
    }

    response_serious = requests.get("https://api.fda.gov/drug/event.json", params=params_serious, timeout=30)
    response_serious.raise_for_status()
    serious = response_serious.json().get('meta', {}).get('results', {}).get('total', 0)

    return total, serious

print("="*70)
print("DUPIXENT (dupilumab) - DEEP DIVE ANALYSIS")
print("="*70)
print("\nManufacturer: Sanofi / Regeneron")
print("Indication: Atopic dermatitis, asthma, chronic rhinosinusitis")
print("FDA Approval: 2017")
print("Annual Sales: $11B+ (2023)")

drug_name = "DUPIXENT"

# Q4 2024 analysis
q4_2024_start = datetime(2024, 10, 1)
q4_2024_end = datetime(2024, 12, 31)

# Q4 2023 baseline
q4_2023_start = datetime(2023, 10, 1)
q4_2023_end = datetime(2023, 12, 31)

print("\n" + "="*70)
print("ADVERSE EVENT BREAKDOWN - Q4 2024")
print("="*70)

print(f"\nFetching adverse reactions for Q4 2024...")
reactions_2024 = get_reactions_for_drug(drug_name, q4_2024_start, q4_2024_end, limit=30)

print(f"\n{'Rank':<5} {'Adverse Reaction':<45} {'Reports':<10}")
print("-"*70)

for i, (reaction, count) in enumerate(reactions_2024[:20], 1):
    print(f"{i:<5} {reaction[:44]:<45} {count:,}")

print("\n" + "="*70)
print("SERIOUS ADVERSE EVENTS")
print("="*70)

print(f"\nAnalyzing serious events for Q4 2024...")
total_2024, serious_2024 = get_serious_events(drug_name, q4_2024_start, q4_2024_end)
serious_pct_2024 = (serious_2024 / total_2024 * 100) if total_2024 > 0 else 0

print(f"\nQ4 2024:")
print(f"  Total reports:   {total_2024:,}")
print(f"  Serious events:  {serious_2024:,} ({serious_pct_2024:.1f}%)")

print(f"\nAnalyzing serious events for Q4 2023...")
total_2023, serious_2023 = get_serious_events(drug_name, q4_2023_start, q4_2023_end)
serious_pct_2023 = (serious_2023 / total_2023 * 100) if total_2023 > 0 else 0

print(f"\nQ4 2023:")
print(f"  Total reports:   {total_2023:,}")
print(f"  Serious events:  {serious_2023:,} ({serious_pct_2023:.1f}%)")

print(f"\nYear-over-year change:")
serious_change = ((serious_2024 - serious_2023) / serious_2023 * 100) if serious_2023 > 0 else 0
print(f"  Serious events: {serious_2024 - serious_2023:+,} ({serious_change:+.1f}%)")

# Identify concerning trends
print("\n" + "="*70)
print("🚨 PRODUCT LIABILITY ASSESSMENT")
print("="*70)

print(f"\nFetching Q4 2023 reactions for comparison...")
reactions_2023 = get_reactions_for_drug(drug_name, q4_2023_start, q4_2023_end, limit=30)
reactions_2023_dict = {r[0]: r[1] for r in reactions_2023}

print(f"\nTop reactions with significant increases:")
print(f"{'Reaction':<45} {'Q4 2024':<10} {'Q4 2023':<10} {'Change':<10}")
print("-"*70)

reaction_spikes = []
for reaction, count_2024 in reactions_2024[:15]:
    count_2023 = reactions_2023_dict.get(reaction, 0)
    if count_2023 > 0:
        pct_change = ((count_2024 - count_2023) / count_2023) * 100
        if pct_change > 30:  # At least 30% increase
            reaction_spikes.append((reaction, count_2024, count_2023, pct_change))

reaction_spikes.sort(key=lambda x: x[3], reverse=True)

for reaction, count_2024, count_2023, pct_change in reaction_spikes[:10]:
    print(f"{reaction[:44]:<45} {count_2024:,}      {count_2023:,}      +{pct_change:.0f}%")

print("\n" + "="*70)
print("💡 LITIGATION POTENTIAL")
print("="*70)

# Look for high-liability reactions
liability_keywords = [
    'DEATH', 'CANCER', 'BLINDNESS', 'STROKE', 'HEART', 'FAILURE',
    'NECROSIS', 'INJURY', 'PERMANENT', 'DISABILITY', 'AMPUTATION'
]

concerning_reactions = []
for reaction, count in reactions_2024:
    for keyword in liability_keywords:
        if keyword in reaction.upper():
            concerning_reactions.append((reaction, count))
            break

if concerning_reactions:
    print("\n⚠️  HIGH-LIABILITY ADVERSE EVENTS DETECTED:\n")
    for reaction, count in concerning_reactions[:10]:
        print(f"  • {reaction}: {count:,} reports")
else:
    print("\nNo high-severity events with liability keywords found in top reactions.")

print("\n" + "="*70)
print("RECOMMENDATION")
print("="*70)

print(f"""
Status: {'🔴 HIGH PRIORITY' if serious_change > 40 else '🟡 MONITOR'}

Key Findings:
  • +{(total_2024 - total_2023):,} total reports (+{((total_2024 - total_2023) / total_2023 * 100):.1f}%)
  • +{(serious_2024 - serious_2023):,} serious events (+{serious_change:.1f}%)
  • {serious_pct_2024:.1f}% of reports are serious adverse events

Next Steps:
  1. Cross-reference with PACER for existing litigation
  2. Review top adverse reactions for causation patterns
  3. Identify plaintiff law firms already working on this
  4. Assess market size and potential claimant pool
  5. Evaluate statute of limitations windows by jurisdiction

DUPIXENT represents a potential early-stage mass tort signal worth monitoring.
""")

print("="*70)
