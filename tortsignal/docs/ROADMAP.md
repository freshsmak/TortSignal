# TortSignal Implementation Roadmap

## Overview

This roadmap is organized into 4 phases. Each phase produces a working increment you can demo and validate before moving on.

**Total estimated timeline**: 6-8 weeks (solo vibecode pace)

---

## Phase 1: Foundation (Week 1-2)

**Goal**: Database running, UniCourt connector working, basic entity extraction producing candidates you can query.

### Deliverables

- [ ] **1.1 Database setup**
  - Run `schema/001_core.sql` against your Postgres instance
  - Verify all tables created
  - Test basic CRUD with `psql`

- [ ] **1.2 Config and DB module**
  - `src/config.py` — load env vars, validate required keys
  - `src/db.py` — connection pool, upsert helpers
  - Test: can connect and insert a dummy row

- [ ] **1.3 UniCourt connector**
  - `src/connectors/unicourt.py`
  - Implement `fetch_recent_cases(days=7, limit=100)`
  - Filter by NOS codes 365/367 (Product Liability)
  - Return normalized `CaseRecord` objects
  - Test: pull 10 cases from sandbox, print titles

- [ ] **1.4 Entity extraction**
  - `src/extraction/entity_extractor.py`
  - OpenAI structured output for `{defendant, product, injury, confidence}`
  - Handle failures gracefully (log, skip, continue)
  - Test: extract entities from 10 case titles

- [ ] **1.5 Candidate builder (Step 0)**
  - `src/clustering/candidate_builder.py`
  - Cluster by `(defendant, product)` pair-key
  - Track injury distribution, states, firms
  - Compute MVP score: `count * (1 + breadth_states) * (1 + breadth_firms)`
  - Upsert candidates + evidence to database
  - Test: run full pipeline, query `SELECT * FROM candidates ORDER BY score_total DESC LIMIT 10`

### Validation Checkpoint

Run the pipeline against 7 days of UniCourt data. You should see:
- 10-50 candidates created
- Top candidates have recognizable defendant/product pairs
- Evidence links back to source documents

---

## Phase 2: Multi-Source Discovery (Week 3-4)

**Goal**: Add FDA adverse event signals (FAERS + MAUDE) to enrich candidates and surface pharma/device torts.

### Deliverables

- [ ] **2.1 FAERS connector**
  - `src/connectors/faers.py`
  - Query OpenFDA `/drug/event.json` endpoint
  - Implement `get_trending_drugs(days=30)` — top drugs by report count
  - Implement `get_drug_reports(drug_name, days=180)` — time series for specific drug
  - Compute delta vs baseline (same period last year)
  - Test: identify 5 drugs with >100% increase in reports

- [ ] **2.2 MAUDE connector**
  - `src/connectors/maude.py`
  - Query OpenFDA `/device/event.json` endpoint
  - Same pattern as FAERS: trending + specific device lookup
  - Test: identify 5 devices with elevated adverse event rates

- [ ] **2.3 Anomaly detection logic**
  - In `src/connectors/faers.py` and `maude.py`:
  - Compare current period vs baseline
  - Flag products with: (a) not in baseline top 200, OR (b) >200% increase
  - Emit these as "FDA anomaly candidates"

- [ ] **2.4 Cross-source candidate enrichment**
  - When a UniCourt candidate matches an FDA anomaly (by product name):
    - Add `adverse_trend` signal event
    - Boost score based on category weights
  - When FDA anomaly has no court filings yet:
    - Create candidate with source=`faers`/`maude` only
    - Flag as "pre-litigation signal"

- [ ] **2.5 Signal events table population**
  - Every FAERS/MAUDE trend becomes a `signal_events` row
  - Link to candidate via `cluster_id`
  - Store features: `{reports_current, reports_baseline, delta_pct, top_reactions}`

### Validation Checkpoint

Run full pipeline. You should see:
- Candidates with evidence from multiple sources (court + FDA)
- Some FDA-only candidates (potential early signals)
- Score increases when court + FDA signals converge

---

## Phase 3: Scoring Engine (Week 5-6)

**Goal**: Implement category-aware scoring with explainable components. Add PubMed for scientific plausibility.

### Deliverables

- [ ] **3.1 Category assignment**
  - `src/scoring/category_router.py`
  - Rules-based category assignment:
    - If product in known drug list → `pharma`
    - If product in known device list → `device`
    - If defendant is chemical/ag company → `chemical`
    - If defendant is government contractor → `gov_contractor`
    - Else → `consumer` or `other`
  - Allow manual override via `candidates.category` column

- [ ] **3.2 Category weight configuration**
  - `src/scoring/weights.yaml` (or Python dict)
  - Define weights per category:
    ```yaml
    pharma:
      faers_trend: 0.40
      court_velocity: 0.30
      literature: 0.20
      sec_language: 0.10
    device:
      maude_trend: 0.40
      court_velocity: 0.35
      literature: 0.15
      sec_language: 0.10
    chemical:
      literature: 0.40
      court_velocity: 0.30
      epa_action: 0.20  # future
      sec_language: 0.10
    # ... etc
    ```

- [ ] **3.3 PubMed connector**
  - `src/connectors/pubmed.py`
  - Search for `{product} AND {injury}` combinations
  - Prioritize meta-analyses (publication type filter)
  - Return paper count, recency, and key citations
  - Test: search "glyphosate non-hodgkin lymphoma", verify De Roos 2003 appears

- [ ] **3.4 Scoring engine**
  - `src/scoring/scorer.py`
  - Input: candidate + all signal events
  - Process:
    1. Get category from router
    2. Load weight vector for category
    3. Compute component scores (normalize each signal type 0-100)
    4. Weighted sum → `score_total`
    5. Determine stage: <30 Awareness, 30-60 Investigate, >60 High Conviction
  - Output: `score_total`, `score_components`, `stage`, `why_now`

- [ ] **3.5 Scheduled rescoring**
  - Add a job (cron or manual) that:
    1. Pulls all active candidates
    2. Recalculates scores with latest signals
    3. Updates `cluster_scores` time series table
    4. Detects stage transitions for alerting (future)

### Validation Checkpoint

- Run scoring against your candidates
- Verify that pharma candidates weight FAERS heavily
- Verify that chemical candidates weight literature heavily
- Check that `score_components` JSON is populated and explainable

---

## Phase 4: Dashboard MVP (Week 7-8)

**Goal**: Streamlit UI with Watchlist and Dossier views. Something you can demo to the team.

### Deliverables

- [ ] **4.1 Streamlit app scaffold**
  - `app/app.py` — main entry point
  - `app/pages/watchlist.py` — ranked candidate list
  - `app/pages/dossier.py` — single candidate deep dive
  - `app/components/` — reusable UI components

- [ ] **4.2 Watchlist view**
  - Table: Defendant | Product | Injury | Score | Stage | Last Updated
  - Filters: category, stage, date range, min score
  - Sort by score (default), recency, velocity
  - Click row → navigate to Dossier

- [ ] **4.3 Dossier view**
  - Header: Defendant, Product, Category, Score, Stage
  - **Timeline**: Chronological list of signal events (sparkline optional)
  - **Evidence ledger**: Links to source documents with snippets
  - **Metrics panel**: velocity_7d, velocity_28d, breadth_states, breadth_firms
  - **"Why now" box**: Auto-generated explanation of score drivers
  - **Injury distribution**: Bar chart of injury types mentioned

- [ ] **4.4 Manual overrides**
  - Button: "Mark as Reviewed"
  - Button: "Reject (false positive)"
  - Button: "Promote to Active Monitoring"
  - Dropdown: Override category assignment

- [ ] **4.5 Basic auth (optional)**
  - Streamlit secrets for simple username/password
  - Or skip for internal demo

### Validation Checkpoint

- Demo to yourself: can you find a plausible emerging tort?
- Demo to a colleague: is the UI self-explanatory?
- Note any friction points for iteration

---

## Future Phases (Post-MVP)

### Phase 5: SEC EDGAR Integration
- Monitor 10-K/10-Q filings for litigation reserve language changes
- Diff quarter-over-quarter for "new product mentions in legal proceedings"
- Add `sec_language_delta` and `sec_reserve_delta` signal types

### Phase 6: Alerts and Notifications
- Email/Slack alerts when candidates cross stage thresholds
- Configurable alert rules per user/org
- Digest mode: daily/weekly summary of movers

### Phase 7: Entity Resolution Hardening
- Build proper alias graph (subsidiary → parent, brand → ingredient)
- Fuzzy matching for defendant/product names
- Human-in-the-loop alias confirmation

### Phase 8: Historical Backfill
- Pull 2-3 years of UniCourt data
- Backfill FAERS/MAUDE trends
- Validate detection windows against known MDLs

### Phase 9: Multi-Tenancy and CRM Integration
- Org/user management
- "Push to Intake" button → creates campaign in your CRM
- API endpoints for programmatic access

---

## Dependencies and Risks

| Risk | Mitigation |
|------|------------|
| UniCourt rate limits | Implement backoff, cache aggressively |
| OpenAI extraction errors | Graceful fallback, log failures, manual review queue |
| Entity resolution noise | Start with pair-key (defendant, product); add injury disambiguation later |
| False positive fatigue | Clear "Awareness / Investigate / High Conviction" staging; easy reject button |
| Scope creep | Stick to phases; no SEC/alerts until Phase 4 is solid |

---

## Success Criteria (Phase 4 Complete)

1. **Pipeline runs daily** without manual intervention
2. **50+ candidates** in database with scores
3. **Multi-source evidence** for top candidates (court + FDA or court + literature)
4. **Dossier is useful**: a lawyer could look at it and decide "worth investigating" or "pass"
5. **One "aha" moment**: surface a candidate that matches a known emerging tort (e.g., Ozempic, hair relaxer, Camp Lejeune follow-ons)
