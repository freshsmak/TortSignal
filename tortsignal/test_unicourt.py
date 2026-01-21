"""
Test script to probe UniCourt API and understand its structure.
"""

import os
import sys
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_unicourt_authentication():
    """Test basic authentication with UniCourt API."""
    api_key = os.getenv("UNICOURT_API_KEY")
    client_secret = os.getenv("UNICOURT_CLIENT_SECRET")
    base_url = os.getenv("UNICOURT_BASE_URL", "https://enterpriseapi.unicourt.com")

    print(f"Testing UniCourt API at: {base_url}")
    print(f"API Key: {api_key[:10]}...")
    print(f"Client Secret: {client_secret[:10]}...")
    print()

    # Try different authentication methods
    auth_methods = [
        {
            "name": "Bearer Token (API Key)",
            "headers": {"Authorization": f"Bearer {api_key}"}
        },
        {
            "name": "Bearer Token (Client Secret)",
            "headers": {"Authorization": f"Bearer {client_secret}"}
        },
        {
            "name": "Basic Auth (API Key)",
            "auth": (api_key, "")
        },
        {
            "name": "Basic Auth (API Key + Secret)",
            "auth": (api_key, client_secret)
        },
    ]

    # Try different endpoints
    endpoints = [
        "/",
        "/v1/",
        "/api/",
        "/search",
        "/search/cases",
        "/cases",
        "/v1/search/cases",
        "/v1/cases",
    ]

    for endpoint in endpoints:
        print(f"\n{'='*60}")
        print(f"Testing endpoint: {endpoint}")
        print('='*60)

        for auth_method in auth_methods:
            url = f"{base_url}{endpoint}"

            try:
                kwargs = {"timeout": 10}
                if "headers" in auth_method:
                    kwargs["headers"] = auth_method["headers"]
                if "auth" in auth_method:
                    kwargs["auth"] = auth_method["auth"]

                print(f"\n{auth_method['name']}:")
                print(f"  URL: {url}")

                response = requests.get(url, **kwargs)

                print(f"  Status: {response.status_code}")

                if response.status_code == 200:
                    print(f"  ✓ SUCCESS!")
                    print(f"  Response preview:")
                    try:
                        data = response.json()
                        import json
                        print(json.dumps(data, indent=2)[:500])
                    except:
                        print(response.text[:500])
                    print("\n  Found working configuration!")
                    return
                elif response.status_code == 401:
                    print(f"  ✗ Unauthorized")
                elif response.status_code == 404:
                    print(f"  ✗ Not Found")
                else:
                    print(f"  Response: {response.text[:200]}")

            except Exception as e:
                print(f"  ✗ Error: {e}")

    print("\n" + "="*60)
    print("No working configuration found. Try checking UniCourt API docs.")
    print("="*60)


def test_case_search():
    """Test case search with working credentials."""
    base_url = os.getenv("UNICOURT_BASE_URL", "https://enterpriseapi.unicourt.com")
    api_key = os.getenv("UNICOURT_API_KEY")

    # Try a simple search query
    since_date = datetime.now() - timedelta(days=30)

    search_params = {
        "filed_after": since_date.strftime("%Y-%m-%d"),
        "page_size": 10,
    }

    print(f"\n{'='*60}")
    print("Testing case search with parameters:")
    print(f"  filed_after: {search_params['filed_after']}")
    print(f"  page_size: {search_params['page_size']}")
    print('='*60)

    headers = {"Authorization": f"Bearer {api_key}"}

    # Try different search endpoints
    search_urls = [
        f"{base_url}/search/cases",
        f"{base_url}/v1/search/cases",
        f"{base_url}/cases/search",
        f"{base_url}/v1/cases/search",
    ]

    for url in search_urls:
        try:
            print(f"\nTrying: {url}")
            response = requests.get(url, headers=headers, params=search_params, timeout=10)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print("✓ SUCCESS!")
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                print(f"Sample data:")
                import json
                print(json.dumps(data, indent=2)[:1000])
                break
            else:
                print(f"Response: {response.text[:200]}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("UniCourt API Test Script")
    print("="*60)

    test_unicourt_authentication()

    print("\n\nAttempting case search...")
    test_case_search()
