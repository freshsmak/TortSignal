"""
Comprehensive Data Integration Test
Tests NHANES, NIH RePORTER, and CDC WONDER working together

Example: TiO2 → IBD Hypothesis Validation
"""

import sys
sys.path.insert(0, '/home/user/TortSignal/backend')

from integrations.nhanes import NHANESIntegration
from integrations.nih_reporter import NIHReporterAPI
from integrations.cdc_wonder import CDCWonderAPI


def test_tio2_ibd_hypothesis():
    """
    Test all three data sources for TiO2 → IBD hypothesis

    This demonstrates how multiple data sources provide
    converging or diverging evidence for a tort hypothesis.
    """
    print("=" * 80)
    print("COMPREHENSIVE DATA INTEGRATION TEST")
    print("Hypothesis: Titanium Dioxide (E171) → Inflammatory Bowel Disease")
    print("=" * 80)

    # Initialize APIs
    nhanes = NHANESIntegration()
    nih = NIHReporterAPI()
    cdc = CDCWonderAPI()

    # ====================
    # 1. EPIDEMIOLOGY (CDC WONDER)
    # ====================
    print("\n" + "=" * 80)
    print("1. EPIDEMIOLOGY - CDC WONDER")
    print("=" * 80)
    print("Question: Is IBD increasing in the US population?")

    ibd_trend = cdc.query_disease_trend(
        disease_icd10_code='K50-K51',
        start_year=2000,
        end_year=2020
    )

    print(f"\nResult: {ibd_trend.trend_direction} trend")
    print(f"  Change: {ibd_trend.percent_change:+.1f}%")
    print(f"  Data: {len(ibd_trend.years)} years")
    print(f"  Source: {ibd_trend.data_source}")
    print(f"\n  Interpretation: {ibd_trend.interpretation}")

    # Score for Bradford Hill "Consistency"
    epidemiology_score = 'POSITIVE' if ibd_trend.trend_direction == 'INCREASING' else 'NEGATIVE'
    print(f"\n  → Epidemiology Signal: {epidemiology_score}")

    # ====================
    # 2. EXPOSURE (NHANES)
    # ====================
    print("\n" + "=" * 80)
    print("2. EXPOSURE ASSESSMENT - NHANES")
    print("=" * 80)
    print("Question: Are IBD patients exposed to higher TiO2 levels?")

    exposure = nhanes.cross_reference_exposure(
        chemical='titanium',
        disease_icd10='K50-K51',
        disease_demographics={'age_min': 20, 'age_max': 60}
    )

    print(f"\nResult: {exposure.exposure_ratio:.2f}x exposure ratio")
    print(f"  Disease pop: {exposure.biomarker_disease_pop} ng/mL" if exposure.biomarker_disease_pop else "  Disease pop: N/A")
    print(f"  General pop: {exposure.biomarker_general_pop} ng/mL" if exposure.biomarker_general_pop else "  General pop: N/A")
    print(f"  Data quality: {exposure.data_quality}")
    print(f"\n  Interpretation: {exposure.interpretation}")

    # Score for Bradford Hill "Dose-Response"
    exposure_score = 'POSITIVE' if exposure.exposure_ratio >= 1.5 else 'WEAK'
    print(f"\n  → Exposure Signal: {exposure_score}")

    # ====================
    # 3. RESEARCH ACTIVITY (NIH RePORTER)
    # ====================
    print("\n" + "=" * 80)
    print("3. RESEARCH ACTIVITY - NIH RePORTER")
    print("=" * 80)
    print("Question: Is NIH funding research on TiO2 → IBD?")

    nih_trend = nih.analyze_research_trend(
        chemical='titanium dioxide',
        disease='inflammatory bowel disease',
        years_back=10
    )

    print(f"\nResult: {nih_trend.total_grants} grants, ${nih_trend.total_funding:,.0f} funding")
    print(f"  Trend: {nih_trend.trend}")
    print(f"\n  Interpretation: {nih_trend.interpretation}")

    if nih_trend.recent_projects:
        print(f"\n  Recent Projects:")
        for project in nih_trend.recent_projects[:3]:
            print(f"    - [{project.fiscal_year}] {project.project_title[:70]}...")

    # Score for Bradford Hill "Plausibility"
    if nih_trend.total_grants == 0:
        research_score = 'UNDISCOVERED'  # Opportunity!
        print(f"\n  → Research Signal: {research_score} (potential first-mover advantage)")
    elif nih_trend.trend == 'INCREASING':
        research_score = 'EMERGING'
        print(f"\n  → Research Signal: {research_score} (growing academic interest)")
    else:
        research_score = 'ESTABLISHED'
        print(f"\n  → Research Signal: {research_score} (known hypothesis)")

    # ====================
    # 4. BROADER CONTEXT
    # ====================
    print("\n" + "=" * 80)
    print("4. BROADER RESEARCH CONTEXT")
    print("=" * 80)
    print("Question: What about nanoparticles + IBD research in general?")

    nano_trend = nih.analyze_research_trend(
        chemical='nanoparticle',
        disease='colitis',
        years_back=10
    )

    print(f"\nResult: {nano_trend.total_grants} grants, ${nano_trend.total_funding:,.0f} funding")
    print(f"  Trend: {nano_trend.trend}")
    print(f"\n  Interpretation: {nano_trend.interpretation}")

    if nano_trend.total_grants > 0:
        print(f"\n  Top Investigators:")
        for pi in nano_trend.key_investigators[:5]:
            print(f"    - {pi}")

    # ====================
    # 5. SYNTHESIS
    # ====================
    print("\n" + "=" * 80)
    print("5. SYNTHESIS & LITIGATION ASSESSMENT")
    print("=" * 80)

    print("\nEvidence Summary:")
    print(f"  1. Epidemiology (IBD increasing?): {epidemiology_score}")
    print(f"  2. Exposure (TiO2 levels elevated?): {exposure_score}")
    print(f"  3. Research (NIH funding TiO2→IBD?): {research_score}")
    print(f"  4. Broader context (Nanoparticle research): {nano_trend.trend}")

    print("\n" + "-" * 80)
    print("LITIGATION VIABILITY ASSESSMENT")
    print("-" * 80)

    # Calculate composite score
    signals = []
    if epidemiology_score == 'POSITIVE':
        signals.append("✓ Disease increasing (epidemiology)")
    if exposure_score in ['POSITIVE', 'WEAK']:
        signals.append("⚠ Exposure data limited (TiO2 not in NHANES)")
    if research_score == 'UNDISCOVERED':
        signals.append("✓ Hypothesis not on NIH radar (first-mover opportunity)")
    if nano_trend.total_grants > 0:
        signals.append(f"✓ Broader nanoparticle research active ({nano_trend.total_grants} grants)")

    print("\nPositive Signals:")
    for signal in signals:
        print(f"  {signal}")

    print("\nCritical Gaps:")
    gaps = []
    if exposure_score != 'POSITIVE':
        gaps.append("⚠ No direct TiO2 biomarker data in NHANES")
    if research_score == 'UNDISCOVERED':
        gaps.append("⚠ No NIH grants on TiO2→IBD (may indicate weak preliminary data)")
    if len(gaps) == 0:
        gaps.append("None - all data sources align")

    for gap in gaps:
        print(f"  {gap}")

    print("\nRecommendation:")
    if epidemiology_score == 'POSITIVE' and nano_trend.total_grants > 0:
        print("  → MONITOR: Disease increasing + general nanoparticle concern")
        print("  → But: Need more exposure data and mechanistic research")
        print("  → Timeline: 2-3 years for academic literature to develop")
    else:
        print("  → Insufficient evidence at this time")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_tio2_ibd_hypothesis()
