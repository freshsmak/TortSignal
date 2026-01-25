"""
Litigation Viability Scoring Engine
Implements 7-factor business assessment for mass tort potential
Based on EDE_METHODOLOGY.md Section VII
"""

from decimal import Decimal
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class LitigationResult:
    """Result of litigation scoring"""
    composite_score: Decimal
    interpretation: str
    factor_scores: Dict[str, Dict[str, any]]
    strengths: List[str]
    weaknesses: List[str]
    pursuit_recommendation: str


class LitigationScorer:
    """
    Automated litigation viability assessment
    Scores 7 factors on 0-10 scale, applies weights, returns composite 0-100+ score
    """

    # Weights for each factor (must sum to 100)
    WEIGHTS = {
        'causal_strength': 20,      # Must pass Daubert
        'population_size': 15,      # Need critical mass
        'defendant_solvency': 20,   # Deep pockets required
        'preventability': 15,       # Clear wrongdoing
        'social_justice': 10,       # Jury sympathy
        'severity': 15,             # High per-plaintiff damages
        'novelty': 5                # First-mover bonus
    }

    def __init__(self):
        pass

    def score(self, signal_data: Dict, bradford_hill_score: float) -> LitigationResult:
        """
        Main scoring function

        Args:
            signal_data: Dictionary containing business/market data
            bradford_hill_score: Pre-calculated Bradford Hill score (0-100)

        Returns:
            LitigationResult with composite score and recommendations
        """

        scores = {}

        # Score each factor
        scores['causal_strength'] = self.score_causal_strength(bradford_hill_score)
        scores['population_size'] = self.score_population_size(signal_data)
        scores['defendant_solvency'] = self.score_defendant_solvency(signal_data)
        scores['preventability'] = self.score_preventability(signal_data)
        scores['social_justice'] = self.score_social_justice(signal_data)
        scores['severity'] = self.score_severity(signal_data)
        scores['novelty'] = self.score_novelty(signal_data)

        # Calculate weighted scores
        factor_scores = {}
        for factor, raw_score in scores.items():
            weighted_score = (raw_score['score'] / 10) * self.WEIGHTS[factor]
            factor_scores[factor] = {
                'score': raw_score['score'],
                'weighted': weighted_score,
                'evidence': raw_score['evidence']
            }

        # Calculate composite
        composite_score = sum(f['weighted'] for f in factor_scores.values())

        # Interpretation
        interpretation = self._interpret_score(composite_score)

        # Identify strengths (score ≥8)
        strengths = [
            f"{factor.replace('_', ' ').title()} ({factor_scores[factor]['score']}/10)"
            for factor in scores
            if factor_scores[factor]['score'] >= 8
        ]

        # Identify weaknesses (score <6)
        weaknesses = [
            f"{factor.replace('_', ' ').title()} ({factor_scores[factor]['score']}/10)"
            for factor in scores
            if factor_scores[factor]['score'] < 6
        ]

        # Pursuit recommendation
        recommendation = self._generate_recommendation(composite_score, bradford_hill_score, factor_scores)

        return LitigationResult(
            composite_score=Decimal(str(round(composite_score, 1))),
            interpretation=interpretation,
            factor_scores=factor_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            pursuit_recommendation=recommendation
        )

    def score_causal_strength(self, bradford_hill_score: float) -> Dict:
        """
        Factor 1: Causal Strength
        Converts Bradford Hill score to litigation factor

        Args:
            bradford_hill_score: Pre-calculated Bradford Hill score (0-100)

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        if bradford_hill_score >= 95:
            score = 10
            interpretation = 'Very Strong - Expert testimony highly admissible'
        elif bradford_hill_score >= 90:
            score = 9
            interpretation = 'Strong - Expert testimony admissible'
        elif bradford_hill_score >= 85:
            score = 8
            interpretation = 'Strong - Likely to survive Daubert'
        elif bradford_hill_score >= 70:
            score = 6
            interpretation = 'Marginal - May struggle with summary judgment'
        elif bradford_hill_score >= 50:
            score = 3
            interpretation = 'Weak - Unlikely to meet Daubert standard'
        else:
            score = 0
            interpretation = 'Very Weak - Expert testimony inadmissible'

        return {
            'score': score,
            'evidence': {
                'bradford_hill_score': bradford_hill_score,
                'daubert_admissibility': interpretation,
                'comparable_torts': self._get_comparable_torts(bradford_hill_score)
            }
        }

    def score_population_size(self, data: Dict) -> Dict:
        """
        Factor 2: Population Size
        Measures addressable plaintiff pool

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        # Calculate addressable plaintiffs
        exposed_population = data.get('exposed_population', 0)
        disease_prevalence = data.get('disease_prevalence', 0)
        eligibility_filter = data.get('eligibility_filter', 0.5)
        participation_rate = data.get('participation_rate', 0.25)

        diseased_population = exposed_population * disease_prevalence
        eligible_plaintiffs = diseased_population * eligibility_filter
        addressable_plaintiffs = eligible_plaintiffs * participation_rate

        # Scoring thresholds
        if addressable_plaintiffs >= 100000:
            score = 10
            interpretation = f'{int(addressable_plaintiffs):,}+ plaintiffs (Roundup/Opioids scale)'
        elif addressable_plaintiffs >= 50000:
            score = 9
            interpretation = f'{int(addressable_plaintiffs):,} plaintiffs (Large MDL)'
        elif addressable_plaintiffs >= 25000:
            score = 8
            interpretation = f'{int(addressable_plaintiffs):,} plaintiffs (Major MDL)'
        elif addressable_plaintiffs >= 10000:
            score = 7
            interpretation = f'{int(addressable_plaintiffs):,} plaintiffs (Talc/Hair Relaxer scale)'
        elif addressable_plaintiffs >= 5000:
            score = 5
            interpretation = f'{int(addressable_plaintiffs):,} plaintiffs (Medium MDL)'
        elif addressable_plaintiffs >= 1000:
            score = 3
            interpretation = f'{int(addressable_plaintiffs):,} plaintiffs (Boutique tort)'
        else:
            score = 0
            interpretation = f'{int(addressable_plaintiffs):,} plaintiffs (Too small for MDL)'

        return {
            'score': score,
            'evidence': {
                'exposed_population': int(exposed_population),
                'diseased_population': int(diseased_population),
                'eligible_plaintiffs': int(eligible_plaintiffs),
                'addressable_plaintiffs': int(addressable_plaintiffs),
                'participation_rate_assumed': f'{participation_rate:.0%}',
                'interpretation': interpretation
            }
        }

    def score_defendant_solvency(self, data: Dict) -> Dict:
        """
        Factor 3: Defendant Solvency
        Measures defendant financial strength (deep pockets)

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        defendants = data.get('defendants', [])

        if not defendants:
            return {
                'score': 0,
                'evidence': {'total_revenue': 0, 'interpretation': 'No defendants identified'}
            }

        # Calculate total financial strength
        total_revenue = sum(d.get('revenue', 0) for d in defendants)
        total_market_cap = sum(d.get('market_cap', 0) for d in defendants)

        # Scoring based on revenue
        if total_revenue >= 50_000_000_000:  # $50B+
            score = 10
            interpretation = f'Exceptional solvency - ${total_revenue/1e9:.0f}B revenue (Fortune 500)'
        elif total_revenue >= 10_000_000_000:  # $10B-$50B
            score = 9
            interpretation = f'Very strong - ${total_revenue/1e9:.0f}B revenue'
        elif total_revenue >= 5_000_000_000:  # $5B-$10B
            score = 8
            interpretation = f'Strong - ${total_revenue/1e9:.0f}B revenue'
        elif total_revenue >= 1_000_000_000:  # $1B-$5B
            score = 7
            interpretation = f'Good - ${total_revenue/1e9:.0f}B revenue'
        elif total_revenue >= 500_000_000:  # $500M-$1B
            score = 5
            interpretation = f'Moderate - ${total_revenue/1e6:.0f}M revenue'
        elif total_revenue >= 100_000_000:  # $100M-$500M
            score = 3
            interpretation = f'Weak - ${total_revenue/1e6:.0f}M revenue'
        else:
            score = 0
            interpretation = 'Insolvent or too small'

        # Bonus for multiple defendants (spreads risk)
        if len(defendants) >= 5:
            score = min(10, score + 1)

        return {
            'score': score,
            'evidence': {
                'defendants': [
                    {
                        'name': d.get('name'),
                        'revenue': f"${d.get('revenue', 0)/1e9:.1f}B" if d.get('revenue', 0) >= 1e9 else f"${d.get('revenue', 0)/1e6:.0f}M",
                        'market_cap': f"${d.get('market_cap', 0)/1e9:.1f}B" if d.get('market_cap') else 'Private'
                    }
                    for d in defendants
                ],
                'total_revenue': f"${total_revenue/1e9:.1f}B",
                'total_market_cap': f"${total_market_cap/1e9:.1f}B" if total_market_cap else 'N/A',
                'interpretation': interpretation
            }
        }

    def score_preventability(self, data: Dict) -> Dict:
        """
        Factor 4: Preventability (Failure to Warn)
        Measures whether harm was preventable

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        regulatory_actions = data.get('regulatory_actions', [])
        internal_docs_available = data.get('internal_docs_available', False)
        warning_labels = data.get('warning_labels', False)
        scientific_knowledge_date = data.get('scientific_knowledge_date', None)

        score = 5  # Baseline: Assume risk was foreseeable

        # EU ban ignored = strong evidence of preventability
        eu_ban = any(a.get('jurisdiction') == 'EU' and a.get('action_type') == 'BAN' for a in regulatory_actions)
        if eu_ban:
            score += 4

        # Internal documents (smoking gun potential)
        if internal_docs_available:
            score += 1

        # No warning labels despite known risk
        if scientific_knowledge_date and not warning_labels:
            from datetime import datetime
            try:
                knowledge_year = int(scientific_knowledge_date.split('-')[0])
                years_since = datetime.now().year - knowledge_year
                if years_since >= 5:
                    score += 1
            except:
                pass

        score = min(10, score)  # Cap at 10

        # Interpretation
        if score >= 10:
            interpretation = 'Smoking gun - EU ban ignored, no warnings, internal docs likely'
        elif score >= 9:
            interpretation = 'Clear failure to warn - EU ban ignored'
        elif score >= 7:
            interpretation = 'Strong preventability - Known risks, no action'
        elif score >= 5:
            interpretation = 'Foreseeable risk'
        else:
            interpretation = 'Reasonable ignorance'

        return {
            'score': score,
            'evidence': {
                'regulatory_divergence': 'EU banned, US continued' if eu_ban else 'No EU/US divergence',
                'warning_labels': 'Present' if warning_labels else 'Absent',
                'internal_documents': 'Likely exist' if internal_docs_available else 'Unknown',
                'punitive_damages_potential': 'HIGH' if score >= 9 else 'MEDIUM' if score >= 7 else 'LOW',
                'interpretation': interpretation
            }
        }

    def score_social_justice(self, data: Dict) -> Dict:
        """
        Factor 5: Social Justice / Jury Sympathy
        Measures plaintiff demographics and vulnerability

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        plaintiff_demographics = data.get('plaintiff_demographics', 'general_population')
        exposure_voluntary = data.get('exposure_voluntary', True)
        corporate_targeting = data.get('corporate_targeting', False)

        # Base score by demographic
        demographic_scores = {
            'children': 10,
            'pregnant_women': 9,
            'minorities_targeted': 9,
            'elderly': 8,
            'workers_no_choice': 8,
            'consumers_misled': 7,
            'general_population': 5,
            'voluntary_users': 3
        }

        score = demographic_scores.get(plaintiff_demographics, 5)

        # Adjust for targeting
        if corporate_targeting and plaintiff_demographics in ['children', 'minorities_targeted']:
            score = min(10, score + 1)

        # Penalize voluntary exposure
        if exposure_voluntary and plaintiff_demographics not in ['children', 'workers_no_choice']:
            score = max(3, score - 2)

        # Interpretation
        if score >= 9:
            interpretation = 'Exceptional jury sympathy - Vulnerable population targeted'
        elif score >= 7:
            interpretation = 'Strong jury sympathy'
        elif score >= 5:
            interpretation = 'Moderate jury sympathy'
        else:
            interpretation = 'Low jury sympathy - Voluntary risk'

        # Generate narrative
        narrative = self._generate_jury_narrative(plaintiff_demographics, corporate_targeting, exposure_voluntary)

        return {
            'score': score,
            'evidence': {
                'plaintiff_demographics': plaintiff_demographics.replace('_', ' ').title(),
                'exposure_voluntary': exposure_voluntary,
                'corporate_targeting': corporate_targeting,
                'narrative': narrative,
                'media_appeal': 'Very High' if score >= 9 else 'High' if score >= 7 else 'Medium',
                'interpretation': interpretation
            }
        }

    def score_severity(self, data: Dict) -> Dict:
        """
        Factor 6: Severity (Damages Per Plaintiff)
        Measures economic and non-economic damages

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        economic_damages = data.get('economic_damages', 0)
        non_economic_damages = data.get('non_economic_damages', 0)
        punitive_multiplier = data.get('punitive_multiplier', 1.0)

        compensatory = economic_damages + non_economic_damages
        total_damages = compensatory * punitive_multiplier

        # Scoring thresholds
        if total_damages >= 2_000_000:
            score = 10
            interpretation = '$2M+ per plaintiff (Death/catastrophic)'
        elif total_damages >= 1_000_000:
            score = 9
            interpretation = '$1M-$2M per plaintiff (Severe disability)'
        elif total_damages >= 500_000:
            score = 8
            interpretation = '$500K-$1M per plaintiff (Chronic disease, major surgeries)'
        elif total_damages >= 250_000:
            score = 7
            interpretation = '$250K-$500K per plaintiff (Moderate chronic disease)'
        elif total_damages >= 100_000:
            score = 5
            interpretation = '$100K-$250K per plaintiff (Mild chronic disease)'
        elif total_damages >= 50_000:
            score = 3
            interpretation = '$50K-$100K per plaintiff (Acute injury)'
        else:
            score = 0
            interpretation = '<$50K per plaintiff (Too low for contingency)'

        return {
            'score': score,
            'evidence': {
                'economic_damages': f'${economic_damages:,} (medical + lost wages)',
                'non_economic_damages': f'${non_economic_damages:,} (pain/suffering)',
                'punitive_damages': f'{punitive_multiplier}× multiplier' if punitive_multiplier > 1 else 'None expected',
                'total_per_plaintiff': f'${int(total_damages):,}',
                'settlement_range': self._estimate_settlement_range(total_damages),
                'interpretation': interpretation
            }
        }

    def score_novelty(self, data: Dict) -> Dict:
        """
        Factor 7: Novelty (First-Mover Advantage)
        Measures competition level

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        pacer_cases = data.get('pacer_cases_count', 0)
        mdl_status = data.get('mdl_status', 'NONE')
        media_coverage = data.get('media_coverage_count', 0)
        academic_publications = data.get('recent_publications_count', 0)

        # Scoring
        if pacer_cases == 0 and media_coverage == 0:
            score = 10
            interpretation = 'Pure first-mover - ZERO litigation, ZERO media'
        elif pacer_cases == 0 and academic_publications >= 1:
            score = 9
            interpretation = 'Post-publication, pre-litigation window (6-12 months)'
        elif pacer_cases <= 10:
            score = 7
            interpretation = f'Early litigation ({pacer_cases} cases filed, no MDL yet)'
        elif pacer_cases <= 100:
            score = 5
            interpretation = f'Competitive ({pacer_cases} cases, MDL pending)'
        elif pacer_cases <= 500:
            score = 3
            interpretation = f'Crowded field ({pacer_cases}+ cases, MDL likely)'
        else:
            score = 0
            interpretation = f'Saturated ({pacer_cases}+ cases filed)'

        # Penalty for MDL formation
        if mdl_status == 'FORMED':
            score = max(0, score - 3)
        elif mdl_status == 'PETITION':
            score = max(0, score - 1)

        # First-mover window estimate
        if score >= 9:
            window = '12-24 months before competition'
        elif score >= 7:
            window = '6-12 months window remaining'
        elif score >= 5:
            window = '3-6 months window'
        else:
            window = 'Window closed or closing fast'

        return {
            'score': score,
            'evidence': {
                'pacer_cases_filed': pacer_cases,
                'mdl_status': mdl_status,
                'media_coverage': f'{media_coverage} mainstream articles',
                'academic_status': f'{academic_publications} recent publications' if academic_publications else 'No major studies yet',
                'first_mover_window': window,
                'interpretation': interpretation
            }
        }

    # Helper methods

    def _get_comparable_torts(self, bradford_hill_score: float) -> str:
        """Map Bradford Hill score to comparable historical torts"""
        if bradford_hill_score >= 95:
            return 'Asbestos (98), Tobacco (99), Opioids (97)'
        elif bradford_hill_score >= 85:
            return 'Roundup (91), Talc (88), Hair Relaxer (85)'
        elif bradford_hill_score >= 70:
            return 'NEC (75), Paraquat (78)'
        else:
            return 'Below litigation threshold'

    def _generate_jury_narrative(self, demographics: str, targeting: bool, voluntary: bool) -> str:
        """Generate jury-friendly narrative"""
        narratives = {
            'children': 'Children unknowingly poisoned by products marketed to them',
            'workers_no_choice': 'Essential workers exposed without choice or protection',
            'minorities_targeted': 'Vulnerable population specifically targeted for profit',
            'elderly': 'Seniors harmed by products they trusted',
            'general_population': 'Consumers misled about product safety'
        }

        base = narratives.get(demographics, 'Plaintiffs harmed by defendant negligence')

        if targeting:
            base += ' (targeted marketing)'
        if not voluntary:
            base += ' (no choice in exposure)'

        return base

    def _estimate_settlement_range(self, per_plaintiff_damages: float) -> str:
        """Estimate settlement range based on damages"""
        low = int(per_plaintiff_damages * 0.6)
        high = int(per_plaintiff_damages * 1.2)
        return f'${low:,}-${high:,} per plaintiff'

    def _interpret_score(self, score: float) -> str:
        """Convert composite score to interpretation"""
        if score >= 100:
            return 'EXCEPTIONAL'
        elif score >= 90:
            return 'STRONG'
        elif score >= 80:
            return 'MARGINAL'
        else:
            return 'WEAK'

    def _generate_recommendation(self, litigation_score: float, bradford_hill_score: float, factor_scores: Dict) -> str:
        """Generate pursuit recommendation"""
        # Decision matrix
        if bradford_hill_score >= 95 and litigation_score >= 100:
            return 'FILE IMMEDIATELY - Exceptional discovery (all factors align)'

        if bradford_hill_score >= 85 and litigation_score >= 90:
            return 'VALIDATE & PURSUE - Strong discovery, commission expert validation'

        if bradford_hill_score >= 85 and litigation_score >= 80:
            return 'VALIDATE CAREFULLY - Strong science, marginal business case'

        if bradford_hill_score >= 70 and litigation_score >= 90:
            return 'MONITOR CLOSELY - Good business case, science needs strengthening'

        if bradford_hill_score >= 70 and litigation_score >= 80:
            return 'MONITOR - Marginal on both fronts, watch for improvements'

        if bradford_hill_score < 70:
            return 'REJECT - Causation too weak (Bradford Hill <70)'

        if litigation_score < 80:
            return 'REJECT - Insufficient ROI (Litigation <80)'

        return 'REVIEW - Borderline case, needs expert judgment'


# Example usage
if __name__ == "__main__":
    # Test with TiO2 → IBD data
    tio2_litigation_data = {
        'exposed_population': 50_000_000,
        'disease_prevalence': 0.002,  # 0.2%
        'eligibility_filter': 0.50,
        'participation_rate': 0.30,
        'defendants': [
            {'name': 'Mars, Inc.', 'revenue': 45_000_000_000, 'market_cap': None},
            {'name': 'Mondelez International', 'revenue': 35_000_000_000, 'market_cap': 90_000_000_000},
            {'name': 'Hershey Company', 'revenue': 11_000_000_000, 'market_cap': 45_000_000_000},
            {'name': 'General Mills', 'revenue': 20_000_000_000, 'market_cap': 65_000_000_000}
        ],
        'regulatory_actions': [
            {'jurisdiction': 'EU', 'action_type': 'BAN', 'action_date': '2022-08-07'}
        ],
        'internal_docs_available': True,
        'warning_labels': False,
        'scientific_knowledge_date': '2015-01-01',
        'plaintiff_demographics': 'children',
        'exposure_voluntary': False,
        'corporate_targeting': True,
        'economic_damages': 150_000,
        'non_economic_damages': 350_000,
        'punitive_multiplier': 2.0,
        'pacer_cases_count': 0,
        'mdl_status': 'NONE',
        'media_coverage_count': 0,
        'recent_publications_count': 0
    }

    scorer = LitigationScorer()
    result = scorer.score(tio2_litigation_data, bradford_hill_score=94.0)

    print(f"\nLitigation Score: {result.composite_score}/100")
    print(f"Interpretation: {result.interpretation}")
    print(f"\nFactor Breakdown:")
    for factor, scores in result.factor_scores.items():
        print(f"  {factor.replace('_', ' ').title()}: {scores['score']}/10 (weighted: {scores['weighted']})")
    print(f"\nStrengths: {result.strengths}")
    print(f"\nWeaknesses: {result.weaknesses}")
    print(f"\nRecommendation: {result.pursuit_recommendation}")
