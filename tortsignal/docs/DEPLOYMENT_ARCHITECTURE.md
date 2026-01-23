# AUDITSignal Deployment Architecture

## Overview

AUDITSignal is a **Safety Intelligence Platform** that transforms public safety data into actionable intelligence for multiple markets.

---

## Production Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA SOURCES (All Free/Low-Cost)            │
├─────────────────────────────────────────────────────────────────┤
│ • FDA FAERS (drug adverse events)              FREE             │
│ • FDA MAUDE (device malfunctions)              FREE             │
│ • OpenFDA Enforcement (recalls, warnings)      FREE             │
│ • PubMed / Semantic Scholar (literature)       FREE             │
│ • IARC Monographs (carcinogen classifications) FREE             │
│ • UniCourt Premium (AI browser automation)     $300/month       │
│ • PACER (federal court cases, MDL status)      $50-100/month    │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              DISCOVERY PIPELINE (Daily Cron Job)                │
├─────────────────────────────────────────────────────────────────┤
│ 1. Fetch new adverse events (FAERS, MAUDE)                     │
│ 2. Detect statistical spikes (velocity, acceleration)          │
│ 3. Verify litigation status (UniCourt AI agent, PACER)         │
│ 4. Extract literature evidence (PubMed)                         │
│ 5. Calculate risk scores (regulatory, litigation, severity)    │
│ 6. Update Safety Intelligence Graph                            │
│                                                                 │
│ Runs on: Render Cron Job / Heroku Scheduler (free tier)        │
│ Runtime: ~15-30 min/day                                         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│          SAFETY INTELLIGENCE GRAPH (PostgreSQL)                 │
├─────────────────────────────────────────────────────────────────┤
│ Core Tables (001_core.sql):                                    │
│ • defendants, products, injuries                               │
│ • source_documents (FAERS, MAUDE, court cases, literature)    │
│ • signal_events (timeline of evidence)                         │
│ • candidates (tort watchlist)                                  │
│                                                                 │
│ Safety Intelligence Extensions (003_*.sql):                    │
│ • product_signals (product-centric, not tort-centric)         │
│ • regulatory_actions (FDA warnings, recalls, label changes)    │
│ • literature_evidence (PubMed, mechanism, case reports)        │
│ • hazard_classifications (IARC, EPA)                           │
│ • device_scorecards (hospital procurement)                     │
│ • regulatory_risk_forecasts (predict FDA actions)              │
│ • competitive_safety_intel (pharma competitive intelligence)   │
│                                                                 │
│ Hosted on: Render PostgreSQL (free tier → $7/month)           │
│ Storage: ~100MB after 1 month, ~1GB after 1 year              │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              APPLICATION LAYERS (Multi-Market)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │   TortSignal     │  │   SafetyScore    │  │ RegulatoryAI │ │
│  │ (plaintiff firms)│  │   (hospitals)    │  │(pharma/PE)   │ │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────┤ │
│  │ • Tort watchlist │  │ • Device safety  │  │ • Regulatory │ │
│  │ • MDL cross-check│  │   scorecards     │  │   risk score │ │
│  │ • Causation      │  │ • Procurement    │  │ • Competitor │ │
│  │   strength       │  │   recommends     │  │   intel      │ │
│  │ • Evidence       │  │ • Peer compare   │  │ • Action     │ │
│  │   dossiers       │  │ • Alt products   │  │   forecasts  │ │
│  │                  │  │                  │  │              │ │
│  │ TAM: $500M       │  │ TAM: $5B         │  │ TAM: $2B     │ │
│  │ $10k-50k/firm/yr │  │ $50k-200k/hosp/yr│  │ $100k-500k/yr│ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                 │
│  Same data, different views. Marginal cost per app is LOW.    │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CUSTOMERS                                │
├─────────────────────────────────────────────────────────────────┤
│ • Plaintiff law firms (TortSignal)                             │
│ • Hospital value analysis committees (SafetyScore)             │
│ • Pharma regulatory affairs (RegulatoryAI)                     │
│ • Private equity / M&A teams (RegulatoryAI)                    │
│ • Insurance underwriters (RegulatoryAI)                        │
│ • Defense-side counsel (litigation prep)                       │
│ • Pharma competitive intelligence (strategy)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## MVP Deployment Stack

### Infrastructure (Total: ~$400-600/month)

| Component | Service | Cost | Purpose |
|-----------|---------|------|---------|
| **Database** | Render PostgreSQL | Free → $7/month | Safety Intelligence Graph |
| **App Hosting** | Render Web Service | Free → $7/month | Streamlit dashboard |
| **Cron Jobs** | Render Cron Job | Free | Daily discovery pipeline |
| **UniCourt** | Premium Plan | $300/month | Court case research (AI automation) |
| **PACER** | Pay-per-use | $50-100/month | MDL status verification |
| **AI API** | Claude API | $50-100/month | Browser automation, entity extraction |

**Total MVP cost: ~$400-600/month**

**First customer ROI:**
- TortSignal @ $10k/year = 20 months payback
- SafetyScore @ $50k/year = 2 months payback ✅

---

## Deployment Steps (This Week)

### 1. Cloud Database Setup (Today)

```bash
# Create Render PostgreSQL instance
# https://render.com → New PostgreSQL

# Load Safety Intelligence Graph schema
export DATABASE_URL="postgresql://auditsignal:ABC123@dpg-xyz.render.com/auditsignal"
./load_cloud_schema.sh

# Verify
python3 verify_database.py
```

**Expected result:** 33 tables created (21 core + 12 extensions)

### 2. Discovery Pipeline Development (This Week)

```python
# src/pipeline/discovery.py
#
# Daily pipeline that:
# 1. Fetches new FAERS/MAUDE reports
# 2. Detects statistical spikes
# 3. Verifies litigation status
# 4. Populates Safety Intelligence Graph

python3 -m src.pipeline.discovery --days=90  # Initial backfill
```

### 3. UniCourt AI Browser Agent (Next Week)

```python
# src/connectors/unicourt_browser.py
#
# AI agent that logs into UniCourt Premium ($300/month)
# Automates case research triggered by high-conviction signals

class UniCourtBrowserAgent:
    def research_candidate(defendant, product) -> dict
    def check_mdl_status(case_number) -> dict
    def monitor_new_cases(defendant, days_back) -> list
```

### 4. Dashboard Deployment (Next Week)

```bash
# Deploy to Render Web Service
# https://render.com → New Web Service → Connect GitHub

# Environment variables:
DATABASE_URL=postgresql://...
OPENFDA_API_KEY=...
UNICOURT_CLIENT_ID=...
UNICOURT_CLIENT_SECRET=...

# Auto-deploys on git push
```

**Result:** Dashboard live at `https://auditsignal.onrender.com`

---

## Data Flow Example: FARXIGA Case Study

### Day 1: Signal Detection
```
FDA FAERS API → +80% death spike detected
  ↓
INSERT INTO product_signals (
  product_id = FARXIGA,
  injury_id = Death,
  velocity_30d = 715,
  severity_score = 8.5
)
  ↓
INSERT INTO signal_events (
  event_type = 'adverse_trend',
  excerpt = '+80% death spike Q4 2024'
)
```

### Day 30: Litigation Check
```
UniCourt AI Browser Agent → Search "AstraZeneca product liability"
  ↓
Found: MDL No. 2776 (FARXIGA)
  ↓
INSERT INTO court_cases (
  source_uid = 'MDL-2776',
  filed_at = '2017-03-15',
  defendant_text = 'AstraZeneca'
)
  ↓
INSERT INTO signal_events (
  event_type = 'mdl_discovered',
  excerpt = 'MDL No. 2776 - S.D. Cal.'
)
```

### Day 60: MDL Status Update
```
UniCourt → Check MDL status
  ↓
Status: TERMINATED (2020), ~67 cases, no major settlement
  ↓
UPDATE product_signals SET status = 'rejected'
UPDATE candidates SET
  status = 'rejected',
  why_now = 'Prior MDL failed - not viable'
  ↓
INSERT INTO signal_events (
  event_type = 'mdl_terminated',
  excerpt = 'MDL terminated 2020, not viable'
)
```

### Day 90: Dashboard
```
TortSignal Dashboard Query:
SELECT * FROM candidates WHERE status IN ('new', 'in_review')
  ↓
FARXIGA automatically filtered out (status = 'rejected')
  ↓
User never wastes time on false positive
```

---

## Scaling Path

### Year 1: MVP Launch
- **Revenue:** $100k-500k ARR
- **Customers:** 10-20 TortSignal firms, 5-10 SafetyScore hospitals
- **Infrastructure:** Render free tier → $25/month
- **Team:** Solo founder + contractors

### Year 2: Product-Market Fit
- **Revenue:** $1M-3M ARR
- **Customers:** 50+ TortSignal, 20+ SafetyScore, pilot RegulatoryAI
- **Infrastructure:** Render $100-200/month (upgraded database, multiple services)
- **Team:** 2-3 full-time

### Year 3: Scale
- **Revenue:** $5M-10M ARR
- **Customers:** 100+ TortSignal, 50+ SafetyScore, 20+ RegulatoryAI
- **Infrastructure:** AWS RDS + redundancy ($500-1k/month)
- **Team:** 5-10 full-time

---

## Security & Compliance

### Data Handling
- **Public data only:** FAERS, MAUDE, court cases, literature (no PHI, no PII)
- **HIPAA:** Not applicable (no patient-level data)
- **GDPR:** Not applicable (no EU personal data)
- **Terms of Service:** Review UniCourt ToS (likely compliant with Premium plan)

### Infrastructure Security
- **Database:** SSL/TLS enforced (Render default)
- **App hosting:** HTTPS enforced (Render default)
- **Secrets:** Environment variables, never committed to git
- **Backups:** Daily automated (Render default)

### Access Control
- **Multi-tenancy:** Org-level isolation (schema/001_core.sql has `orgs` table)
- **Authentication:** Streamlit auth or custom (phase 2)
- **Audit logs:** All database writes timestamped with `created_at`

---

## Monitoring & Observability

### Health Checks
- Discovery pipeline completion: Email on failure
- Database connections: Monitor active connections (max 22 on free tier)
- API rate limits: FAERS (40 req/min), UniCourt (track usage)

### Metrics to Track
- Signals detected per day
- Candidates created per week
- Discovery pipeline runtime
- Database size growth
- Customer dashboard usage

### Alerts
- Discovery pipeline failure (email)
- Database storage >80% (upgrade trigger)
- API errors >10% (investigate)

---

## Development Workflow

```bash
# Local development (uses local PostgreSQL)
DATABASE_URL=postgresql://tortsignal:pass@localhost:5432/tortsignal
python3 -m streamlit run app/app.py

# Staging (uses cloud database, separate instance)
DATABASE_URL=postgresql://auditsignal:pass@staging.render.com/auditsignal_staging
python3 -m streamlit run app/app.py

# Production (uses cloud database)
DATABASE_URL=postgresql://auditsignal:pass@production.render.com/auditsignal
# Auto-deployed via Render on git push to main
```

---

## Next Steps

1. ✅ **This week:** Deploy cloud database (Render PostgreSQL)
2. ✅ **This week:** Load Safety Intelligence Graph schema (001 + 002 + 003)
3. 🔨 **Next week:** Build discovery pipeline (FAERS + MAUDE connectors)
4. 🔨 **Next week:** Build UniCourt AI browser agent ($300/month automation)
5. 🔨 **2 weeks:** Launch TortSignal MVP dashboard
6. 🔨 **1 month:** First paying customer (TortSignal firm or hospital)
7. 🔨 **2 months:** SafetyScore development begins
8. 🔨 **3 months:** 5-10 paying customers, proof of concept validated

**The cloud database you're deploying today powers all of it.**

Ready to create your Render PostgreSQL instance?
