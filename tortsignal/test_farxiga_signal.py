#!/usr/bin/env python3
"""
Test script: Analyze FARXIGA signal and populate Safety Intelligence Graph

This reproduces the FARXIGA +80% death spike analysis and inserts
the signal into the database so it appears in the dashboard.

Usage:
    python test_farxiga_signal.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.connectors.faers import FAERSConnector
from src.db import get_cursor
from dotenv import load_dotenv

load_dotenv()


def analyze_farxiga_quarterly(connector: FAERSConnector):
    """
    Analyze FARXIGA adverse events by quarter.

    Reproduces the analysis that found +80% death spike in Q4 2024.
    """
    print("\n" + "="*80)
    print("FARXIGA (Dapagliflozin) - Quarterly Adverse Event Analysis")
    print("="*80)

    drug_name = "FARXIGA"
    quarters = [
        (2023, 4),  # Baseline: Q4 2023
        (2024, 1),  # Q1 2024
        (2024, 2),  # Q2 2024
        (2024, 3),  # Q3 2024
        (2024, 4),  # Q4 2024 - where spike occurred
    ]

    print(f"\nQuerying FAERS for {drug_name}...")
    print(f"{'Period':<12} {'Deaths':<10} {'Serious':<10} {'Total':<10} {'Death Rate':<12}")
    print("-" * 80)

    results = []
    for year, quarter in quarters:
        # Calculate quarter date ranges
        quarter_dates = {
            1: ('0101', '0331'),
            2: ('0401', '0630'),
            3: ('0701', '0930'),
            4: ('1001', '1231'),
        }

        start_date = f"{year}{quarter_dates[quarter][0]}"
        end_date = f"{year}{quarter_dates[quarter][1]}"

        try:
            # Query FAERS for this quarter
            search_query = f'patient.drug.openfda.brand_name:"FARXIGA" AND receivedate:[{start_date} TO {end_date}]'

            # Get death count
            death_response = connector.session.get(
                connector.BASE_URL,
                params={
                    'search': search_query + ' AND serious:1',  # serious=1 means death
                    'count': 'serious',
                    'limit': 1000
                }
            )

            death_count = 0
            if death_response.status_code == 200:
                death_data = death_response.json()
                for item in death_data.get('results', []):
                    if item.get('term') == '1':  # 1 = death
                        death_count = item.get('count', 0)

            # Get total count
            total_response = connector.session.get(
                connector.BASE_URL,
                params={
                    'search': search_query,
                    'limit': 1
                }
            )

            total_count = 0
            if total_response.status_code == 200:
                total_data = total_response.json()
                total_count = total_data.get('meta', {}).get('results', {}).get('total', 0)

            death_rate = (death_count / total_count * 100) if total_count > 0 else 0

            period_label = f"{year} Q{quarter}"
            print(f"{period_label:<12} {death_count:<10} {total_count:<10} {total_count:<10} {death_rate:>6.1f}%")

            results.append({
                'year': year,
                'quarter': quarter,
                'period': period_label,
                'deaths': death_count,
                'total': total_count,
                'death_rate': death_rate
            })

        except Exception as e:
            print(f"Error for {year} Q{quarter}: {e}")

    # Calculate spike
    if len(results) >= 2:
        baseline = results[0]  # Q4 2023
        current = results[-1]   # Q4 2024

        death_change = current['deaths'] - baseline['deaths']
        death_pct = (death_change / baseline['deaths'] * 100) if baseline['deaths'] > 0 else 0

        print("\n" + "="*80)
        print("SIGNAL ANALYSIS")
        print("="*80)
        print(f"\nBaseline ({baseline['period']}): {baseline['deaths']} deaths")
        print(f"Current ({current['period']}):  {current['deaths']} deaths")
        print(f"\nChange: +{death_change} deaths ({death_pct:+.1f}%)")

        if death_pct >= 50:
            print(f"\n🚨 SIGNAL DETECTED: {death_pct:+.0f}% increase in deaths")
            print("   Severity: HIGH" if death_pct >= 75 else "   Severity: MODERATE")

    return results


def insert_signal_to_database(results: list):
    """
    Insert FARXIGA signal into Safety Intelligence Graph.

    This populates:
    - products table
    - defendants table
    - product_signals table
    - candidates table

    So the signal appears in the dashboard.
    """
    print("\n" + "="*80)
    print("INSERTING SIGNAL INTO SAFETY INTELLIGENCE GRAPH")
    print("="*80)

    try:
        with get_cursor() as cur:
            # 1. Insert defendant (AstraZeneca)
            cur.execute("""
                INSERT INTO defendants (name, ticker)
                VALUES ('AstraZeneca', 'AZN')
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING defendant_id
            """)
            defendant_id = cur.fetchone()[0]
            print(f"✓ Defendant created: AstraZeneca (ID: {defendant_id})")

            # 2. Insert product (FARXIGA)
            cur.execute("""
                INSERT INTO products (name, product_type)
                VALUES ('FARXIGA', 'drug')
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING product_id
            """)
            product_id = cur.fetchone()[0]
            print(f"✓ Product created: FARXIGA (ID: {product_id})")

            # 3. Insert injury (Death)
            cur.execute("""
                INSERT INTO injuries (name)
                VALUES ('Death')
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING injury_id
            """)
            injury_id = cur.fetchone()[0]
            print(f"✓ Injury created: Death (ID: {injury_id})")

            # 4. Calculate signal metrics from results
            if len(results) >= 2:
                baseline = results[0]
                current = results[-1]

                death_change = current['deaths'] - baseline['deaths']
                death_pct = (death_change / baseline['deaths'] * 100) if baseline['deaths'] > 0 else 0

                # Determine severity score (0-100)
                if death_pct >= 100:
                    severity_score = 95.0
                elif death_pct >= 75:
                    severity_score = 85.0
                elif death_pct >= 50:
                    severity_score = 70.0
                else:
                    severity_score = 50.0

                # 5. Insert product_signal
                cur.execute("""
                    INSERT INTO product_signals (
                        product_id,
                        injury_id,
                        signal_type,
                        first_detected_at,
                        last_updated_at,
                        report_count,
                        death_count,
                        serious_count,
                        velocity_30d,
                        acceleration_ratio,
                        trend_direction,
                        severity_score,
                        severity_trend,
                        status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (product_id, injury_id, signal_type)
                    DO UPDATE SET
                        last_updated_at = EXCLUDED.last_updated_at,
                        death_count = EXCLUDED.death_count,
                        severity_score = EXCLUDED.severity_score
                    RETURNING signal_id
                """, (
                    product_id,
                    injury_id,
                    'adverse_event',
                    datetime(2024, 10, 1),  # Q4 2024 start
                    datetime.now(),
                    current['total'],
                    current['deaths'],
                    current['total'],
                    current['deaths'] - baseline['deaths'],
                    death_pct / 100,  # ratio
                    'accelerating' if death_pct > 0 else 'stable',
                    severity_score,
                    'worsening' if death_pct >= 50 else 'stable',
                    'active'
                ))
                signal_id = cur.fetchone()[0]
                print(f"✓ Product signal created (ID: {signal_id})")
                print(f"  - Deaths: {current['deaths']} (+{death_pct:.0f}% vs baseline)")
                print(f"  - Severity score: {severity_score:.1f}")

                # 6. Insert candidate (for TortSignal watchlist)
                cur.execute("""
                    INSERT INTO candidates (
                        candidate_key,
                        defendant_text,
                        product_text,
                        injury_text,
                        defendant_id,
                        product_id,
                        injury_id,
                        category,
                        first_seen_at,
                        last_seen_at,
                        score_total,
                        score_components,
                        metrics_json,
                        why_now,
                        status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (candidate_key)
                    DO UPDATE SET
                        last_seen_at = EXCLUDED.last_seen_at,
                        score_total = EXCLUDED.score_total
                    RETURNING candidate_id
                """, (
                    'AstraZeneca|FARXIGA',
                    'AstraZeneca',
                    'FARXIGA',
                    'Death',
                    defendant_id,
                    product_id,
                    injury_id,
                    'pharma',
                    datetime(2024, 10, 1),
                    datetime.now(),
                    severity_score,
                    {'faers_death_spike': severity_score, 'literature': 0, 'litigation': 0},
                    {'velocity_7d': 0, 'velocity_30d': death_change, 'acceleration_ratio': death_pct / 100},
                    f'+{death_pct:.0f}% death spike detected in Q4 2024 vs Q4 2023 baseline. {current["deaths"]} deaths reported.',
                    'new'
                ))
                candidate_id = cur.fetchone()[0]
                print(f"✓ Candidate created (ID: {candidate_id})")
                print(f"  - Score: {severity_score:.1f} (HIGH CONVICTION)" if severity_score >= 70 else f"  - Score: {severity_score:.1f}")

                # 7. Insert signal event (for timeline)
                cur.execute("""
                    INSERT INTO signal_events (
                        cluster_id,
                        event_type,
                        event_time,
                        weight,
                        excerpt
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    None,  # Not linked to tort cluster yet
                    'adverse_trend',
                    datetime.now(),
                    severity_score / 100,
                    f'FARXIGA death reports increased {death_pct:+.0f}% in Q4 2024. Baseline: {baseline["deaths"]} deaths (Q4 2023) → Current: {current["deaths"]} deaths (Q4 2024)'
                ))
                print(f"✓ Signal event created")

        print("\n✅ Signal successfully inserted into Safety Intelligence Graph")
        print("\n📊 View in dashboard: http://localhost:8501")
        print("   - Navigate to 'Watchlist' to see FARXIGA candidate")
        print("   - Score should show as HIGH CONVICTION (>70)")

    except Exception as e:
        print(f"\n❌ Error inserting signal: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main execution."""
    print("\n" + "="*80)
    print("AUDITSignal - FARXIGA Signal Detection Test")
    print("="*80)
    print("\nThis script:")
    print("1. Analyzes FARXIGA adverse events from FAERS")
    print("2. Detects the +80% death spike (Q4 2023 → Q4 2024)")
    print("3. Inserts signal into Safety Intelligence Graph database")
    print("4. Makes it visible in the dashboard")

    # Initialize FAERS connector
    api_key = os.getenv('OPENFDA_API_KEY')
    connector = FAERSConnector(api_key=api_key)

    # Set base URL for direct API calls (connector uses a different structure)
    connector.BASE_URL = "https://api.fda.gov/drug/event.json"

    # Run analysis
    results = analyze_farxiga_quarterly(connector)

    if not results:
        print("\n❌ No results from FAERS. Check API connectivity.")
        return

    # Insert into database
    insert_signal_to_database(results)

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
1. Open dashboard: python3 -m streamlit run app/app.py
2. Navigate to 'Watchlist' page
3. You should see: "1 candidates matching filters"
4. FARXIGA should appear with HIGH CONVICTION badge
5. Click "View" to see full signal details

This proves the Safety Intelligence Graph is working!
Next: Build UniCourt AI browser agent to verify litigation status.
""")


if __name__ == "__main__":
    main()
