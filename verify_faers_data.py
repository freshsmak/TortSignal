#!/usr/bin/env python3
"""
Verify FAERS data accuracy for concerning drugs (calcium, folic acid)
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

# Date range from our discovery script
END_DATE = "20251231"
START_DATE = "20240101"

def check_drug(drug_name):
    """Query FAERS for a specific drug and show what we get."""
    print(f"\n{'='*80}")
    print(f"Checking: {drug_name}")
    print('='*80)

    # Escape for URL
    drug_escaped = drug_name.replace('"', '\\"')

    # Query 1: Total serious AEs
    search_query = (
        f'receivedate:[{START_DATE}+TO+{END_DATE}]'
        f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
        f'+AND+serious:1'
    )

    url = f"{FAERS_API_BASE}?search={search_query}&limit=1&api_key={api_key}"

    try:
        response = requests.get(url, timeout=30)
        time.sleep(0.3)

        if response.status_code == 200:
            data = response.json()
            total_serious = data.get('meta', {}).get('results', {}).get('total', 0)
            print(f"Total serious AEs: {total_serious:,}")
        else:
            print(f"API error: {response.status_code}")
            return
    except Exception as e:
        print(f"Error: {e}")
        return

    # Query 2: Deaths
    death_query = (
        f'receivedate:[{START_DATE}+TO+{END_DATE}]'
        f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
        f'+AND+seriousnessdeath:1'
    )

    url = f"{FAERS_API_BASE}?search={death_query}&limit=5&api_key={api_key}"

    try:
        response = requests.get(url, timeout=30)
        time.sleep(0.3)

        if response.status_code == 200:
            data = response.json()
            death_count = data.get('meta', {}).get('results', {}).get('total', 0)
            print(f"Deaths: {death_count:,}")

            # Show first 5 actual cases to understand context
            results = data.get('results', [])
            if results:
                print(f"\nSample death cases (first 5):")
                for i, case in enumerate(results[:5], 1):
                    # Get all drugs in the case (concomitant medications)
                    drugs = case.get('patient', {}).get('drug', [])
                    drug_names = [d.get('medicinalproduct', 'UNKNOWN') for d in drugs]

                    # Get reactions
                    reactions = case.get('patient', {}).get('reaction', [])
                    reaction_terms = [r.get('reactionmeddrapt', 'UNKNOWN') for r in reactions]

                    # Get patient info
                    patient = case.get('patient', {})
                    age = patient.get('patientonsetage', 'unknown')
                    sex = patient.get('patientsex', 'unknown')

                    print(f"\n  Case {i}:")
                    print(f"    Patient: Age {age}, Sex {sex}")
                    print(f"    All drugs reported: {', '.join(drug_names[:10])}")  # First 10 drugs
                    if len(drug_names) > 10:
                        print(f"      ... and {len(drug_names) - 10} more drugs")
                    print(f"    Reactions: {', '.join(reaction_terms[:5])}")  # First 5 reactions

        else:
            print(f"API error: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")


# Check the concerning drugs
drugs_to_check = [
    "CALCIUM",
    "FOLIC ACID",
    "OZEMPIC",  # Known litigation target (for comparison)
    "METHOTREXATE",  # Chemo drug (for comparison)
]

for drug in drugs_to_check:
    check_drug(drug)

print(f"\n{'='*80}")
print("ANALYSIS:")
print('='*80)
print("""
If calcium/folic acid show high death counts, check:
1. Are these CONCOMITANT medications (sick patients taking many drugs)?
2. Are the deaths actually CAUSED by calcium/folic acid or just reported alongside?
3. FAERS is correlation, not causation - multi-drug cases are common

Example: Cancer patient taking chemotherapy + folic acid + calcium + pain meds
→ Death attributed to ALL drugs reported, not just chemo

This is the "confounding by indication" problem in pharmacovigilance.
""")
