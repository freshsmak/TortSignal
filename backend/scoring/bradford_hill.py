"""
Bradford Hill Causal Assessment Scoring Engine
Implements the 9 criteria for causal inference in epidemiology
Based on EDE_METHODOLOGY.md Section VI
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class BradfordHillResult:
    """Result of Bradford Hill scoring"""
    composite_score: Decimal
    interpretation: str
    criteria_scores: Dict[str, Dict[str, any]]
    flagged_weaknesses: List[str]
    next_steps: List[str]


class BradfordHillScorer:
    """
    Automated Bradford Hill causal assessment
    Scores 9 criteria on 0-10 scale, applies weights, returns composite 0-100 score
    """

    # Weights for each criterion (must sum to 100)
    WEIGHTS = {
        'strength': 15,
        'consistency': 12,
        'specificity': 8,
        'temporality': 15,  # REQUIRED
        'biological_gradient': 10,
        'plausibility': 15,
        'coherence': 10,
        'experiment': 10,
        'analogy': 5
    }

    def __init__(self):
        pass

    def score(self, signal_data: Dict) -> BradfordHillResult:
        """
        Main scoring function

        Args:
            signal_data: Dictionary containing all evidence for the signal
                {
                    'chemical': str,
                    'disease': str,
                    'effect_size': float (RR/OR),
                    'studies': List[Dict],  # Epidemiology studies
                    'mechanisms': List[Dict],  # Mechanistic papers
                    'exposure_timeline': Dict,
                    'disease_timeline': Dict,
                    'regulatory_actions': List[Dict],
                    'animal_studies': List[Dict],
                    ...
                }

        Returns:
            BradfordHillResult with composite score and detailed breakdown
        """

        scores = {}

        # Score each criterion
        scores['strength'] = self.score_strength(signal_data)
        scores['consistency'] = self.score_consistency(signal_data)
        scores['specificity'] = self.score_specificity(signal_data)
        scores['temporality'] = self.score_temporality(signal_data)
        scores['biological_gradient'] = self.score_biological_gradient(signal_data)
        scores['plausibility'] = self.score_plausibility(signal_data)
        scores['coherence'] = self.score_coherence(signal_data)
        scores['experiment'] = self.score_experiment(signal_data)
        scores['analogy'] = self.score_analogy(signal_data)

        # Calculate weighted scores
        criteria_scores = {}
        for criterion, raw_score in scores.items():
            weighted_score = (raw_score['score'] / 10) * self.WEIGHTS[criterion]
            criteria_scores[criterion] = {
                'score': raw_score['score'],
                'weighted': weighted_score,
                'evidence': raw_score['evidence']
            }

        # Calculate composite
        composite_score = sum(c['weighted'] for c in criteria_scores.values())

        # Interpretation
        interpretation = self._interpret_score(composite_score)

        # Flag weaknesses (score < 5)
        weaknesses = [
            f"{criterion.replace('_', ' ').title()} ({criteria_scores[criterion]['score']}/10)"
            for criterion in scores
            if criteria_scores[criterion]['score'] < 5
        ]

        # Next steps based on score
        next_steps = self._generate_next_steps(composite_score, criteria_scores)

        return BradfordHillResult(
            composite_score=Decimal(str(round(composite_score, 1))),
            interpretation=interpretation,
            criteria_scores=criteria_scores,
            flagged_weaknesses=weaknesses,
            next_steps=next_steps
        )

    def score_strength(self, data: Dict) -> Dict:
        """
        Criterion 1: Strength of Association
        Measures effect size (RR/OR)

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        effect_size = data.get('effect_size', None)

        if effect_size is None:
            # Try to calculate from trend data
            percent_change = data.get('percent_change', 0)
            if percent_change:
                effect_size = 1 + (percent_change / 100)  # e.g., 72% increase = RR 1.72

        if not effect_size or effect_size < 1.2:
            return {
                'score': 0,
                'evidence': {'effect_size': effect_size or 0, 'interpretation': 'No association or very weak'}
            }
        elif effect_size >= 5.0:
            score = 10
            interpretation = 'Very strong (RR/OR ≥5.0)'
        elif effect_size >= 3.0:
            score = 8
            interpretation = 'Strong (RR/OR 3.0-5.0)'
        elif effect_size >= 2.0:
            score = 6
            interpretation = 'Moderate (RR/OR 2.0-3.0)'
        elif effect_size >= 1.5:
            score = 4
            interpretation = 'Modest (RR/OR 1.5-2.0)'
        else:  # 1.2-1.5
            score = 2
            interpretation = 'Weak (RR/OR 1.2-1.5)'

        return {
            'score': score,
            'evidence': {
                'effect_size': effect_size,
                'metric': 'Relative Risk / Odds Ratio',
                'interpretation': interpretation,
                'source': data.get('effect_size_source', 'Calculated from trend data')
            }
        }

    def score_consistency(self, data: Dict) -> Dict:
        """
        Criterion 2: Consistency
        Measures replication across multiple independent studies

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        studies = data.get('studies', [])

        if not studies:
            return {
                'score': 2,
                'evidence': {
                    'total_studies': 0,
                    'interpretation': 'No epidemiological studies yet (mechanistic only)'
                }
            }

        # Count unique studies (deduplicate by author/dataset)
        unique_studies = self._deduplicate_studies(studies)

        # Classify findings
        positive_count = sum(1 for s in unique_studies if s.get('finding') == 'positive')
        null_count = sum(1 for s in unique_studies if s.get('finding') == 'null')
        negative_count = sum(1 for s in unique_studies if s.get('finding') == 'negative')

        total = len(unique_studies)
        consistency_rate = positive_count / total if total > 0 else 0

        # Scoring
        if total >= 10 and consistency_rate >= 0.80:
            score = 10
        elif total >= 5 and consistency_rate >= 0.80:
            score = 8
        elif total >= 3 and consistency_rate >= 0.75:
            score = 6
        elif total == 2 and consistency_rate == 1.0:
            score = 4
        elif total == 1:
            score = 2
        else:
            score = 0

        return {
            'score': score,
            'evidence': {
                'total_studies': total,
                'positive_studies': positive_count,
                'null_studies': null_count,
                'negative_studies': negative_count,
                'consistency_rate': f"{consistency_rate:.0%}",
                'interpretation': f"{'Strong' if score >= 8 else 'Moderate' if score >= 6 else 'Weak'} consistency"
            }
        }

    def score_specificity(self, data: Dict) -> Dict:
        """
        Criterion 3: Specificity
        Measures whether chemical uniquely causes this disease

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        diseases_associated = data.get('diseases_associated', [])

        disease_count = len(diseases_associated)
        target_disease = data.get('disease')

        # Check if target disease is primary association
        target_paper_count = data.get('target_disease_papers', 0)
        total_paper_count = data.get('total_papers', 1)
        target_proportion = target_paper_count / total_paper_count if total_paper_count > 0 else 0

        if disease_count == 1:
            score = 10
            interpretation = 'Highly specific (1 disease only)'
        elif disease_count <= 2 and target_proportion > 0.50:
            score = 8
            interpretation = 'Primary association (1-2 diseases, target is primary)'
        elif disease_count <= 5:
            score = 6
            interpretation = f'Moderate specificity ({disease_count} diseases associated)'
        elif disease_count <= 10:
            score = 4
            interpretation = f'Low specificity ({disease_count} diseases associated)'
        else:
            score = 2
            interpretation = f'Very low specificity ({disease_count}+ diseases associated)'

        return {
            'score': score,
            'evidence': {
                'diseases_associated': diseases_associated,
                'disease_count': disease_count,
                'target_disease_proportion': f"{target_proportion:.0%}",
                'interpretation': interpretation
            }
        }

    def score_temporality(self, data: Dict) -> Dict:
        """
        Criterion 4: Temporality (REQUIRED)
        Measures whether exposure precedes disease

        THIS IS THE ONLY REQUIRED CRITERION
        If score = 0, causation is IMPOSSIBLE

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        exposure_timeline = data.get('exposure_timeline', {})
        disease_timeline = data.get('disease_timeline', {})

        exposure_start = exposure_timeline.get('start_year')
        disease_start = disease_timeline.get('increase_start_year')

        if not exposure_start or not disease_start:
            return {
                'score': 5,
                'evidence': {
                    'exposure_period': 'Unknown',
                    'disease_period': 'Unknown',
                    'interpretation': 'Temporal sequence probable but not definitively documented'
                }
            }

        # Check if exposure precedes disease
        if exposure_start > disease_start:
            return {
                'score': 0,
                'evidence': {
                    'exposure_period': f"{exposure_start}+",
                    'disease_period': f"{disease_start}+",
                    'interpretation': 'FATAL FLAW: Exposure does NOT precede disease'
                }
            }

        # Calculate latency
        latency_expected = data.get('latency_expected', {})
        min_latency = latency_expected.get('min_years', 10)
        max_latency = latency_expected.get('max_years', 30)

        exposure_peak = exposure_timeline.get('peak_year', exposure_start)
        observed_latency = disease_start - exposure_peak

        # Score based on whether latency is plausible
        if min_latency <= observed_latency <= max_latency:
            score = 10
            interpretation = f'Perfect temporal sequence (latency {observed_latency} years, expected {min_latency}-{max_latency})'
        elif observed_latency < min_latency:
            score = 5
            interpretation = f'Temporal sequence confirmed but latency too short ({observed_latency} years, expected {min_latency}-{max_latency})'
        elif observed_latency > max_latency:
            score = 5
            interpretation = f'Temporal sequence confirmed but latency longer than expected ({observed_latency} years, expected {min_latency}-{max_latency})'
        else:
            score = 8
            interpretation = 'Strong temporal sequence'

        return {
            'score': score,
            'evidence': {
                'exposure_period': f"{exposure_timeline.get('start_year')}-{exposure_timeline.get('end_year') or 'ongoing'}",
                'disease_period': f"{disease_timeline.get('increase_start_year')}-{disease_timeline.get('increase_peak_year')}",
                'observed_latency': f"{observed_latency} years",
                'expected_latency': f"{min_latency}-{max_latency} years",
                'interpretation': interpretation
            }
        }

    def score_biological_gradient(self, data: Dict) -> Dict:
        """
        Criterion 5: Biological Gradient (Dose-Response)
        Measures whether higher exposure → higher disease risk

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        dose_response_studies = data.get('dose_response_studies', [])

        if len(dose_response_studies) >= 3:
            score = 10
            interpretation = 'Clear dose-response documented in multiple studies'
        elif len(dose_response_studies) >= 1:
            score = 8
            interpretation = f'Dose-response in {len(dose_response_studies)} study(ies)'
        else:
            # Check for proxy evidence (occupational exposure higher than general population)
            occupational_risk = data.get('occupational_risk_ratio', None)
            if occupational_risk and occupational_risk > 1.5:
                score = 6
                interpretation = f'Plausible gradient (occupational exposure {occupational_risk}× general population)'
            else:
                score = 4
                interpretation = 'No formal dose-response studies, gradient unclear'

        return {
            'score': score,
            'evidence': {
                'dose_response_studies': len(dose_response_studies),
                'interpretation': interpretation
            }
        }

    def score_plausibility(self, data: Dict) -> Dict:
        """
        Criterion 6: Plausibility (Biological Mechanism)
        CRITICAL FOR DAUBERT ADMISSIBILITY

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        mechanisms = data.get('mechanisms', [])
        mechanistic_papers = data.get('mechanistic_papers_count', len(mechanisms))
        animal_models = data.get('animal_models_count', 0)

        if mechanistic_papers >= 50 and animal_models >= 5:
            score = 10
            interpretation = 'Mechanism fully elucidated (50+ papers, 5+ animal models)'
        elif mechanistic_papers >= 20:
            score = 8
            interpretation = f'Mechanism well-understood ({mechanistic_papers} papers)'
        elif mechanistic_papers >= 10:
            score = 6
            interpretation = f'Mechanism plausible ({mechanistic_papers} papers)'
        elif mechanistic_papers >= 5:
            score = 4
            interpretation = f'Mechanism weakly plausible ({mechanistic_papers} papers)'
        elif mechanistic_papers >= 1:
            score = 2
            interpretation = f'Mechanism speculative ({mechanistic_papers} paper(s))'
        else:
            score = 0
            interpretation = 'No mechanism identified'

        # Extract pathways
        pathways = [m.get('pathway') for m in mechanisms if 'pathway' in m]

        return {
            'score': score,
            'evidence': {
                'mechanistic_papers': mechanistic_papers,
                'animal_models': animal_models,
                'pathways_identified': pathways,
                'interpretation': interpretation
            }
        }

    def score_coherence(self, data: Dict) -> Dict:
        """
        Criterion 7: Coherence
        Measures whether association fits with existing knowledge

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        review_articles = data.get('review_articles_count', 0)

        if review_articles >= 5:
            score = 10
            interpretation = 'Perfectly coherent (5+ review articles validate link)'
        elif review_articles >= 2:
            score = 8
            interpretation = f'Mostly coherent ({review_articles} review articles)'
        elif review_articles == 1:
            score = 6
            interpretation = 'Somewhat coherent (1 review article)'
        else:
            # Default: Assume coherent unless evidence of contradiction
            contradictions = data.get('contradictions', [])
            if contradictions:
                score = 4
                interpretation = f'Weak coherence ({len(contradictions)} contradictions with existing knowledge)'
            else:
                score = 6
                interpretation = 'Assumed coherent (no reviews yet, but no contradictions)'

        return {
            'score': score,
            'evidence': {
                'review_articles': review_articles,
                'interpretation': interpretation
            }
        }

    def score_experiment(self, data: Dict) -> Dict:
        """
        Criterion 8: Experiment (Intervention Studies)
        Measures whether exposure removal reduces disease

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        rct_studies = data.get('rct_studies', [])
        occupational_interventions = data.get('occupational_interventions', [])
        animal_interventions = data.get('animal_intervention_studies', [])
        regulatory_actions = data.get('regulatory_actions', [])

        # Check for RCTs (rare for harms)
        if len(rct_studies) >= 1:
            score = 10
            interpretation = 'RCT or natural experiment shows causation'
        # Check for occupational interventions
        elif len(occupational_interventions) >= 1:
            score = 8
            interpretation = 'Occupational intervention studies show disease reduction'
        # Check for animal interventions
        elif len(animal_interventions) >= 1:
            score = 6
            interpretation = f'Animal intervention studies ({len(animal_interventions)})'
        # Check for regulatory bans as natural experiments
        elif regulatory_actions:
            # Find most recent ban
            bans = [a for a in regulatory_actions if a.get('action_type') == 'BAN']
            if bans:
                most_recent = max(bans, key=lambda x: x.get('action_date', '1900-01-01'))
                ban_year = int(most_recent.get('action_date', '2020-01-01').split('-')[0])
                years_elapsed = datetime.now().year - ban_year

                if years_elapsed >= 3:
                    score = 8
                    interpretation = f'Natural experiment (ban {years_elapsed} years ago, monitoring disease trends)'
                else:
                    score = 4
                    interpretation = f'Natural experiment pending (ban {years_elapsed} years ago, too soon for effect)'
            else:
                score = 2
                interpretation = 'No experimental evidence, theoretically feasible'
        else:
            score = 2
            interpretation = 'No experimental evidence'

        return {
            'score': score,
            'evidence': {
                'rct_studies': len(rct_studies),
                'occupational_interventions': len(occupational_interventions),
                'animal_studies': len(animal_interventions),
                'natural_experiments': f"{len([a for a in regulatory_actions if a.get('action_type') == 'BAN'])} ban(s) provide natural experiment",
                'interpretation': interpretation
            }
        }

    def score_analogy(self, data: Dict) -> Dict:
        """
        Criterion 9: Analogy
        Measures whether similar exposures cause similar diseases

        Returns: {'score': float (0-10), 'evidence': dict}
        """
        chemical_class = data.get('chemical_class', 'Unknown')
        analogous_exposures = data.get('analogous_exposures', [])

        if len(analogous_exposures) >= 3:
            score = 7
            interpretation = f'Moderate analogy ({len(analogous_exposures)} similar exposures → similar diseases)'
        elif len(analogous_exposures) >= 1:
            score = 4
            interpretation = f'Weak analogy ({len(analogous_exposures)} similar exposure(s))'
        else:
            score = 0
            interpretation = 'No analogy identified'

        return {
            'score': score,
            'evidence': {
                'chemical_class': chemical_class,
                'analogous_exposures': analogous_exposures,
                'interpretation': interpretation
            }
        }

    # Helper methods

    def _deduplicate_studies(self, studies: List[Dict]) -> List[Dict]:
        """Remove duplicate studies (same author/dataset)"""
        seen = set()
        unique = []
        for study in studies:
            key = (study.get('author', ''), study.get('dataset', ''))
            if key not in seen:
                seen.add(key)
                unique.append(study)
        return unique

    def _interpret_score(self, score: float) -> str:
        """Convert composite score to interpretation"""
        if score >= 95:
            return 'VERY_STRONG'
        elif score >= 85:
            return 'STRONG'
        elif score >= 70:
            return 'MODERATE'
        elif score >= 50:
            return 'WEAK'
        else:
            return 'VERY_WEAK'

    def _generate_next_steps(self, composite_score: float, criteria_scores: Dict) -> List[str]:
        """Generate recommended next steps based on score"""
        steps = []

        if composite_score >= 95:
            steps.append("File cases immediately, no additional validation needed")
        elif composite_score >= 85:
            steps.append("Commission expert validation (attorney + gastroenterologist)")
            steps.append("Conduct PACER search (confirm zero litigation)")
            steps.append("Survey patients (validate exposure patterns)")
        elif composite_score >= 70:
            steps.append("Monitor for new evidence (quarterly review)")
            steps.append("Wait for academic confirmation study")
        else:
            steps.append("Reject - causation too weak for litigation")

        # Add criterion-specific steps
        if criteria_scores['temporality']['score'] == 0:
            steps.insert(0, "FATAL FLAW: Cannot pursue (exposure does not precede disease)")

        if criteria_scores['plausibility']['score'] < 4:
            steps.append("Commission toxicology expert to review mechanism")

        if criteria_scores['consistency']['score'] < 4:
            steps.append("Wait for more epidemiological studies (insufficient replication)")

        return steps


# Example usage
if __name__ == "__main__":
    # Test with TiO2 → IBD data
    tio2_data = {
        'chemical': 'Titanium Dioxide',
        'disease': 'Inflammatory Bowel Disease',
        'effect_size': 1.65,  # 22-72% increase midpoint
        'percent_change': 47,  # Average of 22-72%
        'studies': [
            {'author': 'CDC', 'finding': 'positive', 'dataset': 'NHIS'},
            {'author': 'California DPH', 'finding': 'positive', 'dataset': 'State Registry'},
            {'author': 'European Study', 'finding': 'positive', 'dataset': 'EU IBD Registry'},
            {'author': 'Meta-analysis', 'finding': 'null', 'dataset': 'Combined'}
        ],
        'diseases_associated': ['Inflammatory Bowel Disease', 'Colorectal Cancer', 'Genotoxicity'],
        'target_disease_papers': 45,
        'total_papers': 100,
        'exposure_timeline': {'start_year': 1990, 'peak_year': 2000, 'end_year': None},
        'disease_timeline': {'increase_start_year': 2010, 'increase_peak_year': 2020},
        'latency_expected': {'min_years': 10, 'max_years': 30},
        'dose_response_studies': [],  # No formal studies yet
        'mechanisms': [
            {'pathway': 'NLRP3 inflammasome activation', 'evidence_count': 34},
            {'pathway': 'Gut microbiome disruption', 'evidence_count': 23}
        ],
        'mechanistic_papers_count': 78,
        'animal_models_count': 9,
        'review_articles_count': 7,
        'rct_studies': [],
        'occupational_interventions': [],
        'animal_intervention_studies': [{'description': 'Mice study showing IBD reduction'}],
        'regulatory_actions': [
            {'action_type': 'BAN', 'action_date': '2022-08-07', 'agency': 'EU ECHA'}
        ],
        'chemical_class': 'Nanoparticles',
        'analogous_exposures': [
            'Silver nanoparticles → gut inflammation',
            'Silica nanoparticles → intestinal barrier dysfunction'
        ]
    }

    scorer = BradfordHillScorer()
    result = scorer.score(tio2_data)

    print(f"\nBradford Hill Score: {result.composite_score}/100")
    print(f"Interpretation: {result.interpretation}")
    print(f"\nCriteria Breakdown:")
    for criterion, scores in result.criteria_scores.items():
        print(f"  {criterion.replace('_', ' ').title()}: {scores['score']}/10 (weighted: {scores['weighted']})")
    print(f"\nWeaknesses: {result.flagged_weaknesses}")
    print(f"\nNext Steps:")
    for step in result.next_steps:
        print(f"  - {step}")
