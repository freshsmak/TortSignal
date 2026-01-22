"""
Set up SQLite database for TortSignal development.

SQLite is easier than PostgreSQL for local development, and we can
migrate to Postgres later. The schema is designed to be portable.
"""

import sqlite3
import os
from pathlib import Path

def convert_postgres_to_sqlite(postgres_sql: str) -> str:
    """Convert PostgreSQL schema to SQLite."""
    sqlite_sql = postgres_sql

    # Remove PostgreSQL-specific extensions
    sqlite_sql = sqlite_sql.replace("CREATE EXTENSION IF NOT EXISTS pgcrypto;", "")

    # Replace UUID type with TEXT
    sqlite_sql = sqlite_sql.replace("UUID PRIMARY KEY DEFAULT gen_random_uuid()",
                                     "TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16))))")
    sqlite_sql = sqlite_sql.replace("UUID REFERENCES", "TEXT REFERENCES")
    sqlite_sql = sqlite_sql.replace("UUID NOT NULL", "TEXT NOT NULL")
    sqlite_sql = sqlite_sql.replace("UUID", "TEXT")

    # Replace TIMESTAMPTZ with TEXT (ISO 8601)
    sqlite_sql = sqlite_sql.replace("TIMESTAMPTZ NOT NULL DEFAULT now()",
                                     "TEXT NOT NULL DEFAULT (datetime('now'))")
    sqlite_sql = sqlite_sql.replace("TIMESTAMPTZ NOT NULL", "TEXT NOT NULL")
    sqlite_sql = sqlite_sql.replace("TIMESTAMPTZ", "TEXT")

    # Replace JSONB with TEXT
    sqlite_sql = sqlite_sql.replace("JSONB NOT NULL DEFAULT '{}'::jsonb",
                                     "TEXT NOT NULL DEFAULT '{}'")
    sqlite_sql = sqlite_sql.replace("JSONB", "TEXT")

    # Replace TEXT[] with TEXT
    sqlite_sql = sqlite_sql.replace("TEXT[]", "TEXT")

    # Replace FLOAT with REAL
    sqlite_sql = sqlite_sql.replace("FLOAT", "REAL")

    # Remove ON DELETE CASCADE (SQLite handles differently)
    # Keep it for now, SQLite supports it

    return sqlite_sql

def setup_database(db_path: str = "tortsignal.db"):
    """Set up SQLite database with schema."""

    print(f"Setting up SQLite database: {db_path}")

    # Read PostgreSQL schemas
    schema_dir = Path(__file__).parent / "schema"

    core_schema = (schema_dir / "001_core.sql").read_text()
    timeseries_schema = (schema_dir / "002_timeseries.sql").read_text()

    # Convert to SQLite
    core_sqlite = convert_postgres_to_sqlite(core_schema)
    timeseries_sqlite = convert_postgres_to_sqlite(timeseries_schema)

    # Create database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Creating tables from 001_core.sql...")
        cursor.executescript(core_sqlite)

        print("Creating tables from 002_timeseries.sql...")
        cursor.executescript(timeseries_sqlite)

        conn.commit()
        print(f"✓ Database created successfully: {db_path}")

        # Show tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        print(f"\n✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"  • {table[0]}")

        return db_path

    except Exception as e:
        print(f"✗ Error creating database: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    db_path = setup_database()

    print(f"""
{'='*70}
DATABASE READY
{'='*70}

SQLite database created at: {db_path}

To use in your .env file:
DATABASE_URL=sqlite:///{os.path.abspath(db_path)}

Next steps:
1. Run discovery pipeline to populate data
2. Launch dashboard: streamlit run app/app.py
3. View watchlist and track signals over time

The database enables:
✓ Persistent watchlist of tort candidates
✓ Historical tracking of adverse events
✓ Evidence accumulation over time
✓ MDL status monitoring
✓ Velocity/acceleration calculations

This is what separates TortSignal from "just running searches."
{'='*70}
""")
