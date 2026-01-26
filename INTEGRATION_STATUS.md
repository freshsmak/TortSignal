# TortSignal Integration Status & Architecture

**Last Updated:** 2026-01-26
**Purpose:** Complete overview of integrations, their connection status, and what's needed for frontend development

---

## Executive Summary

TortSignal is an **Epidemiological Discovery Engine (EDE)** that identifies mass tort litigation opportunities 2-4 years before they become public knowledge. The system has **two parallel architectures**:

| Directory | Purpose | Status |
|-----------|---------|--------|
| `backend/` | Phase 2 EDE - Full scoring system, FastAPI | Production-ready |
| `tortsignal/` | Post-pivot - Discovery-first, connectors | Active development |

---

## Three Core Workflows

### 1. Discovery (Finding New Signals)
**Entry Points:**
- `run_discovery_scan.py` - Main dual-methodology discovery
- `tortsignal/src/pipeline/fda_discovery.py` - FDA FAERS/MAUDE scanning

**Methodologies:**
- **Hazard-First:** Regulatory ban → Map exposure → Predict disease → Validate epidemiology
- **Epidemiology-First:** Disease anomaly → Cross-reference biomarkers → Find mechanism

### 2. Analysis (Scoring Signals)
**Entry Points:**
- `backend/scoring/bradford_hill.py` - 9-criteria causal assessment (0-100)
- `backend/scoring/litigation.py` - 7-factor viability assessment (0-100)

### 3. Watchlist/Monitoring (Tracking Signals)
**Entry Points:**
- `discovery_watchlist.json` - Current active signals
- `tortsignal/app/app.py` - Streamlit dashboard

---

## Integration Status Matrix

### FULLY WORKING (No API Key Required)

| Integration | Location | Status | Notes |
|-------------|----------|--------|-------|
| **OpenFDA FAERS** | `tortsignal/src/connectors/faers.py` | ✅ LIVE | Drug adverse events. Free tier: 1k/day, with key: 120k/day |
| **OpenFDA MAUDE** | `tortsignal/src/connectors/maude.py` | ✅ LIVE | Device adverse events. Same rate limits |
| **PubMed E-utilities** | `tortsignal/src/connectors/pubmed.py` | ✅ LIVE | Scientific literature. 3 req/sec free, 10 with key |
| **FDA Federal Register** | `backend/scanners/regulatory.py` | ✅ LIVE | Proposed rules/bans via API |

### PARTIALLY WORKING (Needs API Key or Has Fallbacks)

| Integration | Location | Status | Notes |
|-------------|----------|--------|-------|
| **SEER Cancer Registry** | `backend/integrations/epidemiology.py` | ⚠️ NEEDS KEY | Real API needs `SEER_API_KEY`. Has literature fallback |
| **CDC WONDER** | `backend/integrations/cdc_wonder_enhanced.py` | ⚠️ LIMITED | 6-layer fallback: XML→Form→TSV→HTML→CSV→Literature. API often unavailable |
| **NHANES Biomarkers** | `backend/integrations/nhanes.py` | ⚠️ PARTIAL | Downloads XPT files. TiO2 NOT measured, uses literature estimates |
| **EU ECHA** | `backend/scanners/regulatory.py` | ⚠️ SCRAPING | Web scraping, may break. Has mock data fallback |
| **IARC** | `backend/scanners/regulatory.py` | ⚠️ NEEDS FEEDPARSER | RSS feed parsing, needs `feedparser` package |

### REQUIRES PAID API KEY

| Integration | Location | Status | Notes |
|-------------|----------|--------|-------|
| **UniCourt** | `tortsignal/src/connectors/unicourt.py` | 🔑 PAID | Court filings. Needs `UNICOURT_CLIENT_ID` + `UNICOURT_CLIENT_SECRET` |
| **Anthropic Claude** | `tortsignal/src/extraction/entity_extractor.py` | 🔑 PAID | Entity extraction. Needs `ANTHROPIC_API_KEY` |

### NOT YET IMPLEMENTED

| Integration | Purpose | Location | Priority |
|-------------|---------|----------|----------|
| **NIH RePORTER** | Grant tracking (novelty) | Mentioned but no connector | Medium |
| **PACER/CourtListener** | Free court data alternative | None | Low (UniCourt preferred) |
| **SEC Filings** | Defendant solvency | None | Low (manual currently) |
| **OSHA** | Occupational exposure | None | Low |

---

## Environment Variables Required

```bash
# Required for core functionality
DATABASE_URL=postgresql://user:pass@localhost:5432/tortsignal

# Required for entity extraction
ANTHROPIC_API_KEY=sk-ant-xxx

# Required for court filings
UNICOURT_CLIENT_ID=xxx
UNICOURT_CLIENT_SECRET=xxx

# Optional - improves rate limits
OPENFDA_API_KEY=xxx
SEER_API_KEY=xxx
NCBI_API_KEY=xxx  # For PubMed

# Optional - app config
LOG_LEVEL=INFO
DISCOVERY_DAYS=7
DISCOVERY_LIMIT=100
```

---

## Data Models

### Core Models (`tortsignal/src/models.py`)

| Model | Purpose | Used By |
|-------|---------|---------|
| `CaseRecord` | Court filing from UniCourt | Discovery pipeline |
| `FAERSReport` | Drug adverse event | FAERS connector |
| `MAUDEReport` | Device adverse event | MAUDE connector |
| `PubMedArticle` | Scientific paper | PubMed connector |
| `AdverseTrend` | Drug trend signal | FAERS discovery |
| `ReactionTrend` | Injury trend (reaction-first) | FAERS discovery |
| `DeviceTrend` | Device trend signal | MAUDE discovery |
| `DeviceCategoryTrend` | Device category signal | MAUDE discovery |
| `CandidateCluster` | Aggregated tort candidate | Clustering |

### Backend Models (`backend/models.py`)

12-table SQLAlchemy ORM including: Signal, RegulatoryAction, Exposure, Prediction, EpidemiologyValidation, BradfordHillScore, LitigationScore, Defendant, PubMedPaper, etc.

---

## Discovery Paradigms

### FAERS (Drug) Discovery Modes

1. **Product-First:** "Is Drug X showing elevated adverse events?"
2. **Reaction-First:** "What injuries are spiking across ALL drugs?" → trace back to drugs
3. **Pair Discovery:** "What drug+reaction combinations are anomalous?"
4. **Manufacturer-Level:** "Is a company having systemic quality issues?"

### MAUDE (Device) Discovery Modes

1. **Device-First:** Traditional product monitoring
2. **Category-First:** Whole device classes (by FDA product code)
3. **Manufacturer-First:** Systemic company issues

---

## Scoring Systems

### Bradford Hill (Causation) - 9 Criteria

| Criterion | Weight | Data Sources |
|-----------|--------|--------------|
| Strength (RR/OR) | 15% | PubMed studies |
| Consistency | 12% | Study count |
| Specificity | 8% | Disease classification |
| **Temporality** | 15% | CDC WONDER + exposure timeline |
| Biological Gradient | 10% | Dose-response studies |
| Plausibility | 15% | Mechanistic papers |
| Coherence | 10% | Review articles |
| Experiment | 10% | Animal/intervention studies |
| Analogy | 5% | Similar exposures |

**Thresholds:**
- ≥85: VERY STRONG - Expert validation recommended
- ≥70: STRONG - Ready for validation
- ≥60: MODERATE - Litigation winner benchmark (Roundup = 60%)
- <50: WEAK - Insufficient for litigation

### Litigation Score (Viability) - 7 Factors

| Factor | Weight | Data Sources |
|--------|--------|--------------|
| Causal Strength | 20% | BH score |
| Population Size | 15% | Exposure proxies, CDC |
| Defendant Solvency | 20% | SEC filings (manual) |
| Preventability | 15% | Regulatory warnings |
| Social Justice | 10% | Demographics |
| Severity | 15% | Disease severity |
| Novelty | 5% | Litigation status, NIH grants |

---

## Frontend Requirements

### Dashboard Pages (Streamlit)

| Page | Location | Status |
|------|----------|--------|
| Watchlist | `tortsignal/app/pages/watchlist.py` | Scaffolded |
| Dossier | `tortsignal/app/pages/dossier.py` | Scaffolded |

### API Endpoints (FastAPI)

| Endpoint | Purpose | Location |
|----------|---------|----------|
| `GET /api/signals` | List signals with filters | `backend/api.py` |
| `GET /api/signals/{id}` | Signal details | `backend/api.py` |
| `GET /api/portfolio` | Executive dashboard | `backend/api.py` |
| `POST /api/signals/{id}/actions` | User actions | `backend/api.py` |
| `GET /api/pipeline` | Funnel statistics | `backend/api.py` |
| `GET /api/signals/{id}/dossier.pdf` | Generate PDF | `backend/api.py` |

### Required UI Components

1. **Watchlist View:** Ranked candidates, filtering by score/stage/category
2. **Dossier View:** Deep-dive on single signal with all evidence
3. **Score Display:** Visual Bradford Hill + Litigation breakdowns
4. **Stage Badges:** quiet → awareness → investigate → high_conviction
5. **Trend Charts:** Time series for adverse events and disease rates

---

## Hypothetical Tort Generation (User Feature)

Users can create custom hypothetical torts and query real data:

```python
# Example: User wants to test "Chemical X → Disease Y"
signal_data = {
    'chemical': 'User Chemical',
    'disease': 'User Disease',
    'effect_size': None,  # Will be calculated
    # ... user provides what they know
}

# System queries live data:
# 1. OpenFDA for adverse events
# 2. PubMed for mechanistic papers
# 3. CDC WONDER for disease trends
# 4. NHANES for biomarker levels (if measured)

# Then scores with Bradford Hill
scorer = BradfordHillScorer()
result = scorer.score(signal_data)
```

---

## Database Setup

```bash
# Start PostgreSQL via Docker
cd tortsignal
docker-compose up -d

# Run migrations
psql $DATABASE_URL < schema/001_core.sql
psql $DATABASE_URL < schema/002_timeseries.sql
psql $DATABASE_URL < schema/003_safety_intelligence_extensions.sql
psql $DATABASE_URL < schema/004_add_enrichment_columns.sql
```

---

## Quick Start Commands

```bash
# Run FDA discovery (no database required)
cd tortsignal
python -m src.pipeline.fda_discovery --no-persist --output results.json

# Run full discovery scan
python run_discovery_scan.py

# Start Streamlit dashboard
cd tortsignal
pip install -e ".[dashboard]"
streamlit run app/app.py

# Start FastAPI backend
cd backend
uvicorn api:app --reload
```

---

## Current Watchlist Signals

From `discovery_watchlist.json`:

| ID | Chemical | Disease | BH Score | Status |
|----|----------|---------|----------|--------|
| HAZ-20260126-001 | Titanium Dioxide | IBD | 85 | WATCHLIST |
| HAZ-20260126-002 | Titanium Dioxide | Colorectal Cancer | 70 | WATCHLIST |

---

## Key Files Summary

| Purpose | File Path |
|---------|-----------|
| Main discovery orchestration | `run_discovery_scan.py` |
| FDA discovery (FAERS+MAUDE) | `tortsignal/src/pipeline/fda_discovery.py` |
| FAERS connector | `tortsignal/src/connectors/faers.py` |
| MAUDE connector | `tortsignal/src/connectors/maude.py` |
| PubMed connector | `tortsignal/src/connectors/pubmed.py` |
| UniCourt connector | `tortsignal/src/connectors/unicourt.py` |
| Bradford Hill scorer | `backend/scoring/bradford_hill.py` |
| Litigation scorer | `backend/scoring/litigation.py` |
| Regulatory scanner | `backend/scanners/regulatory.py` |
| SEER integration | `backend/integrations/epidemiology.py` |
| CDC WONDER | `backend/integrations/cdc_wonder_enhanced.py` |
| NHANES biomarkers | `backend/integrations/nhanes.py` |
| Data models | `tortsignal/src/models.py` |
| Configuration | `tortsignal/src/config.py` |
| Streamlit app | `tortsignal/app/app.py` |
| FastAPI backend | `backend/api.py` |
| Database schema | `tortsignal/schema/*.sql` |

---

## What's Truly Connected vs Mock/Fallback

### Truly Live (Making Real API Calls)
- ✅ OpenFDA FAERS - Real drug adverse event data
- ✅ OpenFDA MAUDE - Real device adverse event data
- ✅ PubMed E-utilities - Real scientific literature
- ✅ FDA Federal Register - Real proposed rules

### Has Fallback/Mock Data
- ⚠️ EU ECHA - Web scraping with mock fallback
- ⚠️ IARC - RSS parsing with mock fallback
- ⚠️ SEER - API requires key, falls back to literature estimates
- ⚠️ CDC WONDER - Multi-strategy with literature fallback
- ⚠️ NHANES - Real file downloads, but TiO2/many chemicals not measured

### Requires Setup Before Use
- 🔑 UniCourt - Paid enterprise API
- 🔑 Claude entity extraction - Paid API

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         TortSignal                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   DISCOVERY      │    │   ANALYSIS       │                   │
│  │                  │    │                  │                   │
│  │ - Hazard-First   │    │ - Bradford Hill  │                   │
│  │ - Epi-First      │    │ - Litigation     │                   │
│  │ - FDA Scanning   │    │ - Confidence     │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                             │
│           ▼                       ▼                             │
│  ┌────────────────────────────────────────────┐                 │
│  │              WATCHLIST / MONITORING        │                 │
│  │                                            │                 │
│  │  - Ranked candidates                       │                 │
│  │  - Stage tracking (quiet→high_conviction)  │                 │
│  │  - Trend alerts                            │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                     DATA SOURCES                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ OpenFDA  │ │ PubMed   │ │ UniCourt │ │ CDC/SEER │           │
│  │ (FAERS/  │ │ E-utils  │ │ (Paid)   │ │ (Limited)│           │
│  │  MAUDE)  │ │          │ │          │ │          │           │
│  │   ✅     │ │   ✅     │ │   🔑     │ │   ⚠️     │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                         │
│  │ EU ECHA  │ │  IARC    │ │ NHANES   │                         │
│  │ (Scrape) │ │  (RSS)   │ │ (Files)  │                         │
│  │   ⚠️     │ │   ⚠️     │ │   ⚠️     │                         │
│  └──────────┘ └──────────┘ └──────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Legend: ✅ = Live   ⚠️ = Limited/Fallback   🔑 = Needs Paid Key
```
