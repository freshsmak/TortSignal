#!/usr/bin/env python3
"""
Check if drugcharacterization field is populated in FAERS
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

# Get sample death cases for calcium and check if drugcharacterization exists
drug_escaped = "CALCIUM"
death_query = (
    f'receivedate:[{START_DATE}+TO+{END_DATE}]'
    f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
    f'+AND+seriousnessdeath:1'
)

url = f"{FAERS_API_BASE}?search={death_query}&limit=10&api_key={api_key}"

print("Checking if 'drugcharacterization' field exists in FAERS reports...")
print("="*80)

try:
    response = requests.get(url, timeout=30)
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])

        print(f"Retrieved {len(results)} sample cases for CALCIUM deaths\n")

        for i, case in enumerate(results[:5], 1):
            print(f"Case {i}:")
            drugs = case.get('patient', {}).get('drug', [])

            for j, drug in enumerate(drugs[:5], 1):  # Show first 5 drugs
                drug_name = drug.get('medicinalproduct', 'UNKNOWN')
                characterization = drug.get('drugcharacterization', 'MISSING')

                # Map characterization codes
                char_map = {
                    '1': 'Primary Suspect',
                    '2': 'Secondary Suspect',
                    '3': 'Concomitant',
                    'MISSING': '❌ FIELD NOT PRESENT'
                }

                char_label = char_map.get(str(characterization), f'Unknown code: {characterization}')

                print(f"  Drug {j}: {drug_name:30s} - {char_label}")

            if len(drugs) > 5:
                print(f"  ... and {len(drugs) - 5} more drugs")
            print()

    else:
        print(f"API error: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")

print("="*80)
print("ANALYSIS:")
print("If 'drugcharacterization' is MISSING from most reports, the filter won't work.")
print("Alternative approaches:")
print("1. Count single-drug cases only (drug list length = 1)")
print("2. Exclude known concomitant drugs (vitamins, supplements)")
print("3. Use reaction terms to filter (exclude generic 'death' reactions)")
