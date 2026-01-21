"""Simple test to get ANY data from FDA API."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENFDA_API_KEY")
base_url = "https://api.fda.gov/drug/event.json"

print("Testing FDA API with simplest possible queries...\n")

# Test 1: No date filter at all, just get recent data
print("="*60)
print("Test 1: Get any recent data (no date filter)")
print("="*60)

params = {
    "api_key": api_key,
    "limit": 5
}

try:
    response = requests.get(base_url, params=params, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ SUCCESS! Got {len(data.get('results', []))} results")

        if 'results' in data and len(data['results']) > 0:
            first = data['results'][0]
            print(f"\nFirst result:")
            if 'receivedate' in first:
                print(f"  Receive date: {first['receivedate']}")
            if 'patient' in first and 'drug' in first['patient']:
                drugs = first['patient']['drug']
                print(f"  Drugs: {len(drugs)} mentioned")
                if len(drugs) > 0 and 'medicinalproduct' in drugs[0]:
                    print(f"    First drug: {drugs[0]['medicinalproduct']}")

            print(f"\n🎯 API IS WORKING! We can get data.")

            # Now try aggregation
            print("\n" + "="*60)
            print("Test 2: Try aggregation (top drugs, no date filter)")
            print("="*60)

            agg_params = {
                "api_key": api_key,
                "count": "patient.drug.medicinalproduct.exact",
                "limit": 20
            }

            agg_response = requests.get(base_url, params=agg_params, timeout=30)
            print(f"Status: {agg_response.status_code}")

            if agg_response.status_code == 200:
                agg_data = agg_response.json()
                print(f"✓ AGGREGATION WORKS!")

                if 'results' in agg_data:
                    print(f"\nTop drugs in FDA database:")
                    for i, result in enumerate(agg_data['results'][:15], 1):
                        term = result.get('term', 'Unknown')
                        count = result.get('count', 0)
                        print(f"  {i:2d}. {term:40s} {count:,} reports")

            else:
                print(f"✗ Aggregation failed: {agg_response.status_code}")
                print(agg_response.text[:500])

    else:
        print(f"✗ FAILED: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
