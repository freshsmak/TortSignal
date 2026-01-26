#!/usr/bin/env python3
"""
CDC WONDER - Test with O_age but NO V_D76.V5 values
"""
import requests
import xml.etree.ElementTree as ET

def test_no_age_values():
    print("\n" + "="*80)
    print("TEST: O_age enabled but NO age values (should use all)")
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
        <name>action-Send</name>
        <value>Send</value>
      </parameter>
      <parameter>
        <name>stage</name>
        <value>request</value>
      </parameter>
    </request-parameters>'''

    print("\nRequest XML:")
    print(xml_str)

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
                print("Sample rows:")
                for i, row in enumerate(rows[:10]):
                    cols = row.findall('.//c')
                    values = [c.text if c.text else c.get('l', 'N/A') for c in cols]
                    print(f" Row {i+1}: {values}")

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
    success = test_no_age_values()
    if success:
        print("\n🎉 API WORKS!")
    else:
        print("\nStill failing.")
