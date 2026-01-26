"""
Complete Integration Test - Full EDE Pipeline with All Data Sources
Tests the complete workflow with data from ALL integrations combined
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanners.regulatory import RegulatoryScanner
from integrations.pubmed import PubMedIntegration
from integrations.epidemiology import EpidemiologyIntegration
from scoring.bradford_hill import BradfordHillScorer
from scoring.litigation import LitigationScorer


def test_complete_pipeline():
    """
    Test complete EDE pipeline with TiO2 → IBD using ALL data sources

    This combines:
    1. Regulatory actions (EU ban)
    2. PubMed evidence (mechanistic + epidemiology)
    3. Epidemiology validation (CDC WONDER temporality)
    4. Bradford Hill scoring (with epidemiology integration)
    5. Litigation scoring

    Expected: Bradford Hill ~94/100, Litigation ~106/100
    """
    print("\n" + "="*80)
    print("COMPLETE INTEGRATION TEST: TiO2 → IBD")
    print("Testing with ALL data sources integrated")
    print("="*80 + "\n")

    chemical = "Titanium Dioxide"
    disease = "Inflammatory Bowel Disease"

    # ========================================================================
    # PHASE 1: REGULATORY SCAN
    # ========================================================================
    print("\n" + "-"*80)
    print("PHASE 1: REGULATORY SCAN")
    print("-"*80)

    regulatory_scanner = RegulatoryScanner()
    regulatory_results = regulatory_scanner.scan_all(days_back=365)

    # Find TiO2 ban
    eu_actions = [a for a in regulatory_results.get('eu_echa', []) if 'Titanium' in a.get('chemical', '')]

    regulatory_data = {
        'eu_banned': len(eu_actions) > 0,
        'us_banned': False,  # No US ban
        'regulatory_divergence': True,
        'actions': eu_actions
    }

    print(f"✓ Regulatory Actions Found: {len(eu_actions)}")
    if eu_actions:
        print(f"  - {eu_actions[0]['action_type']} by {eu_actions[0]['agency']} ({eu_actions[0]['action_date']})")

    # ========================================================================
    # PHASE 2: PUBMED EVIDENCE
    # ========================================================================
    print("\n" + "-"*80)
    print("PHASE 2: PUBMED EVIDENCE GATHERING")
    print("-"*80)

    pubmed = PubMedIntegration()
    pubmed_results = pubmed.search_all(chemical, disease, max_results=30)

    # Aggregate PubMed data
    mechanistic_papers = pubmed_results.get('mechanistic', [])
    epidemiology_papers = pubmed_results.get('epidemiology', [])

    # Extract mechanistic pathways
    all_pathways = []
    for paper in mechanistic_papers:
        pathways = paper.get('extracted_evidence', {}).get('pathways', [])
        all_pathways.extend(pathways)

    # Count unique pathways
    unique_pathways = list(set(all_pathways))

    # Extract epidemiology effect sizes
    effect_sizes = []
    for paper in epidemiology_papers:
        effect_size = paper.get('extracted_evidence', {}).get('effect_size')
        if effect_size:
            effect_sizes.append(effect_size)

    avg_effect_size = sum(effect_sizes) / len(effect_sizes) if effect_sizes else 1.65

    pubmed_data = {
        'total_papers': pubmed_results['summary']['total_papers'],
        'mechanistic_count': len(mechanistic_papers),
        'epidemiology_count': len(epidemiology_papers),
        'pathways': unique_pathways,
        'effect_sizes': effect_sizes,
        'avg_effect_size': avg_effect_size
    }

    print(f"✓ Total Papers Found: {pubmed_data['total_papers']}")
    print(f"  - Mechanistic: {pubmed_data['mechanistic_count']}")
    print(f"  - Epidemiology: {pubmed_data['epidemiology_count']}")
    print(f"  - Pathways Identified: {', '.join(unique_pathways[:5])}")
    print(f"  - Average Effect Size: {avg_effect_size:.2f}")

    # ========================================================================
    # PHASE 3: EPIDEMIOLOGY VALIDATION
    # ========================================================================
    print("\n" + "-"*80)
    print("PHASE 3: EPIDEMIOLOGY VALIDATION (CDC WONDER)")
    print("-"*80)

    epi = EpidemiologyIntegration()
    epi_result = epi.analyze_disease_signal(
        disease=disease,
        disease_icd10_code="K50-K51",
        exposure_start_year=1990,
        exposure_peak_year=2000,
        expected_latency=10,
        start_year=1999,
        end_year=2020
    )

    epidemiology_data = {
        'trend_direction': epi_result['trend'].trend_direction,
        'percent_change': epi_result['trend'].percent_change,
        'bradford_hill_temporality_score': epi_result['bradford_hill_temporality_score'],
        'temporality_valid': epi_result['temporality_assessment']['temporality_valid'],
        'latency_period': epi_result['temporality_assessment']['latency_period'],
        'exposure_period': f"{epi_result['temporality_assessment']['exposure_start_year']}-present",
        'disease_period': f"{epi_result['temporality_assessment']['disease_increase_year']}-present",
        'interpretation': epi_result['temporality_assessment']['interpretation']
    }

    print(f"✓ Disease Trend: {epidemiology_data['trend_direction']} ({epidemiology_data['percent_change']:+.1f}%)")
    print(f"✓ Temporality Valid: {epidemiology_data['temporality_valid']}")
    print(f"✓ Temporality Score: {epidemiology_data['bradford_hill_temporality_score']}/10")
    print(f"✓ Interpretation: {epidemiology_data['interpretation']}")

    # ========================================================================
    # PHASE 4: BRADFORD HILL SCORING (WITH ALL DATA)
    # ========================================================================
    print("\n" + "-"*80)
    print("PHASE 4: BRADFORD HILL SCORING (INTEGRATED)")
    print("-"*80)

    scorer = BradfordHillScorer()

    # Build comprehensive scoring data using ALL sources
    bradford_hill_data = {
        'chemical': chemical,
        'disease': disease,

        # Strength: From PubMed epidemiology papers
        'effect_size': avg_effect_size,
        'effect_size_type': 'RR',

        # Consistency: Number of studies found
        'studies': [
            {'type': 'EPIDEMIOLOGY', 'effect_size': es, 'finding': 'positive'}
            for es in effect_sizes
        ] + [
            {'type': 'MECHANISTIC', 'finding': 'positive'}
            for _ in mechanistic_papers
        ],

        # Specificity: IBD is somewhat specific
        'disease_specificity': 'MODERATE',
        'diseases_associated': ['IBD', 'General Inflammation'],
        'target_disease_papers': len(mechanistic_papers) + len(epidemiology_papers),

        # Temporality: FROM EPIDEMIOLOGY VALIDATION (KEY INTEGRATION!)
        'epidemiology_validation': epidemiology_data,

        # Also include manual timeline for comparison
        'exposure_timeline': {
            'start_year': 1990,
            'peak_year': 2000,
            'current_prevalence': 0.50
        },
        'disease_timeline': {
            'baseline_rate': 0.0015,
            'current_rate': 0.0025,
            'increase_start_year': 2005,
            'percent_change': epidemiology_data['percent_change']
        },

        # Biological Gradient: Some evidence
        'dose_response_studies': [
            {'finding': 'POSITIVE', 'description': 'High consumers 2.1× risk'}
        ],

        # Plausibility: Strong mechanistic evidence from PubMed
        'mechanistic_papers_count': len(mechanistic_papers),
        'mechanisms': [
            {'pathway': p, 'strength': 'STRONG', 'papers': 5}
            for p in unique_pathways[:3]
        ],

        # Coherence: Fits IBD pathophysiology
        'coherence_evidence': 'TiO2 nanoparticles cross intestinal barrier, trigger inflammation, disrupt microbiome',

        # Experiment: Animal studies
        'animal_models_count': 9,
        'animal_model_results': 'POSITIVE',

        # Analogy: Similar nanoparticles
        'analogous_exposures': [
            {'exposure': 'Silver nanoparticles', 'disease': 'Gut inflammation', 'strength': 'STRONG'},
            {'exposure': 'Silica nanoparticles', 'disease': 'Intestinal damage', 'strength': 'MODERATE'}
        ]
    }

    # Score with integrated data
    bradford_hill_result = scorer.score(bradford_hill_data)

    print(f"\n{'='*80}")
    print(f"BRADFORD HILL SCORE (WITH INTEGRATION): {bradford_hill_result.composite_score}/100")
    print(f"Interpretation: {bradford_hill_result.interpretation}")
    print(f"{'='*80}\n")

    print("Criterion Breakdown:")
    cs = bradford_hill_result.criteria_scores
    print(f"  1. Strength:             {cs['strength']['score']}/10 (weighted: {cs['strength']['weighted']:.1f}/15)")
    print(f"  2. Consistency:          {cs['consistency']['score']}/10 (weighted: {cs['consistency']['weighted']:.1f}/12)")
    print(f"  3. Specificity:          {cs['specificity']['score']}/10 (weighted: {cs['specificity']['weighted']:.1f}/8)")
    print(f"  4. Temporality:          {cs['temporality']['score']}/10 (weighted: {cs['temporality']['weighted']:.1f}/15) ← FROM EPIDEMIOLOGY!")
    print(f"  5. Biological Gradient:  {cs['biological_gradient']['score']}/10 (weighted: {cs['biological_gradient']['weighted']:.1f}/10)")
    print(f"  6. Plausibility:         {cs['plausibility']['score']}/10 (weighted: {cs['plausibility']['weighted']:.1f}/15)")
    print(f"  7. Coherence:            {cs['coherence']['score']}/10 (weighted: {cs['coherence']['weighted']:.1f}/10)")
    print(f"  8. Experiment:           {cs['experiment']['score']}/10 (weighted: {cs['experiment']['weighted']:.1f}/10)")
    print(f"  9. Analogy:              {cs['analogy']['score']}/10 (weighted: {cs['analogy']['weighted']:.1f}/5)")

    # ========================================================================
    # PHASE 5: LITIGATION SCORING
    # ========================================================================
    print("\n" + "-"*80)
    print("PHASE 5: LITIGATION SCORING")
    print("-"*80)

    litigation_scorer = LitigationScorer()

    litigation_data = {
        'chemical': chemical,
        'disease': disease,

        # Population
        'exposed_population': 50_000_000,
        'disease_prevalence': 0.0025,
        'addressable_plaintiffs_min': 100_000,
        'addressable_plaintiffs_max': 150_000,

        # Defendants
        'defendants': [
            {'name': 'Mars, Inc.', 'revenue': 45_000_000_000},
            {'name': 'Mondelez', 'revenue': 35_000_000_000},
            {'name': 'Nestlé', 'revenue': 95_000_000_000},
            {'name': 'Hershey', 'revenue': 11_000_000_000},
            {'name': 'General Mills', 'revenue': 20_000_000_000},
        ],

        # Preventability
        'preventability': {
            'eu_banned': regulatory_data['eu_banned'],
            'regulatory_warnings': ['EU ECHA ban (2021)', 'EFSA review (2016)'],
            'internal_knowledge': 'PRESUMED',
            'alternative_exists': True,
            'failure_to_warn': True
        },

        # Social Justice
        'plaintiff_demographics': 'children',
        'sympathetic_narrative': 'Kids eating candy developed lifelong chronic disease',
        'David_vs_Goliath': True,

        # Severity
        'disease_severity': 'SEVERE',
        'economic_damages': 150_000,
        'non_economic_damages': 350_000,
        'loss_of_quality_of_life': 'HIGH',
        'punitive_multiplier': 2.0,

        # Novelty
        'pacer_cases_count': 0,
        'mdl_status': None,
        'is_pre_litigation': True,
        'media_coverage_count': 3
    }

    litigation_result = litigation_scorer.score(litigation_data, float(bradford_hill_result.composite_score))

    print(f"\nLitigation Score: {litigation_result.composite_score}/100")
    print(f"Interpretation: {litigation_result.interpretation}")

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("COMPLETE INTEGRATION TEST RESULTS")
    print("="*80)

    print(f"\nData Sources Used:")
    print(f"  ✓ Regulatory: {len(regulatory_data['actions'])} actions (EU ban detected)")
    print(f"  ✓ PubMed: {pubmed_data['total_papers']} papers ({pubmed_data['mechanistic_count']} mechanistic, {pubmed_data['epidemiology_count']} epi)")
    print(f"  ✓ Epidemiology: CDC WONDER validation (temporality {epidemiology_data['bradford_hill_temporality_score']}/10)")

    print(f"\nFinal Scores:")
    print(f"  Bradford Hill: {bradford_hill_result.composite_score}/100 ({bradford_hill_result.interpretation})")
    print(f"  Litigation: {litigation_result.composite_score}/100 ({litigation_result.interpretation})")

    print(f"\nComparison to Expected:")
    expected_bh = 94.0
    expected_lit = 106.0
    bh_diff = float(bradford_hill_result.composite_score) - expected_bh
    lit_diff = float(litigation_result.composite_score) - expected_lit

    print(f"  Bradford Hill: {bradford_hill_result.composite_score}/100 (expected {expected_bh}/100, diff: {bh_diff:+.1f})")
    print(f"  Litigation: {litigation_result.composite_score}/100 (expected {expected_lit}/100, diff: {lit_diff:+.1f})")

    print(f"\nSignal Status:")
    if float(bradford_hill_result.composite_score) >= 85:
        print(f"  ✅ READY TO VALIDATE (Bradford Hill ≥85)")
    else:
        print(f"  ⚠️  NEEDS MORE EVIDENCE (Bradford Hill <85)")
        print(f"     Gap: {85 - float(bradford_hill_result.composite_score):.1f} points")
        print(f"     Key weaknesses: {', '.join(bradford_hill_result.flagged_weaknesses[:3])}")

    print("\n" + "="*80)
    print("✅ COMPLETE INTEGRATION TEST FINISHED")
    print("="*80)

    return {
        'bradford_hill_score': float(bradford_hill_result.composite_score),
        'litigation_score': float(litigation_result.composite_score),
        'data_sources': {
            'regulatory': len(regulatory_data['actions']),
            'pubmed': pubmed_data['total_papers'],
            'epidemiology': epidemiology_data['temporality_valid']
        }
    }


if __name__ == "__main__":
    result = test_complete_pipeline()
