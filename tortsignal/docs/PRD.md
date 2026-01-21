# TortSignal Product Requirements Document

## Product Summary

TortSignal is an early-warning "terminal" that continuously detects and ranks emerging mass-tort clusters (Defendant/Product × Injury) by fusing public signals: court filings, FDA FAERS/MAUDE, scientific literature, and SEC litigation reserves. It produces an explainable Watchlist + Dossier workflow aimed at helping plaintiff firms move 18–36 months earlier than the market.

---

## Problem Statement

Mass torts "tip" from scattered individual suits into consolidation/MDLs after a period where signals are visible but fragmented across:
- Court filings (scattered jurisdictions, different plaintiff firms)
- Adverse event databases (FDA FAERS, MAUDE)
- Scientific literature (case reports → cohort studies → meta-analyses)
- Corporate disclosures (litigation reserves, risk factor language)

Firms miss first-mover advantage because intelligence is manual, noisy, and siloed.

---

## Target Users

| User | Role | Primary Need |
|------|------|--------------|
| **Plaintiff Firms** | Intake/marketing leaders, case strategists, partners | First-mover advantage on case acquisition |
| **Litigation Funders** | Underwriting teams, portfolio strategists | Early identification of fundable portfolios |
| **Insurance Underwriters** | Product liability teams | Pricing emerging risks before claims materialize |
| **Hedge Funds** | Event-driven researchers | Short thesis research on exposed manufacturers |

**MVP Focus**: Plaintiff firms (you have direct access and domain expertise via your CRM role).

---

## Goals

1. Detect "emerging tort candidates" earlier than industry consensus
2. Provide explainable evidence trails (source-linked) for fast diligence
3. Route signals by tort category (pharma/device/chemical/gov-contractor) because sources vary

## Non-Goals (MVP)

- Predict settlement amounts, liability, or legal outcomes
- Provide legal advice
- "Guaranteed next MDL" claims (false positives are expected; Zantac-like reversals exist)
- Lead-gen execution (ads, claimant acquisition ops)
- Multi-tenancy / enterprise features

---

## Core Workflows

### A) Watchlist

**Purpose**: Ranked list of emerging tort candidates for triage.

**Display**:
- Table: Defendant | Product | Injury | Score | Stage | Category | Last Updated
- Filters: category, stage, date range, minimum score, jurisdiction
- Sort: by score (default), by velocity, by recency

**Interactions**:
- Click row → navigate to Dossier
- Bulk actions: mark reviewed, reject, export

### B) Dossier (Per Candidate)

**Purpose**: Deep dive into a single candidate with all evidence.

**Sections**:

1. **Header**
   - Defendant, Product, Injury (or "mixed")
   - Category, Score, Stage
   - First seen / Last updated

2. **Timeline**
   - Chronological list of signal events
   - Event types: filing_new, filing_spike, adverse_trend, paper_published, meta_analysis, sec_language_delta
   - Each event shows: date, type, source link, snippet

3. **Evidence Ledger**
   - All source documents linked to this candidate
   - Columns: Source Type | Title | Date | Link
   - Expandable snippets

4. **Metrics Panel**
   - velocity_7d, velocity_28d, accel_ratio
   - breadth_states, breadth_firms
   - Injury distribution (bar chart)

5. **"Why Now" Box**
   - Auto-generated narrative explaining score drivers
   - Example: "12 new filings in 7 days across 4 states, coinciding with FDA safety communication"

6. **Actions**
   - Mark as Reviewed
   - Reject (false positive)
   - Override category
   - Export to PDF

### C) Alerts (Future)

**Purpose**: Proactive notifications when candidates cross thresholds.

**Triggers**:
- Score crosses stage boundary (Awareness → Investigate → High Conviction)
- Filing velocity spikes (>3x week-over-week)
- New meta-analysis published
- SEC language change detected

**Channels**: Email, Slack, webhook

---

## Data Sources (MVP)

| Source | Signal Type | Category Relevance | Access |
|--------|-------------|-------------------|--------|
| UniCourt/PACER | Court filings, velocity, breadth | All | Paid (user has sandbox) |
| FDA FAERS | Drug adverse events | Pharma | Free API |
| FDA MAUDE | Device adverse events | Devices | Free API |
| PubMed | Scientific literature | All (esp. chemicals) | Free API |
| SEC EDGAR | Litigation reserves, risk language | All public companies | Free |

### Source Priority by Category

| Category | Primary | Secondary | Tertiary |
|----------|---------|-----------|----------|
| Pharma | FAERS | Court filings | PubMed |
| Devices | MAUDE | Court filings | FDA recalls |
| Chemicals/Pesticides | PubMed | Court filings | EPA (future) |
| Gov/Military | Court filings (FCA) | VA data (future) | — |
| Consumer Products | Court filings | PubMed | CPSC (future) |

---

## Scoring System

### Unit of Scoring

**TortCluster** = `(Defendant, Product)` with injury stored as distribution.

Rationale: Early signals are noisy on injury terminology. Clustering by defendant+product maximizes discovery; injury detail tracked as evidence.

### Category Router

Assigns each candidate a category to select the appropriate weight vector.

**Assignment Rules** (MVP):
1. If product matches known drug list → `pharma`
2. If product matches known device list → `device`
3. If defendant is chemical/agricultural company → `chemical`
4. If defendant is government contractor → `gov_contractor`
5. Else → `consumer` or `other`

Manual override always available.

### Weight Vectors by Category

```yaml
pharma:
  faers_trend: 0.40
  court_velocity: 0.30
  court_breadth: 0.10
  literature: 0.15
  sec_language: 0.05

device:
  maude_trend: 0.40
  court_velocity: 0.30
  court_breadth: 0.10
  literature: 0.10
  sec_language: 0.10

chemical:
  literature: 0.40
  court_velocity: 0.25
  court_breadth: 0.15
  iarc_classification: 0.15  # future
  sec_language: 0.05

gov_contractor:
  court_velocity: 0.35
  fca_settlement: 0.30  # future
  court_breadth: 0.20
  sec_language: 0.15

consumer:
  court_velocity: 0.35
  court_breadth: 0.20
  literature: 0.25
  cpsc_reports: 0.10  # future
  sec_language: 0.10
```

### Score Components

Each signal type produces a normalized component (0-100):

- **court_velocity**: Cases filed in last 7 days, scaled against historical baseline
- **court_breadth**: `(unique_states + unique_firms) / max_observed`
- **faers_trend**: `(current_reports / baseline_reports - 1) * 100`, capped
- **maude_trend**: Same as FAERS
- **literature**: Count of relevant papers, weighted by recency and study type (meta-analysis = 3x)
- **sec_language**: Binary or magnitude of reserve increase

### Stage Thresholds

| Stage | Score Range | Meaning |
|-------|-------------|---------|
| Quiet | 0-19 | Background noise, not actionable |
| Awareness | 20-39 | Worth monitoring, insufficient signal |
| Investigate | 40-69 | Credible signal, warrants diligence |
| High Conviction | 70-100 | Strong convergent signals, act now |

### "Why Now" Generation

Template-based narrative:

> "{count} new product-liability filings in the last {days} days across {states} states and {firms} plaintiff firms. {adverse_note} {literature_note} {sec_note}"

Where:
- `adverse_note`: "FAERS reports up {pct}% vs. baseline." (if applicable)
- `literature_note`: "New meta-analysis published in {journal}." (if applicable)
- `sec_note`: "Defendant increased litigation reserves by ${amount}M." (if applicable)

---

## Success Metrics

### Activation (first 30 days)
- Pipeline runs daily without manual intervention
- 50+ candidates in database

### Engagement (first 90 days)
- Dossiers viewed per week
- Time from alert → decision (reviewed/rejected)
- % of alerts marked "worth investigating"

### Quality
- Precision proxy: % of "High Conviction" candidates that correspond to known emerging torts
- Coverage: detection of known torts in backtest (Roundup, AFFF, etc.)

---

## Compliance and Safety

1. **Audit trail**: Immutable raw snapshots + hashes for all source documents
2. **Clear labeling**: UI says "early-warning / investigatory" not "prediction"
3. **No legal advice**: System provides evidence, not conclusions
4. **Respect ToS**: Social listening deferred; any future forum ingestion must be policy-safe
5. **Data retention**: Define policy for raw document storage (suggest 7 years for legal defensibility)

---

## Open Questions

1. **Entity resolution**: How do we handle company/product synonym graphs at scale? (Start with curated lists, add fuzzy matching later)

2. **Minimum viable docket text**: Can we reliably obtain complaint text from UniCourt, or metadata only? (Test in sandbox)

3. **Alert fatigue**: What are sensible default thresholds and throttling rules? (Learn from usage)

4. **Backfill depth**: How far back should we pull historical data for baseline? (Suggest 2 years)

5. **Plaintiff firm extraction**: Do we need firm names, or is count of unique firms sufficient? (Count is sufficient for MVP)

---

## Appendix: Trigger Events from Validation

Historical "trigger events" that preceded MDL formation:

| Tort | Trigger Event | Lead Time |
|------|--------------|-----------|
| Roundup | IARC 2A classification | 19 months |
| AFFF | C8 Science Panel findings | 6 years |
| Vioxx | JAMA meta-analysis | 4 years |
| Opioids | DOJ criminal prosecution | 10 years |
| Pelvic Mesh | FDA safety communication | 3 years |
| 3M Earplugs | False Claims Act settlement | 3 years |
| Talcum | IARC 2B classification | 10 years |
| Paraquat | UCLA epidemiological study | 10+ years |
| Zantac | FDA market withdrawal | 5 months |

These inform signal weighting: IARC classifications, FDA communications, DOJ actions, and peer-reviewed meta-analyses are high-weight trigger events.
