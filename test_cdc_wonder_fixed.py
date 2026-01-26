#!/usr/bin/env python3
"""
Fixed CDC WONDER API test with proper parameters
"""

import requests
import xml.etree.ElementTree as ET
import re

def test_fixed_xml_request():
    """Test CDC WONDER with corrected XML parameters"""
    print("\n" + "="*80)
    print("FIXED XML API REQUEST")
    print("="*80)

    # Build corrected XML request with age groups
    root = ET.Element("request-parameters")
    ET.SubElement(root, "accept_datause_restrictions").text = "true"

    # Group by: Year
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "B_1"
    ET.SubElement(param, "value").text = "D76.V1"  # Year

    # ICD-10 codes filter
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "F_D76.V2"
    ET.SubElement(param, "value").text = "K50"
    ET.SubElement(param, "value").text = "K51"

    # Year range filter
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "F_D76.V1"
    for year in range(2018, 2021):  # 2018-2020
        ET.SubElement(param, "value").text = str(year)

    # *** FIX: Add Age Group Selection ***
    # When requesting age-adjusted rates, must include age groups
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "F_D76.V5"  # Age Groups (10-year)
    # Select all age groups
    for age_group in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]:
        ET.SubElement(param, "value").text = age_group

    # Measures: Deaths
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "M_1"
    ET.SubElement(param, "value").text = "D76.M1"  # Deaths

    # Measures: Age-Adjusted Rate
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "M_2"
    ET.SubElement(param, "value").text = "D76.M3"  # Age-Adjusted Rate

    # Show totals
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "O_show_totals"
    ET.SubElement(param, "value").text = "true"

    # Precision
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "O_precision"
    ET.SubElement(param, "value").text = "1"

    xml_request = ET.tostring(root, encoding='unicode')

    print("\n📤 Sending corrected XML request...")
    print(f"Length: {len(xml_request)} chars")

    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        response = session.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_request, 'accept_datause_restrictions': 'true'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )

        print(f"\n📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Request successful!")

            # Try to parse XML
            try:
                root = ET.fromstring(response.text)
                print(f"✅ Valid XML response")
                print(f"Root tag: {root.tag}")

                # Look for data table
                data_table = root.find('.//data-table')
                if data_table:
                    print(f"✅ Found data-table element!")
                    rows = data_table.findall('.//r')
                    print(f"   Number of rows: {len(rows)}")

                    # Parse first few rows
                    for i, row in enumerate(rows[:5]):
                        year_elem = row.find(".//c[@n='1']")
                        deaths_elem = row.find(".//c[@l='Deaths']")
                        rate_elem = row.find(".//c[@l='Age Adjusted Rate']")

                        if year_elem is not None:
                            year = year_elem.text
                            deaths = deaths_elem.text if deaths_elem is not None else "N/A"
                            rate = rate_elem.text if rate_elem is not None else "N/A"
                            print(f"   Row {i+1}: Year={year}, Deaths={deaths}, Rate={rate}")
                else:
                    print("⚠️ No data-table found in response")

                    # Check for errors
                    messages = root.findall('.//message')
                    if messages:
                        print("⚠️ Error messages:")
                        for msg in messages[:3]:
                            print(f"   - {msg.text}")

            except ET.ParseError as e:
                print(f"❌ Response not valid XML: {e}")
                print(f"\nFirst 2000 chars of response:")
                print(response.text[:2000])

        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"\nFirst 2000 chars of response:")
            print(response.text[:2000])

        return response

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_fixed_form_request():
    """Test CDC WONDER with corrected form parameters"""
    print("\n" + "="*80)
    print("FIXED FORM API REQUEST")
    print("="*80)

    form_data = {
        'accept_datause_restrictions': 'true',
        'stage': 'request',
        'saved_id': '',

        # Group by Year
        'B_1': 'D76.V1',

        # Measures
        'M_1': 'D76.M1',  # Deaths
        'M_2': 'D76.M3',  # Age Adjusted Rate

        # ICD-10 codes
        'F_D76.V2': ['K50', 'K51'],

        # Year range
        'F_D76.V1': ['2018', '2019', '2020'],

        # *** FIX: Add Age Groups ***
        'F_D76.V5': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'],  # All age groups

        # Options
        'O_show_totals': 'true',
        'O_precision': '1',
        'O_export': 'true',
    }

    print("\n📤 Sending corrected form data...")

    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        })

        response = session.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data=form_data,
            timeout=30,
            allow_redirects=True
        )

        print(f"\n📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Request successful!")

            # Check response type
            if '\t' in response.text and 'Year\t' in response.text:
                print("✅ TSV format detected")
                lines = response.text.split('\n')
                print(f"   Number of lines: {len(lines)}")
                print("\n   First 10 lines:")
                for i, line in enumerate(lines[:10]):
                    print(f"   {i+1}: {line[:100]}")

            elif '<table' in response.text.lower():
                print("✅ HTML table detected")
                # Try to extract table rows
                rows = re.findall(r'<tr[^>]*>(.+?)</tr>', response.text, re.DOTALL)
                print(f"   Number of table rows: {len(rows)}")

            else:
                print("⚠️ Unknown response format")
                print(f"\n   First 2000 chars:")
                print(response.text[:2000])

        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"\nFirst 2000 chars of response:")
            print(response.text[:2000])

        return response

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("\n" + "="*80)
    print("CDC WONDER API - FIXED PARAMETER TEST")
    print("="*80)

    # Test XML with fixed parameters
    xml_response = test_fixed_xml_request()

    # Test Form with fixed parameters
    form_response = test_fixed_form_request()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    xml_success = xml_response and xml_response.status_code == 200
    form_success = form_response and form_response.status_code == 200

    print(f"\n✅ XML API:  {'SUCCESS' if xml_success else 'FAILED'}")
    print(f"✅ Form API: {'SUCCESS' if form_success else 'FAILED'}")

    if xml_success or form_success:
        print("\n🎉 At least one method works! We can fix the integration.")
    else:
        print("\n⚠️ Both methods still failing. May need manual authentication.")


if __name__ == "__main__":
    main()
