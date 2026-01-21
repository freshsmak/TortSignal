# TortSignal

**Early-warning system for emerging mass torts.**

> "The Bloomberg Terminal for Mass Torts"

## The Thesis

Mass tort litigation follows predictable patterns. Years before an MDL forms, signals emerge across multiple data sources:

- **FDA adverse events** spike for a drug or device
- **Scientific literature** links a product to an injury
- **Court filings** cluster around a defendant/product pair
- **SEC filings** show increased litigation reserves

TortSignal monitors these signals continuously, scoring emerging candidates and surfacing the highest-conviction opportunities **before they become obvious**.

## Validated Opportunity

Backtested against 9 historical mass torts. In every case, detectable signals preceded the MDL by **3 months to 19 years**:

| Tort | Settlement | Detection Window | Key Signal |
|------|-----------|------------------|------------|
| Roundup/NHL | $11B+ | 19 months | IARC classification |
| AFFF/PFAS | $12B+ | 6 years | C8 Science Panel |
| Opioids | $50B+ | 18 years | DOJ prosecution |
| Pelvic Mesh | $8B+ | 3 years | FDA warning letter |
| 3M Earplugs | $6B | 3 years | False Claims Act |
| Vioxx | $4.85B | 4 years | JAMA meta-analysis |
| Talcum Powder | $1.5B+ | 10 years | IARC classification |
| Paraquat | Ongoing | 10+ years | UCLA epidemiology |
| Zantac | **Dismissed** | 5 months | (cautionary case) |

See `docs/VALIDATION.md` for detailed case studies.

---

## Discovery Mode

TortSignal operates in **Discovery Mode** — continuously scanning for signals you weren't looking for.

### The Problem With Traditional Monitoring

Traditional approach: *"Is Roundup bad?"* → Query FDA for Roundup → Get results

This misses:
- Products you didn't think to search for
- Injury patterns that emerge across multiple products
- Specialty drugs with smaller patient populations
- New device categories without historical baselines

### Signal-First Discovery

TortSignal inverts the question: *"What's going wrong out there?"*

Then traces back to the source.

**Example:** "Gastroparesis reports are up 200% across all drugs" → trace back → "concentrated in GLP-1 agonists" → Ozempic signal detected

### Discovery Axes

**FAERS (Drug Adverse Events):**
| Axis | Question | Catches |
|------|----------|---------|
| Product-first | Is drug X spiking? | Known drugs going bad |
| Reaction-first | What injuries are spiking? | Novel injury patterns |
| Pair discovery | What drug+reaction combos are anomalous? | Specific signals |
| Manufacturer-first | Company having QC issues? | Systemic problems |

**MAUDE (Device Adverse Events):**
| Axis | Question | Catches |
|------|----------|---------|
| Device-first | Is device X spiking? | Known devices going bad |
| Category-first | Are whole device classes failing? | All mesh, all hip implants |
| Manufacturer-first | Company having QC issues? | Systemic problems |

**Court Filings:**
| Axis | Question | Catches |
|------|----------|---------|
| Cluster detection | What defendant/product pairs emerging? | Litigation clusters |
| Geographic spread | How many states? How many firms? | Coordination signals |
| Filing velocity | Is pace accelerating? | Inflection points |

---

## Quick Start

```bash
# Setup
cd tortsignal
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Configure
cp .env.example .env
# Edit .env with DATABASE_URL, OPENAI_API_KEY, etc.

# Check connectors work (no database needed)
make health-check

# Run FDA discovery (dry run - no database)
make fda-discovery-dry

# With database: full discovery
make setup-db
make fda-discovery
make top-candidates
```

---

## Make Commands

```bash
# Discovery Mode
make fda-discovery        # Run FAERS + MAUDE discovery
make fda-discovery-dry    # Dry run (no database writes)
make fda-discovery-json   # Output results to JSON
make court-discovery      # Run court filing discovery
make full-discovery       # Run everything

# Development
make health-check         # Check connector health
make test-faers           # Quick FAERS test
make test-maude           # Quick MAUDE test
make top-candidates       # Show candidates from DB

# Setup
make install              # Install dependencies
make setup-db             # Initialize database schema
```

---

## Project Structure

```
tortsignal/
├── src/
│   ├── connectors/              # Data source connectors
│   │   ├── faers.py             # FDA drug adverse events ✅
│   │   ├── maude.py             # FDA device adverse events ✅
│   │   ├── pubmed.py            # Scientific literature ✅
│   │   └── unicourt.py          # Court filings (needs API key)
│   │
│   ├── extraction/              # LLM entity extraction
│   │   └── entity_extractor.py
│   │
│   ├── clustering/              # Candidate clustering
│   │   └── candidate_builder.py
│   │
│   ├── scoring/                 # Category-aware scoring
│   │   ├── category_router.py
│   │   └── scorer.py
│   │
│   └── pipeline/                # Orchestration
│       ├── discovery.py         # Court discovery
│       └── fda_discovery.py     # FDA discovery (main entry point)
│
├── schema/
│   └── 001_core.sql             # Postgres DDL
│
├── docs/
│   ├── PRD.md                   # Product requirements
│   ├── VALIDATION.md            # 9-tort backtest
│   ├── DATA_CONTRACTS.md        # Connector specs
│   └── ROADMAP.md               # Implementation phases
│
└── tests/
```

---

## Implementation Status

**Working Now:**
- ✅ FAERS connector with multi-axis discovery
- ✅ MAUDE connector with multi-axis discovery  
- ✅ PubMed connector
- ✅ Entity extraction (OpenAI)
- ✅ Candidate clustering and scoring
- ✅ FDA discovery pipeline
- ✅ Database schema

**Needs Your Implementation:**
- ⚠️ UniCourt connector (requires your API credentials)

**Future Phases:**
- SEC EDGAR integration
- Cross-source correlation
- Research Mode (on-demand deep dives)
- Dashboard UI

---

## Key Design Decisions

1. **Reaction-first discovery**: Inverts traditional monitoring to catch signals you weren't looking for.

2. **Pair-key candidates**: Clusters are (defendant, product) with injury as distribution. Maximizes signal when terminology is noisy.

3. **Category-aware scoring**: Weights vary by product category. FAERS 40% for pharma, MAUDE 40% for devices, literature 40% for chemicals.

4. **Explainability-first**: Every score decomposes into events backed by source documents.

5. **Awareness, not certainty**: Zantac proves signals don't guarantee outcomes. UI says "Investigate" not "Buy."

---

## Environment Variables

```bash
# Required
DATABASE_URL=postgres://user:pass@localhost:5432/tortsignal
OPENAI_API_KEY=sk-...

# For court discovery
UNICOURT_API_KEY=your-key
UNICOURT_BASE_URL=https://api.unicourt.com/v2

# Optional
LOG_LEVEL=INFO
DISCOVERY_DAYS=7
```

---

## License

Proprietary — Internal Use Only
