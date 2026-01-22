"""
Demo: What the monitoring pipeline looks like with database.

This is a simulation showing how TortSignal transforms from "one-off search"
to "continuous monitoring system" once the database is running.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def simulate_day_1_discovery():
    """Simulate Day 1: FDA signal detection."""
    print("="*70)
    print("DAY 1: FDA SIGNAL DETECTION")
    print("="*70)
    print("\nRunning: python -m src.pipeline.discovery")
    print("\n[FDA FAERS API] Querying for adverse events (last 7 days)...")

    print("""
┌─────────────────────────────────────────────────────────────────┐
│ SIGNAL DETECTED: FARXIGA (dapagliflozin)                       │
├─────────────────────────────────────────────────────────────────┤
│ Metric         │ Q4 2023  │ Q4 2024  │ Change                   │
├────────────────┼──────────┼──────────┼──────────────────────────┤
│ Deaths         │ 397      │ 715      │ +318 (+80%) 🚨          │
│ Total Reports  │ 2,528    │ 3,444    │ +916 (+36%)             │
│ Death Rate     │ 15.7%    │ 20.8%    │ +5.1pp                  │
└─────────────────────────────────────────────────────────────────┘
""")

    print("WITHOUT DATABASE:")
    print("  → Print to console")
    print("  → Results forgotten")
    print("  → No way to track over time")

    print("\nWITH DATABASE:")
    print("  → Executing SQL...")

    sql_commands = [
        """
    -- Store raw FAERS data
    INSERT INTO source_documents (
        doc_id,
        source_type,
        source_uid,
        published_at,
        raw_payload_json
    ) VALUES (
        gen_random_uuid(),
        'faers_report',
        'FAERS-2024-Q4-FARXIGA',
        '2024-12-31',
        '{"drug": "FARXIGA", "deaths": 715, "total": 3444}'::jsonb
    );
    """,
        """
    -- Create or update candidate
    INSERT INTO candidates (
        candidate_id,
        candidate_key,
        defendant_text,
        product_text,
        score_total,
        status,
        first_seen_at,
        last_seen_at
    ) VALUES (
        gen_random_uuid(),
        'AstraZeneca|FARXIGA',
        'AstraZeneca',
        'FARXIGA',
        8.5,
        'new',
        NOW(),
        NOW()
    ) ON CONFLICT (candidate_key) DO UPDATE SET
        last_seen_at = NOW(),
        score_total = EXCLUDED.score_total;
    """,
        """
    -- Record signal event
    INSERT INTO signal_events (
        event_id,
        candidate_id,
        event_type,
        event_time,
        excerpt
    ) VALUES (
        gen_random_uuid(),
        (SELECT candidate_id FROM candidates WHERE candidate_key = 'AstraZeneca|FARXIGA'),
        'adverse_trend',
        NOW(),
        '+80% death spike in Q4 2024 vs Q4 2023 (397 → 715 deaths)'
    );
    """
    ]

    for sql in sql_commands:
        print(f"  {sql.strip()[:80]}...")

    print("\n✓ Candidate created: AstraZeneca | FARXIGA (status: new)")
    print("✓ Signal event recorded: adverse_trend")
    print("✓ Source document stored: FAERS-2024-Q4-FARXIGA")

def simulate_day_30_litigation_check():
    """Simulate Day 30: UniCourt MDL check."""
    print("\n" + "="*70)
    print("DAY 30: LITIGATION VERIFICATION")
    print("="*70)
    print("\nRunning: python -m src.pipeline.discovery")
    print("\n[UniCourt API] Checking for existing litigation...")

    print("""
Query: CaseType:(Product Liability) AND party:(AstraZeneca) AND caseTitle:FARXIGA
""")

    print("\n✓ Found MDL No. 2776:")
    print("  Case Name: In Re: FARXIGA (Dapagliflozin) Products Liability Litigation")
    print("  Filed: March 15, 2017")
    print("  Court: United States District Court, Southern District of California")
    print("  Status: TERMINATED (2020)")

    print("\nWITHOUT DATABASE:")
    print("  → Manual research required")
    print("  → No way to track MDL status changes")
    print("  → Might waste time on dead litigation")

    print("\nWITH DATABASE:")
    print("  → Executing SQL...")

    sql_commands = [
        """
    -- Store court case
    INSERT INTO court_cases (
        case_id,
        source_uid,
        filed_at,
        defendant_text,
        product_text,
        plaintiff_firm,
        jurisdiction
    ) VALUES (
        gen_random_uuid(),
        'MDL-2776',
        '2017-03-15',
        'AstraZeneca',
        'FARXIGA',
        NULL,
        'S.D. Cal.'
    );
    """,
        """
    -- Record MDL discovery event
    INSERT INTO signal_events (
        event_id,
        candidate_id,
        event_type,
        event_time,
        excerpt
    ) VALUES (
        gen_random_uuid(),
        (SELECT candidate_id FROM candidates WHERE candidate_key = 'AstraZeneca|FARXIGA'),
        'mdl_discovered',
        NOW(),
        'MDL No. 2776 - S.D. Cal., Filed 2017-03-15'
    );
    """
    ]

    for sql in sql_commands:
        print(f"  {sql.strip()[:80]}...")

    print("\n✓ Court case stored: MDL-2776")
    print("✓ Signal event recorded: mdl_discovered")

def simulate_day_60_mdl_termination():
    """Simulate Day 60: MDL status check reveals termination."""
    print("\n" + "="*70)
    print("DAY 60: MDL STATUS UPDATE")
    print("="*70)
    print("\nRunning: python -m src.pipeline.discovery")
    print("\n[UniCourt API] Checking MDL status updates...")

    print("""
MDL No. 2776 Status Update:
  Status: TERMINATED (2020-08-15)
  Total Cases: ~67
  Settlement: No major settlement fund
  Outcome: Most cases voluntarily dismissed
""")

    print("\nWITHOUT DATABASE:")
    print("  → User manually discovers failed litigation")
    print("  → Wasted time investigating non-viable tort")

    print("\nWITH DATABASE:")
    print("  → Executing SQL...")

    sql_commands = [
        """
    -- Record MDL termination
    INSERT INTO signal_events (
        event_id,
        candidate_id,
        event_type,
        event_time,
        excerpt
    ) VALUES (
        gen_random_uuid(),
        (SELECT candidate_id FROM candidates WHERE candidate_key = 'AstraZeneca|FARXIGA'),
        'mdl_terminated',
        NOW(),
        'MDL No. 2776 terminated 2020-08-15. ~67 cases, no major settlement. Not viable.'
    );
    """,
        """
    -- Mark candidate as rejected
    UPDATE candidates
    SET
        status = 'rejected',
        why_now = 'Prior MDL litigation failed (MDL-2776, 2017-2020). Only 67 cases, no settlement. Not viable for new litigation despite FDA signal.',
        last_seen_at = NOW()
    WHERE candidate_key = 'AstraZeneca|FARXIGA';
    """
    ]

    for sql in sql_commands:
        print(f"  {sql.strip()[:80]}...")

    print("\n✓ Candidate status updated: rejected")
    print("✓ Signal event recorded: mdl_terminated")
    print("✓ Reason documented: Prior litigation failed")

def simulate_day_90_dashboard():
    """Simulate Day 90: Dashboard query."""
    print("\n" + "="*70)
    print("DAY 90: DASHBOARD UPDATE")
    print("="*70)
    print("\nUser opens dashboard: streamlit run app/app.py")
    print("\nDashboard query:")

    print("""
    SELECT
        c.candidate_id,
        c.defendant_text,
        c.product_text,
        c.score_total,
        c.status,
        c.why_now,
        COUNT(DISTINCT e.event_id) as event_count,
        MAX(e.event_time) as last_event_at
    FROM candidates c
    LEFT JOIN signal_events e ON e.candidate_id = c.candidate_id
    WHERE c.status IN ('new', 'in_review', 'accepted')  -- ← Filters out 'rejected'
    GROUP BY c.candidate_id
    ORDER BY c.score_total DESC
    LIMIT 100;
""")

    print("\nResult: FARXIGA is NOT shown (status='rejected')")
    print("\n✓ User automatically protected from false positive")
    print("✓ No wasted time on failed prior litigation")
    print("✓ Dashboard shows only viable candidates")

    print("\n" + "="*70)
    print("CANDIDATE DETAIL VIEW (if user clicks into FARXIGA anyway)")
    print("="*70)

    print("""
┌─────────────────────────────────────────────────────────────────┐
│ AstraZeneca | FARXIGA                                           │
├─────────────────────────────────────────────────────────────────┤
│ Status: REJECTED                                                │
│ Score: 8.5 (HIGH FDA SIGNAL - but not viable)                  │
│ First Seen: Day 1                                               │
│ Last Updated: Day 60                                            │
├─────────────────────────────────────────────────────────────────┤
│ Why Rejected:                                                   │
│ Prior MDL litigation failed (MDL-2776, 2017-2020). Only 67      │
│ cases, no major settlement. Not viable for new litigation       │
│ despite +80% death spike in FDA data.                           │
├─────────────────────────────────────────────────────────────────┤
│ TIMELINE:                                                       │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Day 1  │ adverse_trend                                    │  │
│ │        │ +80% death spike in Q4 2024 (397 → 715 deaths)  │  │
│ ├────────┼──────────────────────────────────────────────────┤  │
│ │ Day 30 │ mdl_discovered                                   │  │
│ │        │ MDL No. 2776 - S.D. Cal., Filed 2017-03-15      │  │
│ ├────────┼──────────────────────────────────────────────────┤  │
│ │ Day 60 │ mdl_terminated                                   │  │
│ │        │ MDL terminated 2020. ~67 cases, no settlement.  │  │
│ └────────┴──────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│ EVIDENCE: 1 FAERS report, 1 court case                         │
└─────────────────────────────────────────────────────────────────┘
""")

    print("✓ Complete audit trail of why candidate was rejected")
    print("✓ Evidence preserved for future reference")
    print("✓ User can see the decision-making process")

def show_comparison():
    """Show side-by-side comparison."""
    print("\n" + "="*70)
    print("FINAL COMPARISON")
    print("="*70)

    print("""
┌────────────────────────────────┬────────────────────────────────┐
│ WITHOUT DATABASE               │ WITH DATABASE                  │
│ (One-off searches)             │ (Monitoring system)            │
├────────────────────────────────┼────────────────────────────────┤
│ ❌ No memory                   │ ✅ Persistent watchlist         │
│ ❌ Manual checks               │ ✅ Automated daily pipeline     │
│ ❌ Can't track trends          │ ✅ Velocity/acceleration        │
│ ❌ Can't filter false positives│ ✅ MDL status checking          │
│ ❌ Sample data in dashboard    │ ✅ Real data, live updates      │
│ ❌ Just a script               │ ✅ Actual product               │
├────────────────────────────────┼────────────────────────────────┤
│ "Let me search FAERS again"    │ "Bloomberg for Mass Torts"     │
└────────────────────────────────┴────────────────────────────────┘

THE DATABASE IS THE PRODUCT.

It's what enables:
1. Discovering signals automatically (FDA/MAUDE)
2. Verifying litigation status (UniCourt MDL check)
3. Filtering false positives (terminated MDLs like FARXIGA)
4. Tracking trends over time (velocity, acceleration)
5. Alerting on acceleration (new cases piling up)
6. Building evidence dossier (FAERS, court filings, research)

"The proof is identifying a potential tort in a way that couldn't
be done with just a web search or even a deep search. Then we
have a product." - User

Without database = web search
With database = monitoring system = product
""")

def main():
    """Run the monitoring pipeline simulation."""
    print("\n" + "="*70)
    print("TORTSIGNAL MONITORING PIPELINE SIMULATION")
    print("="*70)
    print("\nThis simulates what happens when the database is running.")
    print("Watch how TortSignal transforms from 'one-off search' to 'monitoring system'.")

    input("\nPress Enter to start simulation...")

    simulate_day_1_discovery()
    input("\n[30 days pass...] Press Enter to continue...")

    simulate_day_30_litigation_check()
    input("\n[30 days pass...] Press Enter to continue...")

    simulate_day_60_mdl_termination()
    input("\n[30 days pass...] Press Enter to continue...")

    simulate_day_90_dashboard()

    show_comparison()

    print("\n" + "="*70)
    print("TO MAKE THIS REAL:")
    print("="*70)
    print("""
1. Start database: docker-compose up -d postgres
2. Update .env: DATABASE_URL=postgresql://...
3. Verify: python verify_database.py
4. Run discovery: python -m src.pipeline.discovery
5. Launch dashboard: streamlit run app/app.py

Then this simulation becomes REALITY.
""")

if __name__ == "__main__":
    main()
