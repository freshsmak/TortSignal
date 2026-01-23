# Bloomberg-Style Product Roadmap

## Vision

Transform AUDITSignal from a signal detection tool into a **Bloomberg Terminal for Product Liability Intelligence** - where the moat is not the data, but the workflow.

## Why Bloomberg Features = Salable Product

**Key Insight**: Raw data is a commodity. **Workflow** is the moat.

Bloomberg Terminal costs $25k/year not because of the data (Reuters, S&P have the same), but because of:
1. Custom watchlists
2. Real-time alerts
3. Comparable analysis
4. Timeline visualization
5. Export & sharing

We can build the exact same for litigation intelligence.

---

## Core Features

### 1. Custom Watchlists

**Problem**: Plaintiff firms focus on specific areas (medical devices not drugs; cardiovascular not oncology)

**Solution**: User-defined filtered watchlists

```
My Watchlists:
- "Cardiovascular Drugs" (drug_class=cardiovascular, score≥60)
- "Medical Devices" (product_type=device, SAE=disability|hospitalization)
- "Tier 1 Opportunities" (score≥80, litigation_cases=0)
- "Monitoring" (score 40-59, recently_updated)
```

**Implementation**:
- Sidebar: "Default Watchlist" | "My Watchlists +"
- Click "+" → Create watchlist with custom filters
- Each watchlist shows count + new signals since last view
- Filters: drug_class, SAE type, score range, litigation status, date range

**Database Schema**:
```sql
CREATE TABLE user_watchlists (
    watchlist_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    name VARCHAR(255),
    filters JSONB,  -- {score_min: 60, drug_class: "cardiovascular"}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE watchlist_items (
    watchlist_id INTEGER REFERENCES user_watchlists(watchlist_id),
    candidate_id INTEGER REFERENCES candidates(candidate_id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**UI Priority**: Phase 2 (after Tier 1 enrichment)

---

### 2. Alerts

**Problem**: Signals change daily - firms can't manually check every drug

**Solution**: Smart alerts with multiple delivery methods

**Alert Types**:
- **Score change**: "OZEMPIC score increased 62→78 (+16 points)"
- **New signal**: "New HIGH_CONVICTION signal detected"
- **FDA action**: "FDA safety communication issued for watched drug"
- **News spike**: "Media mentions >5 articles this week"
- **Litigation**: "New lawsuit filed (comps alert)"

**Delivery Methods**:
- **Email**: Daily digest (default, free tier)
- **Slack**: Real-time (premium tier)
- **API webhook**: For firms with internal systems (enterprise)

**Example Email Digest**:
```
🚨 AUDITSignal Daily Digest - 3 New Alerts

HIGH PRIORITY:
1. OZEMPIC [Hospitalization] - Score jumped 62→78 (+16 pts)
   - Hospitalization spike: +45% in Q2 2025
   - Action: Review signal →

MONITORING:
2. JARDIANCE - FDA safety communication issued
   - Type: Label update (cardiovascular warning)
   - Action: View FDA action →

3. DUPIXENT - 8 new PubMed articles this week
   - Topic: Eosinophilic pneumonia cases
   - Action: Review literature →
```

**Database Schema**:
```sql
CREATE TABLE alert_rules (
    rule_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    watchlist_id INTEGER REFERENCES user_watchlists(watchlist_id),
    rule_type VARCHAR(50),  -- score_change, new_signal, fda_action, news_spike
    threshold JSONB,  -- {score_delta: 10} or {news_count: 5}
    delivery_method VARCHAR(20),  -- email, slack, webhook
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alert_history (
    alert_id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alert_rules(rule_id),
    candidate_id INTEGER REFERENCES candidates(candidate_id),
    alert_type VARCHAR(50),
    message TEXT,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE
);
```

**Implementation**:
- Daily cron job: Re-run discovery, compare scores vs yesterday
- Check for FDA updates, news mentions, litigation filings
- Generate alerts based on user rules
- Send via configured delivery method

**UI Priority**: Phase 3 (after watchlists)

---

### 3. Comparables (Comps)

**Problem**: "FARXIGA has a death signal - but is this unusual for diabetes drugs?"

**Solution**: Automatic comparable analysis by drug class, indication, and SAE type

**Example Output**:
```
FARXIGA [Death] - Score: 75

Comparable Signals (Same Drug Class):
Drug Class: SGLT2 Inhibitors

INVOKANA    [Death]    Score: 68   Status: MDL Active (3,200 cases)
JARDIANCE   [Death]    Score: 52   Status: Pre-litigation
STEGLATRO   [Death]    Score: 23   Status: Monitoring
→ FARXIGA   [Death]    Score: 75   Status: ⚠️ HIGHEST IN CLASS

Class Average: 54.5 | Your signal: 37% above class average

Litigation History:
- INVOKANA: $300M settlement (amputations), ongoing death claims
- Precedent: Diabetes drug MDLs typically settle $150-400M

💡 Insight: FARXIGA death signal is highest in SGLT2 class.
   Previous class litigation suggests strong MDL potential.
```

**How It Works**:
1. Match by drug_class (from FDA label / DailyMed)
2. Match by indication (diabetes, hypertension, etc.)
3. Match by SAE type (deaths vs hospitalizations)
4. Rank by score within class
5. Show litigation status for each comp
6. Calculate class average

**Database Schema**:
```sql
-- Store drug classifications from FDA labels
ALTER TABLE products ADD COLUMN drug_class VARCHAR(255);
ALTER TABLE products ADD COLUMN indication VARCHAR(255);
ALTER TABLE products ADD COLUMN atc_code VARCHAR(20);  -- Anatomical Therapeutic Chemical code

-- Store litigation outcomes for precedent analysis
CREATE TABLE litigation_precedents (
    precedent_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    case_name VARCHAR(255),
    settlement_amount BIGINT,
    case_count INTEGER,
    filed_date DATE,
    resolution_date DATE,
    outcome VARCHAR(50),  -- settled, dismissed, ongoing
    notes TEXT
);
```

**UI Priority**: Phase 3 (requires Tier 1 enrichment for drug_class)

---

### 4. Timeline View

**Problem**: "When did this signal start? Was there a trigger event?"

**Solution**: Interactive timeline showing SAE trends + overlaid events (FDA actions, news, litigation)

**Example Timeline**:
```
OZEMPIC [Hospitalization] Timeline

Jan 2024  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  Dec 2025
          │       │       │           │         │
          │       │       │           │         └─ Q4: 3,444 cases (+36%)
          │       │       │           └─────────── FDA label update (gastroparesis)
          │       │       └─────────────────────── News spike (TikTok coverage)
          │       └─────────────────────────────── Q2: 2,890 cases (+14%)
          └─────────────────────────────────────── Q1: 2,528 baseline

Events Overlaid:
📰 Mar 2024: TikTok "Ozempic face" viral (800k views)
⚠️  Aug 2024: FDA adds gastroparesis to label
📊 Oct 2024: Hospitalization spike begins
🏛️  Nov 2024: First lawsuit filed (CA)
```

**Interactive Features**:
- Hover over timeline → See exact counts
- Click event → See full details (FDA doc, news article, litigation filing)
- Compare multiple drugs on same timeline
- Export timeline as PNG/PDF for presentations

**Database Schema**:
```sql
CREATE TABLE signal_timeline_events (
    event_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    event_type VARCHAR(50),  -- fda_action, news, litigation, score_change
    event_date DATE,
    title VARCHAR(255),
    description TEXT,
    url VARCHAR(500),
    metadata_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Data Sources**:
- FAERS quarterly data (already have)
- FDA safety communications (Tier 1 enrichment)
- News mentions (Tier 1 enrichment)
- UniCourt litigation filings (future)
- Score changes (tracked automatically)

**UI Priority**: Phase 4 (requires historical data)

---

### 5. Export & Sharing

**Problem**: "I need to present this to partners / clients"

**Solution**: One-click professional exports

**Export Formats**:
- **PDF Report**: Formatted litigation memo with charts
- **PowerPoint**: Executive summary deck
- **Excel**: Raw data for custom analysis
- **API**: Programmatic access for quants

**Example PDF Memo Structure**:
```
LITIGATION INTELLIGENCE MEMO
Generated by AUDITSignal | Confidential

RE: OZEMPIC (semaglutide) - Hospitalization Signal

EXECUTIVE SUMMARY
AUDITSignal has detected a HIGH_CONVICTION signal for OZEMPIC...

SIGNAL METRICS
- Score: 78/100 (HIGH_CONVICTION)
- Hospitalization spike: +45% (Q4 2024 → Q2 2025)
- Estimated affected patients: 14,000-56,000 (adjusted for under-reporting)

FDA & REGULATORY STATUS
- Indication: Type 2 diabetes, weight loss
- Label disclosure: Gastroparesis added Aug 2024 (AFTER spike began)
- Recent actions: 1 label update, 0 recalls

COMPARABLE ANALYSIS
- Drug class: GLP-1 Agonists
- Similar signals: BYETTA (settled $24M), VICTOZA (pending)
- Ranking: #1 highest hospitalization rate in class

LITERATURE EVIDENCE
- PubMed: 34 case reports (2024-2025)
- Key studies: [citations]

LITIGATION ASSESSMENT
- Estimated litigation value: $200-500M (based on GLP-1 class comps)
- Recommended action: INVESTIGATE - Strong MDL potential
- Timeline: File within 6 months to capture first-mover advantage

APPENDIX
- Full FAERS data tables
- Timeline chart
- FDA label excerpts
```

**Implementation**:
- Use ReportLab (Python) or Puppeteer (headless Chrome) for PDF generation
- Template system for customizable branding (white-label for Enterprise tier)
- S3 storage for generated reports
- Email delivery + download link

**Database Schema**:
```sql
CREATE TABLE exported_reports (
    report_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    candidate_id INTEGER REFERENCES candidates(candidate_id),
    report_type VARCHAR(20),  -- pdf, pptx, xlsx
    file_path VARCHAR(500),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_count INTEGER DEFAULT 0
);
```

**UI Priority**: Phase 3 (requires Tier 1 enrichment data)

---

## Pricing Strategy (Bloomberg Model)

### Tier 1: Discovery
**$500/month per seat**

Features:
- Access to full watchlist (all signals)
- Basic filters (score, SAE type, date)
- 10 AI reports/month
- Email alerts (daily digest)
- Export to PDF (basic template)

Target: Solo practitioners, small plaintiff firms (1-3 attorneys)

### Tier 2: Intelligence
**$2,000/month per seat**

Everything in Discovery, plus:
- Custom watchlists (unlimited)
- Advanced filters (drug class, indication, litigation status)
- Alerts (email + Slack, custom rules)
- Comparables analysis
- Timeline view
- 100 AI reports/month
- Export to PDF/Excel/PPT (professional templates)
- PubMed & FDA enrichment data

Target: Mid-size plaintiff firms (10-50 attorneys), hospital safety teams, PE firms

### Tier 3: Enterprise
**$10,000/month for firm**

Everything in Intelligence, plus:
- Unlimited seats (firm-wide access)
- API access (programmatic queries)
- White-label reports (firm branding)
- Dedicated customer success manager
- Priority enrichment (request specific drugs on-demand)
- Custom data integrations
- SLA guarantee (99.9% uptime)

Target: Large plaintiff firms (100+ attorneys), pharma companies, insurers

### Add-On: Historical Data
**+$1,000/month**

Features:
- 10+ years FAERS historical data
- Long-term trend analysis
- Litigation outcome database (settlements, verdicts)
- Predictive modeling (ML-based signal forecasting)

---

## Revenue Model

**Year 1 Target Revenue:**

| Customer Segment | Seats/Firms | Price/Month | MRR | ARR |
|------------------|-------------|-------------|-----|-----|
| Plaintiff Firms (Discovery) | 20 seats | $500 | $10k | $120k |
| Plaintiff Firms (Intelligence) | 50 seats | $2,000 | $100k | $1.2M |
| Hospital Systems | 20 seats | $2,000 | $40k | $480k |
| Pharma/PE (Enterprise) | 10 firms | $10,000 | $100k | $1.2M |
| **Total** | | | **$250k** | **$3M** |

**Year 2 Growth (3× scale):**
- 150 Discovery seats × $500 = $75k MRR
- 150 Intelligence seats × $2,000 = $300k MRR
- 30 Enterprise firms × $10,000 = $300k MRR
- **Total Year 2: $675k MRR → $8.1M ARR**

**Unit Economics:**
- CAC (Customer Acquisition Cost): $2,000 (conferences, direct sales)
- LTV (Lifetime Value): $24,000 (avg 2-year retention @ $1,000/mo blended rate)
- LTV:CAC = 12:1 (excellent SaaS metric)
- Gross margin: 85% (low infrastructure costs, API fees ~$50/customer/mo)

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅
- [x] FAERS signal discovery pipeline
- [x] Multi-SAE tracking (deaths, hospitalizations, disability, life-threatening)
- [x] Reporting lag correction
- [x] Scoring algorithm (0-100)
- [x] Database schema (Safety Intelligence Graph)
- [ ] **Next: Tier 1 Enrichment**

### Phase 2: Tier 1 Enrichment (Weeks 3-4)
- [ ] DailyMed API integration (FDA labels)
  - Extract indication, drug class, boxed warnings
  - Check if SAE is disclosed in label
- [ ] PubMed API integration
  - Count articles mentioning drug + SAE
  - Store recent case report titles
- [ ] FDA safety communications scraper
  - Recalls, warnings, label changes (last 2 years)
- [ ] News mention counter (Google News or SerpAPI)
  - Track media spikes (can trigger reporting bias)
- [ ] Add enrichment_tier1 JSONB column to product_signals
- [ ] Run enrichment during discovery pipeline
- [ ] Update dashboard to show enrichment data

### Phase 3: Search & AI Analysis (Weeks 5-6)
- [ ] Search interface (`/search/<drug_name>`)
  - Check database first
  - Generate on-the-fly if not in watchlist
  - Save ad-hoc searches for future queries
- [ ] AI analysis layer (Claude API)
  - "Generate AI Report" button on candidate pages
  - Litigation assessment prompt (10-point scoring)
  - Store AI reports in database (cache)
- [ ] Drug detail page redesign
  - Show Tier 1 enrichment data
  - Add "AI Analysis" section (on-demand)
  - Timeline preview (basic version)

### Phase 4: Watchlists & Alerts (Weeks 7-8)
- [ ] Custom watchlists
  - User-defined filters (drug_class, SAE type, score range)
  - Save/edit/delete watchlists
  - Sidebar navigation
- [ ] Alert system
  - Daily cron: Re-run discovery, detect changes
  - Alert rules (score_delta, new_signal, fda_action)
  - Email delivery (SendGrid or AWS SES)
  - Alert history & acknowledgment

### Phase 5: Comps & Timeline (Weeks 9-10)
- [ ] Comparables analysis
  - Match by drug_class (requires enrichment)
  - Show ranking within class
  - Litigation precedent lookup
- [ ] Timeline view
  - Interactive chart (Chart.js or D3.js)
  - Overlay FDA actions, news, litigation
  - Export timeline as PNG/PDF

### Phase 6: Export & Polish (Weeks 11-12)
- [ ] PDF export (ReportLab)
  - Professional memo template
  - Charts and tables
  - White-label option (Enterprise)
- [ ] Excel export (raw data)
- [ ] PowerPoint export (executive summary)
- [ ] User authentication & billing (Stripe)
- [ ] Admin dashboard (user management, analytics)

### Phase 7: Launch (Week 13+)
- [ ] Beta testing (5-10 friendly plaintiff firms)
- [ ] Iterate based on feedback
- [ ] Marketing site
- [ ] Public launch
- [ ] Sales outreach (conferences, webinars)

---

## Success Metrics

**Product Metrics:**
- **Signal quality**: % of HIGH_CONVICTION signals that form MDLs within 24 months (target: >30%)
- **Coverage**: % of known MDLs detected 6+ months before filing (target: >70%)
- **Precision**: % of signals scored ≥80 that are litigation-worthy (target: >50%)

**Business Metrics:**
- **MRR growth**: 20% month-over-month (Year 1)
- **Churn**: <5% monthly (high stickiness due to workflow integration)
- **NPS (Net Promoter Score)**: >50 (users actively recommend to peers)
- **Expansion revenue**: 30% of customers upgrade tier within 6 months

**User Engagement:**
- **DAU/MAU**: 60%+ (daily active users / monthly active users)
- **Time in product**: 30+ min/session (Bloomberg benchmark)
- **Watchlist usage**: 80% of users create custom watchlists
- **AI reports**: Avg 15 reports/user/month (indicator of deep research)

---

## Competitive Moats

1. **Data Network Effect**: More users → More validation → Better scoring algorithm
2. **Workflow Lock-In**: Custom watchlists + alerts = daily habit (high switching cost)
3. **AI Layer**: Claude analysis = differentiated insight (not just raw data)
4. **Cross-Market Platform**: TortSignal + SafetyScore + RegulatoryAI share same graph (unique positioning)
5. **First-Mover**: No Bloomberg-style product exists for litigation intelligence yet

---

## Next Steps

1. **Wait for V1 discovery to complete** (~10 min remaining)
2. **Review signals** - Validate quality, identify patterns
3. **Build Tier 1 enrichment** - DailyMed, PubMed, FDA, news
4. **Test enrichment** - Apply to current watchlist
5. **Design watchlist UI** - Sketch custom filter interface
6. **Prototype alerts** - Build daily digest email
7. **User testing** - Show to 2-3 plaintiff attorneys, get feedback
8. **Iterate & launch beta** - 30-day pilot with 5 firms

---

## Long-Term Vision (18-24 Months)

**AUDITSignal becomes the Bloomberg Terminal for Product Liability:**
- **10,000+ drugs tracked** (real-time monitoring)
- **500+ law firms** using daily (TortSignal)
- **200+ hospital systems** for procurement (SafetyScore)
- **50+ pharma/PE firms** for regulatory forecasting (RegulatoryAI)
- **$20M+ ARR** (sustainable, profitable SaaS business)

**Exit potential:**
- **Strategic acquirers**: Thomson Reuters, LexisNexis (legal data incumbents)
- **PE buyers**: Vista Equity, Thoma Bravo (SaaS specialists)
- **Valuation**: 10-15× ARR = $200-300M at $20M ARR

The product that wins is not the one with the best data, but the best **workflow**.
