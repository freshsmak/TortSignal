# EDE FRONTEND DESIGN BRIEF
## Epidemiological Discovery Engine - Dashboard UI/UX Specification

**Version:** 1.0
**Date:** January 25, 2026
**Author:** Chase Doyle, Managing Director, AUDITLab
**Purpose:** Frontend design specification for EDE automation platform

---

## 1. PRODUCT OVERVIEW

### What is EDE?

**Epidemiological Discovery Engine (EDE)** is an automated system that identifies mass tort litigation opportunities 2-4 years before they become widely known. It scans regulatory actions, epidemiological trends, and scientific literature to detect chemical-disease associations that meet legal thresholds but haven't been litigated yet.

**Core Value Proposition:**
- "See the future of mass tort litigation before your competitors"
- Discover $100M-$1B+ opportunities with 2-4 year lead time
- Systematically scan 1000+ chemicals × 100+ diseases = 100,000 potential signals
- Filter to 1-3 validated discoveries per year

### How It Works (Backend Engine):

1. **Daily Regulatory Scanner** → Monitors EU ECHA, IARC, FDA, NIOSH for new bans/warnings
2. **Weekly Epidemiology Scanner** → Analyzes SEER cancer data for demographic anomalies
3. **Automated Scoring** → Bradford Hill (causation 0-100) + Litigation (business viability 0-100)
4. **Signal Filtering** → Keeps only signals with BH ≥70, Litigation ≥80, and zero active lawsuits
5. **Discovery Dossier Generation** → Produces 15-30 page reports for validated signals

**User Goal:** Monitor pipeline of potential tort discoveries, validate promising signals, and decide which to pursue.

---

## 2. USER PERSONAS

### Primary User: "The Tort Entrepreneur"
- **Who:** Attorney or investor monitoring tort opportunities
- **Goals:**
  - Find first-mover opportunities before competition
  - Assess which signals are worth investing in ($15K-$65K validation costs)
  - Track multiple signals through validation stages
- **Pain Points:**
  - Information overload (too many false positives)
  - Missing critical signals (competition files first)
  - Can't assess causation strength without PhD in epidemiology
- **Technical Skill:** Medium (comfortable with web dashboards, not a developer)

### Secondary User: "The Expert Validator"
- **Who:** Medical doctor or epidemiologist hired to validate signals
- **Goals:**
  - Review Bradford Hill evidence quickly
  - Provide professional opinion on causation
  - Download dossiers for detailed analysis
- **Pain Points:**
  - Needs to see mechanistic evidence (PubMed papers)
  - Wants raw data (SEER trends, effect sizes)
- **Technical Skill:** High (can read scientific notation, understands statistics)

### Tertiary User: "The Investor/CEO"
- **Who:** Executive deciding whether to fund tort development
- **Goals:**
  - See high-level portfolio view (all discoveries at a glance)
  - Understand ROI potential (market size, settlement estimates)
  - Make go/no-go decisions quickly
- **Pain Points:**
  - Doesn't understand scientific jargon
  - Needs executive summary, not 30-page dossier
- **Technical Skill:** Low (wants simple, visual dashboards)

---

## 3. KEY USER FLOWS

### Flow 1: Daily Monitoring (Primary Use Case)
1. User logs in → Sees **Dashboard** with new signals flagged
2. Clicks on signal → Views **Signal Detail Page** (Bradford Hill breakdown, litigation score, evidence summary)
3. Decides:
   - **"Interesting"** → Add to Watch List
   - **"Pursue"** → Start validation process (commission expert memos)
   - **"Reject"** → Archive signal

### Flow 2: Signal Validation
1. User filters signals by "Ready to Validate" (BH ≥85, Lit ≥90)
2. Reviews top 3-5 signals
3. For each signal:
   - Downloads **Discovery Dossier** (PDF)
   - Shares with attorney/doctor for expert review
   - Marks signal as "In Validation" (status change)
4. Receives expert feedback → Updates signal status:
   - **"Validated"** → Proceed to field testing
   - **"Rejected"** → Archive with reason

### Flow 3: Portfolio Overview (Executive Dashboard)
1. CEO logs in → Sees **Portfolio View**
2. Tiles showing:
   - "3 Validated Discoveries" (TiO2, Glyoxylic Acid, Quats)
   - "$17B-$48B Combined Market Size"
   - "0 Active Litigation Across All 3"
3. Clicks tile → Jumps to individual signal detail
4. Exports portfolio summary → PDF for board meeting

### Flow 4: Historical Validation (Trust Building)
1. New user skeptical of EDE → Clicks **"How We Know This Works"**
2. Views **Validation Page** with case studies:
   - Hair Relaxer backtest (2019 discovery → 2022 NIH → 2023 MDL)
   - PFAS firefighter validation
   - Bradford Hill scores for historical torts (Asbestos, Tobacco, Roundup)
3. User convinced → Returns to dashboard to explore signals

---

## 4. PAGES/VIEWS NEEDED

### 4.1 Dashboard (Home Page)

**Purpose:** At-a-glance view of signal pipeline

**Key Sections:**

**A) Signal Pipeline (Funnel Visual)**
```
DETECTED (BH 70-84)      →  15 signals  [View All]
READY (BH 85+, Lit 90+)  →  3 signals   [View All] ← HIGHLIGHT (action needed)
VALIDATED (Expert OK)    →  2 signals   [View All]
FIELD TESTED (Survey OK) →  1 signal    [View All]
ARCHIVED                 →  47 signals  [View All]
```

**B) New Alerts (Last 7 Days)**
- "1 new regulatory action detected: EU banned Chemical X" (link to signal)
- "2 signals upgraded to 'Ready to Validate'" (links)
- "1 signal archived: Litigation detected in PACER" (link)

**C) Watch List (User's Starred Signals)**
- Table with 3-5 signals user is actively monitoring
- Columns: Signal Name, Bradford Hill, Litigation Score, Status, Last Updated, Actions
- Sortable by score, date, status

**D) Quick Stats (Top Cards)**
```
[Card 1]                [Card 2]                [Card 3]
Total Signals:          Validated Discoveries:  Est. Market Value:
68                      3                       $17B-$48B
(15 new this month)     (TiO2, Glyoxylic, Quats) (combined portfolio)
```

**Design Notes:**
- Clean, modern dashboard (think Stripe/Linear/Notion aesthetic)
- Dark mode optional (attorneys work late nights)
- Responsive (mobile-friendly for checking signals on-the-go)

---

### 4.2 Signal Detail Page

**Purpose:** Deep dive into single signal with all evidence

**URL:** `/signals/{signal_id}` (e.g., `/signals/HAZ-2026-001`)

**Hero Section:**
```
TITANIUM DIOXIDE → INFLAMMATORY BOWEL DISEASE
Status: READY TO VALIDATE
First Detected: January 24, 2026
Last Updated: January 25, 2026

[Download Dossier (PDF)]  [Add to Watch List]  [Start Validation]  [Archive]
```

**Tabs:**

**Tab 1: Overview (Default)**
- **Summary:** 3-4 sentences explaining the signal
- **The Regulatory Hook:** "EU banned TiO2 in food (May 2021), US still allows"
- **The Science:** "22-72% IBD increase in young adults, 78 mechanistic papers on inflammasome activation"
- **The Opportunity:** "50K-100K addressable plaintiffs, $15B-$40B market, $111B defendant revenue"

**Tab 2: Bradford Hill Evidence (Score: 94/100)**
Visual breakdown of 9 criteria:
```
Strength            [████████░░] 9/10  →  22-72% IBD increase (RR 1.2-1.7)
Consistency         [████████░░] 8/10  →  4 independent studies, 75% positive
Specificity         [██████░░░░] 6/10  →  TiO2 linked to 3 diseases (IBD, cancer, genotox)
Temporality         [██████████] 10/10 →  Exposure 1990-2005, disease 2010-2025 (latency 10-30y)
Biological Gradient [███████░░░] 7/10  →  Children (highest exposure) have fastest IBD growth
Plausibility        [█████████░] 9/10  →  78 mechanistic papers, 9 animal models (NLRP3 inflammasome)
Coherence           [█████████░] 9/10  →  7 review articles, fits IBD etiology
Experiment          [████████░░] 8/10  →  EU ban = natural experiment (4 years elapsed)
Analogy             [███████░░░] 7/10  →  Other nanoparticles cause gut inflammation

COMPOSITE SCORE: 94/100 (STRONG - Ready for expert validation)
```

**Tab 3: Litigation Analysis (Score: 106/100)**
```
Causal Strength      [█████████░] 9/10  →  Bradford Hill 94/100 (Daubert admissible)
Population Size      [███████░░░] 7/10  →  15,000 addressable plaintiffs (MDL-scale)
Defendant Solvency   [██████████] 10/10 →  $111B revenue (Mars, Mondelez, Hershey, General Mills)
Preventability       [██████████] 10/10 →  EU ban ignored, no warning labels (failure to warn)
Social Justice       [██████████] 10/10 →  Children targeted by candy marketing (jury sympathy)
Severity             [█████████░] 9/10  →  $800K-$1.5M per plaintiff (lifelong disease, surgeries)
Novelty              [██████████] 10/10 →  ZERO lawsuits filed, ZERO media coverage (first-mover)

COMPOSITE SCORE: 106/100 (EXCEPTIONAL - Pursue immediately)
```

**Tab 4: Evidence Library**
- **Regulatory Actions:** EU ban (May 2021), EFSA review (2021)
- **Epidemiological Data:** CDC IBD trends (22-72% increase), 100K+ pediatric cases
- **Mechanistic Papers:** Link to 78 PubMed papers (sortable by citations, date)
- **Media Coverage:** 0 mainstream articles (NYT, WSJ, WaPo) = pre-hype
- **Litigation Status:** 0 PACER cases, 0 MDLs, 0 plaintiff advertising

**Tab 5: Validation History**
Timeline showing:
```
Jan 24, 2026  →  Signal detected (Regulatory Scanner flagged EU ban)
Jan 24, 2026  →  Bradford Hill scored: 94/100
Jan 24, 2026  →  Litigation scored: 106/100
Jan 24, 2026  →  Status: READY TO VALIDATE
[Future]      →  Expert validation commissioned ($15K)
[Future]      →  Attorney memo received (APPROVED)
[Future]      →  Doctor memo received (APPROVED)
[Future]      →  Status upgraded: VALIDATED
```

**Design Notes:**
- Tabs vs. single-page scroll (test which is better UX)
- Lots of data visualization (bar charts for scores, timelines for validation)
- Downloadable dossier prominent (primary CTA)

---

### 4.3 Signal List (Filtered Views)

**Purpose:** Browse/search all signals in a specific stage

**URL:** `/signals?status=ready` or `/signals?status=validated`

**Filters (Left Sidebar):**
- **Status:** Detected / Ready / Validated / Field-Tested / Archived
- **Bradford Hill Score:** 70-84 / 85-94 / 95-100
- **Litigation Score:** 80-89 / 90-99 / 100+
- **Methodology:** Hazard-First / Epidemiology-First
- **Disease Type:** Cancer / Autoimmune / Neurological / Cardiovascular / Other
- **Defendant Industry:** Food / Pharma / Consumer Products / Chemicals / Occupational
- **Date Range:** Last 7 days / Last 30 days / Last 90 days / All time

**Table View (Right Side):**
Columns:
- **Signal Name** (e.g., "TiO2 → IBD")
- **Bradford Hill Score** (color-coded: green >85, yellow 70-84, red <70)
- **Litigation Score** (color-coded)
- **Status** (badge: "Ready", "Validated", etc.)
- **Market Size** (e.g., "$15B-$40B")
- **Date Detected**
- **Actions** (View / Download / Archive)

**Sorting:**
- Default: Highest Litigation Score
- Options: BH Score, Market Size, Date Detected

**Design Notes:**
- Think "Airtable" or "Notion database" aesthetic
- Fast filtering (instant results, no page reload)
- Bulk actions (select multiple signals → Archive all)

---

### 4.4 Portfolio View (Executive Dashboard)

**Purpose:** High-level summary for CEO/investors

**URL:** `/portfolio`

**Hero Metrics:**
```
[Large Cards]
Validated Discoveries:  3
Combined Market Size:   $17.1B - $48.3B
Active Litigation:      0 (across all 3)
Avg. Bradford Hill:     86/100
```

**Discovery Tiles (3 cards side-by-side):**

**Tile 1: TiO2 → IBD**
```
Bradford Hill: 94/100 | Litigation: 106/100
Market Size: $15B-$40B
Addressable Plaintiffs: 15,000
Status: VALIDATED
Next Step: Field testing ($12K survey)
[View Details] [Download Dossier]
```

**Tile 2: Glyoxylic Acid → Kidney Injury**
```
Bradford Hill: 85/100 | Litigation: 72/100
Market Size: $100M-$300M
Addressable Plaintiffs: 500-2,000
Status: VALIDATED
Next Step: Expert validation ($10K)
[View Details] [Download Dossier]
```

**Tile 3: Quats → Lung Disease**
```
Bradford Hill: 78/100 | Litigation: 88/100
Market Size: $2B-$8B
Addressable Plaintiffs: 5K-25K
Status: READY TO VALIDATE
Next Step: Strengthen causation (monitor for new research)
[View Details] [Download Dossier]
```

**Actions:**
- [Export Portfolio Summary (PDF)] → One-page overview for board meeting
- [Compare Discoveries] → Side-by-side table

**Design Notes:**
- Big, bold numbers (easy to read in presentation)
- Visual hierarchy: Market size most prominent
- Print-friendly (CEO will screenshot for emails)

---

### 4.5 Validation Case Studies (Trust Building)

**Purpose:** Prove EDE methodology works

**URL:** `/validation`

**Hero:**
```
How We Know This Works
EDE has been validated with historical backtests and live discoveries.
Here's the proof.
```

**Case Study Cards:**

**Card 1: Hair Relaxer Backtest (Proof of 45-Month Lead Time)**
```
The Test:
- Used only 2010-2018 data (what we would've known in Jan 2019)
- EDE detected: Uterine cancer 40% higher in Black women
- Generated hypothesis: Hair straighteners → endocrine disruption

The Validation:
- Oct 2022: NIH Sister Study published (45 months later)
- Oct 2022: First lawsuits filed (7 days after publication)
- 2025: MDL 3060 with 10,948 cases

RESULT: 45-month lead time proven

[View Full Analysis]
```

**Card 2: PFAS Firefighter Validation**
**Card 3: TiO2 → IBD (Live Discovery)**
**Card 4: Historical Bradford Hill Scores**

Table comparing EDE scores to established torts:
```
Tort                   | Bradford Hill (EDE) | Outcome
-----------------------|---------------------|------------------
Asbestos → Mesothelioma| 98/100             | $30B settlements
Tobacco → Lung Cancer  | 99/100             | $206B MSA
Roundup → NHL          | 91/100             | $10B settlements
Talc → Ovarian Cancer  | 88/100             | $8B settlements
Hair Relaxer → Uterine | 85/100             | 10,948 cases (ongoing)
-----------------------|---------------------|------------------
TiO2 → IBD (EDE)       | 94/100             | PRE-LITIGATION ✅
Microplastics → Fert.  | 98/100             | PRE-LITIGATION ✅
UPF → Colorectal       | 94/100             | PRE-LITIGATION ✅
```

**Design Notes:**
- Storytelling format (beginning → middle → end)
- Timelines visual (show 45-month gap clearly)
- Social proof (EDE scores match historical mega-torts)

---

## 5. DESIGN PRINCIPLES

### 5.1 Visual Style

**Aesthetic:**
- Modern SaaS dashboard (Stripe, Linear, Notion inspiration)
- Clean, minimal, lots of white space
- Data-first (charts/graphs > decorative elements)

**Color Palette:**
```
Primary:    #2563EB (Blue 600) - CTAs, links
Success:    #10B981 (Green 500) - High scores (BH >85)
Warning:    #F59E0B (Amber 500) - Medium scores (BH 70-84)
Danger:     #EF4444 (Red 500) - Low scores, alerts
Neutral:    #6B7280 (Gray 500) - Text, borders
Background: #FFFFFF (White) / #111827 (Dark mode)
```

**Typography:**
```
Headings:   Inter, -apple-system, sans-serif (700 weight)
Body:       Inter, -apple-system, sans-serif (400 weight)
Numbers:    JetBrains Mono, monospace (data tables, scores)
```

**Scoring Visualization:**
- **90-100:** Green badge/bar (STRONG)
- **70-89:** Yellow badge/bar (MODERATE)
- **<70:** Red badge/bar (WEAK)

### 5.2 Information Hierarchy

**Most Important (Always Visible):**
1. New signals requiring action ("Ready to Validate" count)
2. Bradford Hill + Litigation scores (color-coded)
3. Pre-litigation confirmation (✅ 0 lawsuits filed)

**Secondary (One click away):**
1. Evidence library (PubMed papers, regulatory docs)
2. Market size estimates
3. Validation history timeline

**Tertiary (Two clicks / downloadable):**
1. Full 30-page discovery dossier
2. Raw SEER/CDC data tables
3. Expert validation memos

### 5.3 Mobile Responsiveness

**Critical for mobile:**
- Dashboard (check new signals on-the-go)
- Signal detail overview tab (quick review)
- Download dossier button (send to email for later)

**Desktop-only:**
- Full evidence library (too much data for mobile)
- Portfolio comparison tables
- Detailed charts

### 5.4 Performance

**Speed Requirements:**
- Dashboard loads in <1 second
- Signal filtering instant (<100ms)
- Dossier PDF generation <5 seconds

**Data Freshness:**
- Dashboard auto-refreshes every 5 minutes (when new signals detected)
- User sees "Last updated: 3 minutes ago" timestamp

---

## 6. TECHNICAL CONSTRAINTS

### 6.1 Data from Backend API

The frontend will receive JSON from backend API endpoints:

**GET /api/signals** (all signals)
```json
[
  {
    "signal_id": "HAZ-2026-001",
    "name": "Titanium Dioxide → Inflammatory Bowel Disease",
    "chemical": "Titanium Dioxide",
    "disease": "Inflammatory Bowel Disease",
    "bradford_hill_score": 94,
    "litigation_score": 106,
    "status": "READY_TO_VALIDATE",
    "date_detected": "2026-01-24",
    "market_size_min": 15000000000,
    "market_size_max": 40000000000,
    "methodology": "HAZARD_FIRST"
  },
  {...}
]
```

**GET /api/signals/{signal_id}** (detailed signal)
```json
{
  "signal_id": "HAZ-2026-001",
  "name": "Titanium Dioxide → Inflammatory Bowel Disease",
  "bradford_hill": {
    "composite_score": 94,
    "criteria": {
      "strength": {"score": 9, "weighted": 13.5, "evidence": "..."},
      "consistency": {"score": 8, "weighted": 9.6, "evidence": "..."},
      ...
    }
  },
  "litigation": {
    "composite_score": 106,
    "factors": {
      "causal_strength": {"score": 9, "weighted": 18.0},
      "population_size": {"score": 7, "weighted": 10.5},
      ...
    }
  },
  "evidence": {
    "regulatory_actions": [...],
    "pubmed_papers": [...],
    "epidemiology_data": {...},
    "litigation_status": {"pacer_cases": 0, "mdl_status": "NONE"}
  }
}
```

**GET /api/portfolio** (executive summary)
```json
{
  "validated_discoveries": 3,
  "total_market_size_min": 17100000000,
  "total_market_size_max": 48300000000,
  "avg_bradford_hill": 86,
  "discoveries": [
    {"signal_id": "HAZ-2026-001", "name": "TiO2 → IBD", ...},
    ...
  ]
}
```

### 6.2 User Actions (Frontend → Backend)

**POST /api/signals/{signal_id}/actions**
- `add_to_watchlist`
- `start_validation` (changes status to IN_VALIDATION)
- `archive` (with reason: "litigation_exists", "expert_rejected", etc.)
- `download_dossier` (triggers PDF generation)

**POST /api/signals/{signal_id}/notes**
- User can add notes: "Contacted attorney John Smith, he's interested"

### 6.3 Authentication (Simple for MVP)

- Basic username/password login
- Single user account (Chase Doyle)
- Future: Multi-user with roles (Admin, Viewer, Expert)

---

## 7. WIREFRAME DESCRIPTIONS

### 7.1 Dashboard Wireframe

```
+--------------------------------------------------+
|  EDE Logo    [Dashboard] [Signals] [Portfolio]  |  ← Top Nav
+--------------------------------------------------+
|                                                  |
|  SIGNAL PIPELINE                                 |
|  [=====>] Detected (15)                          |  ← Funnel visual
|    [====>] Ready (3) ← ACTION NEEDED             |
|      [==>] Validated (2)                         |
|        [>] Field Tested (1)                      |
|                                                  |
|  NEW ALERTS (Last 7 Days)                        |
|  🔴 1 new regulatory action: EU banned Chemical X |
|  🟢 2 signals upgraded to "Ready to Validate"    |
|                                                  |
|  WATCH LIST                                      |
|  +------------+-------+------+--------+--------+ |
|  | Signal     | BH    | Lit  | Status | Actions| |
|  +------------+-------+------+--------+--------+ |
|  | TiO2 → IBD | 94    | 106  | Ready  | [View] | |
|  | Quats → COPD| 78   | 88   | Ready  | [View] | |
|  +------------+-------+------+--------+--------+ |
|                                                  |
+--------------------------------------------------+
```

### 7.2 Signal Detail Wireframe

```
+--------------------------------------------------+
|  ← Back to Dashboard                             |
+--------------------------------------------------+
|  TITANIUM DIOXIDE → IBD                          |
|  Status: READY TO VALIDATE                       |
|                                                  |
|  [Download Dossier] [Add to Watch] [Archive]     |
+--------------------------------------------------+
|  [Overview] [Bradford Hill] [Litigation] [Evidence] [History]  ← Tabs
+--------------------------------------------------+
|                                                  |
|  SUMMARY                                         |
|  IBD increased 22-72% in young adults. TiO2     |
|  (E171) banned by EU but allowed in US. 78      |
|  mechanistic papers show inflammasome activation.|
|                                                  |
|  THE REGULATORY HOOK                             |
|  EU banned TiO2 in food (May 2021, effective    |
|  Aug 2022). Basis: "Cannot rule out genotoxicity"|
|                                                  |
|  THE OPPORTUNITY                                 |
|  • Population: 15,000 addressable plaintiffs     |
|  • Market: $15B-$40B                            |
|  • Defendants: $111B revenue (Mars, Mondelez)   |
|  • Competition: 0 lawsuits filed                |
|                                                  |
+--------------------------------------------------+
```

### 7.3 Portfolio View Wireframe

```
+--------------------------------------------------+
|  PORTFOLIO OVERVIEW                              |
+--------------------------------------------------+
|  [3] Validated Discoveries                       |
|  [$17B-$48B] Combined Market Size               |
|  [0] Active Litigation                           |
+--------------------------------------------------+
|                                                  |
|  +---------------+  +---------------+  +--------+|
|  | TiO2 → IBD    |  | Glyoxylic Acid|  | Quats  ||
|  | BH: 94        |  | BH: 85        |  | BH: 78 ||
|  | Lit: 106      |  | Lit: 72       |  | Lit: 88||
|  | $15B-$40B     |  | $100M-$300M   |  | $2B-$8B||
|  | [View Details]|  | [View Details]|  | [View] ||
|  +---------------+  +---------------+  +--------+|
|                                                  |
|  [Export Portfolio PDF]                          |
+--------------------------------------------------+
```

---

## 8. DESIGN INSPIRATION / REFERENCES

**Dashboards to emulate:**
1. **Stripe Dashboard** - Clean metrics, card-based layout, excellent data viz
2. **Linear** - Modern aesthetic, fast performance, great filtering
3. **Notion Databases** - Flexible views (table, board, timeline), powerful filtering
4. **Airtable** - Rich data tables with inline editing
5. **Mixpanel** - Funnel visualizations (for signal pipeline)

**Color-coded scoring inspiration:**
- **GitHub PR checks** - Green ✅ pass, yellow ⚠️ warnings, red ❌ fail
- **Credit scores** - Color gradient (red → yellow → green)

**Evidence tabs:**
- **Wikipedia citations** - Numbered references, expandable details
- **Court dockets (PACER)** - Document lists with download buttons

---

## 9. DELIVERABLES REQUESTED

From the design LLM, please provide:

### Phase 1: Wireframes (Lo-Fi)
- [ ] Dashboard wireframe (desktop)
- [ ] Signal Detail wireframe (desktop)
- [ ] Portfolio View wireframe (desktop)
- [ ] Mobile responsive wireframes (dashboard + signal detail)

### Phase 2: High-Fidelity Mockups
- [ ] Dashboard mockup (with real data from TiO2, Glyoxylic, Quats)
- [ ] Signal Detail mockup (TiO2 → IBD as example)
- [ ] Portfolio View mockup
- [ ] Component library (buttons, cards, badges, score bars)

### Phase 3: HTML/CSS (Production-Ready)
- [ ] Responsive HTML templates for all pages
- [ ] CSS with Tailwind (or vanilla CSS if preferred)
- [ ] JavaScript for:
  - Tab switching (Signal Detail page)
  - Filtering (Signal List page)
  - Sorting tables
  - Dashboard auto-refresh
- [ ] Dark mode toggle

### Phase 4: Design System Documentation
- [ ] Color palette (hex codes)
- [ ] Typography scale
- [ ] Component specs (button sizes, card padding, etc.)
- [ ] Spacing system (4px/8px/16px grid)

---

## 10. TECHNICAL STACK PREFERENCES

**Frontend Framework:**
- **Preferred:** React (Next.js) or Vue.js
- **Alternative:** Vanilla HTML/CSS/JS (easier handoff to backend)

**CSS Framework:**
- **Preferred:** Tailwind CSS (utility-first, fast iteration)
- **Alternative:** Vanilla CSS with BEM naming

**Charts/Data Viz:**
- **Preferred:** Chart.js or Recharts (React) for bar charts, timelines
- **Alternative:** Simple CSS progress bars for scores

**Icons:**
- **Preferred:** Heroicons (MIT license, matches Tailwind aesthetic)
- **Alternative:** Lucide icons

**PDF Generation (Backend):**
- Backend will handle PDF generation (Python + ReportLab or WeasyPrint)
- Frontend just needs [Download PDF] button → triggers GET /api/signals/{id}/dossier.pdf

---

## 11. SUCCESS CRITERIA

**Design is successful if:**
1. ✅ User can identify "action needed" signals in <10 seconds (dashboard scan)
2. ✅ User understands what a signal is and why it matters in <30 seconds (signal detail overview)
3. ✅ User can filter 100 signals to find top 3 in <60 seconds (signal list filtering)
4. ✅ CEO can screenshot portfolio view and email to investor without explanation (self-evident)
5. ✅ Design instills trust (professional, data-driven, not "startup MVP ugly")

**Design has failed if:**
- User confused about what EDE does
- Too much information on one screen (cognitive overload)
- Scores not color-coded (user has to interpret 94/100 = good?)
- Mobile unusable (attorneys check on phones frequently)

---

## 12. TIMELINE & PRIORITIES

**Priority 1 (Must Have for MVP):**
- Dashboard (home page)
- Signal Detail page (Overview + Bradford Hill + Litigation tabs)
- Download Dossier button (triggers PDF generation)

**Priority 2 (Important but not blocking):**
- Signal List (filtered views)
- Portfolio View (executive dashboard)
- Watch List functionality

**Priority 3 (Nice to Have):**
- Validation case studies page
- Dark mode
- Mobile optimization
- User notes on signals

---

## 13. QUESTIONS FOR DESIGN LLM

Before starting, please clarify:

1. **Framework preference?** React/Vue or vanilla HTML/CSS/JS?
2. **Design tool?** Figma mockups or direct-to-code?
3. **Iteration process?** How many rounds of feedback expected?
4. **Accessibility requirements?** WCAG 2.1 AA compliance needed?
5. **Browser support?** Modern browsers only (Chrome, Firefox, Safari) or IE11?

---

## APPENDIX: SAMPLE DATA FOR MOCKUPS

Use this real data for high-fidelity mockups:

### Signal 1: TiO2 → IBD
- Bradford Hill: 94/100
- Litigation: 106/100
- Status: READY_TO_VALIDATE
- Market Size: $15B-$40B
- Addressable Plaintiffs: 15,000
- Defendants: Mars ($45B), Mondelez ($35B), Hershey ($11B), General Mills ($20B)

### Signal 2: Glyoxylic Acid → Kidney Injury
- Bradford Hill: 85/100
- Litigation: 72/100
- Status: VALIDATED
- Market Size: $100M-$300M
- Addressable Plaintiffs: 500-2,000
- Defendants: L'Oréal, Brazilian Blowout

### Signal 3: Quats → Lung Disease
- Bradford Hill: 78/100
- Litigation: 88/100
- Status: READY_TO_VALIDATE
- Market Size: $2B-$8B
- Addressable Plaintiffs: 5,000-25,000
- Defendants: Clorox, Lysol (Reckitt), Ecolab

---

**End of Design Brief**

**Contact:** Chase Doyle, Managing Director, AUDITLab
**Questions?** Tag in design review comments

**Next Step:** Design LLM creates wireframes → Review → Mockups → HTML/CSS → Handoff to backend engineer (Claude)
