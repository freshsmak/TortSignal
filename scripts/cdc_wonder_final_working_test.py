#!/usr/bin/env python3
"""
CDC WONDER - Final Minimal Working Test (All Deaths by Year, 2019-2020)
"""
import requests
import xml.etree.ElementTree as ET

def test_working():
    print("\n" + "="*80)
    print("TEST: Minimal All Deaths by Year (2019-2020)")
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
        <value>&lt;1</value>
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
        <name>F_D76.V1</name>
        <value>2019</value>
        <value>2020</value>
      </parameter>
      <parameter>
        <name>O_V1_fmode</name>
        <value>freg</value>
      </parameter>
      <parameter>
        <name>F_D76.V2</name>
        <value>*All*</value>
      </parameter>
      <parameter>
        <name>O_V2_fmode</name>
        <value>freg</value>
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
        <name>action-Send</name>
        <value>Send</value>
      </parameter>
      <parameter>
        <name>stage</name>
        <value>request</value>
      </parameter>
    </request-parameters>'''

    print("\nRequest XML sent (truncated for display):")
    print(xml_str[:1500] + "...")

    try:
        response = requests.post(
            "https://wonder.cdc.gov/controller/datarequest/D76",
            data={'request_xml': xml_str},
            headers={'User-Agent': 'Mozilla/5.0 (compatible; Python script)'},
            timeout=60
        )

        print(f"\nStatus: {response.status_code}")

        if response.status_code == 200:
            root = ET.fromstring(response.text)
            messages = root.findall('.//message')
            if messages:
                print("\nMessages/Warnings:")
                for msg in messages:
                    print(f" - {msg.text.strip()}")

            data_table = root.find('.//data-table')
            if data_table is not None:
                rows = data_table.findall('.//r')
                print(f"\n✅ SUCCESS! Retrieved {len(rows)} rows.")
                print("Sample rows (Year | Deaths):")
                for i, row in enumerate(rows[:5]):
                    cols = row.findall('.//c')
                    values = [c.text if c.text else c.get('l', 'N/A') for c in cols]
                    print(f" Row {i+1}: {values}")

                # Save successful response
                with open('scripts/cdc_wonder_success.xml', 'w') as f:
                    f.write(response.text)
                print("\n📝 Full response saved to scripts/cdc_wonder_success.xml")

                return True
            else:
                print("⚠️ No data table found in response.")
                print(response.text[:2000])
                return False
        else:
            print(f"❌ Failed with status {response.status_code}")
            try:
                root = ET.fromstring(response.text)
                for msg in root.findall('.//message'):
                    print(f"Error: {msg.text.strip()}")
            except:
                print("Raw response snippet:")
                print(response.text[:2000])
            return False

    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_working()
    if success:
        print("\n" + "="*80)
        print("🎉 API WORKS! Integrate this base structure.")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("Still failing → Switch to Selenium/web UI automation or manual CSV export.")
        print("="*80)
