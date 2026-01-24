# TortSignal - Product Research Archive

**Status**: HOLD - Not building now, revisit in 6-12 months after AUDITFin customer base expansion

**Decision Date**: January 2026

**Decision Maker**: CEO

---

## Executive Summary

We explored building a FAERS-based pharmaceutical signal detection system for plaintiff law firms. Through hands-on development and data analysis, we determined this is **not the right product to build right now**, but gained valuable insights for a future court-centric "Tort Formation Radar" product.

### Key Finding
**FAERS alone cannot support the business case.** A defensible litigation intelligence product must be **court-centric** (PACER/UniCourt) with FAERS as corroboration only.

---

## What We Validated

### ✅ Market Opportunity Exists
- Tort firms pay $25K/year for AUDITFin (financial tracking module)
- Same TAM would pay for early tort detection if it provides 6-12 month marketing lead time
- Estimated market: $500M+ (plaintiff tort firms)

### ✅ Technical Feasibility Confirmed
- UniCourt provides state + federal court coverage (critical for pre-MDL detection)
- CourtListener/RECAP offers free alternative for prototyping
- SEC EDGAR + literature (PubMed/OpenAlex) as enrichment layers
- Architecture mapped, APIs documented

### ✅ Realistic Lead Time: 6-12 Months
- Not 18-36 months (that's marketing fantasy)
- Court filing clusters appear 6-18 months before MDL consolidation
- FAERS lags 3-6 months behind court activity (litigation-contaminated)

### ❌ FAERS Is Not Sufficient
- **Data quality issues**: Calcium (7,344 deaths) and folic acid (4,865 deaths) flagged due to confounding (elderly patients taking supplements)
- **Primary Suspect filter ineffective**: Only 0.3% reduction (reporters mark supplements as suspects incorrectly)
- **Reporting lag**: Quarterly updates, 3+ month delay
- **Underreporting bias**: Voluntary system, massive denominators unknown
- **Litigation contamination**: Lawyers file FAERS reports to build cases

---

## Strategic Rationale for HOLD Decision

### Why Not Now
1. **No existing customer pull**: Build relationships first, let demand emerge organically
2. **Unproven value**: Need to validate firms would act on 6-12 month signals
3. **Complexity vs. ROI**: Court data infrastructure requires investment before proving PMF
4. **Competition**: Lex Machina, Bloomberg Law, Docket Alarm already exist

### Why Later Makes Sense
1. **Distribution through AUDITFin**: Once we have 12+ largest tort firms as customers
2. **Customer-driven features**: Let them tell us what's missing from current tools
3. **Lower risk**: Validate with pilot (CourtListener free tier) before UniCourt commitment
4. **Technical foundation exists**: We know the architecture, can move fast when ready

---

## Fast MVP Playbook (For Future Use)

When timing is right (6-12 months from now), execute this 4-week sprint:

### Week 1: Customer Discovery
- Interview 3-5 AUDITFin users
- Question: "If you could get 6-month early warning on emerging torts, what would success look like?"
- Validate pricing ($10-25K/year add-on module)

### Week 2: Backtest with Free Data
- Use CourtListener/RECAP to ingest 10 historical MDLs
- Build simple clustering: (defendant, product, injury, filing velocity)
- Prove 6-12 month lead time with <50% false positive rate

### Week 3: Build Digest MVP
- Weekly email: "Top 5 Rising Clusters"
- Markdown dossiers: filing counts, jurisdictions, key allegations
- No dashboard - just actionable intelligence

### Week 4: Pilot with 2 Firms
- 4 weeks of digests
- Measure: Did they start marketing campaigns? Secure cases?
- Refine before scaling

**Only then** commit to UniCourt subscription ($5-10K/mo) + dashboard build.

---

## Technical Assets (Preserved in Codebase)

### What We Built
1. **FAERS Discovery Pipeline** (`discover_faers_signals.py`)
   - Queries FDA adverse event database
   - Calculates velocity, acceleration, severity scores
   - Enriches with OpenFDA drug metadata
   - Dual scoring: pharmacovigilance vs litigation intelligence

2. **Litigation Intelligence Scoring**
   - Drug class filters (GLP-1 agonists, anticoagulants, etc.)
   - Indication severity scoring (cosmetic=high risk, terminal=low risk)
   - Supplement detection with contamination spike detection
   - Timeline sweet spot (2-7 years post-approval)
   - Unexpectedness multipliers (observed vs expected SAE rates)

3. **Streamlit Dashboard**
   - Watchlist view (signals sorted by score)
   - Dossier view (detailed signal analysis)
   - Database helpers for PostgreSQL queries

4. **Verification Scripts**
   - Primary Suspect filter testing
   - Supplement scoring validation
   - Drug characterization distribution analysis

### What We Learned (Code-Level)
- **Supplement confounding**: Normal calcium scores 7.5 despite 7,344 deaths (correct)
- **Contamination detection**: Velocity spike (100%+) catches L-Tryptophan pattern (scores 75)
- **Softened multipliers**: Whitelist 1.2x (not 1.5x), blacklist 0.7x (not 0.1x) - history as guide, not constraint
- **Database schema**: Uses dict_row factory (returns dicts, not tuples)

---

## Data Sources Evaluated

### Free/Low-Cost (Prototyping)
| Source | Cost | Freshness | Value for Radar |
|--------|------|-----------|-----------------|
| **CourtListener/RECAP** | Free | Daily | ✅ Federal dockets + webhooks, best for backtesting |
| **PACER PCL API** | $0.10/page | Daily/nightly | ✅ Federal precision, pay per document pull |
| **SEC EDGAR** | Free | Real-time | ✅ Risk disclosures, litigation reserves |
| **PubMed E-Utilities** | Free | Near real-time | ✅ Literature signals (10 rps with key) |
| **OpenAlex** | Free | Rolling updates | ✅ Bibliometrics (100K credits/day from Feb 2026) |
| **FAERS/MAUDE** | Free | Quarterly (+3mo lag) | ⚠️ Corroboration only, not trigger |

### Paid (Production Scale)
| Source | Cost | Value | When to Use |
|--------|------|-------|-------------|
| **UniCourt** | $5-10K/mo | State + federal aggregation | When scaling beyond federal-only |
| **Semantic Scholar** | Varies | Paper enrichment | Optional enhancement |

---

## Backtest Targets (When Ready)

Use these 9 historical MDLs to validate lead time:

1. **Ozempic/Wegovy** (MDL 3094) - Gastroparesis, 3,063 cases (Jan 2026)
2. **Xarelto** (MDL 2592) - Bleeding, $775M settlement (2019)
3. **Invokana** (MDL 2750) - Amputations, $100M+ settlement (2018-2019)
4. **Risperdal** - Gynecomastia, $2.2B fine + verdicts
5. **Zantac** - NDMA cancer, GSK $2.2B settlement (2024)
6. **Taxotere** (MDL 2740) - Permanent alopecia, 2,988 cases, NO settlements
7. **Talcum Powder** - Ovarian cancer, $6.48B proposed, 67,204 cases
8. **Hair Relaxer** (MDL 3060) - Uterine cancer, 10,948 cases (2022→)
9. **Essure** - Device migration, $1.6B settlement (2020)

**Success criteria**: Detect 6/9 MDLs with 6-12 month lead time, <50% false positives

---

## Competitive Landscape

### Existing Solutions
- **Lex Machina**: Analytics on litigation trends (Bloomberg product)
- **Bloomberg Law**: Docket search + analytics
- **Docket Alarm**: Filing alerts + tracking
- **Trellis Law**: AI-powered case search

### Our Differentiation (When We Build)
1. **Tort-specific clustering**: (defendant, product, injury) tuples
2. **Velocity-based alerting**: Not just volume, but acceleration
3. **Multi-source fusion**: Court + FAERS + EDGAR + literature
4. **Marketing-focused**: Designed for plaintiff firm intake/marketing teams
5. **Embedded in workflow**: Add-on to existing AUDITFin relationship

---

## Walk-Away Criteria (Revisit These)

Stop development (or narrow scope) if:

1. **Coverage failure**: Can't get scalable state-court access at viable price
2. **Latency failure**: Lead time < 6 months vs MDL consolidation
3. **Precision failure**: >50% of alerts never become real clusters (100+ filings)
4. **Cost failure**: Document acquisition costs > customer willingness to pay
5. **Moat failure**: Can't articulate advantage vs Lex Machina/Bloomberg

---

## Next Steps (When Timing is Right)

1. **Customer discovery first**: Interview AUDITFin users, validate demand
2. **Backtest with free tools**: CourtListener + PACER for 9 historical MDLs
3. **Build digest MVP**: Weekly emails, no dashboard
4. **2-firm pilot**: 4 weeks of signals, measure action taken
5. **Scale decision**: Only commit to UniCourt after proving value

---

## Repository Contents

```
TortSignal/
├── tortsignal/
│   ├── discover_faers_signals.py    # Main discovery pipeline
│   ├── app/
│   │   ├── app.py                   # Streamlit dashboard
│   │   ├── db_helpers.py            # PostgreSQL queries
│   │   ├── pages/
│   │   │   ├── watchlist.py         # Signal list view
│   │   │   └── dossier.py           # Detail view
│   └── src/
│       ├── config.py                # Configuration
│       └── db.py                    # Database connection
├── PHARMA_TORT_PATTERN_ANALYSIS.md  # 9 MDL case studies
├── TEST_RESULTS_LITIGATION_SCORING.md  # Validation results
├── verify_faers_data.py             # Data quality scripts
└── test_supplement_scoring.py       # Scoring validation
```

---

## Contact & Ownership

**Product Owner**: [Your Company]
**Research Period**: December 2025 - January 2026
**Archive Date**: January 2026
**Revisit Date**: Q3-Q4 2026 (after AUDITFin customer base expansion)

---

## Appendix: Key Insights from Research

### FAERS Data Quality Issues Discovered

1. **Calcium Paradox**: 7,344 deaths reported, but 99.7% marked "Primary Suspect" due to reporter confusion (elderly patients on multiple drugs die → calcium supplement blamed)

2. **Primary Suspect Filter Ineffective**: Adding `drugcharacterization:1` filter reduced counts by only 0.3% (expected 80-95% reduction)

3. **Confounding by Indication**: Sick patients taking supplements alongside treatment drugs → supplements blamed for deaths

4. **Litigation Contamination**: Lawyers file FAERS reports strategically to support cases (query found "lawyers and others" as reporters)

### Scoring Breakthrough: Velocity vs Absolute Counts

**Problem**: Calcium has 7,344 deaths (high absolute) but not a tort
**Solution**: Use velocity (% change) to detect true signals
- Normal calcium: velocity +5% → score 7.5 (low)
- Contaminated supplement: velocity +999% → score 75 (high)
- Ozempic: velocity +37.5% → score 66.4 (litigation risk)

This distinguishes between:
- **Confounded deaths** (sick populations using supplements)
- **Contaminated products** (L-Tryptophan-style sudden spikes)
- **Emerging torts** (unexpected SAEs in healthier populations)

### Pattern Recognition: Not Just Drug Classes

We initially built whitelist (GLP-1 agonists, anticoagulants) and blacklist (chemo, HIV drugs). This was overfitting to historical data.

**Better approach**:
- Indication severity (cosmetic=1, terminal=9)
- Expected baseline SAE rates by class
- Unexpectedness multipliers (observed/expected ratio)
- Softened class filters (1.2x boost, 0.7x penalty - not hard rules)

**Result**: Can detect "next Hair Relaxer" (new drug class causing harm), not just "more Ozempic signals"

---

**End of Archive**
