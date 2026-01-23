# Cloud Database Deployment Guide (Render PostgreSQL)

## Step 1: Create Render PostgreSQL Instance

1. **Sign up for Render** (if you haven't already)
   - Go to https://render.com
   - Sign up with GitHub (easier for deployments later)

2. **Create PostgreSQL database**
   - Click "New +" → "PostgreSQL"
   - Configuration:
     - **Name:** `auditsignal-db` (or `auditsignal-production`)
     - **Database:** `auditsignal`
     - **User:** `auditsignal`
     - **Region:** Choose closest to you (Oregon for West Coast, Ohio for East Coast)
     - **Instance Type:** Free (1GB storage, shared CPU)
   - Click "Create Database"

3. **Wait for provisioning** (1-2 minutes)
   - Status will change from "Creating" → "Available"

4. **Get connection details**
   - Click on your database
   - Scroll to "Connections"
   - Copy the **Internal Database URL** (starts with `postgresql://`)
   - Example: `postgresql://auditsignal:ABC123@dpg-xyz.oregon-postgres.render.com/auditsignal`

---

## Step 2: Load Database Schema

### Option A: Using psql (Recommended)

```bash
cd /path/to/TortSignal/tortsignal

# Replace with your actual DATABASE_URL from Render
export DATABASE_URL="postgresql://auditsignal:ABC123@dpg-xyz.oregon-postgres.render.com/auditsignal"

# Load schemas in order
psql $DATABASE_URL < schema/001_core.sql
psql $DATABASE_URL < schema/002_timeseries.sql
psql $DATABASE_URL < schema/003_safety_intelligence_extensions.sql

# Verify tables created
psql $DATABASE_URL -c "\dt"
```

### Option B: Using Render Dashboard (Web UI)

1. In Render dashboard, click on your database
2. Click "Shell" tab (opens psql in browser)
3. Copy/paste contents of each schema file:
   - First: `001_core.sql`
   - Second: `002_timeseries.sql`
   - Third: `003_safety_intelligence_extensions.sql`
4. Run `\dt` to verify all tables created

---

## Step 3: Update Local .env

Update your `.env` file with the Render connection string:

```bash
# Database - Render PostgreSQL (Cloud)
DATABASE_URL=postgresql://auditsignal:ABC123@dpg-xyz.oregon-postgres.render.com/auditsignal
```

**Important:** Replace with YOUR actual URL from Render dashboard.

---

## Step 4: Verify Connection

Test connection from your Mac:

```bash
cd /path/to/TortSignal/tortsignal
python3 verify_database.py
```

You should see:
```
✓ DATABASE_URL configured
✓ Connected to PostgreSQL
✓ Found 33 tables:  # (21 from core + 12 from extensions)
  • defendants
  • products
  • injuries
  • tort_clusters
  • product_signals          # NEW - Safety Intelligence
  • regulatory_actions       # NEW - Safety Intelligence
  • literature_evidence      # NEW - Safety Intelligence
  • device_scorecards       # NEW - Safety Intelligence
  • regulatory_risk_forecasts # NEW - Safety Intelligence
  ...
```

---

## Step 5: Test Dashboard with Cloud Database

```bash
python3 -m streamlit run app/app.py
```

Dashboard should now connect to cloud database instead of showing sample data.

Since database is empty, you'll see "0 candidates" - that's correct! Next step is running discovery pipeline to populate it.

---

## Alternative: Supabase (If You Prefer)

Supabase also has generous free tier and includes built-in dashboard:

1. Go to https://supabase.com
2. Create new project
3. Get connection string from Settings → Database
4. Same schema loading process

---

## Cost Comparison

| Provider | Free Tier | Paid Tier | Notes |
|----------|-----------|-----------|-------|
| **Render** | 1GB, shared CPU | $7/month (5GB), $20/month (20GB) | Easiest setup |
| **Supabase** | 500MB, 2GB transfer | $25/month (8GB) | Includes auth, storage, realtime |
| **Heroku** | None | $5/month (1GB hobby), $50/month (10GB) | Simple but more expensive |
| **AWS RDS** | 750hrs free (12 months) | $15-30/month | Most scalable, complex setup |

**Recommendation:** Start with Render free tier. Upgrade to $7/month when you hit 1GB.

---

## Expected Database Size (Rough Estimates)

**After 1 month of daily discovery:**
- ~5,000 source_documents (FAERS reports)
- ~500 product_signals
- ~100 candidates
- ~2,000 signal_events
- **Total: ~50-100MB**

**After 1 year:**
- ~60,000 source_documents
- ~5,000 product_signals
- ~1,000 candidates
- ~24,000 signal_events
- **Total: ~500MB-1GB**

Free tier should last 6-12 months of active use.

---

## Security Notes

1. **Never commit DATABASE_URL to git**
   - Already in `.gitignore` ✓
   - Keep .env file local only

2. **Rotate credentials if leaked**
   - Render allows password rotation in dashboard

3. **Use SSL connections**
   - Render enforces SSL by default ✓

4. **Backups**
   - Render free tier: daily backups (7 day retention)
   - Paid tier: continuous backups (30 day retention)

---

## Next Steps After Database Is Live

1. **Run discovery pipeline** to populate Safety Intelligence Graph:
   ```bash
   python3 -m src.pipeline.discovery --days=90
   ```

2. **Build UniCourt AI browser agent** ($300/month plan):
   - Automate case research
   - Triggered by high-conviction FDA signals

3. **Launch TortSignal MVP dashboard**:
   - Real data instead of sample data
   - Prove monitoring concept

4. **Start SafetyScore development**:
   - Same Safety Intelligence Graph
   - Device scorecard application layer

---

## Troubleshooting

**Connection refused:**
- Check if Render database status is "Available"
- Verify DATABASE_URL is correct (no typos)
- Check your IP isn't blocked (Render allows all IPs by default)

**SSL required error:**
- Add `?sslmode=require` to DATABASE_URL
- Example: `postgresql://user:pass@host/db?sslmode=require`

**Tables not created:**
- Run schemas in order: 001 → 002 → 003
- Check for error messages in psql output
- Verify pgcrypto extension is available (Render includes it)

**Out of connections:**
- Free tier: 22 connections max
- Close idle connections: `python3 -c "import psycopg2; conn = psycopg2.connect(os.getenv('DATABASE_URL')); conn.close()"`

---

Ready to proceed? Follow Step 1 above to create your Render PostgreSQL instance!
