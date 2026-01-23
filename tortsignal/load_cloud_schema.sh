#!/bin/bash
# Load AUDITSignal Safety Intelligence Graph schema to cloud database
#
# Usage:
#   1. Set DATABASE_URL environment variable (from Render/Supabase)
#   2. Run: ./load_cloud_schema.sh
#
# Example:
#   export DATABASE_URL="postgresql://auditsignal:ABC123@dpg-xyz.oregon-postgres.render.com/auditsignal"
#   ./load_cloud_schema.sh

set -e  # Exit on error

echo "============================================================"
echo "AUDITSignal Safety Intelligence Graph - Schema Deployment"
echo "============================================================"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set"
    echo ""
    echo "Please set DATABASE_URL to your cloud database connection string:"
    echo "  export DATABASE_URL=\"postgresql://user:pass@host:port/dbname\""
    echo ""
    echo "Get this from:"
    echo "  - Render: Dashboard → Database → Connections → Internal Database URL"
    echo "  - Supabase: Settings → Database → Connection string"
    echo ""
    exit 1
fi

# Verify DATABASE_URL format
if [[ ! "$DATABASE_URL" =~ ^postgresql:// ]]; then
    echo "❌ ERROR: DATABASE_URL doesn't look like a PostgreSQL connection string"
    echo "   Expected format: postgresql://user:pass@host:port/dbname"
    echo "   Got: $DATABASE_URL"
    exit 1
fi

# Extract host for display
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:/]*\).*/\1/p')
echo "Connecting to: $DB_HOST"
echo ""

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo "❌ ERROR: psql not found"
    echo ""
    echo "Install PostgreSQL client:"
    echo "  macOS: brew install postgresql"
    echo "  Ubuntu: sudo apt-get install postgresql-client"
    echo ""
    exit 1
fi

# Load schemas in order
echo "Loading schema files..."
echo ""

echo "1/3 Loading 001_core.sql (Core entities, tort clusters, candidates)..."
psql "$DATABASE_URL" -f schema/001_core.sql
echo "✓ Core schema loaded"
echo ""

echo "2/3 Loading 002_timeseries.sql (Signal timeseries tracking)..."
psql "$DATABASE_URL" -f schema/002_timeseries.sql
echo "✓ Timeseries schema loaded"
echo ""

echo "3/3 Loading 003_safety_intelligence_extensions.sql (Multi-market platform)..."
psql "$DATABASE_URL" -f schema/003_safety_intelligence_extensions.sql
echo "✓ Safety Intelligence extensions loaded"
echo ""

# Verify tables created
echo "============================================================"
echo "Verifying schema deployment..."
echo "============================================================"
echo ""

TABLE_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")

echo "✓ Database schema loaded successfully!"
echo "  Tables created: $TABLE_COUNT"
echo ""

# List all tables
echo "Tables in database:"
psql "$DATABASE_URL" -c "\dt" | grep public

echo ""
echo "============================================================"
echo "Schema deployment complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Update .env file with DATABASE_URL:"
echo "   DATABASE_URL=\"$DATABASE_URL\""
echo ""
echo "2. Verify connection:"
echo "   python3 verify_database.py"
echo ""
echo "3. Run discovery pipeline to populate Safety Intelligence Graph:"
echo "   python3 -m src.pipeline.discovery --days=90"
echo ""
echo "4. Launch dashboard:"
echo "   python3 -m streamlit run app/app.py"
echo ""
