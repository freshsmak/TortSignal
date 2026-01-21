"""Analyze FARXIGA trend through 2025 and verify with UniCourt litigation."""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENFDA_API_KEY")

def get_death_count(drug_name, start_date, end_date):
    """Get death count for a drug in a date range."""
    date_range = f"[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]"

    params = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}" AND patient.reaction.reactionmeddrapt:"DEATH"',
        "limit": 1
    }

    response = requests.get("https://api.fda.gov/drug/event.json", params=params, timeout=30)
    if response.status_code != 200:
        return None

    return response.json().get('meta', {}).get('results', {}).get('total', 0)

def get_total_reports(drug_name, start_date, end_date):
    """Get total adverse event reports for a drug."""
    date_range = f"[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]"

    params = {
        "api_key": api_key,
        "search": f'receivedate:{date_range} AND patient.drug.openfda.brand_name:"{drug_name}"',
        "limit": 1
    }

    response = requests.get("https://api.fda.gov/drug/event.json", params=params, timeout=30)
    if response.status_code != 200:
        return None

    return response.json().get('meta', {}).get('results', {}).get('total', 0)

print("="*70)
print("FARXIGA TREND ANALYSIS: 2023 → 2024 → 2025")
print("="*70)
print("\nToday's date: January 2026")
print("Analyzing complete quarterly data through Q4 2025\n")

drug_name = "FARXIGA"

# Define all quarters
quarters = [
    ("Q1 2023", datetime(2023, 1, 1), datetime(2023, 3, 31)),
    ("Q2 2023", datetime(2023, 4, 1), datetime(2023, 6, 30)),
    ("Q3 2023", datetime(2023, 7, 1), datetime(2023, 9, 30)),
    ("Q4 2023", datetime(2023, 10, 1), datetime(2023, 12, 31)),
    ("Q1 2024", datetime(2024, 1, 1), datetime(2024, 3, 31)),
    ("Q2 2024", datetime(2024, 4, 1), datetime(2024, 6, 30)),
    ("Q3 2024", datetime(2024, 7, 1), datetime(2024, 9, 30)),
    ("Q4 2024", datetime(2024, 10, 1), datetime(2024, 12, 31)),
    ("Q1 2025", datetime(2025, 1, 1), datetime(2025, 3, 31)),
    ("Q2 2025", datetime(2025, 4, 1), datetime(2025, 6, 30)),
    ("Q3 2025", datetime(2025, 7, 1), datetime(2025, 9, 30)),
    ("Q4 2025", datetime(2025, 10, 1), datetime(2025, 12, 31)),
]

print("="*70)
print("QUARTERLY DEATH REPORTS")
print("="*70)

results = []

for quarter_name, start, end in quarters:
    print(f"\nFetching {quarter_name}...")

    deaths = get_death_count(drug_name, start, end)
    total = get_total_reports(drug_name, start, end)

    if deaths is not None and total is not None:
        death_rate = (deaths / total * 100) if total > 0 else 0
        results.append({
            'quarter': quarter_name,
            'deaths': deaths,
            'total': total,
            'death_rate': death_rate
        })
        print(f"  Deaths: {deaths:,}")
        print(f"  Total reports: {total:,}")
        print(f"  Death rate: {death_rate:.2f}%")
    else:
        print(f"  Failed to fetch data")

print("\n" + "="*70)
print("TREND SUMMARY")
print("="*70)

print(f"\n{'Quarter':<10} {'Deaths':<10} {'Total Reports':<15} {'Death Rate':<12} {'QoQ Change'}")
print("-"*70)

for i, r in enumerate(results):
    quarter = r['quarter']
    deaths = f"{r['deaths']:,}"
    total = f"{r['total']:,}"
    rate = f"{r['death_rate']:.2f}%"

    # Calculate quarter-over-quarter change
    if i > 0:
        prev_deaths = results[i-1]['deaths']
        if prev_deaths > 0:
            qoq_change = ((r['deaths'] - prev_deaths) / prev_deaths * 100)
            change_str = f"{qoq_change:+.1f}%"
        else:
            change_str = "N/A"
    else:
        change_str = "-"

    print(f"{quarter:<10} {deaths:<10} {total:<15} {rate:<12} {change_str}")

# Calculate key metrics
if len(results) >= 4:
    q4_2023 = next(r for r in results if r['quarter'] == 'Q4 2023')
    q4_2024 = next(r for r in results if r['quarter'] == 'Q4 2024')
    q4_2025 = next((r for r in results if r['quarter'] == 'Q4 2025'), None)

    print("\n" + "="*70)
    print("YEAR-OVER-YEAR COMPARISON")
    print("="*70)

    yoy_2024 = ((q4_2024['deaths'] - q4_2023['deaths']) / q4_2023['deaths'] * 100)
    print(f"\nQ4 2023 → Q4 2024:")
    print(f"  Deaths: {q4_2023['deaths']:,} → {q4_2024['deaths']:,}")
    print(f"  Change: {yoy_2024:+.1f}% ({q4_2024['deaths'] - q4_2023['deaths']:+,} deaths)")

    if q4_2025:
        yoy_2025 = ((q4_2025['deaths'] - q4_2024['deaths']) / q4_2024['deaths'] * 100)
        print(f"\nQ4 2024 → Q4 2025:")
        print(f"  Deaths: {q4_2024['deaths']:,} → {q4_2025['deaths']:,}")
        print(f"  Change: {yoy_2025:+.1f}% ({q4_2025['deaths'] - q4_2024['deaths']:+,} deaths)")

        # Total 2-year change
        total_change = ((q4_2025['deaths'] - q4_2023['deaths']) / q4_2023['deaths'] * 100)
        print(f"\nQ4 2023 → Q4 2025 (2-year trend):")
        print(f"  Deaths: {q4_2023['deaths']:,} → {q4_2025['deaths']:,}")
        print(f"  Change: {total_change:+.1f}% ({q4_2025['deaths'] - q4_2023['deaths']:+,} deaths)")

# Calculate 2025 annual totals
deaths_2025 = sum(r['deaths'] for r in results if '2025' in r['quarter'])
total_2025 = sum(r['total'] for r in results if '2025' in r['quarter'])
deaths_2024 = sum(r['deaths'] for r in results if '2024' in r['quarter'])
total_2024 = sum(r['total'] for r in results if '2024' in r['quarter'])

print("\n" + "="*70)
print("ANNUAL TOTALS")
print("="*70)

if deaths_2024 > 0:
    print(f"\n2024 Total:")
    print(f"  Deaths: {deaths_2024:,}")
    print(f"  Total reports: {total_2024:,}")
    print(f"  Death rate: {(deaths_2024/total_2024*100):.2f}%")

if deaths_2025 > 0:
    print(f"\n2025 Total:")
    print(f"  Deaths: {deaths_2025:,}")
    print(f"  Total reports: {total_2025:,}")
    print(f"  Death rate: {(deaths_2025/total_2025*100):.2f}%")

    annual_change = ((deaths_2025 - deaths_2024) / deaths_2024 * 100)
    print(f"\n2024 → 2025 Change:")
    print(f"  {annual_change:+.1f}% ({deaths_2025 - deaths_2024:+,} deaths)")

print("\n" + "="*70)
print("🚨 SIGNAL ASSESSMENT")
print("="*70)

# Determine trend
if q4_2025:
    if q4_2025['deaths'] > q4_2024['deaths'] * 1.2:
        trend = "🔴 ACCELERATING"
        assessment = "Signal is getting WORSE - litigation risk increasing"
    elif q4_2025['deaths'] > q4_2024['deaths']:
        trend = "🟠 CONTINUING"
        assessment = "Signal persisting - sustained elevated risk"
    elif q4_2025['deaths'] < q4_2024['deaths'] * 0.8:
        trend = "🟢 DECLINING"
        assessment = "Signal may have been transient or corrective action taken"
    else:
        trend = "🟡 STABLE"
        assessment = "Signal stable at elevated level"

    print(f"\nTrend: {trend}")
    print(f"Assessment: {assessment}")

    print(f"\nNext Step: Cross-reference with UniCourt to check for litigation filings")
    print(f"Expected: If signal is real, plaintiff firms may have started filing in 2025")

print("\n" + "="*70)
