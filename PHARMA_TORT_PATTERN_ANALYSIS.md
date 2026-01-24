# Pharmaceutical Tort Pattern Analysis
## Reverse Engineering Major MDLs (2014-2025) for Litigation Intelligence

**Purpose**: Extract codeable patterns from major pharmaceutical product liability cases to build filters that distinguish litigation opportunities from pharmacovigilance signals.

**Key Insight**: Not all high-SAE drugs are litigation opportunities. We need to filter for *unexpected harm in relatively healthy populations*, not just high absolute SAE counts.

---

## Part 1: Major Cases Inventory

| Drug/Product | Defendant | Class | Indication | Primary SAE | Timeline | Cases | Settlement/Status | Patient Pop |
|--------------|-----------|-------|------------|-------------|----------|-------|-------------------|-------------|
| **Ozempic/Wegovy** | Novo Nordisk | GLP-1 agonist | Diabetes/obesity | Gastroparesis, bowel obstruction | 2024→ | 3,063 pending | $2B+ exposure, no settlement yet | Relatively healthy |
| **Xarelto** | Bayer/J&J | Anticoagulant | AFib, DVT | Uncontrollable bleeding (no antidote) | 2014-2019 | ~25,000 | $775M (2019) | Chronic but stable |
| **Invokana** | J&J | SGLT2 inhibitor | Type 2 diabetes | Ketoacidosis, amputations, kidney injury | 2016-2019 | 878 active (2019) | $100M+ confidential | Manageable condition |
| **Risperdal** | J&J | Antipsychotic | Schizophrenia | Gynecomastia (boys/men) | 2013→ | Thousands | $2.2B DOJ + individual verdicts | **Off-label pediatric** |
| **Zantac** | GSK/Sanofi | H2 blocker | Heartburn | NDMA → cancer | 2019-2024 | 90K+ filed | GSK $2.2B, Sanofi $200-250M | Very healthy (heartburn) |
| **Taxotere** | Sanofi | Chemotherapy | Breast cancer | **Permanent alopecia** | 2016→ | 2,988 pending | **NO settlements** (defense wins) | Terminal cancer |
| **Talcum Powder** | J&J | Consumer product | Cosmetic | Ovarian cancer, mesothelioma | 2013-2024 | 67,204 active | $6.48B proposed, $700M states | Healthy consumers |
| **Hair Relaxer** | L'Oreal et al | Consumer product | Cosmetic | Uterine/endometrial cancer | 2022→ | 10,948 pending | No settlement yet, trials 2027 | Healthy consumers |
| **Essure** | Bayer | Device | Contraception | Migration, perforation, pain | 2016-2020 | ~39,000 | $1.6B (2020) | Healthy women |

---

## Part 2: Pattern Extraction

### A. Drug Class Patterns

**HIGH LITIGATION RISK**:
- **Diabetes drugs**: Invokana (SGLT2), Ozempic (GLP-1) → Lifestyle/chronic management class
- **Anticoagulants**: Xarelto → Chronic condition, wide usage
- **Heartburn**: Zantac → Very benign indication, high volume
- **Consumer products**: Talc, hair relaxer → Cosmetic use, healthy populations
- **Devices**: Essure → Elective procedure, healthy populations

**LOW/NO LITIGATION RISK**:
- **Chemotherapy**: Taxotere → 2,988 cases but **NO settlements**, defense wins
- **Antipsychotics**: Risperdal litigation driven by **off-label pediatric use**, not core indication

**PATTERN**: Litigation thrives on drugs for manageable/elective conditions in relatively healthy populations. Terminal disease drugs face "assumption of risk" defense.

### B. Indication Severity Score

| Indication | Severity Score | Litigation Risk | Examples |
|------------|----------------|-----------------|----------|
| Cosmetic/lifestyle | 1 | ⭐⭐⭐⭐⭐ HIGHEST | Hair relaxer, talc, Ozempic (weight loss) |
| Heartburn/minor GI | 2 | ⭐⭐⭐⭐⭐ HIGHEST | Zantac |
| Type 2 diabetes | 3 | ⭐⭐⭐⭐ HIGH | Invokana, Ozempic |
| AFib/clotting (chronic) | 4 | ⭐⭐⭐ MODERATE | Xarelto |
| Contraception | 3 | ⭐⭐⭐⭐ HIGH | Essure |
| Schizophrenia (adult) | 6 | ⭐⭐ LOW | Risperdal (core indication) |
| Cancer | 9 | ⭐ VERY LOW | Taxotere (NO settlements despite cases) |
| Transplant/HIV | 9 | ⭐ VERY LOW | (Expected high SAEs) |

**CODEABLE RULE**: `litigation_risk_score = (10 - indication_severity) * SAE_velocity`

### C. SAE Type Patterns

**LITIGATION TRIGGERS** (Permanent/Disfiguring/Life-Altering):
- ✅ Amputations (Invokana)
- ✅ Permanent hair loss (Taxotere - though defense won)
- ✅ Gynecomastia (Risperdal)
- ✅ Cancer (Zantac, talc, hair relaxer)
- ✅ Gastroparesis/chronic GI (Ozempic)
- ✅ Device migration/chronic pain (Essure)
- ✅ Uncontrollable bleeding with no antidote (Xarelto)

**NOT LITIGATION TRIGGERS**:
- ❌ Expected chemo side effects (nausea, fatigue)
- ❌ Temporary/reversible events in terminal patients

**PATTERN**: Permanent disfigurement or chronic conditions from drugs meant for manageable problems = high litigation.

### D. Timeline Patterns

| Case | Drug Approval | Lawsuit Filed | Lag Time | Notes |
|------|---------------|---------------|----------|-------|
| Hair Relaxer | N/A (old product) | Oct 2022 | Immediate | Right after NIH study |
| Ozempic | 2017 (diabetes), 2021 (weight) | 2024 | 3-7 years | After widespread off-label use |
| Zantac | 1983 | 2019 | 36 years | NDMA discovery triggered |
| Invokana | 2013 | 2016 | 3 years | After FDA warnings |
| Xarelto | 2011 | 2014 | 3 years | After market penetration |
| Essure | 2002 | 2016 | 14 years | After adverse event accumulation |

**SWEET SPOT**: 2-7 years post-approval or post-blockbuster status
- Year 1-2: Not enough cases accumulated
- Year 2-7: Evidence builds, attorneys notice patterns
- Year 7+: May be flagged already or settled

**FAERS IMPLICATION**: Look for drugs approved 2018-2023 showing recent SAE velocity spikes.

### E. Patient Population

**HIGH LITIGATION**:
- Healthy consumers (talc, hair relaxer)
- Lifestyle medication users (Ozempic for weight loss)
- Chronic but stable conditions (diabetes, AFib)
- Elective procedures (Essure)
- **Off-label pediatric** (Risperdal)

**LOW LITIGATION**:
- Terminal cancer patients (Taxotere)
- Transplant recipients
- HIV/AIDS patients
- Severely mentally ill (core Risperdal indication)

**PATTERN**: "Could this person have avoided the drug?" = litigation risk

---

## Part 3: Codeable Filters for Litigation Intelligence

### Filter 1: Drug Class Whitelist/Blacklist

```python
# HIGH LITIGATION RISK CLASSES (include)
WHITELIST_DRUG_CLASSES = [
    'GLP-1 agonist',           # Ozempic
    'SGLT2 inhibitor',         # Invokana
    'H2 blocker',              # Zantac
    'PPI',                     # Proton pump inhibitors
    'Anticoagulant (oral)',    # Xarelto, Eliquis
    'Weight loss',             # Lifestyle drugs
    'ED treatment',            # Lifestyle
    'Hair loss treatment',     # Cosmetic
    'Cosmetic device',         # Essure-like
]

# LOW LITIGATION RISK CLASSES (exclude)
BLACKLIST_DRUG_CLASSES = [
    'Chemotherapy',            # Taxotere - terminal patients
    'Antiretroviral',          # HIV - life-saving
    'Immunosuppressant',       # Transplant - life-saving
    'Antipsychotic',           # Severe mental illness (unless pediatric off-label)
    'Antimicrobial',           # Generally low risk
]
```

### Filter 2: Indication Severity Score

```python
def get_indication_severity(drug_metadata):
    """Return 1-10 score where 1=cosmetic, 10=terminal"""

    INDICATION_SCORES = {
        'cosmetic': 1,
        'weight_loss': 2,
        'heartburn': 2,
        'gerd': 2,
        'type_2_diabetes': 3,
        'contraception': 3,
        'erectile_dysfunction': 2,
        'afib': 4,
        'dvt': 5,
        'hypertension': 4,
        'schizophrenia': 6,
        'bipolar': 6,
        'hiv': 8,
        'cancer': 9,
        'transplant': 9,
    }

    # Check metadata for indication keywords
    for indication, score in INDICATION_SCORES.items():
        if indication in drug_metadata.get('indication', '').lower():
            return score

    return 5  # Default: moderate severity
```

### Filter 3: Expected SAE Baseline by Drug Class

```python
def get_expected_death_rate(drug_class):
    """Return expected death rate per 10K patients"""

    BASELINE_DEATH_RATES = {
        'chemotherapy': 500,        # 5% mortality expected
        'immunosuppressant': 200,   # 2% mortality expected
        'antiretroviral': 100,      # 1% mortality expected
        'anticoagulant': 50,        # 0.5% bleeding mortality expected
        'antipsychotic': 30,        # 0.3% sudden cardiac death
        'diabetes': 10,             # 0.1% baseline
        'heartburn': 1,             # 0.01% (essentially zero)
        'cosmetic': 0.1,            # Near zero expected
    }

    return BASELINE_DEATH_RATES.get(drug_class, 10)

def is_unexpected_sae_rate(drug, observed_deaths_per_10k):
    """Return True if death rate exceeds expected baseline"""
    expected = get_expected_death_rate(drug['drug_class'])
    return observed_deaths_per_10k > (expected * 2)  # 2x baseline = signal
```

### Filter 4: Litigation Timeline Model

```python
from datetime import datetime

def get_litigation_window_score(drug_approval_year):
    """Return 0-10 score for litigation timing sweet spot"""
    current_year = datetime.now().year
    years_since_approval = current_year - drug_approval_year

    if years_since_approval < 2:
        return 2  # Too early, not enough cases
    elif 2 <= years_since_approval <= 7:
        return 10  # SWEET SPOT
    elif 7 < years_since_approval <= 15:
        return 6  # Still viable, but may be flagged already
    else:
        return 3  # Old drug, likely already settled or known
```

### Filter 5: Off-Label / Pediatric Use Flag

```python
def check_high_risk_population(drug_metadata):
    """Check for high-litigation-risk populations"""

    HIGH_RISK_FLAGS = {
        'pediatric_use': 3.0,      # Risperdal pattern
        'off_label_cosmetic': 2.5, # Ozempic for weight loss
        'pregnancy': 2.0,          # Zofran pattern
        'healthy_consumer': 2.0,   # Talc, hair relaxer
    }

    multiplier = 1.0
    metadata_text = str(drug_metadata).lower()

    for flag, mult in HIGH_RISK_FLAGS.items():
        if flag.replace('_', ' ') in metadata_text:
            multiplier *= mult

    return multiplier
```

### Filter 6: Composite Litigation Risk Score

```python
def calculate_litigation_risk_score(drug, faers_signal):
    """
    Combine all factors into 0-100 litigation risk score.

    Args:
        drug: Dict with drug_class, indication, approval_year, metadata
        faers_signal: Dict with SAE counts, velocity, etc.

    Returns:
        Float 0-100, where 70+ = HIGH_CONVICTION litigation opportunity
    """

    # Base score from FAERS velocity
    base_score = min(faers_signal['velocity'] * 2, 40)  # Cap at 40

    # Indication severity factor (inverse - cosmetic=high, cancer=low)
    indication_severity = get_indication_severity(drug)
    indication_factor = (10 - indication_severity) / 10  # 0.0-1.0

    # Drug class multiplier
    if drug['drug_class'] in WHITELIST_DRUG_CLASSES:
        class_multiplier = 1.5
    elif drug['drug_class'] in BLACKLIST_DRUG_CLASSES:
        class_multiplier = 0.1
    else:
        class_multiplier = 1.0

    # Timeline score
    timeline_score = get_litigation_window_score(drug['approval_year']) * 2  # 0-20

    # Unexpected SAE multiplier
    observed_rate = faers_signal['death_count'] / faers_signal['total_reports'] * 10000
    if is_unexpected_sae_rate(drug, observed_rate):
        sae_multiplier = 1.5
    else:
        sae_multiplier = 1.0

    # Population risk multiplier
    population_multiplier = check_high_risk_population(drug)

    # Composite score
    litigation_score = (
        (base_score * indication_factor * class_multiplier * sae_multiplier) +
        timeline_score
    ) * population_multiplier

    return min(litigation_score, 100)  # Cap at 100
```

---

## Part 4: Re-Analysis of Our 100 Discovered Drugs

### Current Discovery Results (Top Signals)

From our FAERS run, we flagged drugs like:
- Acetaminophen (Tylenol)
- Methotrexate (chemo)
- Prednisone (steroid)
- Tacrolimus (immunosuppressant)
- Fentanyl (opioid)
- Ibuprofen (NSAID)

### Why These Are NOT Litigation Opportunities

| Drug | Class | Indication | Why Not Litigable | Expected Death Rate |
|------|-------|------------|-------------------|---------------------|
| Methotrexate | Chemo | Cancer | Terminal patients, expected SAEs | 5% (500/10K) |
| Tacrolimus | Immunosuppressant | Transplant | Life-saving, expected SAEs | 2% (200/10K) |
| Prednisone | Corticosteroid | Inflammation | Known risks, generic, old | 0.5% (50/10K) |
| Acetaminophen | Analgesic | Pain/fever | OTC, extremely old, known risks | 0.01% (1/10K) |
| Fentanyl | Opioid | Severe pain | Scheduled, known risks, opioid crisis | 1% (100/10K) |

**These are pharmacovigilance signals, not litigation intelligence.**

### What We SHOULD Be Flagging

Using our new filters, we should prioritize:

**Tier 1 - Highest Litigation Potential**:
1. **GLP-1 agonists** (Ozempic class) - IF showing gastroparesis/bowel signals
2. **SGLT2 inhibitors** (Invokana class) - IF showing amputation/ketoacidosis
3. **Newer anticoagulants** - IF showing bleeding without antidote
4. **Weight loss drugs** (2018-2023 approvals) - Any permanent SAEs
5. **Cosmetic devices** - Migration, chronic pain
6. **Heartburn drugs** (PPIs, H2 blockers) - Cancer signals

**Tier 2 - Moderate Litigation Potential**:
1. **Type 2 diabetes drugs** (non-GLP-1) - Unexpected SAEs
2. **Contraceptives** (devices, pills) - Permanent harm
3. **Hair loss treatments** - Permanent disfigurement
4. **ED drugs** - Unexpected vision/hearing loss

**Tier 3 - Low Priority (Pharmacovigilance Only)**:
1. **Chemotherapy** - Any SAEs (expected in terminal patients)
2. **Immunosuppressants** - Any SAEs (life-saving, expected)
3. **HIV drugs** - Any SAEs (life-saving, expected)
4. **Antipsychotics** - SAEs in adult patients (expected)

---

## Part 5: Implementation Roadmap

### Step 1: Enrich Drug Metadata (IMMEDIATE)

We need to add to our FAERS discovery script:

```python
def enrich_drug_metadata(drug_name):
    """
    Query OpenFDA drug API for:
    - Drug class (route, pharmacologic_class)
    - Indications (indications_and_usage)
    - Approval year (openfda.application_number -> approval date)
    """
    # OpenFDA drugs API: https://api.fda.gov/drug/label.json?search=...
    pass
```

### Step 2: Apply Litigation Filters (IMMEDIATE)

Modify scoring in `discover_faers_signals.py`:

```python
# OLD SCORE (pharmacovigilance)
score_total = (severity_score * 0.4) + (velocity_score * 0.3) + ...

# NEW SCORE (litigation intelligence)
score_total = calculate_litigation_risk_score(
    drug={
        'drug_class': drug_metadata['class'],
        'indication': drug_metadata['indication'],
        'approval_year': drug_metadata['approval_year'],
        'metadata': drug_metadata
    },
    faers_signal={
        'velocity': velocity,
        'death_count': death_recent,
        'total_reports': total_reports,
        ...
    }
)
```

### Step 3: Add Separate "Pharmavigilance Score" (NEXT SPRINT)

Keep both scoring systems:

```sql
ALTER TABLE candidates
ADD COLUMN pharma_score FLOAT,        -- For hospitals/FDA
ADD COLUMN litigation_score FLOAT;    -- For plaintiff firms
```

### Step 4: Dashboard Filters (NEXT SPRINT)

Add toggle in Streamlit:
- "Litigation Intelligence Mode" (our plaintiff firm product)
- "Pharmacovigilance Mode" (hospital/pharma/FDA product)

---

## Part 6: Expected Outcomes

### Before Litigation Filters (Current)
Top 10 signals:
1. Methotrexate (chemo) - Score 89
2. Tacrolimus (transplant) - Score 87
3. Acetaminophen (OTC pain) - Score 82
4. Prednisone (steroid) - Score 78
5. ... (all old drugs with expected SAEs)

### After Litigation Filters (Expected)
Top 10 signals:
1. **Ozempic/Wegovy** (if gastroparesis signal) - Score 92
2. **Mounjaro** (GLP-1, newer) - Score 88
3. **Jardiance** (SGLT2, if amputation signal) - Score 84
4. **[New weight loss drug 2022]** - Score 81
5. **[New heartburn drug with cancer signal]** - Score 78
6. **[Cosmetic device with migration]** - Score 75
7. ... (actual litigation opportunities)

---

## Part 7: Business Model Implications

### Product Line 1: Litigation Intelligence (TortSignal - Plaintiff Focus)
**Customer**: Plaintiff law firms (mass tort)
**Filters**: Litigation risk score 70+
**Value Prop**: "Discover the next Ozempic MDL before 10,000 cases are filed"
**Pricing**: $5K-50K/month per firm

### Product Line 2: Pharmacovigilance Signals (SafetySignal - Hospital/Pharma Focus)
**Customer**: Hospital systems, pharma companies, FDA contractors
**Filters**: Pharma score 70+ (raw SAE velocity, no indication filtering)
**Value Prop**: "Early warning system for adverse events requiring protocol changes"
**Pricing**: $10K-100K/year per institution

**CRITICAL**: These are different products for different customers. We keep both scoring systems.

---

## Part 8: Validation Test

### Hypothesis Test: "Would our new filters have caught Ozempic?"

**Ozempic Facts**:
- Drug class: GLP-1 agonist ✅ (whitelist)
- Indication: Type 2 diabetes (severity=3) / Weight loss (severity=2) ✅ (high litigation risk)
- Approval: 2017 diabetes, 2021 weight loss → 2024 lawsuits = 3-7 year window ✅ (sweet spot)
- SAE type: Gastroparesis (chronic, permanent) ✅ (litigation trigger)
- Patient population: Relatively healthy (diabetes/obesity management) ✅ (high risk)
- Expected death rate: ~0.1% (10/10K) for diabetes drugs
- Observed rate: IF showing 2x baseline → ✅ unexpected

**NEW LITIGATION SCORE**: ~85-95 (HIGH_CONVICTION)
**OLD PHARMA SCORE**: Maybe 60-70 (would be buried under chemo drugs)

### Hypothesis Test: "Would our filters correctly REJECT Taxotere?"

**Taxotere Facts**:
- Drug class: Chemotherapy ❌ (blacklist)
- Indication: Breast cancer (severity=9) ❌ (terminal, low litigation risk)
- SAE type: Permanent alopecia ⚠️ (disfiguring, but...)
- Patient population: Terminal cancer patients ❌ (assumption of risk)
- Litigation outcome: 2,988 cases, **NO settlements**, defense wins ✅ (confirms low value)

**NEW LITIGATION SCORE**: ~15-25 (QUIET) - correctly rejected
**OLD PHARMA SCORE**: 75+ (false positive)

**VALIDATION**: New filters would correctly prioritize Ozempic over Taxotere. ✅

---

## Conclusion

We successfully built a **pharmacovigilance tool** that flags high-SAE drugs. Now we're pivoting to also build a **litigation intelligence tool** by adding indication severity, drug class, and patient population filters.

**Key Insight**: Litigation thrives on *unexpected permanent harm in relatively healthy populations from drugs for manageable conditions*. Our filters now encode this.

**Next Steps**:
1. Enrich drug metadata (class, indication, approval year)
2. Implement litigation_risk_score()
3. Re-run discovery with new filters
4. Validate against known MDL cases
5. Separate dashboard modes (litigation vs pharmacovigilance)

**Expected Impact**: Transform from "another FAERS dashboard" into "MDL prediction engine" that plaintiff firms will pay $50K/year for.
