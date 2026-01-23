#!/usr/bin/env python3
"""
Simplified FARXIGA signal insertion - bypasses FAERS query issues.

Directly inserts a known signal into the database for testing.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.db import get_cursor
from dotenv import load_dotenv

load_dotenv()


def insert_farxiga_signal():
    """
    Insert FARXIGA signal directly into database.

    Uses known data from FARXIGA analysis:
    - Q4 2023: 397 deaths (baseline)
    - Q4 2024: 715 deaths (+80% spike)
    """
    print("\n" + "="*80)
    print("AUDITSignal - Direct FARXIGA Signal Insertion")
    print("="*80)

    # Known data from FARXIGA analysis
    baseline_deaths = 397
    current_deaths = 715
    death_change = current_deaths - baseline_deaths
    death_pct = (death_change / baseline_deaths * 100)

    print(f"\nInserting FARXIGA signal:")
    print(f"  Baseline (Q4 2023): {baseline_deaths} deaths")
    print(f"  Current (Q4 2024): {current_deaths} deaths")
    print(f"  Change: +{death_change} deaths (+{death_pct:.0f}%)")
    print(f"  Severity: HIGH CONVICTION")

    severity_score = 85.0  # High conviction threshold

    try:
        with get_cursor() as cur:
            # 1. Create unique constraint on defendants.name if it doesn't exist
            print("\n1. Ensuring database constraints...")
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = 'ux_defendants_name'
                    ) THEN
                        CREATE UNIQUE INDEX ux_defendants_name ON defendants(name);
                    END IF;
                END $$;
            """)

            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = 'ux_products_name'
                    ) THEN
                        CREATE UNIQUE INDEX ux_products_name ON products(name);
                    END IF;
                END $$;
            """)

            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = 'ux_injuries_name'
                    ) THEN
                        CREATE UNIQUE INDEX ux_injuries_name ON injuries(name);
                    END IF;
                END $$;
            """)
            print("✓ Constraints verified")

            # 2. Insert defendant (AstraZeneca)
            print("\n2. Inserting defendant...")
            cur.execute("""
                INSERT INTO defendants (name, ticker)
                VALUES ('AstraZeneca', 'AZN')
                ON CONFLICT (name) DO UPDATE SET ticker = EXCLUDED.ticker
                RETURNING defendant_id
            """)
            defendant_id = cur.fetchone()[0]
            print(f"✓ AstraZeneca (ID: {defendant_id})")

            # 3. Insert product (FARXIGA)
            print("\n3. Inserting product...")
            cur.execute("""
                INSERT INTO products (name, product_type)
                VALUES ('FARXIGA', 'drug')
                ON CONFLICT (name) DO UPDATE SET product_type = EXCLUDED.product_type
                RETURNING product_id
            """)
            product_id = cur.fetchone()[0]
            print(f"✓ FARXIGA (ID: {product_id})")

            # 4. Insert injury (Death)
            print("\n4. Inserting injury...")
            cur.execute("""
                INSERT INTO injuries (name)
                VALUES ('Death')
                ON CONFLICT (name) DO NOTHING
                RETURNING injury_id
            """)
            result = cur.fetchone()
            if result:
                injury_id = result[0]
            else:
                cur.execute("SELECT injury_id FROM injuries WHERE name = 'Death'")
                injury_id = cur.fetchone()[0]
            print(f"✓ Death (ID: {injury_id})")

            # 5. Insert product_signal
            print("\n5. Inserting product signal...")
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
                    %s, %s, 'adverse_event', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                datetime(2024, 10, 1),
                datetime.now(),
                3444,  # total reports Q4 2024
                current_deaths,
                3444,
                death_change,
                death_pct / 100,
                'accelerating',
                severity_score,
                'worsening',
                'active'
            ))
            signal_id = cur.fetchone()[0]
            print(f"✓ Product signal (ID: {signal_id})")
            print(f"  - Severity score: {severity_score}")
            print(f"  - Death count: {current_deaths} (+{death_pct:.0f}%)")

            # 6. Insert candidate
            print("\n6. Inserting candidate...")
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
                    'AstraZeneca|FARXIGA',
                    'AstraZeneca',
                    'FARXIGA',
                    'Death',
                    %s, %s, %s,
                    'pharma',
                    %s, %s,
                    %s,
                    %s::jsonb,
                    %s::jsonb,
                    %s,
                    'new'
                )
                ON CONFLICT (candidate_key)
                DO UPDATE SET
                    last_seen_at = EXCLUDED.last_seen_at,
                    score_total = EXCLUDED.score_total
                RETURNING candidate_id
            """, (
                defendant_id,
                product_id,
                injury_id,
                datetime(2024, 10, 1),
                datetime.now(),
                severity_score,
                '{"faers_death_spike": 85, "literature": 0, "litigation": 0}',
                '{"velocity_7d": 0, "velocity_30d": 318, "acceleration_ratio": 0.8}',
                f'+{death_pct:.0f}% death spike detected in Q4 2024. {current_deaths} deaths vs {baseline_deaths} baseline.'
            ))
            candidate_id = cur.fetchone()[0]
            print(f"✓ Candidate (ID: {candidate_id})")
            print(f"  - Score: {severity_score} (HIGH CONVICTION)")

            # 7. Insert signal event
            print("\n7. Inserting signal event...")
            cur.execute("""
                INSERT INTO signal_events (
                    event_type,
                    event_time,
                    weight,
                    excerpt
                ) VALUES (%s, %s, %s, %s)
            """, (
                'adverse_trend',
                datetime.now(),
                severity_score / 100,
                f'FARXIGA death reports increased +{death_pct:.0f}% in Q4 2024. Baseline: {baseline_deaths} deaths (Q4 2023) → Current: {current_deaths} deaths (Q4 2024)'
            ))
            print(f"✓ Signal event created")

        print("\n" + "="*80)
        print("✅ SUCCESS - FARXIGA signal inserted into Safety Intelligence Graph")
        print("="*80)

        print("\n📊 Open dashboard: http://localhost:8501")
        print("\nYou should see:")
        print("  - Quick Stats: Active Candidates = 1")
        print("  - Watchlist: '1 candidates matching filters'")
        print("  - FARXIGA row with HIGH CONVICTION badge")
        print("  - Score: 85.0")

        print("\n" + "="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    insert_farxiga_signal()
