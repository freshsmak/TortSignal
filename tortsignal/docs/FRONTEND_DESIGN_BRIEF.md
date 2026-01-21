# TortSignal Frontend Design Brief

## Overview

TortSignal is "The Bloomberg Terminal for Mass Torts" - an early-warning dashboard that detects emerging mass tort litigation 18-36 months before MDL formation.

**Target Users**: Plaintiff firms, litigation funders, insurance underwriters, hedge funds
**Primary Use Case**: First-mover advantage on case acquisition and risk assessment

---

## Design Philosophy

### Terminal-First Aesthetic
- **Bloomberg/Reuters-inspired**: Dense information, professional, fast
- **Data over decoration**: Maximize signal-to-noise ratio
- **Explainable intelligence**: Every score backed by traceable evidence
- **Awareness, not certainty**: UI says "investigate" not "guaranteed win"

### Color Palette

```
Primary:
  Navy:        #1e3a5f  (headers, primary actions)
  Charcoal:    #2d3748  (backgrounds)
  White:       #ffffff  (text on dark)

Accent:
  Alert Red:   #e53e3e  (high conviction)
  Warning:     #ed8936  (investigate)
  Caution:     #ecc94b  (awareness)
  Quiet:       #718096  (quiet stage)

Data Viz:
  Court:       #4299e1  (court filing signals)
  FDA:         #48bb78  (FAERS/MAUDE signals)
  Literature:  #9f7aea  (PubMed signals)
  SEC:         #ed8936  (SEC signals)
```

### Typography
- **Headings**: Inter, SF Pro, or Roboto (16-24px, semibold)
- **Body**: Inter or SF Pro (14px, regular)
- **Monospace**: JetBrains Mono or SF Mono (12px, for IDs, dates)

---

## Core Screens

### 1. Watchlist (Primary Landing)

**Purpose**: Ranked table of emerging tort candidates for triage

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ TORTSIGNAL          [Filters ▼] [Refresh] [Settings]       │
├─────────────────────────────────────────────────────────────┤
│ WATCHLIST                                   Updated: 2m ago │
│                                                              │
│ Filters: [All Categories ▼] [All Stages ▼] [Date: 30d ▼]   │
│ Sort: [Score (High→Low) ▼]                                  │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Defendant  │ Product │ Injury │ Score│ Stage│Updated │   │
│ ├──────────────────────────────────────────────────────┤   │
│ │ Bayer AG   │ Roundup │ NHL    │  92  │ HIGH │ 2h ago │   │
│ │ J&J        │ Talc    │ Cancer │  78  │ HIGH │ 1d ago │   │
│ │ Novo       │ Ozempic │ Gastro │  64  │ INVEST│ 3h ago│   │
│ │ ...        │ ...     │ ...    │  ... │ ...  │ ...    │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ [Export CSV] [Bulk Actions ▼]                               │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- **Stage badges**: Color-coded (Red=High, Orange=Investigate, Yellow=Awareness, Gray=Quiet)
- **Score**: Large, bold number (0-100)
- **Click row** → Navigate to Dossier
- **Hover**: Show quick tooltip with velocity_7d and breadth stats
- **Filters**: Multi-select category, stage; date range slider; min score slider
- **Sort**: Score, Velocity, Recency, Breadth
- **Bulk actions**: Mark reviewed, Reject, Export

**Responsive**:
- Desktop: Full table (10 columns)
- Tablet: Collapse injury column, show on hover
- Mobile: Card layout, 1 candidate per card

---

### 2. Dossier (Candidate Deep Dive)

**Purpose**: Comprehensive evidence view for a single candidate

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Watchlist                        [Actions ▼]      │
├─────────────────────────────────────────────────────────────┤
│ BAYER AG × ROUNDUP × NON-HODGKIN LYMPHOMA                  │
│ Category: Pharma  │ Score: 92  │ Stage: HIGH CONVICTION     │
│ First Seen: 2019-03-15  │ Last Updated: 2h ago             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌─ WHY NOW ─────────────────────────────────────────────┐  │
│ │ 47 new filings in last 7 days across 12 states and    │  │
│ │ 9 plaintiff firms. FAERS reports up 210% vs baseline. │  │
│ │ Recent meta-analysis published in JAMA Oncology.      │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌─ METRICS ─────────────────────────────────────────────┐  │
│ │ Velocity (7d): 47 filings  │ Velocity (28d): 183      │  │
│ │ Breadth: 12 states, 9 firms│ Accel Ratio: 2.3x        │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌─ TIMELINE ────────────────────────────────────────────┐  │
│ │ ● 2025-01-20  FILING_SPIKE   +47 cases in 7 days      │  │
│ │ ● 2025-01-18  ADVERSE_TREND  FAERS +210% baseline     │  │
│ │ ● 2025-01-15  META_ANALYSIS  JAMA Oncology published  │  │
│ │ ● 2024-12-10  FILING_NEW     First CA case filed      │  │
│ │ ● 2019-03-15  IARC_2A        IARC probable carcinogen │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌─ EVIDENCE LEDGER ─────────────────────────────────────┐  │
│ │ Source  │ Title                  │ Date       │ Link   │  │
│ ├─────────────────────────────────────────────────────────│  │
│ │ Court   │ Doe v. Bayer AG       │ 2025-01-20 │ [View] │  │
│ │ FAERS   │ Glyphosate NHL Trend  │ 2025-01-18 │ [View] │  │
│ │ PubMed  │ Glyphosate Meta       │ 2025-01-15 │ [View] │  │
│ │ ...     │ ...                   │ ...        │ ...    │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌─ INJURY DISTRIBUTION ─────────────────────────────────┐  │
│ │ Non-Hodgkin Lymphoma    ████████████████████ 78%      │  │
│ │ Leukemia                ███████ 15%                    │  │
│ │ Multiple Myeloma        ██ 7%                          │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌─ SCORE BREAKDOWN ─────────────────────────────────────┐  │
│ │ FAERS Trend (40%):      [████████████████] 95         │  │
│ │ Court Velocity (30%):   [█████████████] 85            │  │
│ │ Literature (20%):       [██████████████] 92            │  │
│ │ Court Breadth (10%):    [██████████] 70               │  │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │  │
│ │ TOTAL SCORE: 92                                        │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Actions Dropdown**:
- Mark as Reviewed
- Reject (False Positive)
- Override Category
- Export Dossier to PDF
- Pin to Dashboard

---

### 3. Settings (Optional Phase 1)

**Purpose**: Configure user preferences and alert thresholds

**Sections**:
- **Alert Preferences**: Email, Slack webhook, stage thresholds
- **Display**: Dark mode toggle, density (compact/comfortable)
- **Data Refresh**: Auto-refresh interval, manual sync button
- **Filters**: Save default filter sets

---

## Component Library

### 1. Stage Badge
```jsx
<StageBadge stage="HIGH_CONVICTION" />
<StageBadge stage="INVESTIGATE" />
<StageBadge stage="AWARENESS" />
<StageBadge stage="QUIET" />
```
- **Colors**: Red, Orange, Yellow, Gray
- **Icons**: ● (filled circle)
- **Hover**: Show stage description

### 2. Score Indicator
```jsx
<ScoreIndicator value={92} max={100} />
```
- **Display**: Large number (24px) with small "/ 100"
- **Color gradient**: 0-39 Gray, 40-69 Orange, 70-100 Red
- **Optional**: Circular progress indicator

### 3. Timeline Event
```jsx
<TimelineEvent
  type="FILING_SPIKE"
  date="2025-01-20"
  description="+47 cases in 7 days"
  sourceLink="..."
/>
```
- **Icon by type**: ⚖️ Court, 💊 FDA, 📄 Literature, 🏢 SEC
- **Date**: Monospace, gray
- **Hover**: Expand snippet preview

### 4. Evidence Row
```jsx
<EvidenceRow
  source="Court"
  title="Doe v. Bayer AG"
  date="2025-01-20"
  link="https://..."
  snippet="Plaintiff alleges..."
/>
```
- **Expandable**: Click to show full snippet
- **Link**: External icon, opens in new tab

### 5. Injury Distribution Chart
```jsx
<InjuryChart data={[
  {injury: "NHL", count: 78},
  {injury: "Leukemia", count: 15},
  ...
]} />
```
- **Type**: Horizontal bar chart
- **Colors**: Gradient based on count
- **Tooltip**: Show exact counts on hover

---

## Data Flow

### Watchlist Data Structure
```json
{
  "candidates": [
    {
      "cluster_id": "uuid",
      "defendant_text": "Bayer AG",
      "product_text": "Roundup",
      "injury_text": "Non-Hodgkin Lymphoma",
      "score_total": 92,
      "stage": "HIGH_CONVICTION",
      "category": "pharma",
      "last_updated": "2025-01-20T14:30:00Z",
      "velocity_7d": 47,
      "breadth_states": 12,
      "breadth_firms": 9
    }
  ],
  "total_count": 234,
  "last_refresh": "2025-01-20T14:32:00Z"
}
```

### Dossier Data Structure
```json
{
  "candidate": {
    "cluster_id": "uuid",
    "defendant_text": "Bayer AG",
    "product_text": "Roundup",
    "injury_text": "Non-Hodgkin Lymphoma",
    "score_total": 92,
    "score_components": {
      "faers_trend": 95,
      "court_velocity": 85,
      "literature": 92,
      "court_breadth": 70
    },
    "stage": "HIGH_CONVICTION",
    "category": "pharma",
    "first_seen": "2019-03-15",
    "last_updated": "2025-01-20T14:30:00Z",
    "why_now": "47 new filings in last 7 days across 12 states..."
  },
  "timeline": [
    {
      "event_id": "uuid",
      "event_type": "FILING_SPIKE",
      "detected_at": "2025-01-20",
      "snippet": "+47 cases in 7 days",
      "source_link": "..."
    }
  ],
  "evidence": [
    {
      "document_id": "uuid",
      "source_type": "Court",
      "title": "Doe v. Bayer AG",
      "filed_date": "2025-01-20",
      "external_url": "https://...",
      "snippet": "Plaintiff alleges..."
    }
  ],
  "injuries": [
    {"injury": "Non-Hodgkin Lymphoma", "count": 78, "pct": 0.78},
    {"injury": "Leukemia", "count": 15, "pct": 0.15}
  ],
  "metrics": {
    "velocity_7d": 47,
    "velocity_28d": 183,
    "accel_ratio": 2.3,
    "breadth_states": 12,
    "breadth_firms": 9
  }
}
```

---

## Technical Stack

### Frontend Framework: **Streamlit**

**Rationale**:
- Fast prototyping for data-heavy apps
- Native Python (matches backend)
- Built-in components for tables, charts, filters
- Easy deployment (Streamlit Cloud, Docker)

**Alternatives considered**:
- React + FastAPI: More customizable, but slower to build
- Gradio: Too toy-like for professional users
- Dash: Good for dashboards, but less flexible than Streamlit

### Key Dependencies
```toml
streamlit = "^1.28"
plotly = "^5.17"         # Interactive charts
pandas = "^2.1"          # Data manipulation
altair = "^5.1"          # Declarative viz (Streamlit native)
streamlit-aggrid = "^0.3" # Advanced table features
streamlit-extras = "^0.3" # UI enhancements
```

---

## Implementation Notes

### 1. State Management
- Use `st.session_state` for:
  - Selected candidate ID (for Dossier routing)
  - Active filters
  - User preferences
- Cache database queries with `@st.cache_data(ttl=300)` (5min)

### 2. Performance
- **Lazy loading**: Paginate Watchlist (20 rows at a time)
- **SQL optimization**: Index on `score_total`, `last_updated`, `category`
- **Caching**: Cache Dossier data for 5 minutes
- **Async loading**: Use `st.spinner()` for long queries

### 3. Routing
```python
# app.py
pages = {
    "Watchlist": watchlist_page,
    "Dossier": dossier_page,
    "Settings": settings_page,
}

selection = st.sidebar.radio("Navigation", pages.keys())
pages[selection]()
```

### 4. Database Queries
```python
# app/db_helpers.py
def get_watchlist(filters: dict) -> pd.DataFrame:
    """Fetch candidates with filters applied"""

def get_dossier(cluster_id: str) -> dict:
    """Fetch full dossier for one candidate"""

def mark_reviewed(cluster_id: str):
    """Update candidate status"""
```

---

## Deployment

### Option 1: Streamlit Cloud (MVP)
```bash
# streamlit run app/app.py
```
- Free tier: 1 app, 1GB RAM
- Custom domain: tortsignal.streamlit.app
- Auto-deploy from Git

### Option 2: Docker (Production)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
CMD ["streamlit", "run", "app/app.py", "--server.port=8501"]
```

### Option 3: AWS/GCP (Enterprise)
- Deploy on ECS/Cloud Run
- Use CloudFront/CDN for assets
- Add authentication (AWS Cognito, Auth0)

---

## Future Enhancements

### Phase 2: Interactivity
- **Drill-down charts**: Click bar in injury chart → filter evidence
- **Source highlighting**: Hover over score component → highlight contributing events
- **Inline editing**: Click category badge → dropdown to override

### Phase 3: Collaboration
- **Comments**: Add notes to candidates
- **Assignment**: Assign candidates to team members
- **Status workflow**: Draft → Under Review → Rejected → Monitoring → Acting

### Phase 4: Advanced Viz
- **Network graph**: Defendant-Product relationships
- **Heatmap**: Geographic distribution of filings
- **Time series**: Score evolution over weeks/months

---

## Accessibility

- **Keyboard navigation**: Tab through table rows, Enter to open Dossier
- **Screen reader**: ARIA labels on all interactive elements
- **Color contrast**: WCAG AA compliance (4.5:1 for text)
- **Focus indicators**: Visible blue outline on focused elements

---

## Security

- **Authentication**: Username/password (Streamlit secrets) for MVP
- **HTTPS**: Always use TLS for production
- **API keys**: Never expose in client-side code
- **Rate limiting**: Prevent brute-force on auth
- **Input sanitization**: Escape all user inputs in SQL queries

---

## Success Metrics

### Usage (First 30 Days)
- Daily active users
- Avg dossiers viewed per session
- Time from alert → decision (reviewed/rejected)

### Quality
- % of "High Conviction" candidates marked "worth investigating"
- False positive rate (rejected / total reviewed)

### Performance
- Page load time < 2s (p95)
- Time to interactive < 3s
- Database query time < 500ms (p95)

---

## Changelog

- **v0.1.0** (Phase 4): Watchlist + Dossier MVP
- **v0.2.0** (Phase 5): SEC integration, enhanced timeline
- **v0.3.0** (Phase 6): Alerts and notifications
- **v1.0.0** (Phase 9): Multi-tenancy, CRM integration
