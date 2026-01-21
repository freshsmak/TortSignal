"""FDA FAERS (drug adverse events) connector with broad discovery capabilities."""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Generator

import requests

from src.connectors.base import BaseConnector
from src.models import FAERSReport, AdverseTrend, ReactionTrend, DrugReactionSignal

logger = logging.getLogger(__name__)

FAERS_BASE_URL = "https://api.fda.gov/drug/event.json"


class FAERSConnector(BaseConnector):
    """
    Connector for FDA FAERS adverse event data via OpenFDA API.
    
    Supports multiple discovery paradigms:
    1. Product-first: "Is drug X showing elevated adverse events?"
    2. Reaction-first: "What adverse reactions are spiking across ALL drugs?"
    3. Pair discovery: "What drug+reaction combinations are anomalous?"
    4. Manufacturer-level: "Is a company having systemic quality issues?"
    
    The reaction-first approach catches signals that product-first misses,
    especially for novel injury patterns or low-volume specialty drugs.
    """

    def __init__(self, api_key: str | None = None, reference_date: datetime | None = None):
        # Load API key from environment if not provided
        self.api_key = api_key or os.getenv("OPENFDA_API_KEY")
        self.reference_date = reference_date or datetime.now(timezone.utc)
        self.session = requests.Session()
        if self.api_key:
            self.session.params = {"api_key": self.api_key}
            logger.debug("Using OpenFDA API key (rate limit: 120k/day)")
        else:
            logger.debug("No API key - using free tier (rate limit: 1k/day)")

    @property
    def source_name(self) -> str:
        return "faers"

    def health_check(self) -> bool:
        try:
            response = self.session.get(FAERS_BASE_URL, params={"limit": 1}, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"FAERS health check failed: {e}")
            return False

    # =========================================================================
    # CORE FETCH METHODS
    # =========================================================================

    def fetch(
        self,
        drug_name: str | None = None,
        reaction: str | None = None,
        days: int = 180,
        limit: int = 100,
        serious_only: bool = False,
    ) -> Generator[FAERSReport, None, None]:
        """Fetch FAERS reports with flexible filtering."""
        end_date = self.reference_date
        start_date = end_date - timedelta(days=days)
        date_range = f"[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]"

        search_parts = [f"receivedate:{date_range}"]
        if drug_name:
            search_parts.append(
                f'(patient.drug.openfda.brand_name:"{drug_name}"+OR+'
                f'patient.drug.openfda.generic_name:"{drug_name}")'
            )
        if reaction:
            search_parts.append(f'patient.reaction.reactionmeddrapt:"{reaction}"')
        if serious_only:
            search_parts.append("serious:1")

        search = "+AND+".join(search_parts)

        skip = 0
        fetched = 0
        while fetched < limit:
            batch_limit = min(100, limit - fetched)
            try:
                response = self.session.get(
                    FAERS_BASE_URL,
                    params={"search": search, "limit": batch_limit, "skip": skip},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    break
                raise

            results = data.get("results", [])
            if not results:
                break

            for item in results:
                yield self._parse_report(item)
                fetched += 1

            skip += len(results)
            if len(results) < batch_limit:
                break

    def _parse_report(self, raw: dict[str, Any]) -> FAERSReport:
        patient = raw.get("patient", {})
        return FAERSReport(
            primaryid=str(raw.get("safetyreportid", "")),
            caseid=str(raw.get("safetyreportid", "")),
            receivedate=raw.get("receivedate", ""),
            event_dt=raw.get("occurcountry"),
            drugs=patient.get("drug", []),
            reactions=patient.get("reaction", []),
            outcomes=raw.get("serious", []) if isinstance(raw.get("serious"), list) else [],
            patient_sex=patient.get("patientsex"),
            patient_age=self._parse_age(patient),
            reporter_country=raw.get("occurcountry"),
            narrative=None,
        )

    def _parse_age(self, patient: dict) -> float | None:
        age = patient.get("patientonsetage")
        unit = patient.get("patientonsetageunit")
        if age is None:
            return None
        try:
            age = float(age)
            if unit == "801": return age
            elif unit == "802": return age / 12
            elif unit == "803": return age / 52
            elif unit == "804": return age / 365
            elif unit == "805": return age / 8760
            return age
        except (ValueError, TypeError):
            return None

    # =========================================================================
    # PRODUCT-FIRST DISCOVERY
    # =========================================================================

    def get_trending_drugs(
        self, days: int = 30, top_n: int = 200, serious_only: bool = False
    ) -> list[dict[str, Any]]:
        """Get top drugs by adverse event count."""
        end_date = self.reference_date
        start_date = end_date - timedelta(days=days)
        date_range = f"[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]"

        search = f"receivedate:{date_range}"
        if serious_only:
            search += "+AND+serious:1"

        try:
            response = self.session.get(
                FAERS_BASE_URL,
                params={
                    "search": search,
                    "count": "patient.drug.openfda.brand_name.exact",
                    "limit": min(top_n, 1000),
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return [{"drug_name": item["term"], "count": item["count"]} for item in data.get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get trending drugs: {e}")
            return []

    def get_drug_trend(
        self, drug_name: str, current_days: int = 30, baseline_days: int = 365
    ) -> AdverseTrend | None:
        """Calculate adverse event trend for a specific drug."""
        now = self.reference_date

        current_start = now - timedelta(days=current_days)
        current_count = self._count_reports_for_drug(drug_name, current_start, now)

        baseline_end = now - timedelta(days=baseline_days)
        baseline_start = baseline_end - timedelta(days=current_days)
        baseline_count = self._count_reports_for_drug(drug_name, baseline_start, baseline_end)

        if baseline_count == 0:
            delta_pct = float("inf") if current_count > 0 else 0.0
        else:
            delta_pct = ((current_count - baseline_count) / baseline_count) * 100

        top_reactions = self._get_top_reactions_for_drug(drug_name, current_start, now)

        return AdverseTrend(
            source="faers",
            product_name=drug_name,
            window_days=current_days,
            reports_current=current_count,
            reports_baseline=baseline_count,
            delta_pct=delta_pct,
            top_reactions=top_reactions,
        )

    def _count_reports_for_drug(self, drug_name: str, start: datetime, end: datetime) -> int:
        date_range = f"[{start.strftime('%Y%m%d')}+TO+{end.strftime('%Y%m%d')}]"
        search = (
            f"receivedate:{date_range}+AND+"
            f'(patient.drug.openfda.brand_name:"{drug_name}"+OR+'
            f'patient.drug.openfda.generic_name:"{drug_name}")'
        )
        try:
            response = self.session.get(FAERS_BASE_URL, params={"search": search, "limit": 1}, timeout=30)
            if response.status_code == 404:
                return 0
            response.raise_for_status()
            return response.json().get("meta", {}).get("results", {}).get("total", 0)
        except Exception as e:
            logger.error(f"Failed to count reports for {drug_name}: {e}")
            return 0

    def _get_top_reactions_for_drug(self, drug_name: str, start: datetime, end: datetime, top_n: int = 10) -> list[str]:
        date_range = f"[{start.strftime('%Y%m%d')}+TO+{end.strftime('%Y%m%d')}]"
        search = (
            f"receivedate:{date_range}+AND+"
            f'(patient.drug.openfda.brand_name:"{drug_name}"+OR+'
            f'patient.drug.openfda.generic_name:"{drug_name}")'
        )
        try:
            response = self.session.get(
                FAERS_BASE_URL,
                params={"search": search, "count": "patient.reaction.reactionmeddrapt.exact", "limit": top_n},
                timeout=30,
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return [item["term"] for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get reactions for {drug_name}: {e}")
            return []

    # =========================================================================
    # REACTION-FIRST DISCOVERY (Key innovation - catches what product-first misses)
    # =========================================================================

    def get_trending_reactions(
        self, days: int = 30, top_n: int = 200, serious_only: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get top adverse reactions by count across ALL drugs.

        This is the key to reaction-first discovery: instead of asking
        "is Drug X bad?", we ask "what injuries are happening?" and then
        trace back to the drugs causing them.
        """
        end_date = self.reference_date
        start_date = end_date - timedelta(days=days)
        date_range = f"[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]"

        search = f"receivedate:{date_range}"
        if serious_only:
            search += "+AND+serious:1"

        try:
            response = self.session.get(
                FAERS_BASE_URL,
                params={
                    "search": search,
                    "count": "patient.reaction.reactionmeddrapt.exact",
                    "limit": min(top_n, 1000),
                },
                timeout=30,
            )
            response.raise_for_status()
            return [{"reaction": item["term"], "count": item["count"]} for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get trending reactions: {e}")
            return []

    def get_reaction_trend(
        self, reaction: str, current_days: int = 30, baseline_days: int = 365
    ) -> ReactionTrend | None:
        """
        Calculate trend for a specific adverse reaction across all drugs.
        Returns the reaction trend with top associated drugs (the trace-back step).
        """
        now = self.reference_date

        current_start = now - timedelta(days=current_days)
        current_count = self._count_reports_for_reaction(reaction, current_start, now)

        baseline_end = now - timedelta(days=baseline_days)
        baseline_start = baseline_end - timedelta(days=current_days)
        baseline_count = self._count_reports_for_reaction(reaction, baseline_start, baseline_end)

        if baseline_count == 0:
            delta_pct = float("inf") if current_count > 0 else 0.0
        else:
            delta_pct = ((current_count - baseline_count) / baseline_count) * 100

        top_drugs = self._get_top_drugs_for_reaction(reaction, current_start, now)

        return ReactionTrend(
            source="faers",
            reaction=reaction,
            window_days=current_days,
            reports_current=current_count,
            reports_baseline=baseline_count,
            delta_pct=delta_pct,
            top_drugs=top_drugs,
        )

    def _count_reports_for_reaction(self, reaction: str, start: datetime, end: datetime) -> int:
        date_range = f"[{start.strftime('%Y%m%d')}+TO+{end.strftime('%Y%m%d')}]"
        search = f'receivedate:{date_range}+AND+patient.reaction.reactionmeddrapt:"{reaction}"'
        try:
            response = self.session.get(FAERS_BASE_URL, params={"search": search, "limit": 1}, timeout=30)
            if response.status_code == 404:
                return 0
            response.raise_for_status()
            return response.json().get("meta", {}).get("results", {}).get("total", 0)
        except Exception as e:
            logger.error(f"Failed to count reports for reaction {reaction}: {e}")
            return 0

    def _get_top_drugs_for_reaction(self, reaction: str, start: datetime, end: datetime, top_n: int = 20) -> list[dict[str, Any]]:
        """Get top drugs associated with a specific reaction (the trace-back step)."""
        date_range = f"[{start.strftime('%Y%m%d')}+TO+{end.strftime('%Y%m%d')}]"
        search = f'receivedate:{date_range}+AND+patient.reaction.reactionmeddrapt:"{reaction}"'
        try:
            response = self.session.get(
                FAERS_BASE_URL,
                params={"search": search, "count": "patient.drug.openfda.brand_name.exact", "limit": top_n},
                timeout=30,
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return [{"drug_name": item["term"], "count": item["count"]} for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get drugs for reaction {reaction}: {e}")
            return []

    # =========================================================================
    # BROAD DISCOVERY METHODS (The main discovery mode entry points)
    # =========================================================================

    def discover_reaction_anomalies(
        self,
        current_days: int = 30,
        baseline_days: int = 365,
        min_current_reports: int = 100,
        min_delta_pct: float = 50.0,
        top_n: int = 100,
    ) -> list[ReactionTrend]:
        """
        REACTION-FIRST DISCOVERY: Find adverse reactions that are spiking.
        
        This catches injury patterns you weren't looking for. Example:
        "Gastroparesis reports are up 200%" → trace to GLP-1 drugs → Ozempic signal
        """
        logger.info(f"Discovering trending reactions (last {current_days} days vs {baseline_days} days ago)")
        
        current_reactions = self.get_trending_reactions(days=current_days, top_n=top_n, serious_only=True)
        
        anomalies = []
        for item in current_reactions:
            reaction = item["reaction"]
            current_count = item["count"]
            
            if current_count < min_current_reports:
                continue
            
            trend = self.get_reaction_trend(reaction, current_days, baseline_days)
            
            if trend and (trend.delta_pct >= min_delta_pct or trend.reports_baseline == 0):
                anomalies.append(trend)
                logger.debug(f"  Trending reaction: {reaction} ({trend.reports_current} current, {trend.delta_pct:.0f}% delta)")
        
        anomalies.sort(key=lambda x: x.delta_pct if x.delta_pct != float("inf") else 999999, reverse=True)
        logger.info(f"Found {len(anomalies)} trending reactions")
        return anomalies

    def discover_drug_anomalies(
        self,
        current_days: int = 30,
        baseline_days: int = 365,
        min_current_reports: int = 50,
        min_delta_pct: float = 100.0,
        include_new_entrants: bool = True,
    ) -> list[AdverseTrend]:
        """PRODUCT-FIRST DISCOVERY: Find drugs with anomalous adverse event increases."""
        logger.info(f"Discovering drug anomalies (last {current_days} days)")

        now = self.reference_date
        current_drugs = self.get_trending_drugs(days=current_days, top_n=500)
        
        # Get baseline
        baseline_end = now - timedelta(days=baseline_days)
        baseline_start = baseline_end - timedelta(days=current_days)
        baseline_search = f"receivedate:[{baseline_start.strftime('%Y%m%d')}+TO+{baseline_end.strftime('%Y%m%d')}]"
        
        try:
            response = self.session.get(
                FAERS_BASE_URL,
                params={"search": baseline_search, "count": "patient.drug.openfda.brand_name.exact", "limit": 500},
                timeout=30,
            )
            response.raise_for_status()
            baseline_drugs = {item["term"]: item["count"] for item in response.json().get("results", [])}
        except Exception:
            baseline_drugs = {}

        anomalies = []
        for item in current_drugs:
            drug_name = item["drug_name"]
            current_count = item["count"]
            
            if current_count < min_current_reports:
                continue
            
            baseline_count = baseline_drugs.get(drug_name, 0)
            
            if baseline_count == 0:
                if not include_new_entrants:
                    continue
                delta_pct = float("inf")
                is_new = True
            else:
                delta_pct = ((current_count - baseline_count) / baseline_count) * 100
                is_new = False
            
            if delta_pct >= min_delta_pct or is_new:
                top_reactions = self._get_top_reactions_for_drug(drug_name, now - timedelta(days=current_days), now)
                anomalies.append(AdverseTrend(
                    source="faers",
                    product_name=drug_name,
                    window_days=current_days,
                    reports_current=current_count,
                    reports_baseline=baseline_count,
                    delta_pct=delta_pct,
                    top_reactions=top_reactions,
                    is_new_entrant=is_new,
                ))

        anomalies.sort(key=lambda x: x.delta_pct if x.delta_pct != float("inf") else 999999, reverse=True)
        logger.info(f"Found {len(anomalies)} drug anomalies")
        return anomalies

    def discover_drug_reaction_pairs(
        self,
        current_days: int = 30,
        baseline_days: int = 365,
        min_reports: int = 20,
        min_delta_pct: float = 100.0,
        top_drugs: int = 100,
        top_reactions_per_drug: int = 5,
    ) -> list[DrugReactionSignal]:
        """
        PAIR DISCOVERY: Find specific drug+reaction combinations that are spiking.

        More specific than drug-level or reaction-level. "Ozempic + Gastroparesis"
        might spike even if overall Ozempic and overall Gastroparesis look normal.
        """
        logger.info("Discovering drug+reaction pair anomalies")

        now = self.reference_date
        current_start = now - timedelta(days=current_days)
        baseline_end = now - timedelta(days=baseline_days)
        baseline_start = baseline_end - timedelta(days=current_days)
        
        drugs = self.get_trending_drugs(days=current_days, top_n=top_drugs)
        
        signals = []
        for drug_item in drugs:
            drug_name = drug_item["drug_name"]
            reactions = self._get_top_reactions_for_drug(drug_name, current_start, now, top_n=top_reactions_per_drug)
            
            for reaction in reactions:
                current_count = self._count_drug_reaction_pair(drug_name, reaction, current_start, now)
                if current_count < min_reports:
                    continue
                
                baseline_count = self._count_drug_reaction_pair(drug_name, reaction, baseline_start, baseline_end)
                
                if baseline_count == 0:
                    delta_pct = float("inf") if current_count > 0 else 0.0
                else:
                    delta_pct = ((current_count - baseline_count) / baseline_count) * 100
                
                if delta_pct >= min_delta_pct:
                    signals.append(DrugReactionSignal(
                        drug_name=drug_name,
                        reaction=reaction,
                        reports_current=current_count,
                        reports_baseline=baseline_count,
                        delta_pct=delta_pct,
                        window_days=current_days,
                    ))
        
        signals.sort(key=lambda x: x.delta_pct if x.delta_pct != float("inf") else 999999, reverse=True)
        logger.info(f"Found {len(signals)} drug+reaction pair signals")
        return signals

    def _count_drug_reaction_pair(self, drug_name: str, reaction: str, start: datetime, end: datetime) -> int:
        date_range = f"[{start.strftime('%Y%m%d')}+TO+{end.strftime('%Y%m%d')}]"
        search = (
            f"receivedate:{date_range}+AND+"
            f'(patient.drug.openfda.brand_name:"{drug_name}"+OR+'
            f'patient.drug.openfda.generic_name:"{drug_name}")+AND+'
            f'patient.reaction.reactionmeddrapt:"{reaction}"'
        )
        try:
            response = self.session.get(FAERS_BASE_URL, params={"search": search, "limit": 1}, timeout=30)
            if response.status_code == 404:
                return 0
            response.raise_for_status()
            return response.json().get("meta", {}).get("results", {}).get("total", 0)
        except Exception as e:
            logger.error(f"Failed to count {drug_name}+{reaction}: {e}")
            return 0

    # =========================================================================
    # MANUFACTURER-LEVEL DISCOVERY
    # =========================================================================

    def get_trending_manufacturers(self, days: int = 30, top_n: int = 100) -> list[dict[str, Any]]:
        """Get manufacturers by total adverse event count (detect systemic QC issues)."""
        end_date = self.reference_date
        start_date = end_date - timedelta(days=days)
        date_range = f"[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]"

        try:
            response = self.session.get(
                FAERS_BASE_URL,
                params={
                    "search": f"receivedate:{date_range}",
                    "count": "patient.drug.openfda.manufacturer_name.exact",
                    "limit": min(top_n, 1000),
                },
                timeout=30,
            )
            response.raise_for_status()
            return [{"manufacturer": item["term"], "count": item["count"]} for item in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get trending manufacturers: {e}")
            return []

    # =========================================================================
    # FULL DISCOVERY SCAN (Main entry point for Discovery Mode)
    # =========================================================================

    def run_full_discovery(self, current_days: int = 30, baseline_days: int = 365) -> dict[str, Any]:
        """
        Run all discovery methods and return consolidated results.
        This is the main entry point for Discovery Mode.
        """
        logger.info("=" * 60)
        logger.info("FAERS FULL DISCOVERY SCAN")
        logger.info("=" * 60)

        results = {
            "scan_time": self.reference_date.isoformat(),
            "source": "faers",
            "parameters": {"current_days": current_days, "baseline_days": baseline_days, "reference_date": self.reference_date.isoformat()},
            "drug_anomalies": [],
            "reaction_anomalies": [],
            "pair_signals": [],
            "summary": {},
        }
        
        # 1. Drug-level anomalies
        try:
            drug_anomalies = self.discover_drug_anomalies(
                current_days=current_days, baseline_days=baseline_days,
                min_current_reports=50, min_delta_pct=100.0
            )
            results["drug_anomalies"] = [
                {
                    "product_name": a.product_name,
                    "reports_current": a.reports_current,
                    "reports_baseline": a.reports_baseline,
                    "delta_pct": a.delta_pct if a.delta_pct != float("inf") else "new_entrant",
                    "top_reactions": a.top_reactions[:5],
                    "is_new_entrant": getattr(a, "is_new_entrant", False),
                }
                for a in drug_anomalies[:50]
            ]
        except Exception as e:
            logger.error(f"Drug anomaly discovery failed: {e}")
        
        # 2. Reaction-level anomalies (the novel approach)
        try:
            reaction_anomalies = self.discover_reaction_anomalies(
                current_days=current_days, baseline_days=baseline_days,
                min_current_reports=100, min_delta_pct=50.0
            )
            results["reaction_anomalies"] = [
                {
                    "reaction": t.reaction,
                    "reports_current": t.reports_current,
                    "reports_baseline": t.reports_baseline,
                    "delta_pct": t.delta_pct if t.delta_pct != float("inf") else "new",
                    "top_drugs": t.top_drugs[:5],
                }
                for t in reaction_anomalies[:50]
            ]
        except Exception as e:
            logger.error(f"Reaction anomaly discovery failed: {e}")
        
        # 3. Drug+reaction pair signals
        try:
            pair_signals = self.discover_drug_reaction_pairs(
                current_days=current_days, baseline_days=baseline_days,
                min_reports=20, min_delta_pct=100.0
            )
            results["pair_signals"] = [
                {
                    "drug_name": s.drug_name,
                    "reaction": s.reaction,
                    "reports_current": s.reports_current,
                    "reports_baseline": s.reports_baseline,
                    "delta_pct": s.delta_pct if s.delta_pct != float("inf") else "new",
                }
                for s in pair_signals[:50]
            ]
        except Exception as e:
            logger.error(f"Pair signal discovery failed: {e}")
        
        results["summary"] = {
            "drug_anomalies_count": len(results["drug_anomalies"]),
            "reaction_anomalies_count": len(results["reaction_anomalies"]),
            "pair_signals_count": len(results["pair_signals"]),
        }
        
        logger.info("=" * 60)
        logger.info(f"Discovery complete: {results['summary']}")
        logger.info("=" * 60)
        
        return results

    # Legacy aliases
    def get_adverse_trend(self, drug_name: str, current_days: int = 30, baseline_days: int = 365) -> AdverseTrend | None:
        return self.get_drug_trend(drug_name, current_days, baseline_days)

    def find_anomalies(self, **kwargs) -> list[AdverseTrend]:
        return self.discover_drug_anomalies(**kwargs)
