#!/usr/bin/env python3
"""
Score Glyoxylic Acid → Acute Kidney Injury Discovery
Extracts evidence from intake criteria and applies Bradford Hill + Litigation scoring
"""

import sys
sys.path.insert(0, '/home/user/TortSignal/backend')

from scoring.bradford_hill import BradfordHillScorer
from scoring.litigation import LitigationScorer
from decimal import Decimal

def main():
    # Evidence extracted from GLYOXYLIC_ACID_KIDNEY_INJURY_INTAKE_CRITERIA.md
    glyoxylic_data = {
        'chemical': 'Glyoxylic Acid',
        'disease': 'Acute Kidney Injury (Oxalate Nephropathy)',

        # Criterion 1: Strength - Very strong for acute cases (mechanistic certainty)
        # No formal epidemiology RR/OR yet, but 60+ documented cases with clear mechanism
        'effect_size': 3.0,  # Estimated based on case reports showing consistent AKI after exposure
        'effect_size_source': 'NEJM 2024 case report + animal studies + 60+ documented cases (Israel, France, Tunisia)',

        # Criterion 2: Consistency - Case reports from multiple countries
        'studies': [
            {
                'author': 'NEJM 2024',
                'dataset': 'Case report + animal validation',
                'type': 'CASE_REPORT',
                'effect_size': None,
                'sample_size': 1,
                'year': 2024,
                'finding': 'positive'
            },
            {
                'author': 'Israel Ministry of Health',
                'dataset': '26 documented kidney injury cases',
                'type': 'CASE_SERIES',
                'effect_size': None,
                'sample_size': 26,
                'year': 2023,
                'finding': 'positive'
            },
            {
                'author': 'France ANSES',
                'dataset': '4 hospitalizations',
                'type': 'CASE_SERIES',
                'effect_size': None,
                'sample_size': 4,
                'year': 2024,
                'finding': 'positive'
            },
            {
                'author': 'Global case series',
                'dataset': '60+ documented cases worldwide',
                'type': 'CASE_SERIES',
                'effect_size': None,
                'sample_size': 60,
                'year': 2024,
                'finding': 'positive'
            }
        ],

        # Criterion 3: Specificity - VERY HIGH (glyoxylic acid → oxalate → kidney crystals)
        'diseases_associated': ['Acute Kidney Injury', 'Oxalate Nephropathy'],
        'target_disease_papers': 2,
        'total_papers': 2,

        # Criterion 4: Temporality - PERFECT (24-72 hours after exposure)
        'exposure_timeline': {
            'start_year': 2015,  # Post-formaldehyde ban, glyoxylic acid substitution
            'peak_year': 2023,   # Widespread use after FDA proposed formaldehyde ban (Oct 2023)
            'end_year': None     # Ongoing
        },
        'disease_timeline': {
            'increase_start_year': 2019,  # First documented Israeli cases
            'increase_peak_year': 2023    # Israel ban after 26 cases
        },
        'latency_expected': {
            'min_years': 0,   # Acute injury: 24-72 hours (use 0 to represent <1 year)
            'max_years': 0    # Acute injury: 24-72 hours
        },

        # Criterion 5: Biological Gradient - Clear dose-response in animal studies
        'dose_response_studies': [
            {
                'description': 'NEJM 2024 animal study: Higher glyoxylic acid dose → higher oxalate crystals',
                'gradient': 'Clear dose-dependent crystal deposition'
            }
        ],

        # Criterion 6: Plausibility - EXCELLENT mechanistic evidence
        'mechanisms': [
            {
                'pathway': 'Dermal absorption through scalp',
                'evidence_count': 'NEJM 2024'
            },
            {
                'pathway': 'Hepatic conversion: Glyoxylic acid → Oxalate',
                'evidence_count': 'NEJM 2024 + animal studies'
            },
            {
                'pathway': 'Calcium oxalate crystal deposition in renal tubules',
                'evidence_count': 'Urinalysis showing crystals, NEJM 2024'
            }
        ],
        'mechanistic_papers_count': 5,  # NEJM 2024 + supporting mechanistic papers
        'animal_models_count': 2,  # NEJM 2024 animal studies (mice)

        # Criterion 7: Coherence - Perfectly coherent with known oxalate nephropathy
        'review_articles_count': 1,  # NEJM 2024 is high-impact publication
        'contradictions': [],

        # Criterion 8: Experiment - Animal intervention studies + regulatory bans
        'rct_studies': [],
        'occupational_interventions': [],
        'animal_intervention_studies': [
            {
                'description': 'NEJM 2024: Mice treated with glyoxylic acid developed oxalate crystals'
            },
            {
                'description': 'NEJM 2024: Crystal deposition matched human kidney biopsies'
            }
        ],
        'regulatory_actions': [
            {
                'action_type': 'BAN',
                'jurisdiction': 'Israel',
                'action_date': '2023-05-01',
                'rationale': '26 documented kidney injury cases'
            },
            {
                'action_type': 'WARNING',
                'jurisdiction': 'France ANSES',
                'action_date': '2024-10-01',
                'rationale': '4 hospitalizations, safety alert issued'
            }
        ],

        # Criterion 9: Analogy - Ethylene glycol (antifreeze) → oxalate nephropathy
        'chemical_class': 'Alpha-hydroxy acids',
        'analogous_exposures': [
            'Ethylene glycol (antifreeze) → oxalate nephropathy (PERFECT ANALOGY)',
            'Vitamin C megadoses → oxalate kidney stones',
            'Primary hyperoxaluria → oxalate nephropathy (genetic)'
        ]
    }

    # Litigation viability data
    glyoxylic_litigation_data = {
        # Population size: Brazilian Blowout users
        'exposed_population': 5_000_000,  # US women getting Brazilian Blowouts annually (estimated)
        'disease_prevalence': 0.0002,  # 0.02% develop AKI (60 cases globally, very rare but under-reported)
        'eligibility_filter': 0.80,  # 80% meet criteria (clear timeline, no pre-existing kidney disease)
        'participation_rate': 0.50,  # 50% will join litigation (severe acute injury, high participation)
        # = 5M × 0.02% × 80% × 50% = 400 plaintiffs (conservative, likely under-reported)

        # Defendants: Brazilian Blowout (GIB, LLC), Cezanne, Uberliss, Alfaparf, etc.
        'defendants': [
            {
                'name': 'GIB, LLC (Brazilian Blowout)',
                'revenue': 100_000_000,  # $100M (estimated, private company)
                'market_cap': 0  # Private
            },
            {
                'name': 'Cezanne Hair Professional',
                'revenue': 50_000_000,  # $50M (estimated)
                'market_cap': 0  # Private
            },
            {
                'name': 'Uberliss',
                'revenue': 30_000_000,  # $30M (estimated)
                'market_cap': 0  # Private
            },
            {
                'name': 'Alfaparf Milano',
                'revenue': 200_000_000,  # $200M (global brand)
                'market_cap': 0  # Private
            },
            {
                'name': 'Various smaller brands',
                'revenue': 120_000_000,  # $120M (aggregate)
                'market_cap': 0
            }
        ],

        # Preventability: Israel ban ignored, NEJM publication ignored, no warnings
        'regulatory_actions': [
            {
                'jurisdiction': 'Israel',
                'action_type': 'BAN',
                'action_date': '2023-05-01'
            },
            {
                'jurisdiction': 'France',
                'action_type': 'WARNING',
                'action_date': '2024-10-01'
            }
        ],
        'internal_docs_available': True,  # Discovery: Response to Israel ban, NEJM publication
        'warning_labels': False,  # No kidney injury warnings on labels
        'scientific_knowledge_date': '2023-05-01',  # Israel ban = knowledge of kidney risk

        # Social justice: Consumers misled by "formaldehyde-free" marketing
        'plaintiff_demographics': 'consumers_misled',  # "Safe" and "formaldehyde-free" marketing
        'exposure_voluntary': True,  # Beauty treatment (voluntary)
        'corporate_targeting': False,  # General consumer product

        # Severity: Acute kidney injury, some requiring dialysis
        'economic_damages': 50_000,  # Medical costs ($30K hospitalization + follow-up) + lost wages ($20K)
        'non_economic_damages': 100_000,  # Pain/suffering for acute hospitalization, potential permanent damage
        'punitive_multiplier': 2.0,  # High punitive (Israel ban ignored, NEJM ignored, continued sales)
        # Total: ($50K + $100K) × 2.0 = $300K per plaintiff

        # Novelty: ZERO litigation in US
        'pacer_cases_count': 0,
        'mdl_status': 'NONE',
        'media_coverage_count': 0,
        'recent_publications_count': 1  # NEJM 2024
    }

    print("=" * 80)
    print("GLYOXYLIC ACID → ACUTE KIDNEY INJURY - DISCOVERY SCORING")
    print("=" * 80)
    print()

    # Score Bradford Hill
    print("BRADFORD HILL CAUSAL ASSESSMENT")
    print("-" * 80)
    bh_scorer = BradfordHillScorer()
    bh_result = bh_scorer.score(glyoxylic_data)

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
    lit_result = lit_scorer.score(glyoxylic_litigation_data, float(bh_result.composite_score))

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
    print(f"Discovery: {glyoxylic_data['chemical']} → {glyoxylic_data['disease']}")
    print(f"Bradford Hill Score: {bh_result.composite_score}/100 ({bh_result.interpretation})")
    print(f"Litigation Score: {lit_result.composite_score}/100 ({lit_result.interpretation})")
    print()

    # Market sizing
    exposed = glyoxylic_litigation_data['exposed_population']
    prevalence = glyoxylic_litigation_data['disease_prevalence']
    eligible_filter = glyoxylic_litigation_data['eligibility_filter']
    participation = glyoxylic_litigation_data['participation_rate']
    addressable = int(exposed * prevalence * eligible_filter * participation)

    per_plaintiff = glyoxylic_litigation_data['economic_damages'] + glyoxylic_litigation_data['non_economic_damages']
    per_plaintiff *= glyoxylic_litigation_data['punitive_multiplier']

    total_market_low = addressable * int(per_plaintiff * 0.6)
    total_market_high = addressable * int(per_plaintiff * 1.2)

    print("MARKET SIZING:")
    print(f"  • Exposed Population: {exposed:,} Brazilian Blowout users/year")
    print(f"  • Disease Prevalence: {prevalence:.2%} (rare but severe)")
    print(f"  • Addressable Plaintiffs: {addressable:,}")
    print(f"  • Per-Plaintiff Value: ${int(per_plaintiff):,}")
    print(f"  • Total Market: ${total_market_low/1e6:.0f}M - ${total_market_high/1e6:.0f}M")
    print()

    print("COMPETITIVE POSITION:")
    print(f"  • PACER Cases Filed: {glyoxylic_litigation_data['pacer_cases_count']} (ZERO COMPETITION)")
    print(f"  • First-Mover Window: 12-24 months before plaintiff firms discover")
    print(f"  • Key Hook: NEJM March 2024 publication + Israel ban (May 2023)")
    print()

    print("COMPARABLE TORTS:")
    print(f"  • Causation Strength: Superior to most torts (mechanistic certainty)")
    print(f"  • Market Size (~$72M-$144M): Boutique tort, pristine opportunity")
    print(f"  • Plaintiff Pool (~400): Small but high-value cases")
    print(f"  • Per-Case Value ($300K): Higher than typical due to acute severity")
    print()

    print("KEY EVIDENCE:")
    print(f"  • NEJM 2024: Mechanistic proof (glyoxylic acid → oxalate → kidney crystals)")
    print(f"  • Israel ban (2023): 26 documented cases triggered regulatory action")
    print(f"  • France alert (2024): 4 hospitalizations, safety warning issued")
    print(f"  • 60+ global cases: Tunisia, Brazil, Argentina, US (under-reported)")
    print(f"  • 24-72 hour latency: Perfect temporal relationship (smoking gun)")
    print()

    print("UNIQUE FEATURES:")
    print(f"  • Acute injury tort (24-72 hours): Unlike chronic disease mass torts")
    print(f"  • Mechanistic certainty: Glyoxylic acid → oxalate conversion proven")
    print(f"  • Oxalate crystals: Objective biomarker (urinalysis shows calcium oxalate)")
    print(f"  • Perfect analogy: Ethylene glycol (antifreeze) poisoning pathway")
    print(f"  • 'Formaldehyde-free' hook: Marketed as safe alternative, actually toxic")
    print()

    print("CHALLENGES:")
    print(f"  • Small plaintiff pool: Only ~400 addressable (vs. 10,000+ for typical MDL)")
    print(f"  • Defendant solvency: Mostly private companies, smaller than Big Pharma")
    print(f"  • Under-reporting: Many AKI cases may not connect to hair treatment")
    print(f"  • Voluntary exposure: Beauty treatment (vs. essential workers)")
    print()

    print("PURSUIT STRATEGY:")
    if float(bh_result.composite_score) >= 60 and float(lit_result.composite_score) >= 70:
        print(f"  ✅ PURSUE: Boutique tort with exceptional causation strength")
        print(f"  📋 Next: Commission nephrologist validation")
        print(f"  📋 Next: PACER verification (confirm zero cases)")
        print(f"  📋 Next: Partner with nephrology practices to identify AKI cases")
        print(f"  📋 Next: Social media monitoring ('Brazilian blowout kidney', 'hair straightening hospital')")
        print(f"  📋 Next: Build 10-25 Tier 1 bellwether cases (dialysis, clear timeline)")
        print(f"  📋 Strategy: File small batch (10-25 cases), trigger media attention")
        print(f"  📋 Strategy: NBC/GMA story: 'Beauty Treatment Sent Her to Dialysis'")
    elif float(bh_result.composite_score) >= 50:
        print(f"  ⚠️  MONITOR: Score marginal, watch for additional cases")
        print(f"  📋 Next: Wait for follow-up epidemiological studies")
    else:
        print(f"  ❌ REJECT: Bradford Hill score too weak for litigation")

    print()
    print("COMPARISON TO QUATS:")
    print(f"  • Quats: Larger market (~$1.8B), workers (higher sympathy)")
    print(f"  • Glyoxylic Acid: Smaller market (~$100M), but pristine + mechanistic certainty")
    print(f"  • Both: ZERO competition, 12-24 month first-mover window")
    print(f"  • Verdict: Quats = higher ROI, Glyoxylic Acid = cleaner causation")
    print()

    print("=" * 80)

if __name__ == "__main__":
    main()
