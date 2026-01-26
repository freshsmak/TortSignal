#!/usr/bin/env python3
"""
Analyze CDC WONDER form structure
"""
import requests
from bs4 import BeautifulSoup
import re

def analyze_form():
    print("Fetching CDC WONDER form...")

    response = requests.get("https://wonder.cdc.gov/ucd-icd10.html")

    if response.status_code != 200:
        print(f"Failed to fetch form: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    print("\n" + "="*80)
    print("FORM ANALYSIS")
    print("="*80)

    # Find all select elements
    print("\n### SELECT ELEMENTS ###")
    for select in soup.find_all('select'):
        name = select.get('name', 'unnamed')
        if name.startswith('B_') or name.startswith('O_'):
            options = [opt.get('value') for opt in select.find_all('option')]
            print(f"\n{name}:")
            for opt in options[:10]:  # First 10 options
                print(f"  - {opt}")

    # Find radio button groups related to age
    print("\n\n### RADIO BUTTONS (Age related) ###")
    age_radios = soup.find_all('input', {'type': 'radio', 'name': re.compile('.*age.*|.*V5.*', re.I)})
    for radio in age_radios:
        name = radio.get('name')
        value = radio.get('value')
        print(f"{name} = {value}")

    # Find O_ parameters
    print("\n\n### O_ PARAMETERS (Options) ###")
    o_inputs = soup.find_all('input', {'name': re.compile('^O_')})
    for inp in o_inputs:
        name = inp.get('name')
        value = inp.get('value', '')
        input_type = inp.get('type', 'text')
        print(f"{name} ({input_type}) = {value}")

    o_selects = soup.find_all('select', {'name': re.compile('^O_')})
    for select in o_selects:
        name = select.get('name')
        options = [opt.get('value') for opt in select.find_all('option')]
        print(f"{name} (select) options: {', '.join(options[:5])}")

    # Look for age group configuration specifically
    print("\n\n### AGE GROUP CONFIGURATION ###")

    # Find any element with "Ten-Year Age Groups" text
    age_elements = soup.find_all(string=re.compile('Ten-Year Age', re.I))
    print(f"Found {len(age_elements)} elements mentioning 'Ten-Year Age Groups'")

    for elem in age_elements[:3]:
        parent = elem.parent
        if parent:
            # Look for nearby radio buttons or select elements
            nearby_inputs = parent.find_all(['input', 'select'])
            for inp in nearby_inputs:
                name = inp.get('name', '')
                value = inp.get('value', '')
                input_type = inp.get('type', '')
                print(f"  Near 'Ten-Year Age Groups': {name} ({input_type}) = {value}")

    # Find section about age groups
    print("\n\n### SEARCHING FOR AGE BUTTON/SELECTOR ###")

    # Look for radio buttons with age-related values
    all_radios = soup.find_all('input', {'type': 'radio'})
    for radio in all_radios:
        value = radio.get('value', '')
        name = radio.get('name', '')
        if 'V5' in value or 'age' in value.lower():
            checked = 'checked' if radio.get('checked') else ''
            print(f"{name} = {value} {checked}")

            # Find the label
            radio_id = radio.get('id')
            if radio_id:
                label = soup.find('label', {'for': radio_id})
                if label:
                    print(f"  Label: {label.get_text(strip=True)}")

if __name__ == "__main__":
    analyze_form()
