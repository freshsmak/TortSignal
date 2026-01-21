"""Scorer - computes weighted scores for tort candidates."""

import logging
from dataclasses import dataclass
from typing import Any

from src.scoring.category_router import CategoryRouter

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    """Result of scoring a candidate."""

    score_total: float
    confidence: float
    stage: str
    score_components: dict[str, Any]
    why_now: str


class Scorer:
    """
    Computes scores for tort candidates using category-aware weighting.
    
    The scorer takes signals from multiple sources (court filings, FDA,
    literature, SEC) and combines them using category-specific weights.
    """

    # Stage thresholds
    STAGE_THRESHOLDS = {
        "quiet": (0, 20),
        "awareness": (20, 40),
        "investigate": (40, 70),
        "high_conviction": (70, 100),
    }

    def __init__(self):
        self.router = CategoryRouter()

    def score(
        self,
        defendant: str,
        product: str,
        injury: str | None,
        signals: dict[str, Any],
        category_override: str | None = None,
    ) -> ScoreResult:
        """
        Compute the score for a candidate.

        Args:
            defendant: Defendant name
            product: Product name
            injury: Injury description (optional)
            signals: Dict of signal data with keys like:
                - court_filings: {count, breadth_states, breadth_firms, velocity_7d, velocity_28d}
                - faers_trend: {reports_current, reports_baseline, delta_pct, top_reactions}
                - maude_trend: {reports_current, reports_baseline, delta_pct}
                - literature: {paper_count, meta_analysis_count, recent_papers}
                - sec_language: {delta_score, reserve_delta_usd}
            category_override: Optional manual category assignment

        Returns:
            ScoreResult with total score, components, stage, and explanation
        """
        # Determine category
        if category_override:
            category = category_override
        else:
            category = self.router.assign_category(defendant, product, injury)

        weights = self.router.get_weights(category)

        # Compute component scores (each normalized to 0-100)
        components = {}
        explanations = []

        # Court filings component
        if "court_filings" in signals:
            court = signals["court_filings"]
            court_score = self._score_court_filings(court)
            components["court_velocity"] = court_score["velocity"]
            components["court_breadth"] = court_score["breadth"]
            if court_score["velocity"] > 30:
                explanations.append(
                    f"{court.get('count', 0)} filings across "
                    f"{court.get('breadth_states', 0)} states and "
                    f"{court.get('breadth_firms', 0)} firms"
                )

        # FAERS trend (pharma)
        if "faers_trend" in signals and category == "pharma":
            faers = signals["faers_trend"]
            faers_score = self._score_adverse_trend(faers)
            components["faers_trend"] = faers_score
            if faers_score > 30:
                delta = faers.get("delta_pct", 0)
                explanations.append(f"FAERS reports up {delta:.0f}% vs baseline")

        # MAUDE trend (device)
        if "maude_trend" in signals and category == "device":
            maude = signals["maude_trend"]
            maude_score = self._score_adverse_trend(maude)
            components["maude_trend"] = maude_score
            if maude_score > 30:
                delta = maude.get("delta_pct", 0)
                explanations.append(f"MAUDE reports up {delta:.0f}% vs baseline")

        # Literature
        if "literature" in signals:
            lit = signals["literature"]
            lit_score = self._score_literature(lit)
            components["literature"] = lit_score
            meta_count = lit.get("meta_analysis_count", 0)
            if meta_count > 0:
                explanations.append(f"{meta_count} meta-analysis paper(s) found")

        # SEC language
        if "sec_language" in signals:
            sec = signals["sec_language"]
            sec_score = self._score_sec(sec)
            components["sec_language"] = sec_score
            reserve_delta = sec.get("reserve_delta_usd", 0)
            if reserve_delta > 0:
                explanations.append(
                    f"Litigation reserve increased by ${reserve_delta / 1e6:.1f}M"
                )

        # Compute weighted total
        score_total = 0.0
        total_weight = 0.0

        for signal_type, weight in weights.items():
            if signal_type in components:
                score_total += components[signal_type] * weight
                total_weight += weight

        # Normalize if we don't have all signals
        if total_weight > 0 and total_weight < 1.0:
            score_total = score_total / total_weight

        # Cap at 100
        score_total = min(100.0, max(0.0, score_total))

        # Compute confidence based on data completeness
        confidence = self._compute_confidence(signals, weights)

        # Determine stage
        stage = self._determine_stage(score_total)

        # Build "why now" explanation
        if explanations:
            why_now = ". ".join(explanations) + "."
        else:
            why_now = "Emerging signal detected; monitoring for additional evidence."

        return ScoreResult(
            score_total=round(score_total, 2),
            confidence=round(confidence, 2),
            stage=stage,
            score_components={
                "category": category,
                "weights_used": weights,
                "raw_components": components,
            },
            why_now=why_now,
        )

    def _score_court_filings(self, data: dict[str, Any]) -> dict[str, float]:
        """Score court filing signals."""
        count = data.get("count", 0)
        states = data.get("breadth_states", 0)
        firms = data.get("breadth_firms", 0)
        velocity_7d = data.get("velocity_7d", count)

        # Velocity score: logarithmic scaling
        # 1 case = 10, 10 cases = 50, 50+ cases = 80+
        if velocity_7d <= 0:
            velocity_score = 0
        elif velocity_7d < 5:
            velocity_score = velocity_7d * 10
        elif velocity_7d < 20:
            velocity_score = 50 + (velocity_7d - 5) * 2
        else:
            velocity_score = min(100, 80 + (velocity_7d - 20) * 0.5)

        # Breadth score: states + firms
        breadth_score = min(100, (states * 8) + (firms * 5))

        return {
            "velocity": velocity_score,
            "breadth": breadth_score,
        }

    def _score_adverse_trend(self, data: dict[str, Any]) -> float:
        """Score FDA adverse event trend."""
        current = data.get("reports_current", 0)
        baseline = data.get("reports_baseline", 0)
        delta_pct = data.get("delta_pct", 0)

        if current < 10:
            # Too few reports to be meaningful
            return 0

        # Score based on delta percentage
        if delta_pct <= 0:
            return 0
        elif delta_pct < 50:
            return delta_pct * 0.4  # 0-20
        elif delta_pct < 100:
            return 20 + (delta_pct - 50) * 0.6  # 20-50
        elif delta_pct < 200:
            return 50 + (delta_pct - 100) * 0.3  # 50-80
        else:
            return min(100, 80 + (delta_pct - 200) * 0.1)  # 80-100

    def _score_literature(self, data: dict[str, Any]) -> float:
        """Score scientific literature signals."""
        paper_count = data.get("paper_count", 0)
        meta_count = data.get("meta_analysis_count", 0)
        recent_count = data.get("recent_papers", 0)  # last 2 years

        if paper_count == 0:
            return 0

        # Base score from paper count (log scale)
        if paper_count < 5:
            base_score = paper_count * 5
        elif paper_count < 20:
            base_score = 25 + (paper_count - 5) * 2
        else:
            base_score = min(60, 55 + (paper_count - 20) * 0.25)

        # Bonus for meta-analyses (strong evidence)
        meta_bonus = min(30, meta_count * 15)

        # Bonus for recent activity
        recent_bonus = min(10, recent_count * 2)

        return min(100, base_score + meta_bonus + recent_bonus)

    def _score_sec(self, data: dict[str, Any]) -> float:
        """Score SEC filing signals."""
        delta_score = data.get("delta_score", 0)  # 0-1 semantic similarity change
        reserve_delta = data.get("reserve_delta_usd", 0)

        score = 0

        # Language change score
        if delta_score > 0.5:
            score += 30
        elif delta_score > 0.3:
            score += 20
        elif delta_score > 0.1:
            score += 10

        # Reserve increase score
        if reserve_delta > 1e9:  # > $1B
            score += 70
        elif reserve_delta > 500e6:  # > $500M
            score += 50
        elif reserve_delta > 100e6:  # > $100M
            score += 30
        elif reserve_delta > 10e6:  # > $10M
            score += 15

        return min(100, score)

    def _compute_confidence(
        self,
        signals: dict[str, Any],
        weights: dict[str, float],
    ) -> float:
        """
        Compute confidence score based on data completeness.
        
        Higher confidence when we have more signal types with meaningful data.
        """
        present_signals = 0
        total_signals = len(weights)

        # Check which signals have meaningful data
        if "court_filings" in signals:
            if signals["court_filings"].get("count", 0) > 0:
                present_signals += 1

        if "faers_trend" in signals:
            if signals["faers_trend"].get("reports_current", 0) > 0:
                present_signals += 1

        if "maude_trend" in signals:
            if signals["maude_trend"].get("reports_current", 0) > 0:
                present_signals += 1

        if "literature" in signals:
            if signals["literature"].get("paper_count", 0) > 0:
                present_signals += 1

        if "sec_language" in signals:
            if signals["sec_language"].get("delta_score", 0) > 0:
                present_signals += 1

        # Confidence is proportion of available signals
        return present_signals / max(1, min(total_signals, 4))

    def _determine_stage(self, score: float) -> str:
        """Determine the stage label based on score."""
        for stage, (low, high) in self.STAGE_THRESHOLDS.items():
            if low <= score < high:
                return stage
        return "high_conviction"
