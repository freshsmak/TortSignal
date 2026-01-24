#!/usr/bin/env python3
"""
Test impact of Primary Suspect filter on calcium/folic acid counts
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tortsignal/src'))

import requests
import time
from config import get_config

FAERS_API_BASE = "https://api.fda.gov/drug/event.json"

config = get_config()
api_key = config.openfda.api_key

END_DATE = "20251231"
START_DATE = "20240101"

def compare_filters(drug_name):
    """Compare death counts with and without Primary Suspect filter."""
    print(f"\n{'='*80}")
    print(f"Testing: {drug_name}")
    print('='*80)

    drug_escaped = drug_name.replace('"', '\\"')

    # Query WITHOUT filter (old way - includes concomitant)
    query_old = (
        f'receivedate:[{START_DATE}+TO+{END_DATE}]'
        f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
        f'+AND+seriousnessdeath:1'
    )

    url_old = f"{FAERS_API_BASE}?search={query_old}&limit=1&api_key={api_key}"

    try:
        response = requests.get(url_old, timeout=30)
        time.sleep(0.3)
        if response.status_code == 200:
            old_count = response.json().get('meta', {}).get('results', {}).get('total', 0)
        else:
            old_count = 0
    except:
        old_count = 0

    # Query WITH filter (new way - Primary Suspect only)
    query_new = (
        f'receivedate:[{START_DATE}+TO+{END_DATE}]'
        f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
        f'+AND+patient.drug.drugcharacterization:1'
        f'+AND+seriousnessdeath:1'
    )

    url_new = f"{FAERS_API_BASE}?search={query_new}&limit=1&api_key={api_key}"

    try:
        response = requests.get(url_new, timeout=30)
        time.sleep(0.3)
        if response.status_code == 200:
            new_count = response.json().get('meta', {}).get('results', {}).get('total', 0)
        else:
            new_count = 0
    except:
        new_count = 0

    # Calculate reduction
    if old_count > 0:
        reduction_pct = ((old_count - new_count) / old_count) * 100
    else:
        reduction_pct = 0

    print(f"WITHOUT filter (all mentions):     {old_count:,} deaths")
    print(f"WITH filter (Primary Suspect):     {new_count:,} deaths")
    print(f"Reduction: {reduction_pct:.1f}% ({old_count - new_count:,} cases removed)")

    return old_count, new_count

# Test drugs
print("\n" + "="*80)
print("IMPACT OF PRIMARY SUSPECT FILTER")
print("="*80)

results = {}
test_drugs = [
    ("CALCIUM", "Expected: Large reduction (mostly concomitant)"),
    ("FOLIC ACID", "Expected: Large reduction (mostly concomitant)"),
    ("OZEMPIC", "Expected: Small reduction (mostly primary suspect)"),
    ("METHOTREXATE", "Expected: Moderate reduction (mix of primary and concomitant)"),
]

for drug_name, expectation in test_drugs:
    print(f"\n{expectation}")
    old, new = compare_filters(drug_name)
    results[drug_name] = (old, new)

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

for drug, (old, new) in results.items():
    if old > 0:
        reduction = ((old - new) / old) * 100
        print(f"{drug:20s}: {old:6,} → {new:6,} ({reduction:5.1f}% reduction)")
    else:
        print(f"{drug:20s}: No data")

print("\nExpected outcome:")
print("- Calcium/Folic Acid: 80-95% reduction (concomitant supplements)")
print("- Ozempic: 10-30% reduction (mostly primary suspect)")
print("- Methotrexate: 40-60% reduction (some chemo primary, some concomitant)")
