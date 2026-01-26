#!/usr/bin/env python3
"""
CDC WONDER test with O_V5 AND individual age group values
"""
import requests
import xml.etree.ElementTree as ET

def test_final():
    print("\n" + "="*80)
    print("TEST: With O_V5 + Individual Age Group Values")
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

                # Save full response for analysis
                print("\n📝 Saving full response to cdc_wonder_response.xml")
                with open('scripts/cdc_wonder_response.xml', 'w') as f:
                    f.write(response.text)

                return True
            else:
                print("⚠️ No data table in response")
                # Still save response for debugging
                with open('scripts/cdc_wonder_response_no_data.xml', 'w') as f:
                    f.write(response.text)
                return False
        else:
            print(f"❌ Failed: {response.status_code}")
            try:
                root = ET.fromstring(response.text)
                messages = root.findall('.//message')
                print("\nErrors:")
                for msg in messages[:10]:
                    print(f" - {msg.text}")

                # Save error response
                with open('scripts/cdc_wonder_error.xml', 'w') as f:
                    f.write(response.text)
            except:
                print(response.text[:2000])
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_final()

    if success:
        print("\n" + "="*80)
        print("🎉 CDC WONDER API ACCESS SUCCESSFUL!")
        print("="*80)
        print("\nNext steps:")
        print("1. Integrate this XML structure into the main cdc_wonder_enhanced.py")
        print("2. Add dynamic year/age configuration")
        print("3. Implement TiO2 exposure window filtering")
    else:
        print("\n" + "="*80)
        print("⚠️ API ACCESS STILL FAILING")
        print("="*80)
        print("\nRecommendation: Move forward with manual CSV import tool")
        print("The API appears to have undocumented requirements or validation issues")
