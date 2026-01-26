"""
Confidence & Uncertainty Propagation System

Addresses robustness gap #3: No explicit uncertainty or confidence scoring across pipelines

This module provides:
1. Data quality scoring for each integration (CDC WONDER, SEER, NHANES, OpenFDA, PubMed)
2. Confidence propagation through Bradford Hill and litigation scoring
3. Uncertainty-aware score penalization
4. Explicit confidence reporting in final outputs

Design Principles:
- Real data > Parsed data > Literature estimates > Synthetic data
- Confidence penalties are multiplicative (multiple weak sources compound uncertainty)
- Scores are adjusted by confidence_factor (0.0-1.0)
- All confidence metrics are explicitly tracked and reported
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from decimal import Decimal


class ConfidenceLevel(Enum):
    """Confidence levels for data quality"""
    VERY_HIGH = "VERY_HIGH"  # 0.95-1.0: Real-time API, n>=1000, direct measurement
    HIGH = "HIGH"            # 0.80-0.95: Real-time API, n>=100, validated source
    MODERATE = "MODERATE"    # 0.60-0.80: Parsed/CSV data, n>=50, peer-reviewed
    LOW = "LOW"              # 0.40-0.60: Literature estimates, n<50, indirect
    VERY_LOW = "VERY_LOW"    # 0.20-0.40: Synthetic/mock data, expert opinion
    NONE = "NONE"            # 0.0-0.20: No data available, pure speculation


class DataSource(Enum):
    """Data sources with baseline confidence levels"""
    # Epidemiology
    CDC_WONDER_API = ("CDC_WONDER_API", ConfidenceLevel.HIGH, 0.90)
    CDC_WONDER_PARSED = ("CDC_WONDER_PARSED", ConfidenceLevel.MODERATE, 0.70)
    CDC_WONDER_LITERATURE = ("CDC_WONDER_LITERATURE", ConfidenceLevel.LOW, 0.50)

    SEER_API = ("SEER_API", ConfidenceLevel.HIGH, 0.90)
    SEER_CSV = ("SEER_CSV", ConfidenceLevel.MODERATE, 0.75)
    SEER_LITERATURE = ("SEER_LITERATURE", ConfidenceLevel.LOW, 0.50)

    # Exposure
    NHANES_DIRECT = ("NHANES_DIRECT", ConfidenceLevel.HIGH, 0.85)
    NHANES_INDIRECT = ("NHANES_INDIRECT", ConfidenceLevel.MODERATE, 0.65)
    NHANES_LITERATURE = ("NHANES_LITERATURE", ConfidenceLevel.LOW, 0.45)

    # Adverse Events
    OPENFDA_HIGH_VOLUME = ("OPENFDA_HIGH_VOLUME", ConfidenceLevel.HIGH, 0.85)  # >1000 reports
    OPENFDA_MEDIUM_VOLUME = ("OPENFDA_MEDIUM_VOLUME", ConfidenceLevel.MODERATE, 0.70)  # 100-1000
    OPENFDA_LOW_VOLUME = ("OPENFDA_LOW_VOLUME", ConfidenceLevel.LOW, 0.50)  # <100

    # Literature
    PUBMED_SYSTEMATIC_REVIEW = ("PUBMED_SYSTEMATIC_REVIEW", ConfidenceLevel.HIGH, 0.85)
    PUBMED_RCT = ("PUBMED_RCT", ConfidenceLevel.HIGH, 0.80)
    PUBMED_COHORT = ("PUBMED_COHORT", ConfidenceLevel.MODERATE, 0.70)
    PUBMED_CASE_CONTROL = ("PUBMED_CASE_CONTROL", ConfidenceLevel.MODERATE, 0.65)
    PUBMED_MECHANISTIC = ("PUBMED_MECHANISTIC", ConfidenceLevel.MODERATE, 0.60)
    PUBMED_CASE_REPORT = ("PUBMED_CASE_REPORT", ConfidenceLevel.LOW, 0.45)

    # Regulatory
    EU_ECHA_DIRECT = ("EU_ECHA_DIRECT", ConfidenceLevel.HIGH, 0.90)
    EU_ECHA_SCRAPED = ("EU_ECHA_SCRAPED", ConfidenceLevel.MODERATE, 0.70)
    EU_ECHA_MOCK = ("EU_ECHA_MOCK", ConfidenceLevel.VERY_LOW, 0.30)

    # Litigation
    PACER_API = ("PACER_API", ConfidenceLevel.HIGH, 0.90)
    PACER_MANUAL = ("PACER_MANUAL", ConfidenceLevel.MODERATE, 0.70)
    PACER_ESTIMATE = ("PACER_ESTIMATE", ConfidenceLevel.LOW, 0.50)

    # Fallbacks
    MOCK_DATA = ("MOCK_DATA", ConfidenceLevel.VERY_LOW, 0.25)
    EXPERT_OPINION = ("EXPERT_OPINION", ConfidenceLevel.LOW, 0.40)
    SYNTHETIC = ("SYNTHETIC", ConfidenceLevel.VERY_LOW, 0.20)

    def __init__(self, source_name: str, level: ConfidenceLevel, base_score: float):
        self.source_name = source_name
        self.level = level
        self.base_score = base_score


@dataclass
class DataQualityMetrics:
    """Metrics for assessing data quality"""
    source: DataSource
    sample_size: Optional[int] = None
    time_span_years: Optional[int] = None
    measurement_type: str = "unknown"  # 'direct', 'indirect', 'estimated', 'synthetic'
    peer_reviewed: bool = False
    replication_count: int = 1  # Number of independent sources confirming
    recency_years: Optional[int] = None  # Years since data collection

    def calculate_confidence_score(self) -> float:
        """
        Calculate overall confidence score (0.0-1.0)

        Starts with base score from DataSource, then applies adjustments:
        - Sample size: +0.0 to +0.15
        - Time span: +0.0 to +0.10
        - Peer review: +0.05
        - Replication: +0.0 to +0.10
        - Recency: -0.0 to -0.20 (penalty for old data)
        """
        score = self.source.base_score

        # Sample size adjustment
        if self.sample_size is not None:
            if self.sample_size >= 10000:
                score += 0.15
            elif self.sample_size >= 1000:
                score += 0.10
            elif self.sample_size >= 100:
                score += 0.05
            elif self.sample_size < 30:
                score -= 0.10

        # Time span adjustment (longer = better for trend analysis)
        if self.time_span_years is not None:
            if self.time_span_years >= 20:
                score += 0.10
            elif self.time_span_years >= 10:
                score += 0.05
            elif self.time_span_years < 3:
                score -= 0.05

        # Peer review bonus
        if self.peer_reviewed:
            score += 0.05

        # Replication adjustment
        if self.replication_count >= 5:
            score += 0.10
        elif self.replication_count >= 3:
            score += 0.05
        elif self.replication_count >= 2:
            score += 0.02

        # Recency penalty (data freshness matters)
        if self.recency_years is not None:
            if self.recency_years <= 2:
                score += 0.05  # Very recent
            elif self.recency_years <= 5:
                pass  # No adjustment
            elif self.recency_years <= 10:
                score -= 0.05
            else:
                score -= 0.10

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, score))

    def get_confidence_level(self) -> ConfidenceLevel:
        """Get categorical confidence level"""
        score = self.calculate_confidence_score()

        if score >= 0.95:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.80:
            return ConfidenceLevel.HIGH
        elif score >= 0.60:
            return ConfidenceLevel.MODERATE
        elif score >= 0.40:
            return ConfidenceLevel.LOW
        elif score >= 0.20:
            return ConfidenceLevel.VERY_LOW
        else:
            return ConfidenceLevel.NONE


@dataclass
class SourceConfidence:
    """Confidence assessment for a single data source"""
    source_name: str
    data_quality: DataQualityMetrics
    confidence_score: float
    confidence_level: ConfidenceLevel
    notes: str = ""

    @classmethod
    def from_metrics(cls, source_name: str, metrics: DataQualityMetrics, notes: str = ""):
        """Create SourceConfidence from DataQualityMetrics"""
        score = metrics.calculate_confidence_score()
        level = metrics.get_confidence_level()

        return cls(
            source_name=source_name,
            data_quality=metrics,
            confidence_score=score,
            confidence_level=level,
            notes=notes
        )


@dataclass
class BradfordHillConfidence:
    """Confidence assessment for Bradford Hill criteria scoring"""

    # Per-criterion confidence
    strength_confidence: SourceConfidence
    consistency_confidence: SourceConfidence
    specificity_confidence: SourceConfidence
    temporality_confidence: SourceConfidence
    biological_gradient_confidence: SourceConfidence
    plausibility_confidence: SourceConfidence
    coherence_confidence: SourceConfidence
    experiment_confidence: SourceConfidence
    analogy_confidence: SourceConfidence

    # Overall metrics
    composite_confidence: float = 0.0
    weakest_criterion: str = ""
    weakest_confidence: float = 1.0
    flagged_concerns: List[str] = field(default_factory=list)

    def calculate_composite_confidence(self) -> float:
        """
        Calculate overall Bradford Hill confidence

        Uses weighted geometric mean to penalize weak links
        (one very weak source drags down overall confidence more than arithmetic mean)
        """
        # Bradford Hill weights (from bradford_hill.py)
        weights = {
            'strength': 0.15,
            'consistency': 0.12,
            'specificity': 0.08,
            'temporality': 0.15,
            'biological_gradient': 0.10,
            'plausibility': 0.15,
            'coherence': 0.10,
            'experiment': 0.10,
            'analogy': 0.05
        }

        criteria_scores = {
            'strength': self.strength_confidence.confidence_score,
            'consistency': self.consistency_confidence.confidence_score,
            'specificity': self.specificity_confidence.confidence_score,
            'temporality': self.temporality_confidence.confidence_score,
            'biological_gradient': self.biological_gradient_confidence.confidence_score,
            'plausibility': self.plausibility_confidence.confidence_score,
            'coherence': self.coherence_confidence.confidence_score,
            'experiment': self.experiment_confidence.confidence_score,
            'analogy': self.analogy_confidence.confidence_score
        }

        # Weighted geometric mean
        product = 1.0
        for criterion, weight in weights.items():
            score = criteria_scores[criterion]
            product *= score ** weight

        self.composite_confidence = product

        # Identify weakest criterion
        weakest = min(criteria_scores.items(), key=lambda x: x[1])
        self.weakest_criterion = weakest[0]
        self.weakest_confidence = weakest[1]

        # Flag concerns (confidence < 0.60)
        self.flagged_concerns = []
        for criterion, score in criteria_scores.items():
            if score < 0.60:
                level = self._score_to_level(score)
                self.flagged_concerns.append(
                    f"{criterion.upper()}: {level} confidence ({score:.2f}) - "
                    f"{self._get_concern_reason(criterion)}"
                )

        return self.composite_confidence

    def _score_to_level(self, score: float) -> str:
        """Convert confidence score to categorical level"""
        if score >= 0.80:
            return "HIGH"
        elif score >= 0.60:
            return "MODERATE"
        elif score >= 0.40:
            return "LOW"
        else:
            return "VERY LOW"

    def _get_concern_reason(self, criterion: str) -> str:
        """Get reason for low confidence in criterion"""
        reasons = {
            'strength': "Effect size based on limited or low-quality studies",
            'consistency': "Few replication studies or conflicting results",
            'specificity': "Insufficient data to assess disease specificity",
            'temporality': "Exposure timeline based on estimates, not direct data",
            'biological_gradient': "Dose-response relationship not well-established",
            'plausibility': "Limited mechanistic evidence or synthetic data",
            'coherence': "Few comprehensive reviews or meta-analyses",
            'experiment': "No intervention studies or only animal models",
            'analogy': "Limited analogous exposures for comparison"
        }
        return reasons.get(criterion, "Data quality concerns")

    def apply_confidence_penalty(self, original_score: float) -> float:
        """
        Apply confidence penalty to Bradford Hill composite score

        Penalty Formula:
        adjusted_score = original_score * confidence_factor

        where confidence_factor = composite_confidence ** 0.5
        (square root to moderate the penalty - we don't want to completely zero out
        scores based on data quality alone, just appropriately discount them)
        """
        confidence_factor = self.composite_confidence ** 0.5
        adjusted_score = original_score * confidence_factor

        return adjusted_score


@dataclass
class LitigationConfidence:
    """Confidence assessment for litigation viability scoring"""

    # Per-factor confidence
    causal_strength_confidence: SourceConfidence
    population_size_confidence: SourceConfidence
    defendant_solvency_confidence: SourceConfidence
    preventability_confidence: SourceConfidence
    social_justice_confidence: SourceConfidence
    severity_confidence: SourceConfidence
    novelty_confidence: SourceConfidence

    # Overall metrics
    composite_confidence: float = 0.0
    weakest_factor: str = ""
    weakest_confidence: float = 1.0
    flagged_concerns: List[str] = field(default_factory=list)

    def calculate_composite_confidence(self) -> float:
        """Calculate overall litigation viability confidence"""
        # Litigation weights (from litigation.py)
        weights = {
            'causal_strength': 0.20,
            'population_size': 0.15,
            'defendant_solvency': 0.20,
            'preventability': 0.15,
            'social_justice': 0.10,
            'severity': 0.15,
            'novelty': 0.05
        }

        factors_scores = {
            'causal_strength': self.causal_strength_confidence.confidence_score,
            'population_size': self.population_size_confidence.confidence_score,
            'defendant_solvency': self.defendant_solvency_confidence.confidence_score,
            'preventability': self.preventability_confidence.confidence_score,
            'social_justice': self.social_justice_confidence.confidence_score,
            'severity': self.severity_confidence.confidence_score,
            'novelty': self.novelty_confidence.confidence_score
        }

        # Weighted geometric mean
        product = 1.0
        for factor, weight in weights.items():
            score = factors_scores[factor]
            product *= score ** weight

        self.composite_confidence = product

        # Identify weakest factor
        weakest = min(factors_scores.items(), key=lambda x: x[1])
        self.weakest_factor = weakest[0]
        self.weakest_confidence = weakest[1]

        # Flag concerns
        self.flagged_concerns = []
        for factor, score in factors_scores.items():
            if score < 0.60:
                level = self._score_to_level(score)
                self.flagged_concerns.append(
                    f"{factor.upper()}: {level} confidence ({score:.2f})"
                )

        return self.composite_confidence

    def _score_to_level(self, score: float) -> str:
        """Convert confidence score to categorical level"""
        if score >= 0.80:
            return "HIGH"
        elif score >= 0.60:
            return "MODERATE"
        elif score >= 0.40:
            return "LOW"
        else:
            return "VERY LOW"

    def apply_confidence_penalty(self, original_score: float) -> float:
        """Apply confidence penalty to litigation viability score"""
        confidence_factor = self.composite_confidence ** 0.5
        adjusted_score = original_score * confidence_factor

        return adjusted_score


@dataclass
class CompositeConfidenceReport:
    """Comprehensive confidence report for a signal"""
    signal_id: str
    chemical: str
    disease: str

    # Source-level confidence
    source_confidences: Dict[str, SourceConfidence]

    # Scoring-level confidence
    bradford_hill_confidence: Optional[BradfordHillConfidence] = None
    litigation_confidence: Optional[LitigationConfidence] = None

    # Adjusted scores
    original_bradford_hill_score: Optional[float] = None
    adjusted_bradford_hill_score: Optional[float] = None
    confidence_penalty_bh: Optional[float] = None

    original_litigation_score: Optional[float] = None
    adjusted_litigation_score: Optional[float] = None
    confidence_penalty_lit: Optional[float] = None

    # Overall assessment
    overall_confidence: float = 0.0
    overall_confidence_level: ConfidenceLevel = ConfidenceLevel.MODERATE
    recommendation: str = ""

    def calculate_overall_confidence(self) -> Tuple[float, ConfidenceLevel]:
        """
        Calculate overall signal confidence

        Combines Bradford Hill and litigation confidence
        """
        if self.bradford_hill_confidence and self.litigation_confidence:
            # Weight BH more heavily (70%) as it's the scientific foundation
            bh_conf = self.bradford_hill_confidence.composite_confidence
            lit_conf = self.litigation_confidence.composite_confidence

            overall = (0.70 * bh_conf) + (0.30 * lit_conf)
        elif self.bradford_hill_confidence:
            overall = self.bradford_hill_confidence.composite_confidence
        elif self.litigation_confidence:
            overall = self.litigation_confidence.composite_confidence
        else:
            # Fall back to average of source confidences
            if self.source_confidences:
                overall = sum(s.confidence_score for s in self.source_confidences.values()) / len(self.source_confidences)
            else:
                overall = 0.50

        self.overall_confidence = overall

        # Assign level
        if overall >= 0.80:
            self.overall_confidence_level = ConfidenceLevel.HIGH
        elif overall >= 0.60:
            self.overall_confidence_level = ConfidenceLevel.MODERATE
        elif overall >= 0.40:
            self.overall_confidence_level = ConfidenceLevel.LOW
        else:
            self.overall_confidence_level = ConfidenceLevel.VERY_LOW

        return overall, self.overall_confidence_level

    def generate_recommendation(self) -> str:
        """Generate confidence-aware recommendation"""
        if not self.adjusted_bradford_hill_score or not self.adjusted_litigation_score:
            return "Insufficient data for recommendation"

        bh = self.adjusted_bradford_hill_score
        lit = self.adjusted_litigation_score
        conf = self.overall_confidence

        # Confidence-gated recommendations
        if conf >= 0.80:
            # High confidence - normal thresholds
            if bh >= 95 and lit >= 100:
                return "FILE IMMEDIATELY (high confidence)"
            elif bh >= 85 and lit >= 90:
                return "VALIDATE & PURSUE (high confidence)"
            elif bh >= 70 and lit >= 80:
                return "VALIDATE CAREFULLY (high confidence)"
            elif bh >= 70 or lit >= 80:
                return "MONITOR CLOSELY (high confidence)"
            else:
                return "REJECT - insufficient merit (high confidence)"

        elif conf >= 0.60:
            # Moderate confidence - raise thresholds slightly
            if bh >= 95 and lit >= 100:
                return "VALIDATE & PURSUE (moderate confidence - verify data quality)"
            elif bh >= 85 and lit >= 90:
                return "VALIDATE CAREFULLY (moderate confidence - strengthen weak sources)"
            elif bh >= 70 and lit >= 80:
                return "MONITOR CLOSELY (moderate confidence - improve data quality before pursuing)"
            else:
                return "REJECT - insufficient merit (moderate confidence)"

        else:
            # Low confidence - significantly raise thresholds
            if bh >= 95 and lit >= 100:
                return "VALIDATE CAREFULLY (LOW CONFIDENCE - data quality concerns prevent immediate filing)"
            elif bh >= 85:
                return "IMPROVE DATA QUALITY (low confidence - strengthen evidence before validation)"
            else:
                return "REJECT - data quality insufficient for reliable assessment"

    def to_dict(self) -> Dict:
        """Export as dictionary for JSON serialization"""
        return {
            'signal_id': self.signal_id,
            'chemical': self.chemical,
            'disease': self.disease,
            'overall_confidence': round(self.overall_confidence, 3),
            'overall_confidence_level': self.overall_confidence_level.value,
            'bradford_hill': {
                'original_score': self.original_bradford_hill_score,
                'adjusted_score': self.adjusted_bradford_hill_score,
                'confidence_penalty': self.confidence_penalty_bh,
                'composite_confidence': self.bradford_hill_confidence.composite_confidence if self.bradford_hill_confidence else None,
                'flagged_concerns': self.bradford_hill_confidence.flagged_concerns if self.bradford_hill_confidence else []
            },
            'litigation': {
                'original_score': self.original_litigation_score,
                'adjusted_score': self.adjusted_litigation_score,
                'confidence_penalty': self.confidence_penalty_lit,
                'composite_confidence': self.litigation_confidence.composite_confidence if self.litigation_confidence else None,
                'flagged_concerns': self.litigation_confidence.flagged_concerns if self.litigation_confidence else []
            },
            'recommendation': self.recommendation,
            'source_confidences': {
                name: {
                    'score': conf.confidence_score,
                    'level': conf.confidence_level.value,
                    'notes': conf.notes
                }
                for name, conf in self.source_confidences.items()
            }
        }


# Convenience functions for creating common confidence assessments

def create_cdc_wonder_confidence(
    data_source_type: str,  # 'api', 'parsed', 'literature'
    years_of_data: int,
    sample_size: Optional[int] = None
) -> SourceConfidence:
    """Create confidence assessment for CDC WONDER data"""
    source_map = {
        'api': DataSource.CDC_WONDER_API,
        'parsed': DataSource.CDC_WONDER_PARSED,
        'literature': DataSource.CDC_WONDER_LITERATURE
    }

    source = source_map.get(data_source_type, DataSource.CDC_WONDER_LITERATURE)

    metrics = DataQualityMetrics(
        source=source,
        sample_size=sample_size,
        time_span_years=years_of_data,
        measurement_type='direct' if data_source_type == 'api' else 'indirect',
        peer_reviewed=False,  # CDC data, not peer-reviewed publication
        replication_count=1,
        recency_years=1 if data_source_type == 'api' else 5
    )

    notes = f"CDC WONDER {data_source_type} data, {years_of_data} years"

    return SourceConfidence.from_metrics("CDC_WONDER", metrics, notes)


def create_seer_confidence(
    data_source_type: str,  # 'api', 'csv', 'literature'
    years_of_data: int,
    sample_size: Optional[int] = None
) -> SourceConfidence:
    """Create confidence assessment for SEER data"""
    source_map = {
        'api': DataSource.SEER_API,
        'csv': DataSource.SEER_CSV,
        'literature': DataSource.SEER_LITERATURE
    }

    source = source_map.get(data_source_type, DataSource.SEER_LITERATURE)

    metrics = DataQualityMetrics(
        source=source,
        sample_size=sample_size,
        time_span_years=years_of_data,
        measurement_type='direct' if data_source_type != 'literature' else 'estimated',
        peer_reviewed=False,
        replication_count=1,
        recency_years=2 if data_source_type == 'api' else 5
    )

    notes = f"SEER {data_source_type} data, {years_of_data} years"

    return SourceConfidence.from_metrics("SEER", metrics, notes)


def create_nhanes_confidence(
    biomarker_available: bool,
    sample_size: int,
    cycles: int = 1
) -> SourceConfidence:
    """Create confidence assessment for NHANES exposure data"""
    if biomarker_available:
        if sample_size >= 100:
            source = DataSource.NHANES_DIRECT
        else:
            source = DataSource.NHANES_INDIRECT
    else:
        source = DataSource.NHANES_LITERATURE

    metrics = DataQualityMetrics(
        source=source,
        sample_size=sample_size if biomarker_available else None,
        time_span_years=cycles * 2,  # Each NHANES cycle is ~2 years
        measurement_type='direct' if biomarker_available else 'estimated',
        peer_reviewed=False,
        replication_count=cycles,
        recency_years=3
    )

    notes = f"NHANES {'biomarker' if biomarker_available else 'literature'}, n={sample_size}, {cycles} cycles"

    return SourceConfidence.from_metrics("NHANES", metrics, notes)


def create_openfda_confidence(report_count: int) -> SourceConfidence:
    """Create confidence assessment for OpenFDA adverse event data"""
    if report_count >= 1000:
        source = DataSource.OPENFDA_HIGH_VOLUME
    elif report_count >= 100:
        source = DataSource.OPENFDA_MEDIUM_VOLUME
    else:
        source = DataSource.OPENFDA_LOW_VOLUME

    metrics = DataQualityMetrics(
        source=source,
        sample_size=report_count,
        time_span_years=10,  # FAERS data typically 10+ years
        measurement_type='direct',
        peer_reviewed=False,
        replication_count=1,
        recency_years=0  # Real-time API
    )

    notes = f"OpenFDA FAERS, {report_count} reports"

    return SourceConfidence.from_metrics("OpenFDA", metrics, notes)


def create_pubmed_confidence(
    paper_count: int,
    study_types: List[str],  # ['rct', 'cohort', 'case_control', 'mechanistic']
    replication_count: int = 1
) -> SourceConfidence:
    """Create confidence assessment for PubMed literature evidence"""
    # Prioritize highest-quality study type
    if 'systematic_review' in study_types:
        source = DataSource.PUBMED_SYSTEMATIC_REVIEW
    elif 'rct' in study_types:
        source = DataSource.PUBMED_RCT
    elif 'cohort' in study_types:
        source = DataSource.PUBMED_COHORT
    elif 'case_control' in study_types:
        source = DataSource.PUBMED_CASE_CONTROL
    elif 'mechanistic' in study_types:
        source = DataSource.PUBMED_MECHANISTIC
    else:
        source = DataSource.PUBMED_CASE_REPORT

    metrics = DataQualityMetrics(
        source=source,
        sample_size=None,  # Varies by study
        time_span_years=None,
        measurement_type='direct' if 'mechanistic' not in study_types else 'indirect',
        peer_reviewed=True,
        replication_count=replication_count,
        recency_years=5  # Assume median 5 years
    )

    notes = f"PubMed: {paper_count} papers, types: {', '.join(study_types)}"

    return SourceConfidence.from_metrics("PubMed", metrics, notes)
