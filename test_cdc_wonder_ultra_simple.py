#!/usr/bin/env python3
"""
Ultra-simple CDC WONDER test - absolute bare minimum
"""

import requests
import xml.etree.ElementTree as ET

def test_ultra_minimal():
    """Test with absolute minimum parameters"""
    print("\n" + "="*80)
    print("TEST: Ultra-Minimal Request (Bare Minimum)")
    print("="*80)

    # Try the simplest possible query - just deaths, no filters
    xml_str = """<request-parameters>
  <parameter>
    <name>accept_datause_restrictions</name>
    <value>true</value>
  </parameter>
  <parameter>
    <name>B_1</name>
    <value>D76.V1-level1</value>
  </parameter>
  <parameter>
    <name>M_1</name>
    <value>D76.M1</value>
  </parameter>
</request-parameters>"""

    print("\n📤 Request (no filters, just group by year, measure deaths):")
    print(xml_str)

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_str},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=30
        )

        print(f"\n📥 Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS!")
            root = ET.fromstring(response.text)

            # Check for data
            data_table = root.find('.//data-table')
            if data_table:
                rows = data_table.findall('.//r')
                print(f"✅ Got {len(rows)} rows of data!")

                # Show sample
                for i, row in enumerate(rows[:3]):
                    cols = row.findall('.//c')
                    print(f"   Row {i+1}: {[c.text for c in cols if c.text]}")

                return True
            else:
                print("⚠️ No data table in response")
                messages = root.findall('.//message')
                for msg in messages[:3]:
                    print(f"   {msg.text}")
        else:
            print(f"❌ Failed: {response.status_code}")
            root = ET.fromstring(response.text)
            messages = root.findall('.//message')
            print("\n   Error messages:")
            for msg in messages[:5]:
                print(f"   - {msg.text}")

        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_with_finder():
    """Test using the Finder format (O_V parameter style)"""
    print("\n" + "="*80)
    print("TEST: Using Finder/O_V Parameter Style")
    print("="*80)

    # Try using O_V parameters which may be the right format
    xml_str = """<request-parameters>
  <parameter>
    <name>accept_datause_restrictions</name>
    <value>true</value>
  </parameter>
  <parameter>
    <name>B_1</name>
    <value>D76.V1</value>
  </parameter>
  <parameter>
    <name>M_1</name>
    <value>D76.M1</value>
  </parameter>
  <parameter>
    <name>O_V1_fmode</name>
    <value>freg</value>
  </parameter>
  <parameter>
    <name>V_D76.V1</name>
    <value>*All*</value>
  </parameter>
  <parameter>
    <name>O_V2_fmode</name>
    <value>freg</value>
  </parameter>
  <parameter>
    <name>V_D76.V2</name>
    <value>*All*</value>
  </parameter>
</request-parameters>"""

    print("\n📤 Testing with O_V parameters...")

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_str},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=30
        )

        print(f"📥 Status: {response.status_code}")

        if response.status_code == 200:
            root = ET.fromstring(response.text)
            data_table = root.find('.//data-table')
            if data_table:
                print("✅ SUCCESS!")
                return True

        root = ET.fromstring(response.text)
        messages = root.findall('.//message')
        for msg in messages[:3]:
            print(f"   {msg.text}")

        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def inspect_web_form():
    """Fetch the web form to see what parameters it expects"""
    print("\n" + "="*80)
    print("TEST: Inspect Web Form for Parameter Names")
    print("="*80)

    try:
        response = requests.get("https://wonder.cdc.gov/ucd-icd10.html", timeout=15)

        if response.status_code == 200:
            print("✅ Got form page")

            # Look for parameter names in the HTML
            import re

            # Find input names
            inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\']', response.text)
            select_names = re.findall(r'<select[^>]*name=["\']([^"\']+)["\']', response.text)

            param_names = set(inputs + select_names)

            # Filter for relevant ones
            relevant = [p for p in param_names if any(x in p for x in ['B_', 'M_', 'V_', 'F_', 'O_', 'accept'])]

            print(f"\n   Found {len(relevant)} relevant parameter names:")
            for name in sorted(relevant)[:20]:
                print(f"     {name}")

            # Look for specific patterns
            print(f"\n   Looking for patterns in form...")
            if 'B_1' in param_names:
                print(f"     ✓ Found B_1 (grouping)")
            if 'M_1' in param_names:
                print(f"     ✓ Found M_1 (measures)")
            if 'accept_datause_restrictions' in param_names:
                print(f"     ✓ Found accept_datause_restrictions")

            # Try to find examples of parameter values
            finder_codes = re.findall(r'F_D76\.V\d+', response.text)
            if finder_codes:
                print(f"\n   Found filter parameters: {set(finder_codes)}")

    except Exception as e:
        print(f"❌ Could not fetch form: {e}")


def main():
    print("\n" + "="*80)
    print("CDC WONDER - ULTRA-SIMPLE DEBUGGING")
    print("="*80)

    # Test 1: Inspect form
    inspect_web_form()

    # Test 2: Ultra minimal
    success1 = test_ultra_minimal()

    # Test 3: O_V style
    success2 = test_with_finder()

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"\n  Ultra-minimal: {'SUCCESS' if success1 else 'FAILED'}")
    print(f"  O_V style:     {'SUCCESS' if success2 else 'FAILED'}")

    if not (success1 or success2):
        print("\n💡 The API may require:")
        print("   1. Specific parameter combinations we haven't tried")
        print("   2. All filter parameters even if set to *All*")
        print("   3. Additional O_ option parameters")
        print("\n   Consider reaching out to wonder@cdc.gov for guidance")


if __name__ == "__main__":
    main()
