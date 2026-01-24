#!/usr/bin/env python3
"""
Test supplement scoring logic with the new nuanced approach

Should demonstrate:
1. Normal calcium (7,344 deaths) scores LOW despite high counts
2. Hypothetical contaminated supplement scores HIGH due to extreme unexpectedness
3. Ozempic scores HIGH (GLP-1 agonist, diabetes, unexpected gastroparesis)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tortsignal'))

# Import the scoring functions
from discover_faers_signals import (
    get_indication_severity,
    get_unexpectedness_multiplier,
    check_drug_class_filter,
    calculate_litigation_risk_score,
    is_supplement
)

print("="*80)
print("SUPPLEMENT SCORING VALIDATION")
print("="*80)

# Test Case 1: Normal Calcium (High death count but expected for elderly)
print("\nTest 1: CALCIUM (normal - elderly patients taking supplements)")
print("-"*80)

calcium_metadata = {
    'drug_class': 'supplement',
    'indication': 'supplement',
    'approval_year': 1980,
    'pharmacologic_class': []
}

calcium_metrics = {
    'total_count': 7344,  # Actual FAERS count
    'sae_type': 'Death',
    'velocity': 5,  # Slight increase
    'baseline_count': 3500,
    'recent_count': 3672
}

# Pharma score (would be high due to absolute count)
calcium_pharma_score = 60

# Calculate observed rate
observed_rate_calcium = (7344 / 100000) * 10000  # 734.4 per 10K
print(f"Observed death rate: {observed_rate_calcium:.2f} per 10K")
print(f"Expected for supplement: 0.01 per 10K")
print(f"Ratio: {observed_rate_calcium / 0.01:.0f}x expected")

unexpectedness = get_unexpectedness_multiplier(calcium_metadata, observed_rate_calcium)
print(f"Unexpectedness multiplier: {unexpectedness}")

calcium_lit_score = calculate_litigation_risk_score(
    calcium_metadata,
    calcium_metrics,
    calcium_pharma_score
)

print(f"\nPharma Score: {calcium_pharma_score}")
print(f"Litigation Score: {calcium_lit_score:.1f}")
print(f"✓ Expected: LOW score (~5-15) despite high death counts")

# Test Case 2: Contaminated Supplement (L-Tryptophan pattern)
print("\n\nTest 2: CONTAMINATED SUPPLEMENT (hypothetical L-Tryptophan scenario)")
print("-"*80)

contaminated_metadata = {
    'drug_class': 'supplement',
    'indication': 'supplement',
    'approval_year': 2022,  # New supplement
    'pharmacologic_class': []
}

contaminated_metrics = {
    'total_count': 500,  # Lower absolute count than calcium
    'sae_type': 'Death',
    'velocity': 999,  # Massive spike from zero
    'baseline_count': 0,
    'recent_count': 500
}

contaminated_pharma_score = 80  # High velocity

# Simulate contaminated batch with 100x expected deaths
observed_rate_contaminated = (500 / 100000) * 10000  # 50 per 10K
# But this is 50 / 0.01 = 5000x expected!
print(f"Observed death rate: {observed_rate_contaminated:.2f} per 10K")
print(f"Expected for supplement: 0.01 per 10K")
print(f"Ratio: {observed_rate_contaminated / 0.01:.0f}x expected")

unexpectedness_cont = get_unexpectedness_multiplier(contaminated_metadata, observed_rate_contaminated)
print(f"Unexpectedness multiplier: {unexpectedness_cont}")

contaminated_lit_score = calculate_litigation_risk_score(
    contaminated_metadata,
    contaminated_metrics,
    contaminated_pharma_score
)

print(f"\nPharma Score: {contaminated_pharma_score}")
print(f"Litigation Score: {contaminated_lit_score:.1f}")
print(f"✓ Expected: HIGH score (60-80) due to extreme unexpectedness bonus")

# Test Case 3: Ozempic (Known litigation target)
print("\n\nTest 3: OZEMPIC (GLP-1 agonist - known MDL target)")
print("-"*80)

ozempic_metadata = {
    'drug_class': 'glp-1 agonist',
    'indication': 'type 2 diabetes',
    'approval_year': 2017,
    'pharmacologic_class': ['incretin mimetic [epc]']
}

ozempic_metrics = {
    'total_count': 480,  # Actual FAERS deaths
    'sae_type': 'Death',
    'velocity': 37.5,  # From test data
    'baseline_count': 1200,
    'recent_count': 1650
}

ozempic_pharma_score = 68  # From test run

# Check if detected as supplement
is_supp = is_supplement("OZEMPIC", ozempic_metadata)
print(f"Detected as supplement: {is_supp} (should be False)")

indication_severity = get_indication_severity(ozempic_metadata)
print(f"Indication severity: {indication_severity} (3 = diabetes)")

class_mult = check_drug_class_filter(ozempic_metadata)
print(f"Class multiplier: {class_mult} (1.2 = whitelisted GLP-1)")

ozempic_lit_score = calculate_litigation_risk_score(
    ozempic_metadata,
    ozempic_metrics,
    ozempic_pharma_score
)

print(f"\nPharma Score: {ozempic_pharma_score}")
print(f"Litigation Score: {ozempic_lit_score:.1f}")
print(f"✓ Expected: HIGH score (70-90) - whitelisted + diabetes indication")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

results = [
    ("CALCIUM (normal)", calcium_lit_score, "5-15", calcium_lit_score >= 5 and calcium_lit_score <= 15),
    ("CONTAMINATED SUPPLEMENT", contaminated_lit_score, "60-80", contaminated_lit_score >= 60 and contaminated_lit_score <= 80),
    ("OZEMPIC", ozempic_lit_score, "70-90", ozempic_lit_score >= 70 and ozempic_lit_score <= 90),
]

print(f"\n{'Drug':<30s} {'Score':>10s} {'Expected':>15s} {'Status':>10s}")
print("-"*80)
for drug, score, expected_range, passed in results:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{drug:<30s} {score:>10.1f} {expected_range:>15s} {status:>10s}")

all_passed = all(r[3] for r in results)

print("\n" + "="*80)
if all_passed:
    print("✓ ALL TESTS PASSED")
    print("\nThe nuanced supplement scoring is working correctly:")
    print("- Normal supplements (calcium) score LOW despite high death counts")
    print("- Contaminated supplements get extreme unexpectedness bonus")
    print("- Known litigation targets (Ozempic) score HIGH")
else:
    print("✗ SOME TESTS FAILED - review scoring logic")
print("="*80)
