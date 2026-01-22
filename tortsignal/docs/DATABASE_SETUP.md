# Database Setup Guide

## The Problem We're Solving

**Without a database:** TortSignal is just running one-off searches. You find a signal, print it, and forget it.

**With a database:** TortSignal becomes a monitoring system that:
- ✅ **Maintains a watchlist** of tort candidates
- ✅ **Listens continuously** for new adverse events, publications, litigation
- ✅ **Builds evidence** over time for each candidate
- ✅ **Tracks historical trends** (velocity, acceleration, breadth)
- ✅ **Prevents false positives** by checking MDL status
- ✅ **Powers the Bloomberg-like dashboard**

**This is what separates TortSignal from "just searching."**

---

## Quick Start (Docker Compose)

### 1. Start the Database

```bash
cd /path/to/TortSignal/tortsignal

# Start PostgreSQL
docker-compose up -d postgres

# Check it's running
docker-compose ps
```

### 2. Update .env

```bash
# Uncomment and update:
DATABASE_URL=postgresql://tortsignal:tortsignal_dev_password@localhost:5432/tortsignal
```

### 3. Verify Schema

```bash
# The schema files in schema/ are automatically loaded on first startup
docker-compose logs postgres

# Should see:
# "CREATE TABLE defendants"
# "CREATE TABLE products"
# etc.
```

### 4. Test Connection

```python
from src.config import get_config

config = get_config()
print(f"Database: {config.database.url}")
# Should not error
```

---

## What the Database Enables

### Example: FARXIGA with Database vs. Without

#### ❌ Without Database (What We Did)

```bash
$ python analyze_farxiga.py
# Prints:
# "FARXIGA: +80% death spike"
# "714 deaths in Q4 2024"
# "Investigate immediately"

# Then... nothing persists.
# Run the script tomorrow, same results.
# No memory of what we found.
```

#### ✅ With Database (What We Should Do)

```bash
$ python -m src.pipeline.discovery

Day 1:
  → FDA API: FARXIGA +80% death spike
  → INSERT INTO candidates (defendant_text='AstraZeneca', product_text='FARXIGA', status='new')
  → INSERT INTO signal_events (event_type='adverse_trend', excerpt='+80% death spike')

Day 30:
  → UniCourt API: Found MDL No. 2776
  → INSERT INTO court_cases (source_uid='MDL-2776', defendant_text='AstraZeneca')
  → INSERT INTO signal_events (event_type='mdl_discovered')

Day 60:
  → UniCourt API: MDL status = terminated (2020)
  → INSERT INTO signal_events (event_type='mdl_terminated', excerpt='Closed 2020, ~67 cases')
  → UPDATE candidates SET status='rejected', why_now='Already litigated and failed'

Day 90:
  → Dashboard shows: FARXIGA marked REJECTED (filter out)
  → Move on to next candidate
```

---

## Schema Overview

### Core Tables

#### 1. **Watchlist** (`candidates`)

```sql
CREATE TABLE candidates (
    candidate_id UUID PRIMARY KEY,
    candidate_key TEXT,  -- "AstraZeneca|FARXIGA"
    defendant_text TEXT,
    product_text TEXT,
    score_total FLOAT,
    status TEXT,  -- new, in_review, accepted, rejected
    first_seen_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ
);
```

**Use:** The main watchlist. Each row is a potential tort being monitored.

#### 2. **Listening** (`signal_events`)

```sql
CREATE TABLE signal_events (
    event_id UUID PRIMARY KEY,
    candidate_id UUID,
    event_type TEXT,  -- adverse_trend, filing_spike, paper_published, mdl_terminated
    event_time TIMESTAMPTZ,
    excerpt TEXT
);
```

**Use:** Every signal detected (FDA spike, new litigation, research published).

#### 3. **Evidence** (`source_documents`)

```sql
CREATE TABLE source_documents (
    doc_id UUID PRIMARY KEY,
    source_type TEXT,  -- faers_report, court_case, pubmed_article
    source_uid TEXT,   -- Upstream ID
    published_at TIMESTAMPTZ,
    raw_payload_json JSONB
);
```

**Use:** Store raw evidence (FAERS reports, court filings, research papers).

#### 4. **Historical Tracking** (`candidate_rollups`)

```sql
CREATE TABLE candidate_rollups (
    candidate_id UUID,
    as_of_date DATE,
    velocity_7d INT,       -- Cases filed in last 7 days
    velocity_28d INT,      -- Cases filed in last 28 days
    accel_ratio FLOAT,     -- velocity_7d / velocity_28d
    breadth_states INT,    -- Geographic spread
    PRIMARY KEY (candidate_id, as_of_date)
);
```

**Use:** Daily snapshots for trend analysis and acceleration detection.

#### 5. **Court Cases** (`court_cases`)

```sql
CREATE TABLE court_cases (
    case_id UUID PRIMARY KEY,
    source_uid TEXT,       -- UniCourt case ID or MDL number
    filed_at DATE,
    defendant_text TEXT,
    product_text TEXT,
    plaintiff_firm TEXT,
    jurisdiction TEXT
);
```

**Use:** Track litigation filings and MDL status.

---

## Discovery Pipeline with Database

### Daily Cron Job

```bash
# Run every morning at 6 AM
0 6 * * * cd /path/to/tortsignal && python -m src.pipeline.discovery
```

### What It Does

```python
# 1. Query FDA FAERS for new adverse events (last 7 days)
faers_reports = FAERSConnector().fetch(days=7)

for report in faers_reports:
    # Store raw document
    doc = insert_source_document(
        source_type='faers_report',
        source_uid=report.id,
        raw_payload=report.raw_data
    )

    # Extract product/defendant
    product = extract_product(report)
    defendant = extract_manufacturer(report)

    # Find or create candidate
    candidate = get_or_create_candidate(
        defendant_text=defendant,
        product_text=product
    )

    # Create signal event
    insert_signal_event(
        candidate_id=candidate.id,
        event_type='adverse_event_reported',
        doc_id=doc.id,
        excerpt=f"{report.reaction}: {report.count} reports"
    )

    # Update candidate metrics
    update_candidate_rollup(
        candidate_id=candidate.id,
        as_of_date=today
    )

# 2. Query UniCourt for new cases (last 7 days)
cases = UniCourtConnector().fetch(days=7, strategy='hybrid')

for case in cases:
    # Store case
    insert_court_case(
        source_uid=case.source_uid,
        filed_at=case.filed_date,
        defendant_text=case.defendant_text,
        product_text=case.product_text
    )

    # Link to candidate
    candidate = match_case_to_candidate(case)
    if candidate:
        insert_signal_event(
            candidate_id=candidate.id,
            event_type='filing_new',
            excerpt=f"Filed in {case.state}"
        )

# 3. Calculate scores
for candidate in get_active_candidates():
    score = calculate_score(candidate)
    update_candidate(
        candidate_id=candidate.id,
        score_total=score.total,
        score_components=score.components
    )

# 4. Check for MDL status changes
for candidate in get_high_score_candidates():
    mdl_status = check_mdl_status(candidate)
    if mdl_status == 'terminated':
        update_candidate(
            candidate_id=candidate.id,
            status='rejected',
            why_now='MDL terminated - not viable'
        )
```

---

## Dashboard Integration

### Before (No Database)

```python
# app/db_helpers.py

def get_watchlist():
    # Return hardcoded sample data
    return SAMPLE_DATA
```

**Problem:** No real data. Can't track trends. Can't show velocity.

### After (With Database)

```python
# app/db_helpers.py

def get_watchlist(filters=None):
    conn = get_db_connection()

    query = """
        SELECT
            c.candidate_id,
            c.defendant_text,
            c.product_text,
            c.score_total,
            c.status,
            r.velocity_7d,
            r.breadth_states,
            COUNT(DISTINCT e.event_id) as event_count,
            MAX(e.event_time) as last_event_at
        FROM candidates c
        LEFT JOIN candidate_rollups r ON r.candidate_id = c.candidate_id
            AND r.as_of_date = CURRENT_DATE
        LEFT JOIN signal_events e ON e.candidate_id = c.candidate_id
        WHERE c.status IN ('new', 'in_review', 'accepted')
        GROUP BY c.candidate_id
        ORDER BY c.score_total DESC
        LIMIT 100
    """

    return pd.read_sql(query, conn)
```

**Benefits:**
- ✅ Real data from discoveries
- ✅ Live velocity calculations
- ✅ Filter by status (hide rejected)
- ✅ Track when last event occurred

---

## Migration Path

### Phase 1: Development (Local Docker)

```bash
docker-compose up -d postgres
# DATABASE_URL=postgresql://tortsignal:tortsignal_dev_password@localhost:5432/tortsignal
```

### Phase 2: Production (Cloud)

#### Option A: AWS RDS

```bash
# DATABASE_URL=postgresql://user:pass@tortsignal.xxxxx.us-east-1.rds.amazonaws.com:5432/tortsignal
```

#### Option B: Heroku Postgres

```bash
heroku addons:create heroku-postgresql:standard-0
# Automatically sets DATABASE_URL
```

#### Option C: Render.com

```bash
# Create PostgreSQL instance via dashboard
# Copy DATABASE_URL
```

### Schema Migration

```bash
# Run migrations when schema changes
psql $DATABASE_URL < schema/001_core.sql
psql $DATABASE_URL < schema/002_timeseries.sql
```

---

## Performance Considerations

### Indexes

The schema includes indexes on:
- `candidates.score_total DESC` (watchlist sorting)
- `candidates.status` (filtering)
- `signal_events.candidate_id, event_time DESC` (timeline)
- `candidate_rollups.candidate_id, as_of_date DESC` (trend queries)

### Data Volume Estimates

**Modest usage:**
- 100 active candidates
- 50 new court cases/day
- 500 FAERS reports/day
- Daily rollups for all candidates

**Storage:**
- ~10 GB/year

**Queries:**
- Watchlist: <100ms
- Candidate timeline: <50ms
- Score calculation: <200ms

### Archival

```sql
-- After 1 year, archive candidates with status='rejected'
UPDATE candidates
SET status = 'archived'
WHERE status = 'rejected'
  AND last_seen_at < NOW() - INTERVAL '1 year';
```

---

## Backup Strategy

### Development

```bash
# Backup
docker-compose exec postgres pg_dump -U tortsignal tortsignal > backup.sql

# Restore
docker-compose exec -T postgres psql -U tortsignal tortsignal < backup.sql
```

### Production

```bash
# Daily automated backups
0 2 * * * pg_dump $DATABASE_URL | gzip > backups/tortsignal-$(date +\%Y\%m\%d).sql.gz

# Retain 30 days
find backups/ -name "*.sql.gz" -mtime +30 -delete
```

---

## Troubleshooting

### Can't Connect to Database

```bash
# Check if running
docker-compose ps

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U tortsignal -c "SELECT 1"
```

### Schema Not Loading

```bash
# Check if schema files were loaded
docker-compose exec postgres psql -U tortsignal -c "\dt"

# Manually load
docker-compose exec -T postgres psql -U tortsignal tortsignal < schema/001_core.sql
```

### Dashboard Shows "DATABASE_URL not set"

```bash
# Verify .env file
cat .env | grep DATABASE_URL

# Should be uncommented:
DATABASE_URL=postgresql://tortsignal:tortsignal_dev_password@localhost:5432/tortsignal
```

---

## Next Steps

1. **Start the database:** `docker-compose up -d postgres`
2. **Update .env:** Uncomment `DATABASE_URL`
3. **Run discovery:** `python -m src.pipeline.discovery --dry-run`
4. **Launch dashboard:** `streamlit run app/app.py`
5. **Verify watchlist:** Should show real candidates, not sample data

**Once the database is running, TortSignal transforms from "search tool" to "monitoring system."**

---

## Summary: Why Database = Product

| Without Database | With Database |
|------------------|---------------|
| One-off searches | Continuous monitoring |
| No memory | Historical tracking |
| Manual checks | Automated alerts |
| Can't detect acceleration | Velocity calculations |
| Can't filter false positives | MDL status checking |
| Sample data in dashboard | Real data, live updates |
| **Just a script** | **Actual product** |

**The database is the foundation of the "Bloomberg for Mass Torts."**

