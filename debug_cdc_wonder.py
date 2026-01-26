#!/usr/bin/env python3
"""
Debug script to investigate CDC WONDER API failures

Tests each strategy to identify exactly where and why requests fail.
"""

import requests
import xml.etree.ElementTree as ET
import sys
import traceback
from pprint import pprint

def test_xml_request():
    """Test CDC WONDER XML API request"""
    print("\n" + "="*80)
    print("TEST 1: XML API Request")
    print("="*80)

    # Build minimal XML request
    root = ET.Element("request-parameters")
    ET.SubElement(root, "accept_datause_restrictions").text = "true"

    # Group by: Year
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "B_1"
    ET.SubElement(param, "value").text = "D76.V1"

    # ICD-10 codes filter
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "F_D76.V2"
    ET.SubElement(param, "value").text = "K50"
    ET.SubElement(param, "value").text = "K51"

    # Year range filter (just 2 years for testing)
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "F_D76.V1"
    ET.SubElement(param, "value").text = "2019"
    ET.SubElement(param, "value").text = "2020"

    # Measures
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "M_1"
    ET.SubElement(param, "value").text = "D76.M1"

    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "M_2"
    ET.SubElement(param, "value").text = "D76.M3"

    xml_request = ET.tostring(root, encoding='unicode')

    print("\n📤 Sending XML request:")
    print(xml_request[:500] + "..." if len(xml_request) > 500 else xml_request)

    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) TortSignal/1.0 Research Tool',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        response = session.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_request, 'accept_datause_restrictions': 'true'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )

        print(f"\n📥 Response Status: {response.status_code}")
        print(f"Response Headers:")
        pprint(dict(response.headers))

        print(f"\n📄 Response Body (first 2000 chars):")
        print(response.text[:2000])

        if len(response.text) > 2000:
            print(f"\n... (response truncated, total length: {len(response.text)} chars)")

        # Try to parse as XML
        try:
            root = ET.fromstring(response.text)
            print("\n✅ Response is valid XML")
            print(f"Root tag: {root.tag}")
            print(f"Children: {[child.tag for child in root]}")
        except ET.ParseError as e:
            print(f"\n❌ Response is not valid XML: {e}")

        return response

    except Exception as e:
        print(f"\n❌ XML Request Failed: {e}")
        traceback.print_exc()
        return None


def test_form_request():
    """Test CDC WONDER Form-based request"""
    print("\n" + "="*80)
    print("TEST 2: Form-based Request")
    print("="*80)

    form_data = {
        'accept_datause_restrictions': 'true',
        'stage': 'request',
        'saved_id': '',
        'dataset_code': 'D76',

        # Group by Year
        'B_1': 'D76.V1',

        # Measures
        'M_1': 'D76.M1',  # Deaths
        'M_2': 'D76.M3',  # Age Adjusted Rate

        # ICD-10 codes
        'F_D76.V2': ['K50', 'K51'],

        # Year range (just 2 years)
        'F_D76.V1': ['2019', '2020'],

        # Export options
        'O_show_totals': 'true',
        'O_precision': '1',
        'O_export': 'true',
    }

    print("\n📤 Sending form data:")
    pprint(form_data)

    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) TortSignal/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        response = session.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data=form_data,
            timeout=30,
            allow_redirects=True
        )

        print(f"\n📥 Response Status: {response.status_code}")
        print(f"Response URL: {response.url}")
        print(f"Response Headers:")
        pprint(dict(response.headers))

        print(f"\n📄 Response Body (first 2000 chars):")
        print(response.text[:2000])

        if len(response.text) > 2000:
            print(f"\n... (response truncated, total length: {len(response.text)} chars)")

        # Check for common patterns
        if 'error' in response.text.lower():
            print("\n⚠️ Error message detected in response")
        if '<table' in response.text.lower():
            print("\n✅ HTML table detected in response")
        if '\t' in response.text and 'Year' in response.text:
            print("\n✅ TSV format detected in response")
        if 'data use agreement' in response.text.lower():
            print("\n⚠️ Data use agreement detected - may need to accept terms")
        if 'session' in response.text.lower():
            print("\n⚠️ Session-related text detected - may need authentication")

        return response

    except Exception as e:
        print(f"\n❌ Form Request Failed: {e}")
        traceback.print_exc()
        return None


def test_simple_get():
    """Test simple GET request to CDC WONDER homepage"""
    print("\n" + "="*80)
    print("TEST 3: Simple GET Request (Homepage)")
    print("="*80)

    try:
        response = requests.get(
            "https://wonder.cdc.gov/",
            timeout=10
        )

        print(f"\n📥 Response Status: {response.status_code}")
        print(f"✅ CDC WONDER is accessible")

        return response

    except Exception as e:
        print(f"\n❌ Cannot reach CDC WONDER: {e}")
        return None


def test_dataset_page():
    """Test accessing the dataset page directly"""
    print("\n" + "="*80)
    print("TEST 4: Dataset Page Access (D76)")
    print("="*80)

    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        })

        response = session.get(
            "https://wonder.cdc.gov/ucd-icd10.html",  # D76 page
            timeout=10
        )

        print(f"\n📥 Response Status: {response.status_code}")

        # Check for cookies
        if session.cookies:
            print("\n🍪 Cookies received:")
            for cookie in session.cookies:
                print(f"  {cookie.name}: {cookie.value}")
        else:
            print("\n❌ No cookies received")

        # Check if there's a form we need to fill
        if 'data use agreement' in response.text.lower():
            print("\n⚠️ Data use agreement form detected")
        if 'agree' in response.text.lower():
            print("⚠️ Agreement acceptance may be required")

        print(f"\n📄 Page content (first 1000 chars):")
        print(response.text[:1000])

        return session, response

    except Exception as e:
        print(f"\n❌ Cannot access dataset page: {e}")
        traceback.print_exc()
        return None, None


def main():
    print("\n" + "="*80)
    print("CDC WONDER API DEBUG SCRIPT")
    print("="*80)

    # Test 1: Basic connectivity
    print("\n🔍 Testing basic connectivity...")
    homepage_response = test_simple_get()
    if not homepage_response:
        print("\n❌ CRITICAL: Cannot reach CDC WONDER at all")
        return

    # Test 2: Dataset page access
    print("\n🔍 Testing dataset page access...")
    session, dataset_response = test_dataset_page()

    # Test 3: XML API
    print("\n🔍 Testing XML API...")
    xml_response = test_xml_request()

    # Test 4: Form API
    print("\n🔍 Testing Form API...")
    form_response = test_form_request()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print("\n📊 Test Results:")
    print(f"  Homepage GET:     {'✅ PASS' if homepage_response else '❌ FAIL'}")
    print(f"  Dataset Page:     {'✅ PASS' if dataset_response else '❌ FAIL'}")
    print(f"  XML API:          {'✅ PASS' if xml_response and xml_response.status_code == 200 else '❌ FAIL'}")
    print(f"  Form API:         {'✅ PASS' if form_response and form_response.status_code == 200 else '❌ FAIL'}")

    print("\n💡 Recommendations:")

    if xml_response and form_response:
        if 'data use agreement' in (xml_response.text + form_response.text).lower():
            print("  1. ⚠️  Data use agreement may need to be accepted")
            print("  2. Try manual session approach with browser cookies")
        elif 'session' in (xml_response.text + form_response.text).lower():
            print("  1. ⚠️  Session authentication may be required")
            print("  2. Try manual authentication approach")
        elif xml_response.status_code != 200 or form_response.status_code != 200:
            print("  1. ⚠️  HTTP errors encountered")
            print("  2. Check API endpoint URLs")
        else:
            print("  1. ⚠️  Requests succeed but data parsing may be failing")
            print("  2. Review response format parsing logic")
    else:
        print("  1. ❌ API requests failing at network level")
        print("  2. Check firewall, proxy, or network restrictions")

    print("\n✅ Debug complete")


if __name__ == "__main__":
    main()
