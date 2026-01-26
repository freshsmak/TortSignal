#!/usr/bin/env python3
"""
Simplified CDC WONDER test - just death counts, no age-adjustment
"""

import requests
import xml.etree.ElementTree as ET

def test_simple_xml():
    """Test with minimal parameters - just death counts"""
    print("\n" + "="*80)
    print("SIMPLE XML REQUEST - Deaths Only (No Age Adjustment)")
    print("="*80)

    root = ET.Element("request-parameters")
    ET.SubElement(root, "accept_datause_restrictions").text = "true"

    # Group by: Year only
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "B_1"
    ET.SubElement(param, "value").text = "D76.V1"

    # ICD-10 codes
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "F_D76.V2"
    ET.SubElement(param, "value").text = "K50"

    # Years
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "F_D76.V1"
    ET.SubElement(param, "value").text = "2019"
    ET.SubElement(param, "value").text = "2020"

    # Only measure: Deaths (no age-adjusted rate)
    param = ET.SubElement(root, "parameter")
    ET.SubElement(param, "name").text = "M_1"
    ET.SubElement(param, "value").text = "D76.M1"

    xml_request = ET.tostring(root, encoding='unicode')

    print(f"\n📤 Request: {xml_request}")

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_request, 'accept_datause_restrictions': 'true'},
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0'
            },
            timeout=30
        )

        print(f"\n📥 Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS!")
            try:
                root = ET.fromstring(response.text)
                data_table = root.find('.//data-table')
                if data_table:
                    print("✅ Found data!")
                    rows = data_table.findall('.//r')
                    for row in rows[:5]:
                        print(f"  {ET.tostring(row, encoding='unicode')[:200]}")
                else:
                    print("⚠️ No data table")
                    print(response.text[:1000])
            except:
                print(response.text[:2000])
        else:
            print(f"❌ Failed")
            print(response.text[:2000])

        return response

    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


def test_simple_form():
    """Test form request without age-adjusted rates"""
    print("\n" + "="*80)
    print("SIMPLE FORM REQUEST - Deaths Only")
    print("="*80)

    form_data = {
        'accept_datause_restrictions': 'true',
        'stage': 'request',
        'B_1': 'D76.V1',
        'M_1': 'D76.M1',  # Just deaths
        'F_D76.V2': 'K50',
        'F_D76.V1': ['2019', '2020'],
        'O_show_totals': 'true',
        'O_export': 'true',
    }

    print(f"\n📤 Sending form...")

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data=form_data,
            timeout=30
        )

        print(f"\n📥 Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS!")
            print(response.text[:2000])
        else:
            print("❌ Failed")
            print(response.text[:2000])

        return response

    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


if __name__ == "__main__":
    print("Testing simplified CDC WONDER requests...")

    xml_resp = test_simple_xml()
    form_resp = test_simple_form()

    print("\n" + "="*80)
    if (xml_resp and xml_resp.status_code == 200) or (form_resp and form_resp.status_code == 200):
        print("✅ At least one method works!")
    else:
        print("❌ Both methods failed - CDC WONDER API may require browser session")
