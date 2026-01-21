# TortSignal Frontend Design Brief

## Executive Summary

TortSignal is an early-warning intelligence platform that detects emerging mass tort litigation opportunities by monitoring FDA adverse events, court filings, scientific literature, and SEC disclosures. Think "Bloomberg Terminal for Mass Torts."

The frontend needs to serve two primary modes:
1. **Discovery Mode**: Proactive surveillance — "What's emerging that I don't know about?"
2. **Research Mode** (future): On-demand deep dives — "Tell me everything about [specific product]"

This document focuses on Discovery Mode, which is the MVP.

---

## Target Users

### Primary: Plaintiff Law Firm Partners
- **Goal**: Find the next big mass tort before competitors
- **Behavior**: Check dashboard 1-2x daily, want ranked list of opportunities
- **Pain point**: Currently relies on word-of-mouth, legal news, conferences
- **Technical sophistication**: Low-to-medium; wants simple, scannable UI

### Secondary: Litigation Funders
- **Goal**: Underwrite emerging tort portfolios early
- **Behavior**: Weekly review, deeper due diligence on top candidates
- **Pain point**: Deal flow comes too late, after MDL formation
- **Technical sophistication**: Medium; comfortable with data-heavy interfaces

### Tertiary: Mass Tort Case Acquisition Teams
- **Goal**: Decide which advertising campaigns to launch
- **Behavior**: Daily monitoring, need to act fast
- **Pain point**: Launch too early (waste money) or too late (miss window)
- **Technical sophistication**: Medium; needs actionable signals

---

## Core Concepts / Glossary

| Term | Definition |
|------|------------|
| **Candidate** | A potential emerging mass tort, identified by a (defendant, product) pair. Example: (Bayer, Roundup) |
| **Signal** | A single piece of evidence: a court filing, FDA report spike, scientific paper, etc. |
| **Score** | 0-100 rating of a candidate's strength, computed from weighted signals |
| **Stage** | Lifecycle phase: `quiet` → `awareness` → `investigate` → `high_conviction` |
| **Category** | Product type that determines scoring weights: `pharma`, `device`, `chemical`, `gov_contractor`, `consumer` |
| **MDL** | Multi-District Litigation — the "finish line" where mass tort becomes official |
| **FAERS** | FDA Adverse Event Reporting System (drugs) |
| **MAUDE** | FDA device adverse event database |
| **Dossier** | Complete evidence package for a single candidate |

---

## Data Models

### Candidate (the core entity)

```typescript
interface Candidate {
  id: string;
  candidateKey: string;           // "bayer corporation|roundup"
  
  // Identity
  defendantText: string;          // "Bayer Corporation"
  productText: string;            // "Roundup"
  injuryText: string;             // "Non-Hodgkin Lymphoma" or "mixed"
  category: Category;             // "pharma" | "device" | "chemical" | "gov_contractor" | "consumer"
  
  // Scoring
  scoreTotal: number;             // 0-100
  scoreComponents: ScoreComponents;
  stage: Stage;                   // "quiet" | "awareness" | "investigate" | "high_conviction"
  confidence: number;             // 0-1, based on data completeness
  
  // Tracking
  status: Status;                 // "new" | "watching" | "reviewing" | "rejected" | "promoted"
  firstSeenAt: Date;
  lastSeenAt: Date;
  
  // Evidence summary
  metrics: CandidateMetrics;
  whyNow: string;                 // Human-readable explanation
}

interface CandidateMetrics {
  // Court signals
  courtFilingCount?: number;
  courtFilingCount7d?: number;
  courtFilingCount28d?: number;
  courtBreadthStates?: number;    // How many states have filings
  courtBreadthFirms?: number;     // How many plaintiff firms involved
  courtVelocity?: number;         // Filings per week trend
  
  // FDA signals (drugs)
  faersReportsCurrent?: number;
  faersReportsBaseline?: number;
  faersDeltaPct?: number;
  faersTopReactions?: string[];
  faersIsNewEntrant?: boolean;
  
  // FDA signals (devices)
  maudeReportsCurrent?: number;
  maudeReportsBaseline?: number;
  maudeDeltaPct?: number;
  maudeTopProblems?: string[];
  
  // Literature signals
  pubmedPaperCount?: number;
  pubmedMetaAnalysisCount?: number;
  pubmedRecentPapers?: number;    // Last 2 years
  
  // Trend data (for sparklines)
  trendData?: TimeSeriesPoint[];
}

interface TimeSeriesPoint {
  period: string;                 // "2024-Q1"
  reportCount: number;
}

interface ScoreComponents {
  category: Category;
  weightsUsed: Record<string, number>;
  rawComponents: {
    courtVelocity?: number;
    courtBreadth?: number;
    faersTrend?: number;
    maudeTrend?: number;
    literature?: number;
    secLanguage?: number;
  };
}

type Category = "pharma" | "device" | "chemical" | "gov_contractor" | "consumer";
type Stage = "quiet" | "awareness" | "investigate" | "high_conviction";
type Status = "new" | "watching" | "reviewing" | "rejected" | "promoted";
```

### Signal Event (evidence backing a candidate)

```typescript
interface SignalEvent {
  id: string;
  candidateId: string;
  
  eventType: EventType;
  eventTime: Date;
  detectedAt: Date;
  
  // Source document reference
  sourceType: string;             // "court_filing" | "faers_report" | "maude_report" | "pubmed_paper"
  sourceUid: string;              // External ID
  sourceUrl?: string;             // Link to original
  
  // Content
  title?: string;
  snippet?: string;               // Relevant excerpt
  
  // Scoring contribution
  weight: number;
  features: Record<string, any>;
}

type EventType = 
  | "filing_new"           // New court filing
  | "filing_spike"         // Unusual increase in filings
  | "adverse_trend"        // FDA adverse events trending up
  | "adverse_new_entrant"  // Product newly appearing in FDA data
  | "paper_published"      // New scientific paper
  | "meta_analysis"        // Meta-analysis published (high signal)
  | "fda_warning"          // FDA warning letter
  | "recall"               // Product recall
  | "sec_reserve_increase" // Litigation reserve increased
  | "sec_language_change"; // Risk language changed in filings
```

### Discovery Scan Results

```typescript
interface DiscoveryScanResults {
  scanTime: Date;
  source: "faers" | "maude" | "court" | "all";
  parameters: {
    currentDays: number;
    baselineDays: number;
  };
  
  // FAERS results
  drugAnomalies: DrugAnomaly[];
  reactionAnomalies: ReactionAnomaly[];
  pairSignals: DrugReactionPair[];
  
  // MAUDE results
  deviceAnomalies: DeviceAnomaly[];
  categoryAnomalies: CategoryAnomaly[];
  manufacturerAnomalies: ManufacturerAnomaly[];
  
  summary: {
    drugAnomaliesCount: number;
    reactionAnomaliesCount: number;
    deviceAnomaliesCount: number;
    categoryAnomaliesCount: number;
    totalCandidatesCreated: number;
  };
}

interface DrugAnomaly {
  productName: string;
  reportsCurrent: number;
  reportsBaseline: number;
  deltaPct: number | "new_entrant";
  topReactions: string[];
  isNewEntrant: boolean;
}

interface ReactionAnomaly {
  reaction: string;              // The injury/adverse event
  reportsCurrent: number;
  reportsBaseline: number;
  deltaPct: number;
  topDrugs: Array<{             // Which drugs are causing this
    drugName: string;
    count: number;
  }>;
}

interface DeviceAnomaly {
  deviceName: string;
  manufacturer?: string;
  reportsCurrent: number;
  reportsBaseline: number;
  deltaPct: number | "new_entrant";
  topProblems: string[];
  isNewEntrant: boolean;
}

interface CategoryAnomaly {
  productCode: string;           // FDA device category code
  productCodeName?: string;
  reportsCurrent: number;
  reportsBaseline: number;
  deltaPct: number;
  topManufacturers: Array<{ manufacturer: string; count: number }>;
  topBrands: Array<{ brandName: string; count: number }>;
}
```

---

## Application Views

### 1. Watchlist (Primary View)

**Purpose**: Ranked list of all candidates, sortable and filterable. This is where users spend 80% of their time.

**URL**: `/watchlist` or `/` (default)

**Layout**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│  TORTSIGNAL                    [Search...]            [Settings] [User] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WATCHLIST                                          Last scan: 2h ago   │
│                                                                         │
│  ┌─── Filters ───────────────────────────────────────────────────────┐  │
│  │ Stage: [All ▼]  Category: [All ▼]  Status: [All ▼]  Score: [>0 ▼] │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── Candidates ─────────────────────────────────────────────────────┐ │
│  │                                                                     │ │
│  │  #1  ████████████████████████████████████████░░░░░  87             │ │
│  │      OZEMPIC (Novo Nordisk)                          PHARMA        │ │
│  │      Gastroparesis, Pancreatitis                     ▲ 340%        │ │
│  │      "2,847 FAERS reports in 30d, 8 consecutive quarters rising"   │ │
│  │      [Watch] [Reject] [View Dossier →]                             │ │
│  │                                                                     │ │
│  │  ─────────────────────────────────────────────────────────────────  │ │
│  │                                                                     │ │
│  │  #2  ██████████████████████████████████░░░░░░░░░░░  72             │ │
│  │      PHILIPS CPAP (Philips)                          DEVICE        │ │
│  │      Respiratory injury, Cancer                      ▲ 890%        │ │
│  │      "FDA recall + 12,000 MAUDE reports"                           │ │
│  │      [Watch] [Reject] [View Dossier →]                             │ │
│  │                                                                     │ │
│  │  ...                                                                │ │
│  │                                                                     │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Showing 1-20 of 147 candidates                    [← Prev] [Next →]   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Candidate Row Components**:
- **Score bar**: Visual 0-100, color-coded by stage
- **Product name (defendant)**: Primary identifier
- **Category badge**: pharma/device/chemical/etc.
- **Injury tags**: Top 2-3 injuries
- **Delta indicator**: ▲/▼ with percentage vs. baseline
- **Why now snippet**: One-line explanation
- **Sparkline** (optional): 8-quarter trend mini-chart
- **Action buttons**: Watch, Reject, View Dossier

**Filters**:
- Stage: All, Quiet, Awareness, Investigate, High Conviction
- Category: All, Pharma, Device, Chemical, Gov Contractor, Consumer
- Status: All, New, Watching, Reviewing, Rejected, Promoted
- Score: Slider or presets (>50, >70, >90)
- Time: First seen (last 7d, 30d, 90d, all)

**Sorting**:
- Score (default, descending)
- Delta % (biggest movers)
- First seen (newest)
- Last updated
- Court filing count
- FDA report count

**Interactions**:
- Click row → expand inline preview OR navigate to dossier
- Bulk actions: select multiple → reject all, export
- Keyboard navigation: j/k to move, enter to open

---

### 2. Candidate Dossier (Detail View)

**Purpose**: Complete evidence package for a single candidate. Everything needed to make an investment/pursuit decision.

**URL**: `/candidate/{id}` or `/candidate/{defendant}/{product}`

**Layout**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← Back to Watchlist                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  OZEMPIC                                                    Score: 87   │
│  Novo Nordisk                                               ███████████ │
│  Category: Pharma                                                       │
│  Stage: INVESTIGATE                   Status: [Watching ▼]              │
│                                                                         │
│  ┌─── Why Now ──────────────────────────────────────────────────────┐  │
│  │ "2,847 FAERS adverse event reports in last 30 days (+340% vs     │  │
│  │  baseline). Gastroparesis reports specifically up 890%. 3 new    │  │
│  │  meta-analyses published in 2024 linking GLP-1 agonists to       │  │
│  │  gastroparesis. 47 federal court filings across 12 states."      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── Score Breakdown ──────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │  FAERS Trend        ████████████████████████████████░░  40% × 85 │  │
│  │  Court Velocity     ██████████████████░░░░░░░░░░░░░░░░  25% × 72 │  │
│  │  Literature         █████████████████████░░░░░░░░░░░░░  15% × 68 │  │
│  │  Court Breadth      ████████████████░░░░░░░░░░░░░░░░░░  10% × 54 │  │
│  │  SEC Language       ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  10% × N/A│  │
│  │                                                    ──────────────│  │
│  │                                                    Total:    87  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── Tabs ─────────────────────────────────────────────────────────┐  │
│  │ [Overview] [FDA Data] [Court Filings] [Literature] [Timeline]    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── Tab Content ──────────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │  (Content varies by selected tab - see below)                    │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─── Actions ──────────────────────────────────────────────────────┐  │
│  │ [Add to Watchlist] [Export PDF] [Share Link] [Mark Reviewed]     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Tab: Overview**
- Key metrics cards (filing count, FDA reports, papers, states, firms)
- Trend chart: 8-quarter time series of FDA reports
- Injury distribution: pie/bar chart of reported injuries
- Geographic distribution: US map with state highlighting

**Tab: FDA Data**
- FAERS report trend chart (line graph over time)
- Top adverse reactions table
- Serious outcome breakdown (death, hospitalization, etc.)
- Raw report samples (expandable)

**Tab: Court Filings**
- Filing velocity chart (filings per week/month)
- Geographic spread map
- Plaintiff firms involved (table)
- Recent filings list with links

**Tab: Literature**
- Paper count over time
- Meta-analyses highlighted
- Key papers list with abstracts
- MeSH term cloud

**Tab: Timeline**
- Chronological event log
- All signals on a single timeline
- Filterable by event type
- Key milestones marked (FDA warning, first MDL filing, etc.)

---

### 3. Discovery Feed (Signal Stream)

**Purpose**: Real-time feed of new signals as they're detected. Like a Twitter feed for tort signals.

**URL**: `/feed` or `/signals`

**Layout**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│  DISCOVERY FEED                                    [Filter ▼] [Refresh] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ○ 2 minutes ago                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 🔬 NEW META-ANALYSIS                                              │  │
│  │ "GLP-1 receptor agonists and risk of gastroparesis: systematic    │  │
│  │  review and meta-analysis"                                        │  │
│  │ → Links to: OZEMPIC, WEGOVY, MOUNJARO                             │  │
│  │ [View Paper] [View Candidates]                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ○ 47 minutes ago                                                       │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ ⚠️ REACTION SPIKE                                                 │  │
│  │ "Gastroparesis" reports up 340% across all drugs                  │  │
│  │ Top drivers: OZEMPIC (2,100), WEGOVY (890), MOUNJARO (445)        │  │
│  │ [View Analysis] [View Affected Candidates]                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ○ 2 hours ago                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 📄 NEW COURT FILING                                               │  │
│  │ "Smith v. Novo Nordisk" - N.D. California                         │  │
│  │ Plaintiff firm: Morgan & Morgan                                   │  │
│  │ → Links to: OZEMPIC                                               │  │
│  │ [View Filing] [View Candidate]                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ○ 3 hours ago                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 📊 DEVICE CATEGORY SPIKE                                          │  │
│  │ Product code "BZG" (CPAP devices) up 450%                         │  │
│  │ Top brands: Philips DreamStation, ResMed AirSense                 │  │
│  │ [View Analysis] [View Affected Candidates]                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [Load more...]                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Signal Types (with icons)**:
- 📄 Court filing (new, spike)
- ⚠️ FDA adverse event (drug spike, reaction spike, device spike, category spike)
- 🔬 Scientific paper (especially meta-analyses)
- 🏛️ Regulatory action (FDA warning, recall)
- 💰 SEC filing (reserve increase, language change)
- 🆕 New candidate detected

**Filters**:
- Signal type
- Category (pharma/device/etc.)
- Time range
- Linked candidate

---

### 4. Analytics Dashboard

**Purpose**: High-level metrics and trends across all candidates. Executive summary view.

**URL**: `/analytics` or `/dashboard`

**Components**:

**Summary Cards**:
- Total active candidates
- New candidates (last 7d)
- High conviction candidates
- Candidates promoted to review

**Stage Funnel**:
```
Quiet (89) → Awareness (34) → Investigate (19) → High Conviction (5)
```

**Category Breakdown**:
- Pie chart: candidates by category
- Bar chart: average score by category

**Top Movers**:
- Biggest score increases (last 7d)
- Biggest score decreases
- Newly detected candidates

**Trend Charts**:
- Total FDA reports over time (stacked by category)
- Court filings over time
- New candidates per week

---

### 5. Settings / Configuration

**Purpose**: User preferences and system configuration.

**Sections**:

**Alert Configuration**:
- Email alerts: on/off, frequency (real-time, daily digest, weekly)
- Alert thresholds: score > X, stage change, new candidate in category
- Watched candidates: notify on any update

**Display Preferences**:
- Default watchlist sort
- Default filters
- Cards per page
- Dark mode

**Data Sources**:
- Show FAERS data: on/off
- Show MAUDE data: on/off
- Show court data: on/off
- Show literature: on/off

---

## Design System Recommendations

### Color Palette

**Stage Colors** (traffic light concept):
- Quiet: Gray (#6B7280)
- Awareness: Blue (#3B82F6)
- Investigate: Yellow/Amber (#F59E0B)
- High Conviction: Red (#EF4444)

**Category Colors**:
- Pharma: Purple (#8B5CF6)
- Device: Teal (#14B8A6)
- Chemical: Orange (#F97316)
- Gov Contractor: Blue (#3B82F6)
- Consumer: Green (#22C55E)

**Delta Indicators**:
- Positive (bad for defendant): Red with ▲
- Negative (good for defendant): Green with ▼
- Neutral: Gray

### Typography

- **Headlines**: Bold, clear hierarchy
- **Data**: Monospace for numbers, clear alignment
- **Body**: Readable at small sizes (lots of information density)

### Information Density

This is a professional tool, not a consumer app. Users want:
- High information density
- Scannable tables and lists
- Minimal clicks to get to data
- Keyboard shortcuts

Think Bloomberg Terminal, not Instagram.

### Responsive Considerations

Primary use: Desktop (1440px+)
Secondary: Tablet (landscape)
Rare: Mobile (basic read-only views)

---

## Key Interactions

### Quick Actions (on candidate rows)
- **Watch**: Add to user's watched list, enable notifications
- **Reject**: Mark as not interesting, hide from default view
- **Promote**: Escalate for team review
- **Export**: Generate PDF dossier

### Bulk Operations
- Select multiple candidates
- Bulk reject, bulk watch, bulk export

### Keyboard Navigation
- `j`/`k`: Move up/down in list
- `Enter`: Open dossier
- `w`: Watch
- `r`: Reject
- `/`: Focus search
- `?`: Show shortcuts

### Search
- Global search across candidates
- Autocomplete with product names, defendant names
- Recent searches
- Saved searches

---

## Empty States

**No candidates match filters**:
"No candidates match your current filters. Try adjusting your criteria or [reset filters]."

**No signals yet**:
"Discovery scan is running. New signals will appear here as they're detected."

**New user, no data**:
"Welcome to TortSignal. Run your first discovery scan to populate the watchlist. [Run Discovery →]"

---

## Error States

**API error**:
"Unable to load data. Please try again. [Retry]"

**Scan failed**:
"Discovery scan encountered an error. [View Details] [Retry]"

**Stale data warning**:
"Data was last updated 24 hours ago. [Run Discovery]"

---

## Technical Considerations

### API Endpoints (assumed)

```
GET  /api/candidates              # List with filters, pagination
GET  /api/candidates/{id}         # Single candidate with full dossier
PATCH /api/candidates/{id}        # Update status

GET  /api/signals                 # Signal feed with filters
GET  /api/signals/{id}            # Single signal detail

GET  /api/discovery/status        # Current scan status
POST /api/discovery/run           # Trigger new discovery scan

GET  /api/analytics/summary       # Dashboard metrics
GET  /api/analytics/trends        # Time series data
```

### Real-time Updates

Consider WebSocket or SSE for:
- Discovery scan progress
- New signal notifications
- Score updates

### Caching

- Candidate list: short TTL (1-5 min)
- Dossier data: medium TTL (15 min)
- Analytics: medium TTL (15 min)
- Historical trend data: long TTL (1 hour)

---

## Future Considerations (Not MVP)

### Research Mode
- Search by product/defendant name
- On-demand dossier generation for any product
- "What if" scoring scenarios

### Collaboration
- Team workspaces
- Shared watchlists
- Comments on candidates
- Audit log

### Integrations
- Export to CRM
- Slack notifications
- Email reports
- API access for power users

### Comparison Tools
- Compare two candidates side-by-side
- "Similar to [historical tort]" analysis
- Benchmark against historical cases

---

## Summary

The TortSignal frontend is a professional intelligence tool with three core views:

1. **Watchlist**: Ranked, filterable candidate list (primary)
2. **Dossier**: Deep-dive evidence package (detail)
3. **Feed**: Real-time signal stream (monitoring)

Design for:
- High information density
- Fast scanning and triage
- Keyboard-first power users
- Clear visual hierarchy (score → stage → category)

The user journey is:
```
Feed catches signal → Signal links to Candidate → 
Candidate appears on Watchlist → User triages (watch/reject) →
User opens Dossier for deep dive → User takes action (promote/export)
```

Build for Discovery Mode first. Research Mode layers on top later.
