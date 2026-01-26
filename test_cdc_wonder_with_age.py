#!/usr/bin/env python3
"""
Test CDC WONDER with age group parameters included
"""

import requests
import xml.etree.ElementTree as ET

def test_with_age_groups_v1():
    """Test with age groups included (attempt 1)"""
    print("\n" + "="*80)
    print("TEST: With Age Groups (F_D76.V5 style)")
    print("="*80)

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
    <name>F_D76.V5</name>
    <value>*All*</value>
  </parameter>
  <parameter>
    <name>F_D76.V1</name>
    <value>2020</value>
  </parameter>
  <parameter>
    <name>F_D76.V2</name>
    <value>K50</value>
  </parameter>
</request-parameters>"""

    print("\n📤 Testing with F_D76.V5 = *All* (age groups)...")

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_str},
            timeout=30
        )

        print(f"📥 Status: {response.status_code}")

        root = ET.fromstring(response.text)

        if response.status_code == 200:
            data_table = root.find('.//data-table')
            if data_table:
                print("✅ SUCCESS!")
                rows = data_table.findall('.//r')
                print(f"   Got {len(rows)} rows")

                for i, row in enumerate(rows[:5]):
                    cols = row.findall('.//c')
                    print(f"   Row {i+1}: {[c.text for c in cols if c.text]}")

                return True

        messages = root.findall('.//message')
        print("   Errors:")
        for msg in messages[:3]:
            print(f"   - {msg.text}")

        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_with_explicit_age_selection():
    """Test with explicit age group selection"""
    print("\n" + "="*80)
    print("TEST: With Explicit Age Groups Selected")
    print("="*80)

    # Try selecting specific age groups
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
    <name>F_D76.V5</name>
    <value>1</value>
  </parameter>
  <parameter>
    <name>F_D76.V5</name>
    <value>2</value>
  </parameter>
  <parameter>
    <name>F_D76.V5</name>
    <value>3</value>
  </parameter>
  <parameter>
    <name>F_D76.V5</name>
    <value>4</value>
  </parameter>
  <parameter>
    <name>F_D76.V5</name>
    <value>5</value>
  </parameter>
  <parameter>
    <name>F_D76.V5</name>
    <value>6</value>
  </parameter>
  <parameter>
    <name>F_D76.V5</name>
    <value>7</value>
  </parameter>
  <parameter>
    <name>F_D76.V5</name>
    <value>8</value>
  </parameter>
  <parameter>
    <name>F_D76.V5</name>
    <value>9</value>
  </parameter>
  <parameter>
    <name>F_D76.V5</name>
    <value>10</value>
  </parameter>
  <parameter>
    <name>F_D76.V1</name>
    <value>2020</value>
  </parameter>
  <parameter>
    <name>F_D76.V2</name>
    <value>K50</value>
  </parameter>
</request-parameters>"""

    print("\n📤 Testing with explicit age groups 1-10...")

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_str},
            timeout=30
        )

        print(f"📥 Status: {response.status_code}")

        root = ET.fromstring(response.text)

        if response.status_code == 200:
            data_table = root.find('.//data-table')
            if data_table:
                print("✅ SUCCESS!")
                rows = data_table.findall('.//r')
                print(f"   Got {len(rows)} rows of data")

                # Extract and show data
                for i, row in enumerate(rows[:5]):
                    cols = row.findall('.//c')
                    values = []
                    for c in cols:
                        if c.text:
                            values.append(c.text)
                        elif c.get('l'):  # Label attribute
                            values.append(c.get('l'))
                    print(f"   Row {i+1}: {values}")

                return True

        messages = root.findall('.//message')
        print("   Errors:")
        for msg in messages[:3]:
            print(f"   - {msg.text}")

        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_no_filters():
    """Test with no ICD/year filters, just deaths by year"""
    print("\n" + "="*80)
    print("TEST: No Filters - All Deaths By Year")
    print("="*80)

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
    <name>F_D76.V5</name>
    <value>*All*</value>
  </parameter>
  <parameter>
    <name>F_D76.V1</name>
    <value>*All*</value>
  </parameter>
  <parameter>
    <name>F_D76.V2</name>
    <value>*All*</value>
  </parameter>
</request-parameters>"""

    print("\n📤 Testing with all filters = *All*...")

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_str},
            timeout=30
        )

        print(f"📥 Status: {response.status_code}")

        root = ET.fromstring(response.text)

        if response.status_code == 200:
            data_table = root.find('.//data-table')
            if data_table:
                print("✅ SUCCESS!")
                rows = data_table.findall('.//r')
                print(f"   Got {len(rows)} rows of data")

                for i, row in enumerate(rows[:5]):
                    cols = row.findall('.//c')
                    print(f"   Row {i+1}: {[c.text for c in cols if c.text]}")

                return True

        messages = root.findall('.//message')
        if messages:
            print("   Errors:")
            for msg in messages[:5]:
                text = msg.text.strip() if msg.text else ""
                if text and not text.startswith("{"):
                    print(f"   - {text}")

        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print("CDC WONDER - TEST WITH AGE GROUPS")
    print("="*80)
    print("\nThe API keeps complaining about age groups.")
    print("Let's try explicitly including age group parameters.\n")

    success1 = test_with_age_groups_v1()
    success2 = test_with_explicit_age_selection()
    success3 = test_no_filters()

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"\n  F_D76.V5 = *All*:        {'SUCCESS' if success1 else 'FAILED'}")
    print(f"  Explicit age groups:     {'SUCCESS' if success2 else 'FAILED'}")
    print(f"  All filters = *All*:     {'SUCCESS' if success3 else 'FAILED'}")

    if any([success1, success2, success3]):
        print("\n🎉 Found a working combination!")
    else:
        print("\n⚠️  Still not working. The CDC WONDER API may:")
        print("     1. Require additional undocumented parameters")
        print("     2. Have changed its XML format")
        print("     3. Not support programmatic access in the way documented")
        print("\n     Recommendation: Contact wonder@cdc.gov for current API documentation")


if __name__ == "__main__":
    main()
