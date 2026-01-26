"""
OpenFDA Integration - FAERS (FDA Adverse Event Reporting System)
Queries adverse event reports to validate safety signals

API Documentation: https://open.fda.gov/apis/drug/event/
"""

import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
import time


@dataclass
class AdverseEventSignal:
    """Adverse event signal from FAERS"""
    substance_name: str
    reaction: str
    report_count: int
    serious_count: int
    death_count: int
    top_countries: List[Dict]
    date_range: Dict
    interpretation: str
    confidence: str  # HIGH, MEDIUM, LOW


class OpenFDAIntegration:
    """
    Integration with OpenFDA FAERS API for adverse event reports

    No API key required, but rate limited to:
    - Without key: 240 requests per minute, 120,000 per day
    - With key: 240 requests per minute, 240,000 per day
    """

    BASE_URL = "https://api.fda.gov/drug/event.json"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TortSignal/1.0 (Mass Tort Discovery)'
        })

    def search_adverse_events(
        self,
        substance_name: str,
        reaction_terms: List[str],
        start_date: str = "20000101",  # YYYYMMDD format
        end_date: str = "20250131"
    ) -> AdverseEventSignal:
        """
        Search FAERS for adverse events matching substance + reaction

        Args:
            substance_name: Chemical/drug name (e.g., "Titanium Dioxide")
            reaction_terms: List of MedDRA reaction terms (e.g., ["Crohn's Disease", "Ulcerative Colitis"])
            start_date: Start date (YYYYMMDD)
            end_date: End date (YYYYMMDD)

        Returns:
            AdverseEventSignal with report counts and analysis
        """
        print(f"\n[OpenFDA FAERS] Searching: {substance_name} + {reaction_terms}")

        try:
            # Build search query
            # Example: patient.drug.openfda.substance_name:"Titanium Dioxide"+AND+(patient.reaction.reactionmeddrapt:"Crohn's Disease"+OR+patient.reaction.reactionmeddrapt:"Ulcerative Colitis")

            reaction_query = "+OR+".join([
                f'patient.reaction.reactionmeddrapt:"{term}"'
                for term in reaction_terms
            ])

            search_query = (
                f'patient.drug.openfda.substance_name:"{substance_name}"'
                f'+AND+({reaction_query})'
                f'+AND+receivedate:[{start_date}+TO+{end_date}]'
            )

            # Get total count
            count_result = self._query_api(search_query, limit=1)
            total_count = count_result.get('meta', {}).get('results', {}).get('total', 0)

            print(f"[OpenFDA FAERS] Found {total_count} adverse event reports")

            if total_count == 0:
                return self._empty_signal(substance_name, reaction_terms)

            # Get detailed breakdown (serious outcomes, deaths, countries)
            serious_count = self._count_serious_outcomes(search_query)
            death_count = self._count_deaths(search_query)
            top_countries = self._get_top_countries(search_query, limit=5)

            # Get date range
            date_stats = count_result.get('meta', {}).get('results', {})

            # Interpret signal strength
            interpretation, confidence = self._interpret_signal(
                total_count,
                serious_count,
                death_count
            )

            return AdverseEventSignal(
                substance_name=substance_name,
                reaction=" OR ".join(reaction_terms),
                report_count=total_count,
                serious_count=serious_count,
                death_count=death_count,
                top_countries=top_countries,
                date_range={
                    'start': start_date,
                    'end': end_date
                },
                interpretation=interpretation,
                confidence=confidence
            )

        except Exception as e:
            print(f"[OpenFDA FAERS] Error: {e}")
            return self._empty_signal(substance_name, reaction_terms)

    def _query_api(self, search: str, limit: int = 1, count: Optional[str] = None) -> Dict:
        """
        Execute OpenFDA API query

        Args:
            search: Search query string
            limit: Number of results to return
            count: Field to count by (e.g., "patient.patientsex")

        Returns:
            JSON response from API
        """
        params = {
            'search': search,
            'limit': limit
        }

        if count:
            params['count'] = count

        if self.api_key:
            params['api_key'] = self.api_key

        response = self.session.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()

        # Rate limiting (240 per minute)
        time.sleep(0.25)  # Sleep 250ms between requests

        return response.json()

    def _count_serious_outcomes(self, base_search: str) -> int:
        """Count reports with serious outcomes (hospitalization, disability, death, etc.)"""
        try:
            serious_search = f'{base_search}+AND+serious:1'
            result = self._query_api(serious_search, limit=1)
            return result.get('meta', {}).get('results', {}).get('total', 0)
        except:
            return 0

    def _count_deaths(self, base_search: str) -> int:
        """Count reports with death outcome"""
        try:
            death_search = f'{base_search}+AND+seriousnessdeath:1'
            result = self._query_api(death_search, limit=1)
            return result.get('meta', {}).get('results', {}).get('total', 0)
        except:
            return 0

    def _get_top_countries(self, base_search: str, limit: int = 5) -> List[Dict]:
        """Get top reporting countries"""
        try:
            result = self._query_api(
                base_search,
                limit=1,
                count='occurcountry'
            )

            countries = result.get('results', [])[:limit]
            return [
                {
                    'country': c.get('term', 'Unknown'),
                    'count': c.get('count', 0)
                }
                for c in countries
            ]
        except:
            return []

    def _interpret_signal(
        self,
        total_count: int,
        serious_count: int,
        death_count: int
    ) -> tuple[str, str]:
        """
        Interpret signal strength

        Returns:
            (interpretation_text, confidence_level)
        """
        if total_count == 0:
            return "No adverse event reports found", "NONE"

        serious_pct = (serious_count / total_count * 100) if total_count > 0 else 0
        death_pct = (death_count / total_count * 100) if total_count > 0 else 0

        # Confidence based on report volume
        if total_count >= 100:
            confidence = "HIGH"
        elif total_count >= 20:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        # Interpretation based on severity
        if death_count >= 10:
            interpretation = f"Strong safety signal: {total_count} reports including {death_count} deaths"
        elif serious_count >= 50:
            interpretation = f"Moderate safety signal: {total_count} reports, {serious_pct:.0f}% serious"
        elif total_count >= 50:
            interpretation = f"Emerging safety signal: {total_count} reports identified"
        else:
            interpretation = f"Weak signal: {total_count} reports (may be noise)"

        return interpretation, confidence

    def _empty_signal(self, substance: str, reactions: List[str]) -> AdverseEventSignal:
        """Return empty signal when no data found"""
        return AdverseEventSignal(
            substance_name=substance,
            reaction=" OR ".join(reactions),
            report_count=0,
            serious_count=0,
            death_count=0,
            top_countries=[],
            date_range={},
            interpretation="No adverse event reports found",
            confidence="NONE"
        )

    def search_multiple_substances(
        self,
        substance_names: List[str],
        reaction_terms: List[str]
    ) -> Dict[str, AdverseEventSignal]:
        """
        Search FAERS for multiple substances (e.g., different forms of TiO2)

        Args:
            substance_names: List of substance names to search
            reaction_terms: Reaction terms to search for

        Returns:
            Dictionary mapping substance name to AdverseEventSignal
        """
        results = {}

        for substance in substance_names:
            signal = self.search_adverse_events(substance, reaction_terms)
            results[substance] = signal

            # Rate limiting
            time.sleep(1)

        return results


# Example usage
if __name__ == "__main__":
    fda = OpenFDAIntegration()

    # Test: TiO2 → IBD
    print("\n" + "="*80)
    print("TEST: Titanium Dioxide → Inflammatory Bowel Disease")
    print("="*80)

    signal = fda.search_adverse_events(
        substance_name="Titanium Dioxide",
        reaction_terms=["Crohn's Disease", "Ulcerative Colitis", "Inflammatory Bowel Disease"],
        start_date="20000101",
        end_date="20250131"
    )

    print(f"\nResults:")
    print(f"  Total Reports: {signal.report_count}")
    print(f"  Serious Outcomes: {signal.serious_count}")
    print(f"  Deaths: {signal.death_count}")
    print(f"  Confidence: {signal.confidence}")
    print(f"  Interpretation: {signal.interpretation}")

    if signal.top_countries:
        print(f"\n  Top Reporting Countries:")
        for country in signal.top_countries:
            print(f"    {country['country']}: {country['count']} reports")

    # Test: Multiple substance forms
    print("\n" + "="*80)
    print("TEST: Multiple TiO2 Forms")
    print("="*80)

    substances = [
        "Titanium Dioxide",
        "Titanium Oxide",
        "TiO2"
    ]

    results = fda.search_multiple_substances(
        substances,
        ["Inflammatory Bowel Disease", "Colitis"]
    )

    print(f"\nComparative Results:")
    for substance, signal in results.items():
        print(f"  {substance}: {signal.report_count} reports ({signal.confidence})")
