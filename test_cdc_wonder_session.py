#!/usr/bin/env python3
"""
Test CDC WONDER with session - simulate browser workflow
"""

import requests
from bs4 import BeautifulSoup
import re

def extract_hidden_fields(html):
    """Extract hidden form fields from HTML"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        hidden_fields = {}
        for input_field in soup.find_all('input', type='hidden'):
            name = input_field.get('name')
            value = input_field.get('value', '')
            if name:
                hidden_fields[name] = value
        return hidden_fields
    except ImportError:
        print("⚠️ BeautifulSoup not available, using regex")
        # Fallback to regex
        pattern = r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']'
        matches = re.findall(pattern, html, re.IGNORECASE)
        return {name: value for name, value in matches}


def test_with_session():
    """Test CDC WONDER by establishing a proper session"""
    print("\n" + "="*80)
    print("TEST: CDC WONDER with Session")
    print("="*80)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    # Step 1: Visit the dataset page
    print("\n📍 Step 1: Visit dataset page...")
    try:
        resp = session.get("https://wonder.cdc.gov/ucd-icd10.html", timeout=15)
        print(f"   Status: {resp.status_code}")
        print(f"   Cookies received: {len(session.cookies)} cookies")

        for cookie in session.cookies:
            print(f"     - {cookie.name}: {cookie.value[:50]}{'...' if len(cookie.value) > 50 else ''}")

        # Check if there's a data use agreement form
        if 'agree' in resp.text.lower() and 'data' in resp.text.lower():
            print("   ⚠️ Data use agreement detected")

            # Try to find and extract the agreement form
            hidden_fields = extract_hidden_fields(resp.text)
            print(f"   Found {len(hidden_fields)} hidden fields")

            # Look for the agreement form action
            form_action_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', resp.text, re.IGNORECASE)
            if form_action_match:
                form_action = form_action_match.group(1)
                print(f"   Form action: {form_action}")

                # Step 2: Submit agreement
                print("\n📍 Step 2: Submit data use agreement...")
                agreement_data = hidden_fields.copy()
                agreement_data['action-I Agree'] = 'I Agree'
                agreement_data['accept_datause_restrictions'] = 'true'

                agree_resp = session.post(
                    f"https://wonder.cdc.gov{form_action}" if form_action.startswith('/') else form_action,
                    data=agreement_data,
                    timeout=15
                )
                print(f"   Status: {agree_resp.status_code}")
                print(f"   Cookies now: {len(session.cookies)} cookies")

    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Step 3: Now try the API request
    print("\n📍 Step 3: Try API request with session...")

    form_data = {
        'accept_datause_restrictions': 'true',
        'stage': 'request',
        'B_1': 'D76.V1',
        'M_1': 'D76.M1',
        'F_D76.V2': 'K50',
        'F_D76.V1': ['2019', '2020'],
        'O_show_totals': 'true',
        'O_export': 'true',
    }

    try:
        resp = session.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data=form_data,
            timeout=30
        )

        print(f"   Status: {resp.status_code}")

        if resp.status_code == 200:
            print("   ✅ SUCCESS!")
            print(f"\n   Response preview:")
            print(resp.text[:1000])

            # Check if we got data
            if '\t' in resp.text or '<table' in resp.text.lower():
                print("\n   ✅ Data detected in response!")
                return True
        else:
            print(f"   ❌ Failed with {resp.status_code}")
            print(f"\n   Response preview:")
            print(resp.text[:1000])

    except Exception as e:
        print(f"   ❌ Exception: {e}")

    return False


def test_wonder_api_documentation():
    """Check if we can access CDC WONDER API documentation"""
    print("\n" + "="*80)
    print("TEST: Check CDC WONDER API Documentation")
    print("="*80)

    try:
        resp = requests.get("https://wonder.cdc.gov/wonder/help/WONDER-API.html", timeout=10)
        print(f"\n📥 Status: {resp.status_code}")

        if resp.status_code == 200:
            print("✅ Documentation accessible")

            # Look for example requests
            examples = re.findall(r'<pre>(.*?)</pre>', resp.text, re.DOTALL)
            if examples:
                print(f"\nFound {len(examples)} example(s):")
                for i, ex in enumerate(examples[:2]):
                    print(f"\nExample {i+1}:")
                    print(ex[:500])
        else:
            print("❌ Cannot access documentation")

    except Exception as e:
        print(f"❌ Failed: {e}")


def main():
    print("\n" + "="*80)
    print("CDC WONDER SESSION-BASED TESTING")
    print("="*80)

    # Try installing beautifulsoup4 if not available
    try:
        import bs4
    except ImportError:
        print("\n📦 BeautifulSoup not found, attempting to install...")
        import subprocess
        try:
            subprocess.check_call(['pip', 'install', '-q', 'beautifulsoup4'])
            print("✅ Installed beautifulsoup4")
        except:
            print("⚠️ Could not install beautifulsoup4, will use regex fallback")

    # Test 1: Try with session
    success = test_with_session()

    # Test 2: Check documentation
    test_wonder_api_documentation()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if success:
        print("✅ Session-based approach works!")
        print("\n💡 Fix: Update CDC WONDER integration to:")
        print("   1. Visit dataset page first")
        print("   2. Accept data use agreement")
        print("   3. Use session cookies for API requests")
    else:
        print("❌ Session-based approach also failed")
        print("\n💡 Options:")
        print("   1. Check CDC WONDER API documentation for working examples")
        print("   2. Use browser automation (Selenium/Playwright) to extract cookies")
        print("   3. Accept the literature fallback (system is honest about data quality)")


if __name__ == "__main__":
    main()
