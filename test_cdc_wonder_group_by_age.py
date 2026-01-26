#!/usr/bin/env python3
"""
Test CDC WONDER with age groups in GROUP BY (B_ parameter)
"""

import requests
import xml.etree.ElementTree as ET

def test_group_by_age():
    """Add age groups to the GROUP BY clause"""
    print("\n" + "="*80)
    print("TEST: Group By Year AND Age Groups")
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
    <name>B_2</name>
    <value>D76.V5</value>
  </parameter>
  <parameter>
    <name>M_1</name>
    <value>D76.M1</value>
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

    print("\n📤 Request: B_1=Year, B_2=AgeGroups, M_1=Deaths...")

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
                print(f"   Got {len(rows)} rows of data!\n")

                # Show first few rows
                for i, row in enumerate(rows[:10]):
                    cols = row.findall('.//c')
                    values = [c.text for c in cols if c.text]
                    print(f"   {values}")

                return True, rows

        messages = root.findall('.//message')
        if messages:
            print("   Errors:")
            for msg in messages[:3]:
                text = msg.text.strip() if msg.text else ""
                if text and not text.startswith("{"):
                    print(f"   - {text}")

        return False, None

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, None


def test_group_by_year_only_no_filters():
    """Try grouping by year only with no filters at all"""
    print("\n" + "="*80)
    print("TEST: Group By Year Only, No Filters")
    print("="*80)

    # Don't include F_ parameters at all
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
    <name>O_show_totals</name>
    <value>true</value>
  </parameter>
</request-parameters>"""

    print("\n📤 Request: Just B_1=Year, M_1=Deaths, no filters...")

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
                print(f"   Got {len(rows)} rows!")

                for i, row in enumerate(rows[:5]):
                    cols = row.findall('.//c')
                    print(f"   {[c.text for c in cols if c.text]}")

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
        return False


def test_summarized_data():
    """Try requesting just totals, no grouping"""
    print("\n" + "="*80)
    print("TEST: Summarized Data (No Grouping)")
    print("="*80)

    # No B_ parameters - just totals
    xml_str = """<request-parameters>
  <parameter>
    <name>accept_datause_restrictions</name>
    <value>true</value>
  </parameter>
  <parameter>
    <name>M_1</name>
    <value>D76.M1</value>
  </parameter>
  <parameter>
    <name>F_D76.V1</name>
    <value>2020</value>
  </parameter>
  <parameter>
    <name>F_D76.V2</name>
    <value>K50</value>
  </parameter>
  <parameter>
    <name>O_show_totals</name>
    <value>true</value>
  </parameter>
</request-parameters>"""

    print("\n📤 Request: No grouping, just M_1=Deaths with filters...")

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_str},
            timeout=30
        )

        print(f"📥 Status: {response.status_code}")

        root = ET.fromstring(response.text)

        if response.status_code == 200:
            # Look for total
            total_elem = root.find('.//total')
            data_table = root.find('.//data-table')

            if total_elem is not None or data_table is not None:
                print("✅ SUCCESS!")

                if total_elem is not None:
                    print(f"   Total: {total_elem.text}")

                if data_table:
                    rows = data_table.findall('.//r')
                    print(f"   Rows: {len(rows)}")
                    for row in rows[:5]:
                        cols = row.findall('.//c')
                        print(f"   {[c.text for c in cols if c.text]}")

                return True

        messages = root.findall('.//message')
        if messages:
            print("   Errors:")
            for msg in messages[:3]:
                text = msg.text.strip() if msg.text else ""
                if text and not text.startswith("{"):
                    print(f"   - {text}")

        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def main():
    print("\n" + "="*80)
    print("CDC WONDER - GROUP BY AGE TEST")
    print("="*80)
    print("\nError says: 'must also select the Ten-Year Age Groups button'")
    print("This suggests we need age groups in the GROUP BY (B_) not just filters\n")

    success1, rows = test_group_by_age()
    success2 = test_group_by_year_only_no_filters()
    success3 = test_summarized_data()

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"\n  Group by Year + Age:     {'SUCCESS ✅' if success1 else 'FAILED'}")
    print(f"  Group by Year only:      {'SUCCESS ✅' if success2 else 'FAILED'}")
    print(f"  Summarized (no group):   {'SUCCESS ✅' if success3 else 'FAILED'}")

    if any([success1, success2, success3]):
        print("\n🎉 BREAKTHROUGH! At least one method works!")
        print("\nNext step: Use the working method to update cdc_wonder_enhanced.py")

        if success1 and rows:
            print(f"\n📊 Example: Retrieved {len(rows)} rows from CDC WONDER API")
            print("     This is REAL DATA, not literature estimates!")

    else:
        print("\n⚠️  None of the methods worked.")
        print("\n💡 Possible issues:")
        print("     1. CDC WONDER API may have changed since documentation")
        print("     2. May require additional session/cookie setup")
        print("     3. Current API parameters may not match D76 database")
        print("\n     Recommendation: Try reaching out to wonder@cdc.gov")
        print("     or accept the literature fallback (which is transparent)")


if __name__ == "__main__":
    main()
