#!/usr/bin/env python3
"""
Analyze distribution of drugcharacterization codes for calcium deaths
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

def analyze_characterization(drug_name):
    """
    Get count of deaths by characterization code.
    """
    print(f"\n{'='*80}")
    print(f"Analyzing: {drug_name}")
    print('='*80)

    drug_escaped = drug_name.replace('"', '\\"')

    # Count deaths by characterization code
    char_map = {
        '1': 'Primary Suspect',
        '2': 'Secondary Suspect',
        '3': 'Concomitant',
        '4': 'Interacting'
    }

    for code, label in char_map.items():
        query = (
            f'receivedate:[{START_DATE}+TO+{END_DATE}]'
            f'+AND+patient.drug.medicinalproduct:"{drug_escaped}"'
            f'+AND+patient.drug.drugcharacterization:{code}'
            f'+AND+seriousnessdeath:1'
        )

        url = f"{FAERS_API_BASE}?search={query}&limit=1&api_key={api_key}"

        try:
            response = requests.get(url, timeout=30)
            time.sleep(0.3)

            if response.status_code == 200:
                count = response.json().get('meta', {}).get('results', {}).get('total', 0)
                print(f"  Code {code} ({label:20s}): {count:6,} deaths")
            else:
                print(f"  Code {code} ({label:20s}): API error")

        except Exception as e:
            print(f"  Code {code} ({label:20s}): Error - {e}")

# Test drugs
drugs = ["CALCIUM", "FOLIC ACID", "OZEMPIC", "METHOTREXATE"]

print("\nDRUG CHARACTERIZATION DISTRIBUTION FOR DEATH CASES")
print("="*80)

for drug in drugs:
    analyze_characterization(drug)

print(f"\n{'='*80}")
print("EXPECTED:")
print("- Calcium/Folic Acid: Mostly code 2 (Secondary) or 3 (Concomitant)")
print("- Ozempic: Mostly code 1 (Primary)")
print("\nIf calcium shows mostly code 1, it means it's being reported as PRIMARY")
print("suspect even though it's a supplement. This is a reporting quality issue.")
