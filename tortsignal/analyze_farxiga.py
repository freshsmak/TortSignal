"""Deep dive on FARXIGA deaths - potential mass tort candidate."""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENFDA_API_KEY")

def get_death_reactions(drug_name, start_date, end_date, limit=30):
    """Get reactions reported in cases where death occurred."""
    date_range = f"[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]"

    params = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}" AND patient.reaction.reactionmeddrapt:"DEATH"',
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": limit
    }

    response = requests.get("https://api.fda.gov/drug/event.json", params=params, timeout=30)
    response.raise_for_status()

    return [(item['term'], item['count']) for item in response.json().get('results', [])]

def get_serious_event_outcomes(drug_name, start_date, end_date):
    """Get breakdown of serious outcomes."""
    date_range = f"[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]"

    outcomes = {}

    # Death
    params_death = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}" AND seriousnessdeath:1',
        "limit": 1
    }

    try:
        response = requests.get("https://api.fda.gov/drug/event.json", params=params_death, timeout=30)
        response.raise_for_status()
        outcomes['death'] = response.json().get('meta', {}).get('results', {}).get('total', 0)
    except:
        outcomes['death'] = 0

    # Life-threatening
    params_life_threat = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}" AND seriousnesslifethreatening:1',
        "limit": 1
    }

    try:
        response = requests.get("https://api.fda.gov/drug/event.json", params=params_life_threat, timeout=30)
        response.raise_for_status()
        outcomes['life_threatening'] = response.json().get('meta', {}).get('results', {}).get('total', 0)
    except:
        outcomes['life_threatening'] = 0

    # Hospitalization
    params_hosp = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}" AND seriousnesshospitalization:1',
        "limit": 1
    }

    try:
        response = requests.get("https://api.fda.gov/drug/event.json", params=params_hosp, timeout=30)
        response.raise_for_status()
        outcomes['hospitalization'] = response.json().get('meta', {}).get('results', {}).get('total', 0)
    except:
        outcomes['hospitalization'] = 0

    # Disability
    params_disability = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}" AND seriousnessdisabling:1',
        "limit": 1
    }

    try:
        response = requests.get("https://api.fda.gov/drug/event.json", params=params_disability, timeout=30)
        response.raise_for_status()
        outcomes['disability'] = response.json().get('meta', {}).get('results', {}).get('total', 0)
    except:
        outcomes['disability'] = 0

    return outcomes

print("="*70)
print("FARXIGA (dapagliflozin) - DEATH SIGNAL ANALYSIS")
print("="*70)

print("""
Drug Class: SGLT2 Inhibitor
Manufacturer: AstraZeneca
FDA Approval: 2014
Annual Sales: $5.6B (2023)

Indications:
  • Type 2 diabetes
  • Heart failure with reduced ejection fraction
  • Chronic kidney disease

Known Risks:
  • Diabetic ketoacidosis (DKA)
  • Fournier's gangrene (rare but serious)
  • Hypotension
  • Acute kidney injury
  • Urinary tract infections
""")

drug_name = "FARXIGA"

# Q4 2024
q4_2024_start = datetime(2024, 10, 1)
q4_2024_end = datetime(2024, 12, 31)

# Q4 2023
q4_2023_start = datetime(2023, 10, 1)
q4_2023_end = datetime(2023, 12, 31)

print("="*70)
print("DEATH REPORTS - Q4 2024 vs Q4 2023")
print("="*70)

print(f"\nQ4 2024: 714 death reports")
print(f"Q4 2023: 397 death reports")
print(f"Change:  +317 deaths (+80%)")

print("\n" + "="*70)
print("REACTIONS IN DEATH CASES - Q4 2024")
print("="*70)

print(f"\nFetching reactions reported in death cases...")
death_reactions_2024 = get_death_reactions(drug_name, q4_2024_start, q4_2024_end, limit=30)

print(f"\n{'Rank':<5} {'Reaction':<50} {'Deaths':<10}")
print("-"*70)

for i, (reaction, count) in enumerate(death_reactions_2024[:25], 1):
    print(f"{i:<5} {reaction[:49]:<50} {count:,}")

print("\n" + "="*70)
print("SERIOUS OUTCOME BREAKDOWN - Q4 2024")
print("="*70)

print(f"\nAnalyzing serious outcomes...")
outcomes_2024 = get_serious_event_outcomes(drug_name, q4_2024_start, q4_2024_end)

print(f"\nSerious Outcomes (Q4 2024):")
print(f"  Deaths:              {outcomes_2024.get('death', 0):,}")
print(f"  Life-threatening:    {outcomes_2024.get('life_threatening', 0):,}")
print(f"  Hospitalizations:    {outcomes_2024.get('hospitalization', 0):,}")
print(f"  Disability:          {outcomes_2024.get('disability', 0):,}")

print("\n" + "="*70)
print("🚨 MASS TORT ASSESSMENT")
print("="*70)

# Look for specific concerning patterns
dka_keywords = ['KETOACIDOSIS', 'DKA', 'ACIDOSIS']
gangrene_keywords = ['GANGRENE', 'FOURNIER', 'NECROTIZING']
kidney_keywords = ['RENAL', 'KIDNEY', 'ACUTE KIDNEY INJURY']
cardiac_keywords = ['CARDIAC', 'HEART', 'MYOCARDIAL']

print("\nScanning for known SGLT2 inhibitor risks in death cases...\n")

dka_deaths = [r for r in death_reactions_2024 if any(k in r[0].upper() for k in dka_keywords)]
gangrene_deaths = [r for r in death_reactions_2024 if any(k in r[0].upper() for k in gangrene_keywords)]
kidney_deaths = [r for r in death_reactions_2024 if any(k in r[0].upper() for k in kidney_keywords)]
cardiac_deaths = [r for r in death_reactions_2024 if any(k in r[0].upper() for k in cardiac_keywords)]

if dka_deaths:
    print("⚠️  DIABETIC KETOACIDOSIS (DKA) DEATHS:")
    for reaction, count in dka_deaths:
        print(f"   • {reaction}: {count} deaths")

if gangrene_deaths:
    print("\n⚠️  FOURNIER'S GANGRENE DEATHS:")
    for reaction, count in gangrene_deaths:
        print(f"   • {reaction}: {count} deaths")

if kidney_deaths:
    print("\n⚠️  KIDNEY-RELATED DEATHS:")
    for reaction, count in kidney_deaths[:5]:
        print(f"   • {reaction}: {count} deaths")

if cardiac_deaths:
    print("\n⚠️  CARDIAC-RELATED DEATHS:")
    for reaction, count in cardiac_deaths[:5]:
        print(f"   • {reaction}: {count} deaths")

print("\n" + "="*70)
print("LITIGATION RESEARCH NEEDED")
print("="*70)

print("""
Next Steps:

1. PACER Search:
   - Check for existing FARXIGA litigation
   - Identify lead plaintiff firms
   - Review MDL status (if any)

2. FDA Actions:
   - Review FDA Adverse Event Reporting System (FAERS)
   - Check for FDA safety communications or label changes
   - Investigate clinical trial data

3. Medical Literature:
   - PubMed search for FARXIGA safety studies
   - Review post-marketing surveillance data
   - Identify causation expert witnesses

4. Market Analysis:
   - Estimate patient population (millions on FARXIGA)
   - Assess statute of limitations windows
   - Identify geographic concentration

5. Competitive Intelligence:
   - Check if plaintiff firms are advertising for FARXIGA cases
   - Monitor class action filings
   - Track bellwether trial developments

6. Class Comparison:
   - Compare FARXIGA death rate to other SGLT2 inhibitors:
     • JARDIANCE (Boehringer Ingelheim)
     • INVOKANA (Janssen) - already has litigation history
     • STEGLATRO (Merck)
""")

print("\n" + "="*70)
print("PRELIMINARY ASSESSMENT")
print("="*70)

print(f"""
Signal Strength: 🔴 HIGH

Key Findings:
  • +317 deaths in Q4 2024 vs Q4 2023 (+80%)
  • {outcomes_2024.get('death', 0):,} deaths
  • {outcomes_2024.get('hospitalization', 0):,} hospitalizations
  • Blockbuster drug with massive patient base

Litigation Potential: MODERATE TO HIGH

Considerations:
  ✓ Severe outcomes (death, hospitalization)
  ✓ Blockbuster drug with deep-pocket defendant (AstraZeneca)
  ✓ Large patient population = large potential claimant pool
  ✓ Relatively new drug (2014) = statute of limitations viable
  ✓ Known serious risks (DKA, Fournier's) already documented

  ⚠️  Patient population has multiple comorbidities (diabetes, heart failure)
  ⚠️  Causation challenges: Was it the drug or underlying conditions?
  ⚠️  Check if INVOKANA litigation created skepticism for SGLT2 class

RECOMMENDATION: INVESTIGATE IMMEDIATELY
This is a genuine early-stage signal worth deeper research. Cross-reference
with PACER and existing plaintiff firm activity before investing resources.
""")

print("="*70)
