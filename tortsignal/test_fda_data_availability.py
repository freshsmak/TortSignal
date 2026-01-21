"""Test FDA API to find what data is actually available."""

import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENFDA_API_KEY")

def test_query(description, url, params):
    """Test a single FDA API query."""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print('='*60)

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS!")

            if 'results' in data:
                print(f"Results count: {len(data['results'])}")
                if len(data['results']) > 0:
                    print(f"First result keys: {list(data['results'][0].keys())}")

            if 'meta' in data:
                print(f"Meta: {data['meta']}")

            if 'results' in data and len(data['results']) > 0:
                return data['results'][0]

        else:
            print(f"✗ FAILED: {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"✗ ERROR: {e}")

    return None

# Test 1: Simple query for recent FAERS data (no aggregation)
print("\n" + "="*70)
print("FINDING AVAILABLE FDA DATA")
print("="*70)

base_url = "https://api.fda.gov/drug/event.json"

# Try different date ranges to find what works
date_ranges = [
    ("Last 30 days", 30),
    ("Last 90 days", 90),
    ("Last 180 days", 180),
    ("Last 365 days", 365),
    ("2024 data", None, "20240101", "20241231"),
    ("2023 data", None, "20230101", "20231231"),
]

for test_case in date_ranges:
    if len(test_case) == 2:
        label, days = test_case
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        date_filter = f"[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]"
    else:
        label, _, start, end = test_case
        date_filter = f"[{start}+TO+{end}]"

    params = {
        "api_key": api_key,
        "search": f"receivedate:{date_filter}",
        "limit": 1
    }

    result = test_query(label, base_url, params)

    if result:
        print(f"\n✓ Found data for {label}!")
        if 'receivedate' in result:
            print(f"  Receive date: {result['receivedate']}")
        break

# If we found working data, try aggregation
print("\n\n" + "="*70)
print("TESTING AGGREGATION QUERIES")
print("="*70)

# Try aggregation on known working date range
test_dates = [
    ("2024 full year", "20240101", "20241231"),
    ("2023 full year", "20230101", "20231231"),
    ("Q4 2024", "20241001", "20241231"),
    ("Q3 2024", "20240701", "20240930"),
]

for label, start, end in test_dates:
    date_filter = f"[{start}+TO+{end}]"

    params = {
        "api_key": api_key,
        "search": f"receivedate:{date_filter}",
        "count": "patient.drug.openfda.brand_name.exact",
        "limit": 10
    }

    print(f"\n{'='*60}")
    print(f"Aggregation test: {label}")
    print('='*60)

    try:
        response = requests.get(base_url, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS!")

            if 'results' in data:
                print(f"Top drugs in {label}:")
                for i, result in enumerate(data['results'][:5], 1):
                    term = result.get('term', 'Unknown')
                    count = result.get('count', 0)
                    print(f"  {i}. {term}: {count} reports")

                print(f"\n🎯 FOUND WORKING CONFIGURATION!")
                print(f"   Date range: {start} to {end}")
                print(f"   API responds to aggregation queries")
                break
        else:
            print(f"✗ FAILED: {response.status_code}")

    except Exception as e:
        print(f"✗ ERROR: {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
