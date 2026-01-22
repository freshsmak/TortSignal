"""
Verify database setup and demonstrate monitoring system.

This script shows the difference between one-off searches vs. persistent monitoring.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def check_database_config():
    """Check if DATABASE_URL is configured."""
    db_url = os.getenv("DATABASE_URL")

    if not db_url or db_url.startswith("#"):
        print("❌ DATABASE_URL not configured in .env")
        print("\nTo set up the database:")
        print("1. Start PostgreSQL:")
        print("   docker-compose up -d postgres")
        print("\n2. Update .env file (uncomment DATABASE_URL):")
        print("   DATABASE_URL=postgresql://tortsignal:tortsignal_dev_password@localhost:5432/tortsignal")
        print("\n3. Run this script again")
        return False

    print(f"✓ DATABASE_URL configured: {db_url[:40]}...")
    return True

def test_connection():
    """Test database connection."""
    print("\nTesting database connection...")

    try:
        import psycopg2
        from urllib.parse import urlparse

        db_url = os.getenv("DATABASE_URL")
        result = urlparse(db_url)

        conn = psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )

        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        print(f"✓ Connected to PostgreSQL")
        print(f"  Version: {version[:60]}...")

        # Check if tables exist
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"\n✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  • {table[0]}")
        else:
            print("\n⚠️  No tables found. Schema may not be loaded.")
            print("   Run: docker-compose exec -T postgres psql -U tortsignal tortsignal < schema/001_core.sql")

        conn.close()
        return True

    except ImportError:
        print("❌ psycopg2 not installed")
        print("   Install: pip install psycopg2-binary")
        return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("   docker-compose up -d postgres")
        return False

def demonstrate_monitoring_concept():
    """Show what the monitoring system looks like."""
    print("\n" + "="*70)
    print("MONITORING SYSTEM CONCEPT")
    print("="*70)

    print("""
WITHOUT DATABASE (Current - One-off searches):
─────────────────────────────────────────────────────────────
$ python analyze_farxiga.py
  → FARXIGA: +80% death spike detected
  → 715 deaths in Q4 2024
  → [Results printed, then forgotten]

$ python analyze_farxiga.py  # Run again next week
  → Same results, no memory of what we found
  → No way to track if signal is getting worse
  → No way to know if litigation already failed (MDL terminated)

WITH DATABASE (Monitoring System):
─────────────────────────────────────────────────────────────
Day 1 (Jan 15, 2025):
  FDA API → +80% death spike detected
  → INSERT INTO candidates (
      defendant_text='AstraZeneca',
      product_text='FARXIGA',
      status='new',
      score_total=8.5
    )
  → INSERT INTO signal_events (
      event_type='adverse_trend',
      excerpt='+80% death spike in Q4 2024'
    )

Day 30 (Feb 14, 2025):
  UniCourt API → Found MDL No. 2776
  → INSERT INTO court_cases (
      source_uid='MDL-2776',
      defendant_text='AstraZeneca',
      filed_at='2017-03-15'
    )
  → INSERT INTO signal_events (
      event_type='mdl_discovered',
      excerpt='MDL No. 2776 - Southern District of California'
    )

Day 60 (Mar 16, 2025):
  UniCourt API → MDL status check
  → INSERT INTO signal_events (
      event_type='mdl_terminated',
      excerpt='MDL terminated 2020, ~67 cases, no major settlement'
    )
  → UPDATE candidates SET
      status='rejected',
      why_now='Prior litigation failed - not viable'

Day 90 (Apr 15, 2025):
  Dashboard query: SELECT * FROM candidates WHERE status IN ('new', 'in_review')
  → FARXIGA automatically filtered out (status='rejected')
  → User never wastes time on failed prior litigation
  → Move on to next viable candidate

─────────────────────────────────────────────────────────────
WHAT THE DATABASE ENABLES:

✓ Persistent watchlist of tort candidates
✓ Continuous listening for new adverse events
✓ Evidence accumulation over time
✓ Historical tracking (velocity, acceleration, breadth)
✓ MDL status monitoring (prevents false positives like FARXIGA)
✓ Bloomberg-like dashboard with real-time updates

THIS IS WHAT SEPARATES TORTSIGNAL FROM "JUST SEARCHING."
─────────────────────────────────────────────────────────────
""")

def show_next_steps():
    """Show what to implement next."""
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)

    print("""
1. START DATABASE (if not already running):
   $ docker-compose up -d postgres
   $ docker-compose ps  # Verify it's running

2. UPDATE .env FILE:
   Uncomment this line:
   DATABASE_URL=postgresql://tortsignal:tortsignal_dev_password@localhost:5432/tortsignal

3. VERIFY SCHEMA LOADED:
   $ docker-compose logs postgres | grep "CREATE TABLE"

   If tables not created automatically:
   $ docker-compose exec -T postgres psql -U tortsignal tortsignal < schema/001_core.sql
   $ docker-compose exec -T postgres psql -U tortsignal tortsignal < schema/002_timeseries.sql

4. TEST CONNECTION:
   $ python verify_database.py

5. RUN FIRST DISCOVERY PIPELINE:
   This will populate the database with real signals:
   $ python -m src.pipeline.discovery --dry-run

6. LAUNCH DASHBOARD:
   Connect to real data instead of sample data:
   $ streamlit run app/app.py

   Dashboard will show:
   - Real candidates from discovery
   - Live velocity calculations
   - Signal event timelines
   - MDL status indicators

─────────────────────────────────────────────────────────────
PROOF OF CONCEPT:

The proof isn't just finding a signal in FAERS.
The proof is the MONITORING SYSTEM that:

1. Detects signals automatically (FDA FAERS/MAUDE)
2. Verifies litigation status (UniCourt MDL check)
3. Filters false positives (terminated MDLs like FARXIGA)
4. Tracks trends over time (velocity, acceleration)
5. Alerts on acceleration (new cases piling up)
6. Builds evidence dossier (FAERS reports, court filings, research)

"The proof is identifying a potential tort in a way that
couldn't be done with just a web search or even a deep search.
Then we have a product." - User

The database IS the product.
─────────────────────────────────────────────────────────────
""")

def main():
    """Main verification flow."""
    print("="*70)
    print("TORTSIGNAL DATABASE VERIFICATION")
    print("="*70)

    # Step 1: Check config
    if not check_database_config():
        demonstrate_monitoring_concept()
        show_next_steps()
        return

    # Step 2: Test connection
    if not test_connection():
        show_next_steps()
        return

    # Step 3: If all good, show what's possible
    print("\n✓ Database is ready!")
    demonstrate_monitoring_concept()
    show_next_steps()

if __name__ == "__main__":
    main()
