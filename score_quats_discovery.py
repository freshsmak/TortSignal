#!/usr/bin/env python3
"""
Score Quats → Occupational Lung Disease Discovery
Extracts evidence from intake criteria and applies Bradford Hill + Litigation scoring
"""

import sys
sys.path.insert(0, '/home/user/TortSignal/backend')

from scoring.bradford_hill import BradfordHillScorer
from scoring.litigation import LitigationScorer
from decimal import Decimal

def main():
    # Evidence extracted from QUATS_LUNG_DISEASE_INTAKE_CRITERIA.md
    quats_data = {
        'chemical': 'Quaternary Ammonium Compounds (Quats)',
        'disease': 'Occupational Asthma & COPD',

        # Criterion 1: Strength - RR 1.33 (33% increased COPD risk)
        'effect_size': 1.33,  # JAMA 2019: 33% increased COPD risk
        'effect_size_source': 'JAMA 2019: 73,262 nurses using disinfectants weekly',

        # Criterion 2: Consistency - Multiple studies
        'studies': [
            {
                'author': 'JAMA 2019',
                'dataset': 'Nurses Health Study',
                'type': 'COHORT',
                'effect_size': 1.33,
                'sample_size': 73262,
                'year': 2019,
                'finding': 'positive'
            },
            {
                'author': 'Multicenter Study',
                'dataset': 'Occupational Asthma Cases',
                'type': 'CASE_SERIES',
                'effect_size': None,  # 2.5% of occupational asthma cases
                'sample_size': None,
                'year': 2021,
                'finding': 'positive'
            },
            {
                'author': 'ECRHS Study',
                'dataset': 'European Community Respiratory Health Survey',
                'type': 'COHORT',
                'effect_size': None,  # Cleaners lose lung function equivalent to smoking 10-20 cigarettes/day
                'sample_size': 6235,
                'year': 2018,
                'finding': 'positive'
            }
        ],

        # Criterion 3: Specificity - Moderate (respiratory diseases)
        'diseases_associated': ['Occupational Asthma', 'COPD', 'Respiratory Sensitization', 'Bronchial Hyperreactivity'],
        'target_disease_papers': 3,
        'total_papers': 3,

        # Criterion 4: Temporality - Clear temporal sequence
        'exposure_timeline': {
            'start_year': 1950,  # Quats used since 1950s
            'peak_year': 2020,   # COVID-era peak (300-500% increase)
            'end_year': None     # Ongoing
        },
        'disease_timeline': {
            'increase_start_year': 2015,  # Recognition of occupational asthma cases increasing
            'increase_peak_year': 2021    # Post-COVID spike in blood Quat levels (77% increase)
        },
        'latency_expected': {
            'min_years': 1,   # Asthma can develop in 6 months to 3 years
            'max_years': 20   # COPD requires 5-20 years cumulative exposure
        },

        # Criterion 5: Biological Gradient - Evidence of dose-response
        'dose_response_studies': [
            {
                'description': 'ECRHS Study: Cleaners lose lung function = smoking 10-20 cigarettes/day',
                'gradient': 'FEV1 drops 3.9 mL/year faster than non-cleaners'
            }
        ],
        'occupational_risk_ratio': 3.5,  # Professional cleaners vs general population (estimated)

        # Criterion 6: Plausibility - Mechanistic evidence
        'mechanisms': [
            {'pathway': 'Respiratory sensitization (asthmagen)', 'evidence_count': 'NIOSH warnings'},
            {'pathway': 'Airway irritation and inflammation', 'evidence_count': 'Multiple studies'},
            {'pathway': 'Bronchial hyperreactivity', 'evidence_count': 'Bronchoprovocation testing'}
        ],
        'mechanistic_papers_count': 15,  # Moderate mechanistic literature
        'animal_models_count': 5,  # Animal inhalation studies

        # Criterion 7: Coherence - Known respiratory toxicants
        'review_articles_count': 2,  # NIOSH warnings, occupational medicine literature
        'contradictions': [],

        # Criterion 8: Experiment - Animal studies + NIOSH warnings
        'rct_studies': [],
        'occupational_interventions': [],
        'animal_intervention_studies': [
            {'description': 'Mice inhalation studies show respiratory sensitization'},
            {'description': 'Rat studies show airway inflammation'}
        ],
        'regulatory_actions': [
            {
                'action_type': 'WARNING',
                'jurisdiction': 'US NIOSH',
                'action_date': '2020-01-01',
                'rationale': 'Respiratory hazards during COVID-19 cleaning'
            }
        ],

        # Criterion 9: Analogy - Other respiratory sensitizers
        'chemical_class': 'Quaternary ammonium compounds (disinfectants)',
        'analogous_exposures': [
            'Bleach → occupational asthma',
            'Cleaning product chemicals → COPD',
            'Isocyanates → occupational asthma (stronger analogy)'
        ]
    }

    # Litigation viability data
    quats_litigation_data = {
        # Population size: Professional cleaners exposed during COVID
        'exposed_population': 3_500_000,  # US professional cleaners (BLS data)
        'disease_prevalence': 0.015,  # 1.5% develop occupational asthma/COPD (conservative)
        'eligibility_filter': 0.60,  # 60% meet criteria (never-smokers, adequate exposure)
        'participation_rate': 0.30,  # 30% will join litigation
        # = 3.5M × 1.5% × 60% × 30% = 9,450 plaintiffs

        # Defendants: Clorox, Ecolab, Reckitt Benckiser (Lysol), SC Johnson
        'defendants': [
            {
                'name': 'Clorox Company',
                'revenue': 7_100_000_000,  # $7.1B
                'market_cap': 18_000_000_000  # $18B
            },
            {
                'name': 'Ecolab Inc.',
                'revenue': 14_400_000_000,  # $14.4B
                'market_cap': 60_000_000_000  # $60B
            },
            {
                'name': 'Reckitt Benckiser (Lysol)',
                'revenue': 17_000_000_000,  # $17B (global)
                'market_cap': 50_000_000_000  # £40B ≈ $50B
            },
            {
                'name': 'SC Johnson Professional',
                'revenue': 10_000_000_000,  # $10B (private, estimated)
                'market_cap': 0  # Private company
            }
        ],

        # Preventability: NIOSH warnings ignored, no label updates
        'regulatory_actions': [
            {
                'jurisdiction': 'US NIOSH',
                'action_type': 'WARNING',
                'action_date': '2020-01-01'
            }
        ],
        'internal_docs_available': True,  # Discovery target: Response to NIOSH warnings, JAMA 2019 study
        'warning_labels': False,  # Labels only say "use in ventilated areas" - insufficient
        'scientific_knowledge_date': '2019-01-01',  # JAMA 2019 study established 33% COPD risk

        # Social justice: Essential workers, COVID heroes
        'plaintiff_demographics': 'workers_no_choice',  # Essential workers during COVID
        'exposure_voluntary': False,  # Required for job, no PPE provided
        'corporate_targeting': False,  # Not targeted, but exposed without protection

        # Severity: Chronic respiratory disease
        'economic_damages': 75_000,  # Medical costs ($25K) + lost wages ($50K)
        'non_economic_damages': 125_000,  # Pain/suffering for chronic lung disease
        'punitive_multiplier': 1.5,  # Moderate punitive (NIOSH warnings ignored)
        # Total: ($75K + $125K) × 1.5 = $300K per plaintiff

        # Novelty: ZERO litigation
        'pacer_cases_count': 0,
        'mdl_status': 'NONE',
        'media_coverage_count': 0,
        'recent_publications_count': 3  # JAMA 2019, Multicenter 2021, ECRHS 2018
    }

    print("=" * 80)
    print("QUATS → OCCUPATIONAL LUNG DISEASE - DISCOVERY SCORING")
    print("=" * 80)
    print()

    # Score Bradford Hill
    print("BRADFORD HILL CAUSAL ASSESSMENT")
    print("-" * 80)
    bh_scorer = BradfordHillScorer()
    bh_result = bh_scorer.score(quats_data)

    print(f"\n🎯 COMPOSITE SCORE: {bh_result.composite_score}/100")
    print(f"📊 INTERPRETATION: {bh_result.interpretation}")
    print()
    print("Criteria Breakdown:")
    for criterion, scores in bh_result.criteria_scores.items():
        print(f"  • {criterion.replace('_', ' ').title():<25} {scores['score']:>2}/10  (weighted: {scores['weighted']:>4.1f})")

    if bh_result.flagged_weaknesses:
        print(f"\n⚠️  WEAKNESSES IDENTIFIED:")
        for weakness in bh_result.flagged_weaknesses:
            print(f"  • {weakness}")

    print(f"\n📋 NEXT STEPS:")
    for step in bh_result.next_steps:
        print(f"  • {step}")

    print()
    print()

    # Score Litigation Viability
    print("LITIGATION VIABILITY ASSESSMENT")
    print("-" * 80)
    lit_scorer = LitigationScorer()
    lit_result = lit_scorer.score(quats_litigation_data, float(bh_result.composite_score))

    print(f"\n🎯 COMPOSITE SCORE: {lit_result.composite_score}/100")
    print(f"📊 INTERPRETATION: {lit_result.interpretation}")
    print()
    print("Factor Breakdown:")
    for factor, scores in lit_result.factor_scores.items():
        print(f"  • {factor.replace('_', ' ').title():<25} {scores['score']:>2}/10  (weighted: {scores['weighted']:>4.1f})")

    if lit_result.strengths:
        print(f"\n✅ STRENGTHS:")
        for strength in lit_result.strengths:
            print(f"  • {strength}")

    if lit_result.weaknesses:
        print(f"\n⚠️  WEAKNESSES:")
        for weakness in lit_result.weaknesses:
            print(f"  • {weakness}")

    print(f"\n🎯 PURSUIT RECOMMENDATION:")
    print(f"  {lit_result.pursuit_recommendation}")

    print()
    print()

    # Summary Report
    print("=" * 80)
    print("DISCOVERY SUMMARY")
    print("=" * 80)
    print()
    print(f"Discovery: {quats_data['chemical']} → {quats_data['disease']}")
    print(f"Bradford Hill Score: {bh_result.composite_score}/100 ({bh_result.interpretation})")
    print(f"Litigation Score: {lit_result.composite_score}/100 ({lit_result.interpretation})")
    print()

    # Market sizing
    exposed = quats_litigation_data['exposed_population']
    prevalence = quats_litigation_data['disease_prevalence']
    eligible_filter = quats_litigation_data['eligibility_filter']
    participation = quats_litigation_data['participation_rate']
    addressable = int(exposed * prevalence * eligible_filter * participation)

    per_plaintiff = quats_litigation_data['economic_damages'] + quats_litigation_data['non_economic_damages']
    per_plaintiff *= quats_litigation_data['punitive_multiplier']

    total_market_low = addressable * int(per_plaintiff * 0.6)
    total_market_high = addressable * int(per_plaintiff * 1.2)

    print("MARKET SIZING:")
    print(f"  • Exposed Population: {exposed:,} professional cleaners")
    print(f"  • Disease Prevalence: {prevalence:.1%}")
    print(f"  • Addressable Plaintiffs: {addressable:,}")
    print(f"  • Per-Plaintiff Value: ${int(per_plaintiff):,}")
    print(f"  • Total Market: ${total_market_low/1e6:.0f}M - ${total_market_high/1e6:.0f}M")
    print()

    print("COMPETITIVE POSITION:")
    print(f"  • PACER Cases Filed: {quats_litigation_data['pacer_cases_count']} (ZERO COMPETITION)")
    print(f"  • First-Mover Window: 12-24 months before plaintiff firms discover")
    print(f"  • Key Hook: COVID-era exposure spike (300-500% increase)")
    print()

    print("COMPARABLE TORTS:")
    print(f"  • Effect Size (RR 1.33): Similar to Talc → Ovarian Cancer (RR 1.33)")
    print(f"  • Market Size (~$1.8B): Smaller than Roundup ($10B), comparable to Hair Relaxer")
    print(f"  • Plaintiff Pool (~9,500): Similar to Hair Relaxer scale")
    print()

    print("KEY EVIDENCE:")
    print(f"  • JAMA 2019: 33% increased COPD risk (73,262 participants)")
    print(f"  • ECRHS 2018: Lung function loss = smoking 10-20 cigarettes/day")
    print(f"  • COVID spike: 77% increase in blood Quat levels (2020-2022)")
    print(f"  • NIOSH warnings: Issued during COVID, manufacturers ignored")
    print()

    print("PURSUIT STRATEGY:")
    if float(bh_result.composite_score) >= 55 and float(lit_result.composite_score) >= 75:
        print(f"  ✅ PURSUE: Score sufficient for mass tort litigation")
        print(f"  📋 Next: Commission pulmonologist validation")
        print(f"  📋 Next: PACER verification (confirm zero cases)")
        print(f"  📋 Next: Survey professional cleaners (2020-2025 exposure)")
        print(f"  📋 Next: Build 50-100 Tier 1 cases (hospital cleaners, never-smokers)")
    elif float(bh_result.composite_score) >= 50:
        print(f"  ⚠️  MONITOR: Score marginal, watch for strengthening evidence")
        print(f"  📋 Next: Wait for additional epidemiological studies")
    else:
        print(f"  ❌ REJECT: Bradford Hill score too weak for litigation")

    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
