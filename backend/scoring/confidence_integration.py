"""
Confidence Integration Layer

Wraps existing Bradford Hill and Litigation scorers to add confidence tracking
and uncertainty-aware score adjustments.

This layer:
1. Tracks data quality for each evidence source
2. Calculates confidence penalties
3. Adjusts final scores based on confidence
4. Generates comprehensive confidence reports
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass, asdict

from .bradford_hill import BradfordHillScorer, BradfordHillResult
from .litigation import LitigationScorer, LitigationResult
from .confidence import (
    BradfordHillConfidence,
    LitigationConfidence,
    SourceConfidence,
    CompositeConfidenceReport,
    DataQualityMetrics,
    DataSource,
    ConfidenceLevel,
    create_cdc_wonder_confidence,
    create_seer_confidence,
    create_nhanes_confidence,
    create_openfda_confidence,
    create_pubmed_confidence
)


@dataclass
class ConfidenceAdjustedBradfordHillResult:
    """Bradford Hill result with confidence adjustments"""
    original_result: BradfordHillResult
    confidence_assessment: BradfordHillConfidence
    adjusted_score: Decimal
    confidence_penalty: float
    interpretation_with_confidence: str


@dataclass
class ConfidenceAdjustedLitigationResult:
    """Litigation result with confidence adjustments"""
    original_result: LitigationResult
    confidence_assessment: LitigationConfidence
    adjusted_score: Decimal
    confidence_penalty: float
    interpretation_with_confidence: str


class ConfidenceAwareBradfordHillScorer:
    """
    Confidence-aware wrapper for Bradford Hill scorer

    Tracks data quality throughout scoring and applies confidence penalties
    """

    def __init__(self):
        self.base_scorer = BradfordHillScorer()

    def score_with_confidence(
        self,
        signal_data: Dict,
        confidence_data: Dict
    ) -> ConfidenceAdjustedBradfordHillResult:
        """
        Score Bradford Hill criteria with confidence tracking

        Args:
            signal_data: Standard Bradford Hill input data
            confidence_data: Data quality metadata
                {
                    'epidemiology': {
                        'source_type': 'api' | 'parsed' | 'literature',
                        'years': int,
                        'sample_size': int
                    },
                    'exposure': {
                        'biomarker_available': bool,
                        'sample_size': int,
                        'cycles': int
                    },
                    'literature': {
                        'paper_count': int,
                        'study_types': List[str],
                        'replication_count': int
                    },
                    'adverse_events': {
                        'report_count': int
                    },
                    ...
                }

        Returns:
            Confidence-adjusted Bradford Hill result
        """
        # Step 1: Run standard Bradford Hill scoring
        original_result = self.base_scorer.score(signal_data)

        # Step 2: Build confidence assessment for each criterion
        bh_confidence = self._build_confidence_assessment(
            signal_data,
            confidence_data,
            original_result
        )

        # Step 3: Calculate composite confidence
        bh_confidence.calculate_composite_confidence()

        # Step 4: Apply confidence penalty
        adjusted_score = bh_confidence.apply_confidence_penalty(
            float(original_result.composite_score)
        )

        confidence_penalty = 1.0 - (adjusted_score / float(original_result.composite_score))

        # Step 5: Generate confidence-aware interpretation
        interpretation = self._generate_confidence_interpretation(
            original_result,
            bh_confidence,
            adjusted_score
        )

        return ConfidenceAdjustedBradfordHillResult(
            original_result=original_result,
            confidence_assessment=bh_confidence,
            adjusted_score=Decimal(str(round(adjusted_score, 1))),
            confidence_penalty=round(confidence_penalty, 3),
            interpretation_with_confidence=interpretation
        )

    def _build_confidence_assessment(
        self,
        signal_data: Dict,
        confidence_data: Dict,
        original_result: BradfordHillResult
    ) -> BradfordHillConfidence:
        """Build per-criterion confidence assessment"""

        # Extract confidence data
        epi_data = confidence_data.get('epidemiology', {})
        exposure_data = confidence_data.get('exposure', {})
        lit_data = confidence_data.get('literature', {})
        adverse_data = confidence_data.get('adverse_events', {})
        regulatory_data = confidence_data.get('regulatory', {})

        # Build source confidences for each criterion

        # 1. Strength - depends on epidemiology quality
        strength_conf = self._create_epidemiology_confidence(epi_data)

        # 2. Consistency - depends on study replication
        consistency_conf = self._create_consistency_confidence(lit_data)

        # 3. Specificity - depends on epidemiology breadth
        specificity_conf = self._create_epidemiology_confidence(epi_data)

        # 4. Temporality - depends on epidemiology + exposure timeline quality
        temporality_conf = self._create_temporality_confidence(epi_data, exposure_data)

        # 5. Biological gradient - depends on dose-response studies
        gradient_conf = self._create_gradient_confidence(lit_data)

        # 6. Plausibility - depends on mechanistic literature
        plausibility_conf = self._create_plausibility_confidence(lit_data)

        # 7. Coherence - depends on review literature
        coherence_conf = self._create_coherence_confidence(lit_data)

        # 8. Experiment - depends on intervention/animal studies
        experiment_conf = self._create_experiment_confidence(lit_data, regulatory_data)

        # 9. Analogy - depends on comparative evidence quality
        analogy_conf = self._create_analogy_confidence(lit_data)

        return BradfordHillConfidence(
            strength_confidence=strength_conf,
            consistency_confidence=consistency_conf,
            specificity_confidence=specificity_conf,
            temporality_confidence=temporality_conf,
            biological_gradient_confidence=gradient_conf,
            plausibility_confidence=plausibility_conf,
            coherence_confidence=coherence_conf,
            experiment_confidence=experiment_conf,
            analogy_confidence=analogy_conf
        )

    def _create_epidemiology_confidence(self, epi_data: Dict) -> SourceConfidence:
        """Create confidence for epidemiology data (CDC WONDER/SEER)"""
        source_type = epi_data.get('source_type', 'literature')
        years = epi_data.get('years', 10)
        sample_size = epi_data.get('sample_size')

        # Determine if CDC WONDER or SEER
        if epi_data.get('source_name') == 'SEER':
            return create_seer_confidence(source_type, years, sample_size)
        else:
            return create_cdc_wonder_confidence(source_type, years, sample_size)

    def _create_consistency_confidence(self, lit_data: Dict) -> SourceConfidence:
        """Create confidence for consistency (replication studies)"""
        paper_count = lit_data.get('paper_count', 0)
        study_types = lit_data.get('study_types', [])
        replication_count = lit_data.get('replication_count', 1)

        return create_pubmed_confidence(paper_count, study_types, replication_count)

    def _create_temporality_confidence(self, epi_data: Dict, exposure_data: Dict) -> SourceConfidence:
        """Create confidence for temporality (requires both epi and exposure data)"""
        epi_source_type = epi_data.get('source_type', 'literature')
        exposure_available = exposure_data.get('biomarker_available', False)

        # If both high-quality, high confidence. If either weak, moderate/low.
        if epi_source_type == 'api' and exposure_available:
            source = DataSource.CDC_WONDER_API
            conf_level = ConfidenceLevel.HIGH
        elif epi_source_type in ['api', 'parsed']:
            source = DataSource.CDC_WONDER_PARSED
            conf_level = ConfidenceLevel.MODERATE
        else:
            source = DataSource.CDC_WONDER_LITERATURE
            conf_level = ConfidenceLevel.LOW

        metrics = DataQualityMetrics(
            source=source,
            sample_size=epi_data.get('sample_size'),
            time_span_years=epi_data.get('years', 10),
            measurement_type='direct' if epi_source_type == 'api' else 'indirect',
            peer_reviewed=False,
            replication_count=1
        )

        return SourceConfidence.from_metrics("Temporality", metrics)

    def _create_gradient_confidence(self, lit_data: Dict) -> SourceConfidence:
        """Create confidence for biological gradient (dose-response studies)"""
        # Look for dose-response specific studies
        dose_response_papers = lit_data.get('dose_response_papers', 0)

        if dose_response_papers >= 3:
            source = DataSource.PUBMED_COHORT
        elif dose_response_papers >= 1:
            source = DataSource.PUBMED_CASE_CONTROL
        else:
            source = DataSource.PUBMED_CASE_REPORT

        metrics = DataQualityMetrics(
            source=source,
            sample_size=None,
            peer_reviewed=True,
            replication_count=dose_response_papers
        )

        return SourceConfidence.from_metrics("BiologicalGradient", metrics)

    def _create_plausibility_confidence(self, lit_data: Dict) -> SourceConfidence:
        """Create confidence for plausibility (mechanistic studies)"""
        mech_papers = lit_data.get('mechanistic_papers', 0)

        if mech_papers >= 50:
            replication = 10
        elif mech_papers >= 20:
            replication = 5
        elif mech_papers >= 10:
            replication = 3
        else:
            replication = 1

        return create_pubmed_confidence(
            paper_count=mech_papers,
            study_types=['mechanistic'],
            replication_count=replication
        )

    def _create_coherence_confidence(self, lit_data: Dict) -> SourceConfidence:
        """Create confidence for coherence (review literature)"""
        review_papers = lit_data.get('review_papers', 0)

        if review_papers >= 5:
            study_types = ['systematic_review']
        elif review_papers >= 2:
            study_types = ['cohort']
        else:
            study_types = ['case_report']

        return create_pubmed_confidence(
            paper_count=review_papers,
            study_types=study_types,
            replication_count=review_papers
        )

    def _create_experiment_confidence(self, lit_data: Dict, regulatory_data: Dict) -> SourceConfidence:
        """Create confidence for experiment (intervention studies)"""
        has_rct = lit_data.get('has_rct', False)
        has_animal = lit_data.get('has_animal_studies', False)
        has_regulatory_ban = regulatory_data.get('has_ban', False)

        if has_rct:
            source = DataSource.PUBMED_RCT
        elif has_regulatory_ban:
            source = DataSource.EU_ECHA_DIRECT
        elif has_animal:
            source = DataSource.PUBMED_MECHANISTIC
        else:
            source = DataSource.PUBMED_CASE_REPORT

        metrics = DataQualityMetrics(
            source=source,
            peer_reviewed=True
        )

        return SourceConfidence.from_metrics("Experiment", metrics)

    def _create_analogy_confidence(self, lit_data: Dict) -> SourceConfidence:
        """Create confidence for analogy (comparative evidence)"""
        analog_count = lit_data.get('analog_exposures', 0)

        source = DataSource.PUBMED_MECHANISTIC if analog_count > 0 else DataSource.PUBMED_CASE_REPORT

        metrics = DataQualityMetrics(
            source=source,
            peer_reviewed=True,
            replication_count=analog_count
        )

        return SourceConfidence.from_metrics("Analogy", metrics)

    def _generate_confidence_interpretation(
        self,
        original_result: BradfordHillResult,
        bh_confidence: BradfordHillConfidence,
        adjusted_score: float
    ) -> str:
        """Generate interpretation that includes confidence context"""
        original_interp = original_result.interpretation
        conf = bh_confidence.composite_confidence
        conf_level = bh_confidence.weakest_criterion

        penalty_pct = (1 - (adjusted_score / float(original_result.composite_score))) * 100

        interp = f"{original_interp}\n\n"
        interp += f"Confidence: {conf:.1%} (weakest: {conf_level})\n"
        interp += f"Confidence penalty: -{penalty_pct:.1f}% (adjusted score: {adjusted_score:.1f})\n\n"

        if bh_confidence.flagged_concerns:
            interp += "Data Quality Concerns:\n"
            for concern in bh_confidence.flagged_concerns:
                interp += f"  - {concern}\n"

        return interp


class ConfidenceAwareLitigationScorer:
    """
    Confidence-aware wrapper for Litigation scorer

    Similar to Bradford Hill wrapper, but for litigation viability assessment
    """

    def __init__(self):
        self.base_scorer = LitigationScorer()

    def score_with_confidence(
        self,
        signal_data: Dict,
        confidence_data: Dict,
        bradford_hill_confidence: Optional[BradfordHillConfidence] = None
    ) -> ConfidenceAdjustedLitigationResult:
        """
        Score litigation viability with confidence tracking

        Args:
            signal_data: Standard litigation input data
            confidence_data: Data quality metadata
            bradford_hill_confidence: Optional BH confidence (affects causal strength confidence)

        Returns:
            Confidence-adjusted litigation result
        """
        # Step 1: Run standard litigation scoring
        # Extract bradford_hill_score from signal_data
        bh_score = signal_data.get('bradford_hill_score', signal_data.get('causal_strength', 70.0))
        original_result = self.base_scorer.score(signal_data, bh_score)

        # Step 2: Build confidence assessment
        lit_confidence = self._build_confidence_assessment(
            signal_data,
            confidence_data,
            bradford_hill_confidence
        )

        # Step 3: Calculate composite confidence
        lit_confidence.calculate_composite_confidence()

        # Step 4: Apply confidence penalty
        adjusted_score = lit_confidence.apply_confidence_penalty(
            float(original_result.composite_score)
        )

        confidence_penalty = 1.0 - (adjusted_score / float(original_result.composite_score))

        # Step 5: Generate interpretation
        interpretation = self._generate_confidence_interpretation(
            original_result,
            lit_confidence,
            adjusted_score
        )

        return ConfidenceAdjustedLitigationResult(
            original_result=original_result,
            confidence_assessment=lit_confidence,
            adjusted_score=Decimal(str(round(adjusted_score, 1))),
            confidence_penalty=round(confidence_penalty, 3),
            interpretation_with_confidence=interpretation
        )

    def _build_confidence_assessment(
        self,
        signal_data: Dict,
        confidence_data: Dict,
        bradford_hill_confidence: Optional[BradfordHillConfidence]
    ) -> LitigationConfidence:
        """Build per-factor confidence assessment"""

        # 1. Causal strength - inherit from Bradford Hill if available
        if bradford_hill_confidence:
            causal_conf = SourceConfidence(
                source_name="CausalStrength",
                data_quality=DataQualityMetrics(source=DataSource.CDC_WONDER_API),
                confidence_score=bradford_hill_confidence.composite_confidence,
                confidence_level=ConfidenceLevel.HIGH if bradford_hill_confidence.composite_confidence >= 0.8 else ConfidenceLevel.MODERATE
            )
        else:
            causal_conf = self._create_default_source_confidence("CausalStrength", 0.70)

        # 2. Population size - depends on epidemiology + exposure data
        pop_conf = self._create_population_confidence(confidence_data)

        # 3. Defendant solvency - typically high confidence (public financial data)
        solvency_conf = self._create_default_source_confidence("DefendantSolvency", 0.95)

        # 4. Preventability - depends on regulatory data quality
        prevent_conf = self._create_preventability_confidence(confidence_data)

        # 5. Social justice - typically moderate confidence (demographic data available)
        justice_conf = self._create_default_source_confidence("SocialJustice", 0.75)

        # 6. Severity - depends on medical literature + economic data
        severity_conf = self._create_severity_confidence(confidence_data)

        # 7. Novelty - depends on litigation database quality
        novelty_conf = self._create_novelty_confidence(confidence_data)

        return LitigationConfidence(
            causal_strength_confidence=causal_conf,
            population_size_confidence=pop_conf,
            defendant_solvency_confidence=solvency_conf,
            preventability_confidence=prevent_conf,
            social_justice_confidence=justice_conf,
            severity_confidence=severity_conf,
            novelty_confidence=novelty_conf
        )

    def _create_population_confidence(self, confidence_data: Dict) -> SourceConfidence:
        """Create confidence for population size estimate"""
        epi_data = confidence_data.get('epidemiology', {})
        exposure_data = confidence_data.get('exposure', {})

        # Need both high-quality for high confidence
        epi_quality = epi_data.get('source_type', 'literature')
        exposure_quality = exposure_data.get('biomarker_available', False)

        if epi_quality == 'api' and exposure_quality:
            conf_score = 0.85
        elif epi_quality in ['api', 'parsed']:
            conf_score = 0.70
        else:
            conf_score = 0.50

        return self._create_default_source_confidence("PopulationSize", conf_score)

    def _create_preventability_confidence(self, confidence_data: Dict) -> SourceConfidence:
        """Create confidence for preventability assessment"""
        regulatory_data = confidence_data.get('regulatory', {})

        if regulatory_data.get('has_direct_data', False):
            conf_score = 0.90
        elif regulatory_data.get('has_scraped_data', False):
            conf_score = 0.70
        else:
            conf_score = 0.50

        return self._create_default_source_confidence("Preventability", conf_score)

    def _create_severity_confidence(self, confidence_data: Dict) -> SourceConfidence:
        """Create confidence for severity/damages estimate"""
        lit_data = confidence_data.get('literature', {})
        has_economic_studies = lit_data.get('has_economic_studies', False)

        if has_economic_studies:
            conf_score = 0.80
        else:
            conf_score = 0.60  # Based on general medical literature

        return self._create_default_source_confidence("Severity", conf_score)

    def _create_novelty_confidence(self, confidence_data: Dict) -> SourceConfidence:
        """Create confidence for novelty/litigation status"""
        litigation_data = confidence_data.get('litigation', {})
        source_type = litigation_data.get('source_type', 'estimate')

        if source_type == 'api':
            conf_score = 0.90
        elif source_type == 'manual':
            conf_score = 0.70
        else:
            conf_score = 0.50

        return self._create_default_source_confidence("Novelty", conf_score)

    def _create_default_source_confidence(self, name: str, score: float) -> SourceConfidence:
        """Create a generic source confidence with specified score"""
        return SourceConfidence(
            source_name=name,
            data_quality=DataQualityMetrics(source=DataSource.EXPERT_OPINION),
            confidence_score=score,
            confidence_level=ConfidenceLevel.HIGH if score >= 0.8 else (
                ConfidenceLevel.MODERATE if score >= 0.6 else ConfidenceLevel.LOW
            )
        )

    def _generate_confidence_interpretation(
        self,
        original_result: LitigationResult,
        lit_confidence: LitigationConfidence,
        adjusted_score: float
    ) -> str:
        """Generate interpretation with confidence context"""
        original_interp = original_result.interpretation
        conf = lit_confidence.composite_confidence

        penalty_pct = (1 - (adjusted_score / float(original_result.composite_score))) * 100

        interp = f"{original_interp}\n\n"
        interp += f"Confidence: {conf:.1%} (weakest: {lit_confidence.weakest_factor})\n"
        interp += f"Confidence penalty: -{penalty_pct:.1f}% (adjusted score: {adjusted_score:.1f})\n\n"

        if lit_confidence.flagged_concerns:
            interp += "Data Quality Concerns:\n"
            for concern in lit_confidence.flagged_concerns:
                interp += f"  - {concern}\n"

        return interp


def generate_composite_report(
    signal_id: str,
    chemical: str,
    disease: str,
    bh_result: ConfidenceAdjustedBradfordHillResult,
    lit_result: ConfidenceAdjustedLitigationResult,
    source_confidences: Dict[str, SourceConfidence]
) -> CompositeConfidenceReport:
    """
    Generate comprehensive confidence report

    Args:
        signal_id: Signal identifier
        chemical: Chemical name
        disease: Disease name
        bh_result: Confidence-adjusted Bradford Hill result
        lit_result: Confidence-adjusted litigation result
        source_confidences: Dictionary of source-level confidences

    Returns:
        Complete confidence report with recommendations
    """
    report = CompositeConfidenceReport(
        signal_id=signal_id,
        chemical=chemical,
        disease=disease,
        source_confidences=source_confidences,
        bradford_hill_confidence=bh_result.confidence_assessment,
        litigation_confidence=lit_result.confidence_assessment,
        original_bradford_hill_score=float(bh_result.original_result.composite_score),
        adjusted_bradford_hill_score=float(bh_result.adjusted_score),
        confidence_penalty_bh=bh_result.confidence_penalty,
        original_litigation_score=float(lit_result.original_result.composite_score),
        adjusted_litigation_score=float(lit_result.adjusted_score),
        confidence_penalty_lit=lit_result.confidence_penalty
    )

    # Calculate overall confidence
    report.calculate_overall_confidence()

    # Generate recommendation
    report.recommendation = report.generate_recommendation()

    return report
