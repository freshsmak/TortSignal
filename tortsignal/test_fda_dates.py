"""Test FDA API with correct date format."""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENFDA_API_KEY")
base_url = "https://api.fda.gov/drug/event.json"

print("Testing FDA API with CORRECT date format (YYYY-MM-DD)...\n")

# Test recent data with proper format
end_date = datetime(2024, 12, 31)
start_date = datetime(2024, 1, 1)

date_range = f"[{start_date.strftime('%Y-%m-%d')}+TO+{end_date.strftime('%Y-%m-%d')}]"

print("="*60)
print(f"Test: 2024 drug reports with corrected date format")
print(f"Date range: {date_range}")
print("="*60)

params = {
    "api_key": api_key,
    "search": f"receivedate:{date_range}",
    "count": "patient.drug.openfda.brand_name.exact",
    "limit": 25
}

try:
    response = requests.get(base_url, params=params, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ SUCCESS!\n")

        if 'results' in data:
            print(f"Top drugs reported in 2024:")
            print(f"{'Rank':<5} {'Drug Name':<40} {'Reports':<10}")
            print("="*60)

            for i, result in enumerate(data['results'], 1):
                term = result.get('term', 'Unknown')
                count = result.get('count', 0)
                print(f"{i:<5} {term:<40} {count:,}")

            print(f"\n🎯 DATE QUERIES WORK! Now let's find emerging signals...")

            # Test Q4 2024 specifically
            print("\n" + "="*60)
            print("Q4 2024 (Oct-Dec) - Most Recent Quarter")
            print("="*60)

            q4_start = datetime(2024, 10, 1)
            q4_end = datetime(2024, 12, 31)
            q4_range = f"[{q4_start.strftime('%Y-%m-%d')}+TO+{q4_end.strftime('%Y-%m-%d')}]"

            q4_params = {
                "api_key": api_key,
                "search": f"receivedate:{q4_range}",
                "count": "patient.drug.openfda.brand_name.exact",
                "limit": 25
            }

            q4_response = requests.get(base_url, params=q4_params, timeout=30)

            if q4_response.status_code == 200:
                q4_data = q4_response.json()
                print(f"\nTop drugs in Q4 2024:")
                print(f"{'Rank':<5} {'Drug Name':<40} {'Reports':<10}")
                print("="*60)

                for i, result in enumerate(q4_data['results'][:15], 1):
                    term = result.get('term', 'Unknown')
                    count = result.get('count', 0)
                    print(f"{i:<5} {term:<40} {count:,}")

    else:
        print(f"✗ FAILED: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
