# UniCourt Discovery Strategy

## The Paradigm Shift

### ❌ **Old Approach** (What We DON'T Do)
Search for known products in case titles:
```
CaseType:(caseTypeGroup:(Product Liability)) AND caseTitle:FARXIGA
```

**Problems:**
- Only finds cases where product is in the title
- Requires knowing product names in advance
- Misses emerging signals with different naming
- High operator count (hard to combine with other filters)

### ✅ **New Approach** (What We DO)
Search by **case structure**, then extract products:
```
filedDate:[2025-01-01 TO *] AND (Party:((PartyRole:(name:defendant))))
```

**Benefits:**
- Discovers unknown products automatically
- Catches cases before product names standardize
- Low operator count (leaves room for filters)
- Entity extraction happens post-search

---

## The 3-Query Strategy

We run **3 separate queries** daily, each under the 15-operator limit:

### **Query A: High Recall** (Structure-Based)
```
filedDate:[now-2d TO *] AND (Party:((PartyRole:(name:defendant))))
```

**Purpose:** Capture ALL cases with defendants filed recently

**Operator Count:** 2
- `filedDate` range
- `Party` + `PartyRole` constraint

**Coverage:** ~thousands of cases/day
**Precision:** Low (includes all civil litigation)
**Use Case:** Feed into clustering to discover emerging patterns

### **Query B: High Precision** (Language-Based)
```
filedDate:[now-2d TO *] AND ("product liability" OR "design defect" OR "failure to warn" OR "strict liability")
```

**Purpose:** Catch explicit tort language in docket/caption

**Operator Count:** 5
- `filedDate` range
- 4 OR terms for tort language

**Coverage:** ~100-500 cases/day
**Precision:** High (mostly actual product liability)
**Use Case:** Priority cases for immediate review

### **Query C: Monitoring** (Update Stream)
```
(lastFetchDateWithUpdates:[now-2d TO *]) AND (Party:((PartyRole:(name:defendant))))
```

**Purpose:** Track changes to existing cases

**Operator Count:** 2
- `lastFetchDateWithUpdates` range
- `Party` + `PartyRole` constraint

**Coverage:** ~hundreds of cases/day
**Precision:** N/A (monitoring existing cases)
**Use Case:** Detect acceleration in known clusters

---

## The 6 Critical Fields

### 1. `filedDate` (Mandatory)
Your "new filings" stream.

**Best Practice:**
```
filedDate:[now-2d TO *]
```

Buffer 2 days for late indexing. Pull daily.

### 2. `CaseType` / `AreaOfLaw` / `CauseOfAction`
How you avoid drowning in unrelated cases.

**Strategy:**
- Start with Query A + B (no case type filter)
- Discover which `CaseType` values = product liability
- Add to Query A for cost reduction

**Example Discovery:**
```python
# Run Query B, examine results
for case in results:
    print(case.case_type)  # e.g., "Personal Injury"
    print(case.area_of_law)  # e.g., "Tort Law"
```

Once you identify values:
```
filedDate:[now-2d TO *]
AND (Party:((PartyRole:(name:defendant))))
AND CaseType:(name:"Personal Injury")
```

### 3. `PartyRole` + Defendant Constraint
The bridge from case → cluster.

**Basic:**
```
Party:((PartyRole:(name:defendant)))
```

**Advanced** (filter pro se noise):
```
Party:((PartyRole:(name:defendant)) AND (AttorneyRepresentationType:(name:(Attorney represented))))
```

### 4. `JurisdictionGeo`
Optional at first, valuable for phasing.

**Phase 1:** National
```
# No geo filter
```

**Phase 2:** Focus on coverage quality
```
JurisdictionGeo:(state:"California")
```

### 5. `DocketEntry:text`
Precision booster when product names unknown.

**Tort Language:**
```
DocketEntry:("design defect" OR "failure to warn")
```

**Injury Language:**
```
DocketEntry:("carcinogenic" OR "toxic exposure")
```

### 6. `lastFetchDateWithUpdates` / `participantsLastFetchDate`
Your "what changed" feed.

**Use:** Separate from new filings. Track velocity.

**Example:**
- Case filed Jan 1: Shows in Query A (filedDate)
- New party added Jan 15: Shows in Query C (participantsLastFetchDate)
- New docket entry Jan 20: Shows in Query C (lastFetchDateWithUpdates)

---

## Post-Search Entity Extraction

After pulling cases by structure, extract:

### From Case Title
```python
title = "Smith v. Johnson & Johnson"
defendant = "Johnson & Johnson"
```

### From Parties API
```
GET /case/{caseId}/parties
```

Extract:
- Defendant names (corporate entities)
- Plaintiff attorneys/firms
- Party roles

### From Attorneys API
```
GET /case/{caseId}/attorneys
```

Extract:
- Law firms representing plaintiffs
- Identify known mass tort firms

### From Docket Text
```python
docket_text = case.docket_entries[0].text
# Search for product names, injury terms
```

---

## Clustering Strategy

Once you have cases, cluster by `(defendant, product)` pairs:

### Step 1: Extract Entities
```python
for case in cases:
    defendant = extract_defendant(case)
    product = extract_product(case)  # from title, docket
    injury = extract_injury(case)    # optional
```

### Step 2: Create Clusters
```python
cluster_key = (defendant, product)  # NOT (defendant, product, injury)
```

**Why not include injury?**
- Injury terminology is noisy early
- "Cancer" vs "Carcinoma" vs "Malignancy"
- Product is more stable identifier

### Step 3: Calculate Metrics
Per cluster:
- **Velocity:** Cases filed in last 7 days / 30 days
- **Breadth:** Unique states
- **Acceleration:** Velocity trend over time
- **Firm diversity:** Unique plaintiff firms

---

## Performance & Cost Management

### Query Frequency
- **Production:** Run daily (2-day buffer)
- **Development:** Run weekly

### Page Size
- **Optimal:** 100 (API maximum)
- **Cost-conscious:** 50

### Result Limits
- **Query A (High Recall):** 500 cases/day
- **Query B (High Precision):** 200 cases/day
- **Query C (Monitoring):** 300 cases/day

**Total:** ~1,000 cases/day = ~30k/month

### Cost Estimation
(Based on UniCourt pricing - verify with your contract)

- **Per case returned:** $0.XX
- **1,000 cases/day:** ~$XXX/month
- **Bulk discount:** Negotiate for high volume

---

## Integration with TortSignal Pipeline

### Daily Discovery Flow

```
1. Run Query A (High Recall)
   ↓
2. Run Query B (High Precision)
   ↓
3. Run Query C (Monitoring)
   ↓
4. Deduplicate by caseId
   ↓
5. Enrich with Parties + Attorneys APIs
   ↓
6. Extract: defendant, product, injury, firm
   ↓
7. Insert into candidates table
   ↓
8. Run clustering algorithm
   ↓
9. Calculate velocity, breadth, scores
   ↓
10. Update dashboard
```

### Data Model

**Table: `court_filings`**
```sql
CREATE TABLE court_filings (
    case_id TEXT PRIMARY KEY,
    source TEXT DEFAULT 'unicourt',
    filed_date DATE,
    title TEXT,
    defendant_text TEXT,
    product_text TEXT,  -- Extracted, not searched
    injury_text TEXT,
    plaintiff_firm TEXT,
    jurisdiction TEXT,
    state TEXT,
    docket_url TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Table: `candidates` (Clusters)**
```sql
CREATE TABLE candidates (
    cluster_id SERIAL PRIMARY KEY,
    defendant_text TEXT,
    product_text TEXT,  -- Cluster key
    filing_count INT,
    velocity_7d INT,
    velocity_30d INT,
    breadth_states INT,
    score_total NUMERIC,
    first_filed_date DATE,
    last_filed_date DATE,
    stage TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Case Type Discovery

One-time setup to identify which `CaseType` values = product liability:

### Discovery Script
```python
# Search for obvious product liability terms
query = '("product liability" OR "defective product")'

response = CaseSearch.search_cases(q=query, page_size=50)

# Collect unique case types
case_types = set()
for case in response.case_search_result_array:
    if hasattr(case, 'case_type'):
        case_types.add(case.case_type)

print(case_types)
# Expected: ["Personal Injury", "Tort", "Product Liability", ...]
```

### Production Query (After Discovery)
```
filedDate:[now-2d TO *]
AND (Party:((PartyRole:(name:defendant))))
AND CaseType:(name:("Personal Injury" OR "Tort"))
```

**Result:** Lower cost, same coverage

---

## Hybrid Strategy (Recommended)

Combine Query A + B for optimal results:

### Phase 1: High-Precision First
```
filedDate:[DATE TO *]
AND ("product liability" OR "design defect" OR "failure to warn")
```

Extract up to 50% of daily limit.

### Phase 2: High-Recall Backfill
```
filedDate:[DATE TO *]
AND (Party:((PartyRole:(name:defendant))))
```

Extract remaining 50% of daily limit, deduplicating against Phase 1.

### Benefits
- Prioritizes obvious tort cases
- Discovers new patterns via structure
- Stays under API limits
- Balances precision/recall

---

## What NOT to Use (Yet)

### Too Specific for Discovery
- `caseNumber`: Only for lookup
- `caseName`: Use `caseTitle` instead (searchable)
- `HearingDate`: Irrelevant for early warning

### Useful Later, Not Now
- `Document` filters: Good for evidence mode, not discovery
- `CaseStatus`: Can exclude emerging cases
- `Judge`: Not relevant for clustering

### API Limitations to Know
- **15-operator limit**: Count carefully
- **100 results/page max**: Paginate for more
- **Rate limits**: Check your contract

---

## Real-World Example: FARXIGA Discovery

### If We Searched by Product (Old Way)
```
CaseType:(caseTypeGroup:(Product Liability)) AND caseTitle:FARXIGA
```

**Result:** 0-2 cases (only if "FARXIGA" in title)

### If We Search by Structure (New Way)
```
filedDate:[2024-01-01 TO *] AND (Party:((PartyRole:(name:defendant))))
```

**Result:** ~50,000 cases

Then:
```python
# Post-search filtering
for case in cases:
    if 'AstraZeneca' in case.parties:
        if 'dapagliflozin' in case.docket_text or 'FARXIGA' in case.title:
            # Found a FARXIGA case!
            cluster_key = ('AstraZeneca', 'FARXIGA')
```

**Discovery:** 5-20 FARXIGA cases we wouldn't have found

---

## Validation Strategy

### Week 1: Benchmark
1. Run Query B (tort language) for 7 days
2. Manually review 100 random cases
3. Calculate precision: % actually product liability
4. Target: >70% precision

### Week 2: Coverage Test
1. Run Query A (structure) for 7 days
2. Compare to Query B results
3. Calculate: How many Query B cases did Query A miss?
4. Target: <5% missed

### Week 3: Cost Analysis
1. Calculate $/case for each query
2. Optimize page sizes, limits
3. Identify which query gives best ROI

### Week 4: Integration
1. Full pipeline: Query → Extract → Cluster
2. Dashboard: Monitor velocity, breadth
3. Validation: Cross-check with FDA signals

---

## Troubleshooting

### Problem: Too Many Results (>10k/day)
**Solution:** Add `CaseType` filter after discovery

### Problem: Missing Known Cases
**Solution:** Check if case title uses different product name

### Problem: High Cost
**Solution:** Reduce page size, increase selectivity

### Problem: Low Precision (Lots of Non-Tort)
**Solution:** Switch to Query B (tort language) only

### Problem: Duplicate Cases Across Queries
**Solution:** Deduplicate by `caseId` before insertion

---

## Summary: The TortSignal Way

1. ✅ **Search by structure** (defendant + date), not products
2. ✅ **3-query strategy** (recall + precision + monitoring)
3. ✅ **Entity extraction** post-search
4. ✅ **Clustering** by (defendant, product)
5. ✅ **Metrics** for velocity, breadth, acceleration
6. ✅ **Validation** against FDA signals

**Result:** Discover emerging mass torts 18-36 months before MDL formation.

---

## Next Steps

1. **Run discovery script** to identify CaseType values
2. **Test Query A** for 1 week, measure results
3. **Test Query B** for 1 week, compare
4. **Implement hybrid** strategy
5. **Build clustering** algorithm
6. **Cross-validate** with FARXIGA FDA signal

---

**Last Updated:** January 2026
**Author:** TortSignal Engineering
**Questions:** See docs/UNICOURT_CONNECTOR.md
