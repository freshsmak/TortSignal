# Pharmacovigilance V2: Litigation-Grade Signal Detection

## Problem Statement

Current FAERS discovery (V1) has critical flaws:
1. **No denominator**: Raw death counts meaningless without exposure data
2. **No baseline comparison**: Can't distinguish expected vs unexpected SAEs
3. **No population adjustment**: Flags cancer drugs (expected deaths) same as lifestyle drugs (unexpected deaths)
4. **No litigation-worthiness filter**: High death count ≠ high lawsuit potential

## Design Goals

Build a **litigation-grade early warning system** that identifies:
- **Unexpected harms** (SAE rate > clinical trial baseline)
- **In vulnerable populations** (otherwise healthy patients)
- **With preventable alternatives** (other drugs available)
- **Pre-litigation** (not yet in MDLs)

## Core Metrics

### 1. Per-Patient SAE Rate (Not Raw Counts)

**Formula:**
```
SAE Rate = (Reported SAEs × Under-reporting Multiplier) / Total Patient-Years Exposure
```

**Data Sources:**
- **Numerator (SAEs)**: FAERS reported + literature
- **Under-reporting multiplier**: 5-20× by SAE type (use conservative range)
- **Denominator (exposure)**:
  - IQVIA prescription data (paid)
  - Medicare Part D claims (free, US patients 65+)
  - FDA approval docs (market size estimates)
  - Analyst reports (prescriptions/revenue)

**Example:**
```
FARXIGA (2025):
  Reported deaths: 715
  Adjusted deaths: 3,575 - 14,300 (5-20× multiplier)
  Patient-years exposure: ~8 million (approx from revenue)
  Death rate: 0.045% - 0.18% per patient-year

KEYTRUDA (2025):
  Reported deaths: 3,892
  Adjusted deaths: 19,460 - 77,840
  Patient-years exposure: ~500,000 (smaller, sicker population)
  Death rate: 3.9% - 15.6% per patient-year

→ KEYTRUDA death rate is 86-200× higher than FARXIGA
→ But KEYTRUDA treats terminal cancer, FARXIGA treats stable diabetes
→ Litigation potential: FARXIGA >> KEYTRUDA
```

### 2. Expected vs Observed SAE Rate

**Formula:**
```
Disproportionality = Observed Rate / Expected Rate
```

**Expected Rate Sources:**
- **Clinical trials**: FDA approval documents (Section 6.1 Adverse Reactions)
- **Drug label**: Package insert adverse reaction frequencies
- **Published literature**: Post-marketing surveillance studies
- **Comparator drugs**: Same indication, same class

**Thresholds:**
- **<1.0×**: Lower than expected (likely under-reporting or protective effect)
- **1.0-2.0×**: Within expected range (monitoring)
- **2.0-5.0×**: Moderate signal (investigate)
- **>5.0×**: Strong signal (high litigation potential)

**Example:**
```
FARXIGA Death Rate:
  Observed (FAERS): 0.09% per year (midpoint estimate)
  Expected (clinical trials): 0.02% per year
  Disproportionality: 4.5× higher than trials
  → SIGNAL: Unexpected excess deaths

KEYTRUDA Death Rate:
  Observed (FAERS): 7.8% per year (midpoint)
  Expected (clinical trials): 8.2% per year
  Disproportionality: 0.95× (lower than trials)
  → NO SIGNAL: Deaths within expected range for terminal cancer
```

### 3. Patient Population Risk Adjustment

**Litigation Severity Multipliers:**

| Population | Multiplier | Rationale |
|------------|-----------|-----------|
| Healthy young adults (18-40) | 5.0× | Unexpected harm, long life expectancy |
| Chronic disease management (diabetes, hypertension) | 3.0× | Stable patients harmed by treatment |
| Elderly with comorbidities | 2.0× | Higher baseline risk, but still actionable |
| Life-threatening illness (heart failure) | 1.0× | Expected higher risk |
| Terminal illness (stage IV cancer) | 0.2× | Death expected, low litigation potential |

**Indication Risk Categories:**

| Indication | Risk | Examples |
|------------|------|----------|
| Lifestyle / Quality of Life | Very High | Erectile dysfunction, hair loss, cosmetics |
| Chronic Disease (stable) | High | Type 2 diabetes, hypertension, GERD |
| Acute/Serious (non-terminal) | Medium | Infections, surgery, pain management |
| Life-threatening | Low | Heart failure, stroke prevention |
| Terminal illness | Very Low | Stage IV cancer, end-stage organ failure |

**Example Scoring:**
```
FARXIGA:
  Indication: Type 2 diabetes (stable chronic disease)
  Population: Average age 62, multiple comorbidities
  Risk multiplier: 2.5×

KEYTRUDA:
  Indication: Stage IV melanoma (terminal cancer)
  Population: Average age 64, metastatic disease
  Risk multiplier: 0.2×

YUVAFEM (estrogen cream):
  Indication: Vaginal dryness (lifestyle/QoL)
  Population: Healthy postmenopausal women
  Risk multiplier: 4.5×
```

### 4. Disclosure & Preventability

**Label Disclosure Status:**
- **Boxed Warning**: Highest severity, clearly disclosed → Lower litigation risk
- **Warnings & Precautions**: Disclosed but not prominent → Medium risk
- **Adverse Reactions (>2% incidence)**: Expected, disclosed → Lower risk
- **Postmarketing reports only**: NOT in label → High litigation risk (failure to warn)

**Alternative Treatment Availability:**
- **Multiple alternatives exist**: Higher litigation risk ("should have prescribed X instead")
- **First-line standard of care**: Lower risk (no better option)
- **Last resort / salvage therapy**: Very low risk (benefit outweighs risk)

**Example:**
```
FARXIGA:
  Label disclosure: Death NOT in boxed warning (only DKA, amputations)
  Alternatives: 10+ other diabetes drugs (metformin, GLP-1s, etc.)
  Litigation risk: HIGH (undisclosed, preventable)

KEYTRUDA:
  Label disclosure: Death IS disclosed (immune-related adverse reactions)
  Alternatives: Limited for stage IV melanoma
  Litigation risk: LOW (disclosed, last resort)
```

### 5. Cross-Source Corroboration

**Evidence Score (0-10):**
- **FAERS signal** (disproportionality + velocity): 0-3 points
- **Literature evidence** (case reports, cohort studies): 0-2 points
- **FDA regulatory action** (warnings, recalls, label changes): 0-3 points
- **Litigation mentions** (existing cases, but not MDL): 0-1 point
- **Regulatory docket** (citizen petitions, safety reviews): 0-1 point

**Corroboration Levels:**
- **8-10 points**: Strong multi-source signal (HIGH CONVICTION)
- **5-7 points**: Moderate signal (INVESTIGATE)
- **3-4 points**: Weak signal (AWARENESS)
- **0-2 points**: Noise (QUIET)

## Final Litigation-Worthiness Score

**Formula:**
```
Litigation Score =
  (Disproportionality Score × 30) +
  (Population Risk × 25) +
  (Disclosure/Preventability × 20) +
  (Velocity/Acceleration × 15) +
  (Corroboration × 10)

Where:
  - Disproportionality: 0-10 (observed vs expected rate)
  - Population Risk: 0-10 (healthy young vs terminal)
  - Disclosure: 0-10 (undisclosed vs boxed warning)
  - Velocity: 0-10 (declining vs accelerating)
  - Corroboration: 0-10 (single source vs multi-source)
```

**Stages:**
- **80-100**: HIGH CONVICTION (sue now)
- **60-79**: INVESTIGATE (dig deeper)
- **40-59**: AWARENESS (monitor closely)
- **0-39**: QUIET (not actionable)

## Example Comparison

### KEYTRUDA (Current V1 Score: 95 → V2 Score: 18)

```
KEYTRUDA - Stage IV Melanoma Immunotherapy

Raw Metrics:
  Deaths (2025): 3,892 reported → 19,460 - 77,840 estimated
  Patient-years: ~500,000
  Death rate: 3.9% - 15.6%

Litigation Scoring:
  Disproportionality: 2/10 (within expected for terminal cancer)
  Population Risk: 1/10 (terminal patients, high baseline mortality)
  Disclosure: 2/10 (deaths clearly disclosed in label)
  Velocity: 6/10 (+45% increase, but from indication expansion)
  Corroboration: 7/10 (FAERS + literature + FDA monitoring)

Final Score: 18/100 - QUIET
Stage: Not litigation-worthy (expected harm in terminal population)
```

### FARXIGA (Current V1 Score: 85 → V2 Score: 76)

```
FARXIGA (dapagliflozin) - Type 2 Diabetes SGLT2 Inhibitor

Raw Metrics:
  Deaths (2025): 715 reported → 3,575 - 14,300 estimated
  Patient-years: ~8,000,000
  Death rate: 0.045% - 0.18%

Litigation Scoring:
  Disproportionality: 8/10 (4.5× higher than clinical trials)
  Population Risk: 7/10 (stable chronic disease patients)
  Disclosure: 8/10 (death not in boxed warning, only DKA/amputation)
  Velocity: 9/10 (+80% spike Q4 2024)
  Corroboration: 6/10 (FAERS + label change + case reports)

Final Score: 76/100 - INVESTIGATE
Stage: High litigation potential (unexpected excess deaths)
Action: Deep dive on causal mechanism, competing litigation
```

### YUVAFEM (Current V1 Score: 25 → V2 Score: 88)

```
YUVAFEM (estradiol vaginal cream) - Vaginal Atrophy Treatment

Raw Metrics:
  Deaths (2025): 12 reported → 60 - 240 estimated
  Patient-years: ~500,000
  Death rate: 0.012% - 0.048%

Litigation Scoring:
  Disproportionality: 9/10 (12× higher than expected for topical cream)
  Population Risk: 9/10 (healthy postmenopausal women, lifestyle drug)
  Disclosure: 10/10 (cardiovascular death NOT in label warnings)
  Velocity: 10/10 (+300% spike in 6 months)
  Corroboration: 6/10 (FAERS spike + 2 case reports + no FDA action yet)

Final Score: 88/100 - HIGH CONVICTION
Stage: Excellent litigation target (unexpected deaths, healthy population)
Action: File MDL petition, recruit plaintiffs NOW
```

## Data Sources & Implementation

### Required Data (In Priority Order)

**Tier 1: Must Have (Free/Cheap)**
1. FAERS adverse events (free, FDA API)
2. FDA drug labels via DailyMed (free)
3. Medicare Part D prescriber data (free, CMS)
4. PubMed literature (free, NIH API)
5. FDA dockets & safety communications (free, regulations.gov)

**Tier 2: Should Have (Paid, <$500/mo)**
1. IQVIA prescription volume ($300-500/month for limited access)
2. UniCourt litigation search ($300/month premium)
3. Clinical trials data from ClinicalTrials.gov (free but needs parsing)

**Tier 3: Nice to Have (Expensive, MVP can skip)**
1. Symphony Health prescription data ($5k+/month)
2. FDA AERS (pre-FAERS historical data)
3. EMA EudraVigilance (European AE data)
4. JMDC (Japan), MHRA Yellow Card (UK)

### MVP Implementation Plan

**Phase 1: Per-Patient Rate Calculation**
- Pull IQVIA prescription volume OR estimate from Medicare Part D
- Calculate SAE rates with uncertainty ranges (5-20× multiplier)
- Compare to clinical trial baselines from FDA labels

**Phase 2: Population Risk Adjustment**
- Parse FDA labels for indication (DailyMed API)
- Map indications to risk categories (manual initially, ML later)
- Apply population multipliers to scores

**Phase 3: Disclosure Analysis**
- Extract boxed warnings, warnings & precautions from labels
- Flag undisclosed SAEs (not in label but in FAERS)
- Score disclosure completeness

**Phase 4: Cross-Source Corroboration**
- Integrate FDA safety communications
- PubMed search for case reports
- UniCourt search for existing litigation
- Calculate multi-source evidence score

**Phase 5: Litigation-Worthiness Scoring**
- Combine all factors into final 0-100 score
- Re-score existing candidates
- Validate against known MDLs (should score low post-litigation)

## Success Metrics

**Precision**: Of drugs scored >80, what % lead to MDLs within 2 years?
- Target: >30% (1 in 3 HIGH CONVICTION signals form MDLs)

**Recall**: Of MDLs formed, what % were in our watchlist 6+ months prior?
- Target: >70% (catch most pre-litigation opportunities)

**Filtering**: Remove terminal illness drugs from tort watchlist
- Target: 0% cancer/hospice drugs in HIGH CONVICTION tier

**Actionability**: Plaintiff firms can act on HIGH CONVICTION signals
- Target: Score >80 = firm opens investigation within 30 days
