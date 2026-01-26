#!/usr/bin/env python3
"""
Capture a real working CDC WONDER request using browser inspection
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def capture_real_request():
    print("Setting up browser to capture network requests...")

    # Enable network logging
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=options)

    try:
        print("\nNavigating to CDC WONDER...")
        driver.get("https://wonder.cdc.gov/ucd-icd10.html")

        print("Waiting for page to load...")
        wait = WebDriverWait(driver, 20)

        # Wait for the form to be ready
        wait.until(EC.presence_of_element_located((By.NAME, "accept_datause_restrictions")))
        print("✓ Page loaded")

        # Accept data use restrictions
        print("\nAccepting data use restrictions...")
        agree_checkbox = driver.find_element(By.NAME, "accept_datause_restrictions")
        if not agree_checkbox.is_selected():
            driver.execute_script("arguments[0].click();", agree_checkbox)

        # Find and configure a simple query
        print("Configuring simple query (All deaths, 2019-2020, grouped by year)...")

        # Section 1: Organize table layout
        # Group by Year
        try:
            group_by_select = driver.find_element(By.NAME, "B_1")
            driver.execute_script("arguments[0].value = 'D76.V1-level1';", group_by_select)
        except Exception as e:
            print(f"Could not set group by: {e}")

        # Select years 2019-2020
        print("Selecting years...")
        try:
            # Find the year section and select 2019, 2020
            year_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='F_D76.V1']")
            years_to_select = ['2019', '2020']

            for inp in year_inputs:
                if inp.get_attribute('value') in years_to_select:
                    if not inp.is_selected():
                        driver.execute_script("arguments[0].click();", inp)
        except Exception as e:
            print(f"Could not select years: {e}")

        # Click Send button
        print("\nSubmitting request...")
        send_button = wait.until(EC.element_to_be_clickable((By.NAME, "action-Send")))

        # Clear previous logs
        driver.get_log('performance')

        # Click send
        driver.execute_script("arguments[0].click();", send_button)

        # Wait a bit for the request to be sent
        time.sleep(3)

        # Capture network logs
        print("\nCapturing network requests...")
        logs = driver.get_log('performance')

        import json

        request_data = None
        for entry in logs:
            try:
                log = json.loads(entry['message'])
                message = log['message']

                # Look for POST requests to datarequest
                if message['method'] == 'Network.requestWillBeSent':
                    request = message['params']['request']
                    if '/datarequest/D76' in request['url'] and request['method'] == 'POST':
                        print(f"\n✓ Found request to: {request['url']}")

                        if 'postData' in request:
                            print("\n" + "="*80)
                            print("POST DATA:")
                            print("="*80)
                            print(request['postData'])
                            request_data = request['postData']

                            # Try to extract just the XML
                            if 'request_xml=' in request_data:
                                from urllib.parse import unquote
                                xml_part = request_data.split('request_xml=')[1]
                                decoded_xml = unquote(xml_part)
                                print("\n" + "="*80)
                                print("DECODED XML:")
                                print("="*80)
                                print(decoded_xml)
                        break
            except Exception as e:
                continue

        if not request_data:
            print("\n❌ Could not capture the request!")
            print("This might be because:")
            print("1. The request was blocked/failed")
            print("2. Network logging didn't capture it")
            print("3. The form submission didn't work")

        return request_data

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    capture_real_request()
