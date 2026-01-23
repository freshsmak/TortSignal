# Safety Intelligence Platform Strategy

## Executive Summary

**The Insight:** TortSignal's core asset isn't a tort-finding tool. It's a **Safety Intelligence Graph** that can power 10+ products across multiple markets.

**Total Addressable Market:**
- Plaintiff tort firms: ~$500M (original TortSignal target)
- Hospital procurement: **~$5B** (device/formulary safety scorecards)
- Regulatory risk intelligence: **~$2B** (pharma, investors, insurers)
- M&A diligence: **~$1B** (PE, corporate dev)
- Defense-side litigation prep: **~$800M** (manufacturers, counsel)

**Strategic Decision:** Build the **Safety Intelligence Graph once**, deploy it to multiple markets with application-specific layers.

---

## The Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               CORE SAFETY INTELLIGENCE GRAPH                 │
│                                                              │
│  • Products + Adverse Events (FAERS, MAUDE)                 │
│  • Regulatory Actions (warnings, recalls, label changes)    │
│  • Literature Evidence (PubMed, Semantic Scholar)           │
│  • Hazard Classifications (IARC, EPA)                       │
│  • Signal Trends (velocity, acceleration, clustering)       │
│                                                              │
│  Data Sources:                                              │
│  - FDA FAERS (drugs) - FREE                                 │
│  - FDA MAUDE (devices) - FREE                               │
│  - OpenFDA enforcement/recalls - FREE                       │
│  - PubMed (NLM API) - FREE                                  │
│  - Semantic Scholar - FREE                                  │
│  - IARC Monographs - FREE                                   │
│  - UniCourt Premium ($300/month) - AI browser automation    │
│  - PACER ($50-100/month) - targeted MDL searches            │
└──────────────────────────────────────────────────────────────┘
                            ▲
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  TortSignal   │   │ SafetyScore   │   │ RegulatoryAI  │
│  (plaintiff)  │   │  (hospitals)  │   │ (pharma/PE)   │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ Adds:         │   │ Adds:         │   │ Adds:         │
│ • Litigation  │   │ • Device      │   │ • Regulatory  │
│   viability   │   │   reliability │   │   risk score  │
│ • Causation   │   │ • Procurement │   │ • Competitor  │
│   strength    │   │   recs        │   │   intel       │
│ • Plaintiff   │   │ • Alternative │   │ • Action      │
│   firm match  │   │   products    │   │   forecasts   │
│ • MDL status  │   │ • Cost-       │   │ • Precedent   │
│               │   │   effectiveness│   │   mapping     │
└───────────────┘   └───────────────┘   └───────────────┘
 $500M TAM           $5B TAM            $2B TAM
```

---

## Market Opportunities (Ranked by Defensibility + TAM)

### 🥇 #1: Hospital Procurement Safety Scorecards

**Product:** SafetyScore - Device/drug safety scorecards for hospital procurement

**Problem:**
- Value analysis committees struggle to compare devices/drugs with real-world safety data
- Current process: manual literature reviews, vendor claims, anecdotal experience
- High-stakes decisions (patient safety + liability exposure) with poor information

**What SafetyScore delivers:**
- Device model scorecards: malfunction rates, serious injury rates, recall history
- Peer comparisons: "This pacemaker is 85th percentile for reliability"
- Drug safety by indication + subpopulation
- Procurement recommendations: preferred, acceptable, caution, avoid

**Why you win:**
- MAUDE data is public but unusable without processing
- You build the explainable evidence pack (signal + literature + precedent)
- Hospitals care about defensible decisions, not raw data

**Revenue model:**
- $50k-200k/year per hospital system (based on bed count)
- 5,000 hospitals in US → **$250M-1B TAM**
- GPO partnerships multiply reach

**Data needed:**
- MAUDE (device malfunctions) - FREE
- FAERS (drug adverse events) - FREE
- FDA recalls/enforcement - FREE
- Device-specific: lot/batch clustering, failure mode taxonomy

**MVP Path:**
1. Focus on high-value devices (orthopedic implants, cardiac devices, surgical robots)
2. Build scorecard for 50 common devices
3. Pilot with 3-5 hospitals (free or discounted)
4. Prove procurement impact (avoided recalls, reduced adverse events)
5. Scale via GPO partnerships

**Why this is #1:**
- **Largest TAM** ($5B if you include GPOs, ASCs, clinics)
- **Defensible moat** (processing MAUDE is hard, evidence compilation is harder)
- **Clear ROI** (avoided liability + better patient outcomes)
- **No competition** (no one is doing this well)

---

### 🥈 #2: Regulatory Risk Forecasting

**Product:** RegulatoryAI - Predict FDA actions before they happen

**Problem:**
- Pharma/medtech teams get surprised by warnings, label changes, recalls
- Investors/PE missprice regulatory risk in deals
- Insurers can't model liability exposure accurately

**What RegulatoryAI delivers:**
- "Probability of Regulatory Action" dashboard:
  - Warning letter: 35% (next 90 days)
  - Safety communication: 60% (next 180 days)
  - Label change: 40% (next 365 days)
- Precedent mapping: "This signal pattern historically led to X action in Y days"
- Subpopulation risk: "Highest risk in elderly + diabetics"

**Why you win:**
- Everyone sees FAERS; almost nobody has predictive models
- Precedent mapping requires deep historical analysis
- You can quantify trend inflection before actions manifest

**Revenue model:**
- Pharma regulatory/PV teams: $100k-500k/year per company
- Investors/PE: $50k-150k/year for portfolio monitoring
- Insurers: $200k-1M/year for underwriting models
- **TAM: $2B**

**Data needed:**
- FAERS trends + acceleration
- Historical regulatory actions → signal patterns
- Literature support (mechanism, case reports)
- Precedent database (signal X → action Y in Z days)

**MVP Path:**
1. Build precedent database (100 historical cases: signal → action)
2. Train forecasting model on historical data
3. Pilot with 2-3 pharma companies (high-risk products)
4. Prove value: "We predicted Drugco's warning letter 60 days early"
5. Scale to investors, insurers

---

### 🥉 #3: TortSignal (Original - Plaintiff Firms)

**Product:** TortSignal - Early-warning system for mass torts

**Problem:**
- Plaintiff firms miss emerging torts or enter too late
- Manual monitoring of FAERS/MAUDE/court filings is unsustainable
- No systematic way to assess litigation viability

**What TortSignal delivers:**
- Watchlist of emerging tort candidates (18-36 months pre-MDL)
- Automatic false-positive filtering (terminated MDLs, weak causation)
- Evidence dossiers (FAERS trends + literature + UniCourt cases)
- Velocity tracking (case filings accelerating or decelerating)

**Why you win:**
- Monitoring system vs one-off searches (database = product)
- Cross-check against terminated MDLs (FARXIGA lesson)
- Causation strength assessment (literature + mechanism)

**Revenue model:**
- $10k-50k/year per plaintiff firm
- 500 tort firms in US → **$5M-25M TAM**

**Data needed:**
- FAERS/MAUDE trends
- UniCourt case discovery (AI browser automation: $300/month)
- PACER MDL status ($50-100/month)
- Literature evidence (PubMed)

**MVP Path:**
1. Prove signal detection (FARXIGA-like analysis)
2. Build MDL cross-check (avoid false positives)
3. Pilot with 3-5 firms
4. Prove value: "Found viable tort 24 months before competitors"
5. Scale via word-of-mouth (tight-knit industry)

**Why this is #3 (not #1):**
- Smaller TAM ($500M vs $5B)
- Harder sales (plaintiff firms are skeptical, slow adopters)
- Regulatory risk (if you're wrong, they lose money)
- Still valuable as proof-of-concept for Safety Intelligence Graph

---

## Other High-Leverage Opportunities

### 4) M&A Diligence: "Safety Debt" Audit
- **Buyers:** PE, corporate dev, banks
- **Problem:** Safety liabilities mispriced in deals
- **Revenue:** $50k-200k per deal (episodic, not recurring)
- **TAM:** $1B

### 5) Defense-Side Litigation Prep
- **Buyers:** Pharma/medtech legal, outside counsel
- **Problem:** Can't see "where litigation is going" early enough
- **Revenue:** $100k-500k/year per manufacturer
- **TAM:** $800M

### 6) Competitive Intelligence (Pharma Strategy)
- **Buyers:** Product marketing, BD, strategy
- **Problem:** Competitor safety trajectory ignored until headlines
- **Revenue:** $50k-200k/year per company
- **TAM:** $500M

---

## Recommended Launch Sequence

### Phase 1: Prove the Safety Intelligence Graph (Q1-Q2 2026)

**Build the core once:**
1. ✅ Database schema (001_core.sql + 003_safety_intelligence_extensions.sql)
2. ✅ FDA FAERS connector (free, unlimited)
3. ✅ FDA MAUDE connector (free, unlimited)
4. 🔨 UniCourt browser AI agent ($300/month)
5. 🔨 PACER connector ($50-100/month)
6. 🔨 PubMed connector (free)
7. 🔨 OpenFDA enforcement/recalls (free)

**Deliverable:** Monitoring pipeline that runs daily, populates Safety Intelligence Graph

---

### Phase 2: Launch TortSignal MVP (Q2 2026)

**Why start here:**
- You already have mental model + domain expertise
- Smallest MVP (just litigation layer on top of graph)
- Proof-of-concept for Safety Intelligence Graph
- Revenue to fund other products

**Build:**
- TortSignal dashboard (Streamlit app exists)
- Litigation viability scoring
- MDL status cross-check (FARXIGA lesson)
- Evidence dossiers

**Go-to-market:**
- 3-5 pilot firms (free or discounted)
- Prove value: "We found X tort 18 months before competitors"
- Word-of-mouth in tight-knit tort community

**Revenue target:** $50k-100k ARR (5-10 firms @ $10k/year)

---

### Phase 3: Launch SafetyScore (Hospital Procurement) (Q3-Q4 2026)

**Why this is the big swing:**
- **Largest TAM** ($5B)
- **Defensible moat** (MAUDE processing is hard)
- **Clear ROI** (avoided liability + better outcomes)

**Build:**
- Device scorecards (50 high-value devices)
- Procurement recommendation engine
- Alternative product suggestions
- Peer comparisons (percentile ranks)

**Go-to-market:**
- 3-5 hospital pilot (free for 6 months)
- Prove procurement impact (case studies)
- GPO partnerships for scale

**Revenue target:** $500k-1M ARR (10-20 hospitals @ $50k/year)

---

### Phase 4: Launch RegulatoryAI (Pharma/Investors) (2027)

**Why later:**
- Requires precedent database (takes time to build)
- Forecasting model needs training data
- Higher bar for accuracy (enterprise sales)

**Build:**
- Precedent database (signal → action patterns)
- Forecasting model (probability of regulatory action)
- Investor/PE dashboard (portfolio monitoring)

**Revenue target:** $1M-3M ARR

---

## The Big Question: Which First?

### TortSignal (MVP) vs SafetyScore (Big Swing)

| Dimension | TortSignal | SafetyScore |
|-----------|-----------|-------------|
| **TAM** | $500M | $5B |
| **Moat** | Moderate | Strong |
| **Time to Revenue** | 3-6 months | 6-12 months |
| **Sales Cycle** | Long (skeptical buyers) | Medium (clear ROI) |
| **Your Expertise** | High | Medium |
| **MVP Complexity** | Low | Medium |
| **Risk** | Low (small checks) | Medium (hospital sales) |

### Recommended: **Parallel Path**

**Q1-Q2 2026:**
1. Build Safety Intelligence Graph (core data platform)
2. Launch TortSignal MVP (fast revenue, proof-of-concept)
3. Start SafetyScore development (bigger prize)

**Q3-Q4 2026:**
1. TortSignal live with 10+ paying firms
2. SafetyScore pilot with 5 hospitals
3. Use TortSignal revenue to fund SafetyScore scale

**2027:**
1. SafetyScore becomes primary revenue driver
2. Launch RegulatoryAI for pharma/investors
3. TortSignal becomes "enterprise tier" for large firms

---

## Database Strategy: Multi-Tenant from Day 1

Your schema already has `orgs` and `users` tables. Use them!

**Architecture:**
```sql
-- TortSignal customer
INSERT INTO orgs (name) VALUES ('Smith & Associates (Plaintiff Firm)');

-- SafetyScore customer
INSERT INTO orgs (name) VALUES ('Mass General Hospital');

-- RegulatoryAI customer
INSERT INTO orgs (name) VALUES ('Pfizer Regulatory Affairs');

-- Same data, different views
-- TortSignal sees: v_tortsignal_candidates
-- SafetyScore sees: v_device_safety_scorecards
-- RegulatoryAI sees: v_regulatory_risk_dashboard
```

**Why this matters:**
- Build the graph once
- Deploy to multiple markets
- Marginal cost per new product is LOW

---

## Cost Structure (MVP)

**Data acquisition:**
- FDA FAERS: FREE
- FDA MAUDE: FREE
- OpenFDA enforcement: FREE
- PubMed: FREE
- Semantic Scholar: FREE
- UniCourt Premium: $300/month (AI browser automation)
- PACER: $50-100/month
- **Total: ~$400/month**

**Infrastructure:**
- Cloud database (Render): $25-50/month
- Hosting (Render/Heroku): $50-100/month
- AI costs (Claude API for browser automation): $100-200/month
- **Total: ~$200-350/month**

**Total MVP cost: $600-750/month**

**First customer ROI:**
- TortSignal customer @ $10k/year = 16 months to cover infrastructure
- SafetyScore customer @ $50k/year = 2 months to profitability

---

## The Proof Point

From your own words:
> "The proof is identifying a potential tort in a way that couldn't be done with just a web search or even a deep search. Then we have a product."

**Expand that:**
- Identifying a tort plaintiff firms couldn't find → TortSignal
- Identifying a device risk hospitals couldn't assess → SafetyScore
- Identifying a regulatory action investors couldn't predict → RegulatoryAI

**Same proof. Different markets. 100x larger TAM.**

---

## Next Steps

1. **This week:** Deploy cloud database with 003_safety_intelligence_extensions.sql
2. **This month:** Build discovery pipeline (FAERS + MAUDE + UniCourt AI agent)
3. **Next 90 days:** Launch TortSignal MVP with 3-5 pilot firms
4. **Next 180 days:** Start SafetyScore development, hospital pilots

**The Safety Intelligence Graph you're building this week powers all of it.**

Want to start with cloud deployment + discovery pipeline?
