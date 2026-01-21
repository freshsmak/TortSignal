"""Debug what URL is actually being sent to FDA API."""

import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENFDA_API_KEY")
base_url = "https://api.fda.gov/drug/event.json"

print("Debugging URL encoding...\n")

# Method 1: Using params dict (what we've been doing)
params = {
    "api_key": api_key,
    "search": "receivedate:[2024-01-01+TO+2024-12-31]",
    "limit": 1
}

# Create a prepared request to see the actual URL
req = requests.Request('GET', base_url, params=params)
prepared = req.prepare()

print("="*70)
print("Method 1: Using params dict")
print("="*70)
print(f"URL: {prepared.url}")
print()

# Method 2: Build URL manually with proper encoding
manual_search = "receivedate:[2024-01-01 TO 2024-12-31]"
manual_params = {
    "api_key": api_key,
    "search": manual_search,
    "limit": 1
}

req2 = requests.Request('GET', base_url, params=manual_params)
prepared2 = req2.prepare()

print("="*70)
print("Method 2: Using spaces instead of +")
print("="*70)
print(f"URL: {prepared2.url}")
print()

# Method 3: Manual URL construction
manual_url = f"{base_url}?api_key={api_key}&search=receivedate:[2024-01-01+TO+2024-12-31]&limit=1"

print("="*70)
print("Method 3: Manual URL construction")
print("="*70)
print(f"URL: {manual_url}")
print()

# Now try each method
methods = [
    ("Method 1 (params with +)", base_url, params),
    ("Method 2 (params with spaces)", base_url, manual_params),
]

for name, url, params in methods:
    print("="*70)
    print(f"Testing: {name}")
    print("="*70)

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS!")
            if 'meta' in data:
                print(f"Results: {data['meta']}")
        else:
            print(f"✗ FAILED")
            print(response.text[:300])

    except Exception as e:
        print(f"✗ ERROR: {e}")

    print()

# Method 3: Try the manual URL directly
print("="*70)
print(f"Testing: Method 3 (manual URL)")
print("="*70)

try:
    response = requests.get(manual_url, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ SUCCESS!")
        if 'meta' in data:
            print(f"Results: {data['meta']}")
    else:
        print(f"✗ FAILED")
        print(response.text[:300])

except Exception as e:
    print(f"✗ ERROR: {e}")
