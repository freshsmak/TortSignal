# TortSignal Dashboard

**The Bloomberg Terminal for Mass Torts**

An early-warning Streamlit dashboard that detects emerging mass tort litigation 18-36 months before MDL formation.

---

## Features

### 📊 Watchlist
- Ranked table of emerging tort candidates
- Filter by category, stage, score, date range
- Sort by score, velocity, recency, breadth
- One-click navigation to detailed dossiers

### 📋 Dossier
- Comprehensive evidence view for each candidate
- Timeline of signal events (filings, FDA trends, literature)
- Evidence ledger with source documents
- Injury distribution charts
- Explainable score breakdown by component
- "Why Now" auto-generated narrative

---

## Quick Start

### 1. Install Dependencies

```bash
# From the tortsignal/ directory
pip install -r app/requirements.txt
```

### 2. Configure Database (Optional)

If you have a PostgreSQL database configured:

```bash
# Ensure .env file exists with DATABASE_URL
export DATABASE_URL="postgresql://user:pass@localhost:5432/tortsignal"
```

The app will work in demo mode with sample data if no database is connected.

### 3. Run the Dashboard

```bash
# From the tortsignal/ directory
streamlit run app/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

## Project Structure

```
app/
├── app.py                  # Main entry point
├── db_helpers.py           # Database query functions
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── pages/
│   ├── __init__.py
│   ├── watchlist.py       # Watchlist page
│   └── dossier.py         # Dossier deep dive page
│
└── components/
    ├── __init__.py
    ├── stage_badge.py     # Stage badge component
    └── score_display.py   # Score display component
```

---

## Configuration

### Display Settings

Accessible via the sidebar Settings expander:
- **Auto-refresh**: Enable 5-minute auto-refresh (default: off)
- **Display density**: Comfortable or Compact mode
- **Clear Cache**: Force refresh of cached data

### Database Connection

The app automatically connects to your PostgreSQL database if:
1. `DATABASE_URL` environment variable is set
2. The database schema has been initialized (`schema/001_core.sql`)

If no database is available, the app runs in **demo mode** with sample data for:
- Bayer/Roundup/NHL
- J&J/Talc/Cancer
- Novo/Ozempic/Gastroparesis

---

## Usage

### Watchlist Workflow

1. **Filter candidates** by category, stage, score, or date
2. **Sort** by score (default), velocity, recency, or breadth
3. **Click "View"** on any row to open the full dossier
4. **Export CSV** for external analysis
5. **Bulk actions** (future): Mark reviewed, reject, etc.

### Dossier Workflow

1. **Review "Why Now"** summary at the top
2. **Check metrics** (velocity, breadth, acceleration)
3. **Scan timeline** for key events (IARC classification, FDA warnings, filing spikes)
4. **Browse evidence** ledger for source documents
5. **Analyze injury distribution** to understand injury patterns
6. **Examine score breakdown** to see which signals drive the score
7. **Take action**: Mark reviewed, reject, export to PDF

---

## Demo Mode

When running without a database connection, the app displays sample data for demonstration purposes:

**Sample Candidates**:
- Bayer AG × Roundup × Non-Hodgkin Lymphoma (Score: 92, HIGH)
- Johnson & Johnson × Talcum Powder × Ovarian Cancer (Score: 78, HIGH)
- Novo Nordisk × Ozempic × Gastroparesis (Score: 64, INVESTIGATE)
- 3M Company × AFFF Foam × Various Cancers (Score: 56, INVESTIGATE)
- Philips × CPAP Machines × Respiratory Issues (Score: 42, INVESTIGATE)

All functionality works in demo mode, making it easy to explore the UI before connecting a live database.

---

## Performance

### Caching

The app uses Streamlit's `@st.cache_data` decorator to cache:
- Watchlist queries (5-minute TTL)
- Dossier data (5-minute TTL)
- Quick stats for sidebar (5-minute TTL)

Use the "Clear Cache" button in Settings to force refresh.

### Pagination

The watchlist is limited to:
- **100 candidates** per query (configurable in `db_helpers.py`)
- Future enhancement: Infinite scroll or pagination UI

---

## Customization

### Color Scheme

Terminal-inspired colors are defined in `app.py`:
- **Navy** (#1e3a5f): Headers, primary actions
- **Charcoal** (#2d3748): Backgrounds
- **Alert Red** (#e53e3e): High conviction stage
- **Warning Orange** (#ed8936): Investigate stage
- **Caution Yellow** (#ecc94b): Awareness stage
- **Quiet Gray** (#718096): Quiet stage

Edit the `<style>` block in `app.py` to customize.

### Stage Thresholds

Score-to-stage mapping (in `components/stage_badge.py`):
- **High Conviction**: 70-100
- **Investigate**: 40-69
- **Awareness**: 20-39
- **Quiet**: 0-19

### Category Weights

Score component weights by category (in `pages/dossier.py` `get_category_weights()`):
- **Pharma**: FAERS 40%, Court Velocity 30%, Breadth 10%, Literature 15%, SEC 5%
- **Device**: MAUDE 40%, Court Velocity 30%, Breadth 10%, Literature 10%, SEC 10%
- **Chemical**: Literature 40%, Court Velocity 25%, Breadth 15%, SEC 5%

---

## Deployment

### Option 1: Local

```bash
streamlit run app/app.py
```

### Option 2: Streamlit Cloud (Free)

1. Push code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect repo and specify `app/app.py` as entry point
4. Add `DATABASE_URL` to secrets
5. Deploy!

### Option 3: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
COPY src/ ./src/
ENV PYTHONPATH=/app
CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t tortsignal .
docker run -p 8501:8501 -e DATABASE_URL=your_db_url tortsignal
```

---

## Troubleshooting

### "Database not connected" message

**Cause**: `DATABASE_URL` not set or database unreachable

**Solution**:
1. Check `.env` file exists and has `DATABASE_URL`
2. Verify database is running: `psql $DATABASE_URL -c "SELECT 1;"`
3. Run `python -m src.db` to test connection
4. App will fall back to demo mode if connection fails

### Blank watchlist

**Cause**: No candidates in database matching filters

**Solution**:
1. Reset filters to default (All categories, All stages, Min score 0)
2. Run discovery pipeline to populate data: `make fda-discovery`
3. Check `SELECT COUNT(*) FROM candidates WHERE status != 'rejected';`

### Slow page loads

**Cause**: Large database queries or cache expired

**Solution**:
1. Reduce date range filter (e.g., Last 30 days instead of All time)
2. Add database indexes: `CREATE INDEX idx_candidates_score ON candidates(score_total DESC);`
3. Increase cache TTL in `db_helpers.py` from 300s to 600s

---

## Future Enhancements

### Phase 2 (Alerts)
- Email/Slack notifications when candidates cross stage thresholds
- Configurable alert rules per user
- Daily/weekly digest mode

### Phase 3 (Collaboration)
- Comments on candidates
- Assignment to team members
- Status workflow (Draft → Under Review → Monitoring → Acting)

### Phase 4 (Advanced Viz)
- Network graph of defendant-product relationships
- Geographic heatmap of filing distribution
- Time series charts showing score evolution
- Interactive drill-downs

---

## Support

For issues or questions:
1. Check the main project README at `/tortsignal/README.md`
2. Review the PRD at `/tortsignal/docs/PRD.md`
3. Review the Frontend Design Brief at `/tortsignal/docs/FRONTEND_DESIGN_BRIEF.md`

---

## License

Part of the TortSignal project. See main project LICENSE file.
