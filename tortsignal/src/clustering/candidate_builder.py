"""Candidate builder - clusters cases into emerging tort candidates."""

import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from src.models import CaseRecord, ExtractedEntities, CandidateCluster

logger = logging.getLogger(__name__)


def normalize_text(s: str) -> str:
    """Normalize text for clustering (lowercase, remove special chars)."""
    s = (s or "").strip().lower()
    s = re.sub(r"[\W_]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def make_candidate_key(defendant: str, product: str) -> str:
    """
    Create a candidate key from defendant and product.
    
    Uses pair-key (defendant, product) rather than triple-key with injury
    because injury terminology is noisy early in discovery.
    """
    return f"{normalize_text(defendant)}|{normalize_text(product)}"


class CandidateBuilder:
    """Builds candidate clusters from case records with extracted entities."""

    def __init__(self):
        self.clusters: dict[str, dict[str, Any]] = {}

    def add_case(
        self,
        case: CaseRecord,
        entities: ExtractedEntities,
    ) -> str | None:
        """
        Add a case to the appropriate cluster.

        Args:
            case: The court case record
            entities: Extracted entities from the case

        Returns:
            The candidate key if added, None if filtered out
        """
        if not entities.is_product_liability:
            logger.debug(f"Skipping non-PL case: {case.source_uid}")
            return None

        defendant = entities.defendant or "unknown"
        product = entities.product or "unknown"
        injury = entities.injury or "unknown"

        # Skip if both defendant and product are unknown
        if defendant == "unknown" and product == "unknown":
            logger.debug(f"Skipping case with unknown defendant and product: {case.source_uid}")
            return None

        key = make_candidate_key(defendant, product)

        if key not in self.clusters:
            self.clusters[key] = {
                "defendant": defendant,
                "product": product,
                "count": 0,
                "states": set(),
                "firms": set(),
                "injury_counts": defaultdict(int),
                "members": [],
                "first_seen": None,
                "last_seen": None,
            }

        cluster = self.clusters[key]
        cluster["count"] += 1

        if case.state:
            cluster["states"].add(case.state)
        if case.plaintiff_firm:
            cluster["firms"].add(case.plaintiff_firm)

        cluster["injury_counts"][injury] += 1

        # Track dates
        filed_dt = self._parse_date(case.filed_date)
        if filed_dt:
            if cluster["first_seen"] is None or filed_dt < cluster["first_seen"]:
                cluster["first_seen"] = filed_dt
            if cluster["last_seen"] is None or filed_dt > cluster["last_seen"]:
                cluster["last_seen"] = filed_dt

        # Store member data (limit to prevent memory bloat)
        if len(cluster["members"]) < 100:
            cluster["members"].append({
                "case_uid": case.source_uid,
                "title": case.title,
                "filed_date": case.filed_date,
                "jurisdiction": case.jurisdiction,
                "state": case.state,
                "plaintiff_firm": case.plaintiff_firm,
                "url": case.url,
                "extract": {
                    "defendant": defendant,
                    "product": product,
                    "injury": injury,
                    "confidence": entities.confidence,
                },
            })

        return key

    def build_candidates(self) -> list[CandidateCluster]:
        """
        Build final candidate clusters with scores.

        Returns:
            List of CandidateCluster objects, sorted by score
        """
        candidates = []

        for key, cluster in self.clusters.items():
            # Compute breadth metrics
            states = sorted(cluster["states"])
            firms = sorted(cluster["firms"])
            breadth_states = len(states)
            breadth_firms = len(firms)

            # Determine injury label
            injury_counts = dict(cluster["injury_counts"])
            injury_label = self._get_injury_label(injury_counts, cluster["count"])

            # Compute MVP score
            # score = count * (1 + breadth_states) * (1 + breadth_firms)
            score = float(cluster["count"]) * (1.0 + breadth_states) * (1.0 + breadth_firms)

            # Build score components
            score_components = {
                "filings": {
                    "count": cluster["count"],
                    "breadth_states": breadth_states,
                    "breadth_firms": breadth_firms,
                    "injury_distribution": injury_counts,
                }
            }

            # Build "why now" narrative
            why_now = (
                f"{cluster['count']} product-liability filings detected "
                f"across {breadth_states} state(s) and {breadth_firms} plaintiff firm(s)."
            )

            candidates.append(CandidateCluster(
                defendant=cluster["defendant"],
                product=cluster["product"],
                injury_label=injury_label,
                injury_counts=injury_counts,
                count=cluster["count"],
                states=states,
                firms=firms[:50],  # Limit for storage
                breadth_states=breadth_states,
                breadth_firms=breadth_firms,
                score_total=score,
                score_components=score_components,
                why_now=why_now,
                first_seen=cluster["first_seen"],
                last_seen=cluster["last_seen"],
                members=cluster["members"],
            ))

        # Sort by score descending
        candidates.sort(key=lambda c: c.score_total, reverse=True)
        return candidates

    def _get_injury_label(self, injury_counts: dict[str, int], total: int) -> str:
        """
        Determine the injury label for a cluster.
        
        Returns the dominant injury if it represents >60% of cases,
        otherwise returns "mixed".
        """
        if not injury_counts:
            return "unknown"

        top_injury, top_count = max(injury_counts.items(), key=lambda x: x[1])

        if top_injury == "unknown":
            # Find next best
            non_unknown = {k: v for k, v in injury_counts.items() if k != "unknown"}
            if non_unknown:
                top_injury, top_count = max(non_unknown.items(), key=lambda x: x[1])
            else:
                return "unknown"

        if top_count / max(1, total) >= 0.6:
            return top_injury
        return "mixed"

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse a YYYY-MM-DD date string to datetime."""
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            return dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None

    def clear(self):
        """Clear all clusters."""
        self.clusters = {}
