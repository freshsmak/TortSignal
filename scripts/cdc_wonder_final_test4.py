#!/usr/bin/env python3
"""
CDC WONDER test with explicit O_V5 parameter to enable age groups
"""
import requests
import xml.etree.ElementTree as ET

def test_with_o_v5():
    print("\n" + "="*80)
    print("TEST: With O_V5 parameter to explicitly enable age groups")
    print("="*80)

    # Try adding O_V5 as the "button" selector
    xml_str = '''<request-parameters>
      <parameter>
        <name>accept_datause_restrictions</name>
        <value>true</value>
      </parameter>
      <parameter>
        <name>B_1</name>
        <value>D76.V1-level1</value>
      </parameter>
      <parameter>
        <name>B_2</name>
        <value>*None*</value>
      </parameter>
      <parameter>
        <name>B_3</name>
        <value>*None*</value>
      </parameter>
      <parameter>
        <name>B_4</name>
        <value>*None*</value>
      </parameter>
      <parameter>
        <name>B_5</name>
        <value>*None*</value>
      </parameter>
      <parameter>
        <name>F_D76.V1</name>
        <value>2019</value>
        <value>2020</value>
      </parameter>
      <parameter>
        <name>F_D76.V2</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>O_V1_fmode</name>
        <value>freg</value>
      </parameter>
      <parameter>
        <name>O_V2_fmode</name>
        <value>freg</value>
      </parameter>
      <parameter>
        <name>O_V5</name>
        <value>D76.V5</value>
      </parameter>
      <parameter>
        <name>O_show_totals</name>
        <value>true</value>
      </parameter>
      <parameter>
        <name>O_timeout</name>
        <value>300</value>
      </parameter>
      <parameter>
        <name>M_1</name>
        <value>D76.M1</value>
      </parameter>
      <parameter>
        <name>V_D76.V1</name>
        <value></value>
      </parameter>
      <parameter>
        <name>V_D76.V2</name>
        <value></value>
      </parameter>
      <parameter>
        <name>V_D76.V5</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>I_D76.V1</name>
        <value>Year</value>
      </parameter>
      <parameter>
        <name>action-Send</name>
        <value>Send</value>
      </parameter>
      <parameter>
        <name>stage</name>
        <value>request</value>
      </parameter>
    </request-parameters>'''

    print("\n📤 Request XML:")
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

            # Check for errors
            messages = root.findall('.//message')
            if messages:
                print("\nWarnings/Errors:")
                for msg in messages[:10]:
                    print(f" - {msg.text}")

            # Extract data
            data_table = root.find('.//data-table')
            if data_table:
                rows = data_table.findall('.//r')
                print(f"\n✅ Got {len(rows)} rows of data!")

                # Show sample
                for i, row in enumerate(rows[:10]):
                    cols = row.findall('.//c')
                    values = [c.text if c.text else c.get('l', '') for c in cols]
                    print(f" Row {i+1}: {values}")

                return True
            else:
                print("⚠️ No data table in response")
                return False
        else:
            print(f"❌ Failed: {response.status_code}")
            try:
                root = ET.fromstring(response.text)
                messages = root.findall('.//message')
                print("\nErrors:")
                for msg in messages[:10]:
                    print(f" - {msg.text}")
            except:
                print(response.text[:2000])
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_with_o_v5()
