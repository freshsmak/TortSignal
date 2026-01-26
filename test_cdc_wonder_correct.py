#!/usr/bin/env python3
"""
Test CDC WONDER with correct XML structure based on user guidance
"""

import requests
import xml.etree.ElementTree as ET
from pprint import pprint

def test_minimal_xml():
    """Test with minimal XML structure provided by user"""
    print("\n" + "="*80)
    print("TEST: Minimal XML Request (User-Provided Template)")
    print("="*80)

    # Build XML request using correct structure
    xml_str = """<request-parameters>
  <parameter>
    <name>B_1</name>
    <value>D76.V1-level1</value> <!-- Group by year -->
  </parameter>
  <parameter>
    <name>M_1</name>
    <value>D76.M1</value> <!-- Deaths -->
  </parameter>
  <parameter>
    <name>V_D76.V2</name>
    <value>K50</value> <!-- IBD: Crohn's disease -->
  </parameter>
  <parameter>
    <name>V_D76.V1</name>
    <value>2018</value> <!-- Year 2018 -->
  </parameter>
  <parameter>
    <name>V_D76.V1</name>
    <value>2019</value> <!-- Year 2019 -->
  </parameter>
  <parameter>
    <name>V_D76.V1</name>
    <value>2020</value> <!-- Year 2020 -->
  </parameter>
  <parameter>
    <name>accept_datause_restrictions</name>
    <value>true</value>
  </parameter>
</request-parameters>"""

    print("\n📤 Sending request:")
    print(xml_str)

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_str},
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            timeout=30
        )

        print(f"\n📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS!")

            # Parse XML response
            try:
                root = ET.fromstring(response.text)
                print(f"\n✅ Valid XML response")
                print(f"   Root tag: {root.tag}")

                # Look for data-table
                data_table = root.find('.//data-table')
                if data_table:
                    print(f"   ✅ Found data-table!")

                    # Count rows
                    rows = data_table.findall('.//r')
                    print(f"   Rows: {len(rows)}")

                    # Show first few rows
                    print(f"\n   Data preview:")
                    for i, row in enumerate(rows[:5]):
                        cols = row.findall('.//c')
                        values = [c.text for c in cols if c.text]
                        print(f"   Row {i+1}: {values}")

                    return True
                else:
                    # Check for errors
                    messages = root.findall('.//message')
                    if messages:
                        print(f"\n   ⚠️ Error messages:")
                        for msg in messages:
                            print(f"   - {msg.text}")
                    else:
                        print(f"\n   Response structure:")
                        print(response.text[:1000])
                    return False

            except ET.ParseError as e:
                print(f"   ❌ Not valid XML: {e}")
                print(f"\n   Response preview:")
                print(response.text[:1000])
                return False
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"\nResponse preview:")
            print(response.text[:1000])
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ibd_deaths():
    """Test IBD mortality query with correct structure"""
    print("\n" + "="*80)
    print("TEST: IBD Deaths (K50-K51) 2018-2020")
    print("="*80)

    # Query for both Crohn's (K50) and UC (K51)
    xml_str = """<request-parameters>
  <parameter>
    <name>B_1</name>
    <value>D76.V1-level1</value>
  </parameter>
  <parameter>
    <name>M_1</name>
    <value>D76.M1</value>
  </parameter>
  <parameter>
    <name>V_D76.V2</name>
    <value>K50</value>
  </parameter>
  <parameter>
    <name>V_D76.V2</name>
    <value>K51</value>
  </parameter>
  <parameter>
    <name>accept_datause_restrictions</name>
    <value>true</value>
  </parameter>
</request-parameters>"""

    print("\n📤 Querying IBD deaths (K50, K51)...")

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
                print("✅ Got data!")
                rows = data_table.findall('.//r')

                print(f"\nIBD Deaths by Year:")
                for row in rows:
                    cols = row.findall('.//c')
                    if len(cols) >= 2:
                        year = cols[0].text if cols[0].text else "Unknown"
                        deaths = cols[1].text if cols[1].text else "0"
                        print(f"  {year}: {deaths} deaths")

                return True
            else:
                messages = root.findall('.//message')
                for msg in messages:
                    print(f"  ⚠️ {msg.text}")
                return False
        else:
            print(f"❌ Failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_with_wonderapi():
    """Test using the wonderapi package"""
    print("\n" + "="*80)
    print("TEST: Using wonderapi Package")
    print("="*80)

    try:
        import wonderapi
        print("✅ wonderapi is installed")
    except ImportError:
        print("⚠️ wonderapi not installed, attempting to install...")
        import subprocess
        try:
            subprocess.check_call(['pip', 'install', '-q', 'wonderapi'])
            print("✅ Installed wonderapi")
            import wonderapi
        except Exception as e:
            print(f"❌ Could not install wonderapi: {e}")
            return False

    try:
        print("\n📤 Creating query with wonderapi...")

        # Note: This is pseudocode based on the package - actual API may differ
        # We'll catch any errors and report them
        query = wonderapi.wonder_api(database="D76")
        query.group_by(["Year"])
        query.measure(["Deaths"])
        query.where({"UCD-ICD10 Codes": "K50"})  # Crohn's disease
        query.parameter("accept_datause_restrictions", "true")

        print("📤 Running query...")
        results = query.run()

        print("✅ SUCCESS with wonderapi!")
        print(f"\nResults:")
        print(results)

        return True

    except Exception as e:
        print(f"⚠️ wonderapi test failed: {e}")
        print("(This is expected if the API has changed)")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print("CDC WONDER - CORRECT API USAGE TEST")
    print("="*80)
    print("\nBased on user guidance:")
    print("- Using correct XML parameter structure")
    print("- V_ for filters, B_ for grouping, M_ for measures")
    print("- accept_datause_restrictions in XML")

    # Test 1: Minimal XML
    success1 = test_minimal_xml()

    # Test 2: IBD specific query
    success2 = test_ibd_deaths()

    # Test 3: wonderapi package
    success3 = test_with_wonderapi()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n✓ Minimal XML:    {'SUCCESS' if success1 else 'FAILED'}")
    print(f"✓ IBD Query:      {'SUCCESS' if success2 else 'FAILED'}")
    print(f"✓ wonderapi pkg:  {'SUCCESS' if success3 else 'FAILED'}")

    if success1 or success2:
        print("\n🎉 CDC WONDER API IS WORKING!")
        print("\n💡 Next steps:")
        print("   1. Update cdc_wonder_enhanced.py with correct XML structure")
        print("   2. Use V_ for filters, B_ for grouping, M_ for measures")
        print("   3. Include accept_datause_restrictions in XML")
        print("   4. Parse response data-table for results")
    elif success3:
        print("\n🎉 wonderapi package works!")
        print("\n💡 Next steps:")
        print("   1. Use wonderapi package for queries")
        print("   2. Wrapper library handles parameter complexity")
    else:
        print("\n⚠️ All tests failed - may need more debugging")
        print("   Check full error messages above")


if __name__ == "__main__":
    main()
