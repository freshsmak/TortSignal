#!/usr/bin/env python3
"""
Working CDC WONDER minimal test
"""
import requests
import xml.etree.ElementTree as ET

def test_working_minimal():
    print("\n" + "="*80)
    print("TEST: Working Minimal Request (All Deaths by Year)")
    print("="*80)

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
        <name>F_D76.V9</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>F_D76.V10</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>F_D76.V27</name>
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
        <name>O_V9_fmode</name>
        <value>freg</value>
      </parameter>
      <parameter>
        <name>O_V10_fmode</name>
        <value>freg</value>
      </parameter>
      <parameter>
        <name>O_V27_fmode</name>
        <value>freg</value>
      </parameter>
      <parameter>
        <name>M_1</name>
        <value>D76.M1</value>
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
        <name>O_age</name>
        <value>D76.V5</value>
      </parameter>
      <parameter>
        <name>V_D76.V5</name>
        <value>1</value>
        <value>1-4</value>
        <value>5-14</value>
        <value>15-24</value>
        <value>25-34</value>
        <value>35-44</value>
        <value>45-54</value>
        <value>55-64</value>
        <value>65-74</value>
        <value>75-84</value>
        <value>85+</value>
      </parameter>
      <parameter>
        <name>V_D76.V6</name>
        <value>00</value>
      </parameter>
      <parameter>
        <name>V_D76.V7</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>V_D76.V8</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>V_D76.V9</name>
        <value></value>
      </parameter>
      <parameter>
        <name>V_D76.V10</name>
        <value></value>
      </parameter>
      <parameter>
        <name>V_D76.V27</name>
        <value></value>
      </parameter>
      <parameter>
        <name>V_D76.V2</name>
        <value></value>
      </parameter>
      <parameter>
        <name>V_D76.V12</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>V_D76.V4</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>V_D76.V17</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>V_D76.V19</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>V_D76.V1</name>
        <value></value>
      </parameter>
      <parameter>
        <name>O_ucd</name>
        <value>D76.V2</value>
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
                for msg in messages[:5]:
                    print(f" - {msg.text}")

            # Extract data
            data_table = root.find('.//data-table')
            if data_table:
                rows = data_table.findall('.//r')
                print(f"✅ Got {len(rows)} rows of data!")

                # Show sample
                for i, row in enumerate(rows[:5]):
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
                for msg in messages[:5]:
                    print(f" - {msg.text}")
            except:
                print(response.text)
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    test_working_minimal()
