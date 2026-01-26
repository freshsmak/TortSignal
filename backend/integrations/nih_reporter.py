"""
NIH RePORTER (Research Portfolio Online Reporting Tools) Integration
Track NIH research grants and publications for emerging signal detection

API Docs: https://api.reporter.nih.gov/
API v2: https://api.reporter.nih.gov/v2/projects/search
"""

import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NIHGrant:
    """NIH research grant project"""
    project_num: str
    project_title: str
    principal_investigator: str
    organization: str
    fiscal_year: int
    award_amount: float
    project_start_date: str
    project_end_date: str
    abstract: str
    keywords: List[str]
    publications: List[str]  # PMIDs
    contact_pi: str


@dataclass
class ResearchTrendAnalysis:
    """Analysis of NIH funding trends for chemical-disease hypothesis"""
    chemical: str
    disease: str
    total_grants: int
    total_funding: float  # USD
    grants_by_year: Dict[int, int]
    funding_by_year: Dict[int, float]
    key_investigators: List[str]
    major_institutions: List[str]
    recent_projects: List[NIHGrant]
    trend: str  # 'INCREASING', 'DECREASING', 'STABLE', 'EMERGING'
    interpretation: str


class NIHReporterAPI:
    """
    NIH RePORTER API Integration

    Queries NIH grant database for:
    - Active research projects
    - Funding trends
    - Publications
    - Investigators

    Use cases:
    - Detect emerging research areas (early signal)
    - Validate mechanistic plausibility
    - Predict when papers will publish (grant cycles)
    - Identify expert witnesses
    """

    BASE_URL = "https://api.reporter.nih.gov/v2"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TortSignal/1.0',
            'Accept': 'application/json'
        })

    def search_grants(
        self,
        keywords: List[str],
        fiscal_years: Optional[List[int]] = None,
        limit: int = 500
    ) -> List[NIHGrant]:
        """
        Search NIH grants by keywords

        Args:
            keywords: Search terms (e.g., ['titanium dioxide', 'inflammatory bowel disease'])
            fiscal_years: Years to search (default: last 10 years)
            limit: Max results (default: 500)

        Returns:
            List of NIHGrant objects
        """
        if fiscal_years is None:
            current_year = datetime.now().year
            fiscal_years = list(range(current_year - 10, current_year + 1))

        print(f"\n[NIH RePORTER] Searching grants: {keywords}")
        print(f"[NIH RePORTER] Fiscal years: {min(fiscal_years)}-{max(fiscal_years)}")

        # Build query
        query = {
            "criteria": {
                "advanced_text_search": {
                    "operator": "and",
                    "search_field": "terms",
                    "search_text": " ".join(keywords)
                },
                "fiscal_years": fiscal_years
            },
            "offset": 0,
            "limit": limit,
            "sort_field": "fiscal_year",
            "sort_order": "desc"
        }

        try:
            response = self.session.post(
                f"{self.BASE_URL}/projects/search",
                json=query,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            grants = []
            if 'results' in data:
                for result in data['results']:
                    grant = self._parse_grant(result)
                    grants.append(grant)

            print(f"[NIH RePORTER] Found {len(grants)} grants")
            return grants

        except requests.exceptions.RequestException as e:
            print(f"[NIH RePORTER] API Error: {e}")
            return []
        except Exception as e:
            print(f"[NIH RePORTER] Parse Error: {e}")
            return []

    def analyze_research_trend(
        self,
        chemical: str,
        disease: str,
        years_back: int = 10
    ) -> ResearchTrendAnalysis:
        """
        Analyze NIH research funding trends for chemical-disease hypothesis

        Returns:
            - Total grants and funding
            - Yearly trends
            - Key investigators
            - Trend interpretation
        """
        print(f"\n[NIH RePORTER] Analyzing trends: {chemical} → {disease}")

        # Search for grants mentioning both chemical and disease
        current_year = datetime.now().year
        fiscal_years = list(range(current_year - years_back, current_year + 1))

        grants = self.search_grants(
            keywords=[chemical, disease],
            fiscal_years=fiscal_years
        )

        # Analyze trends
        total_funding = sum(g.award_amount for g in grants)
        grants_by_year = {}
        funding_by_year = {}

        for grant in grants:
            year = grant.fiscal_year
            grants_by_year[year] = grants_by_year.get(year, 0) + 1
            funding_by_year[year] = funding_by_year.get(year, 0) + grant.award_amount

        # Identify key investigators
        pi_counts = {}
        for grant in grants:
            pi = grant.principal_investigator
            pi_counts[pi] = pi_counts.get(pi, 0) + 1

        key_investigators = sorted(
            pi_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        key_investigators = [pi for pi, count in key_investigators]

        # Identify major institutions
        org_counts = {}
        for grant in grants:
            org = grant.organization
            org_counts[org] = org_counts.get(org, 0) + 1

        major_institutions = sorted(
            org_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        major_institutions = [org for org, count in major_institutions]

        # Determine trend
        trend, interpretation = self._interpret_trend(
            grants_by_year,
            funding_by_year,
            chemical,
            disease
        )

        # Get recent projects (last 3 years)
        recent_cutoff = current_year - 3
        recent_projects = [g for g in grants if g.fiscal_year >= recent_cutoff]

        analysis = ResearchTrendAnalysis(
            chemical=chemical,
            disease=disease,
            total_grants=len(grants),
            total_funding=total_funding,
            grants_by_year=grants_by_year,
            funding_by_year=funding_by_year,
            key_investigators=key_investigators,
            major_institutions=major_institutions,
            recent_projects=recent_projects[:10],  # Top 10 most recent
            trend=trend,
            interpretation=interpretation
        )

        print(f"[NIH RePORTER] Total grants: {analysis.total_grants}")
        print(f"[NIH RePORTER] Total funding: ${analysis.total_funding:,.0f}")
        print(f"[NIH RePORTER] Trend: {trend}")

        return analysis

    def _parse_grant(self, data: Dict) -> NIHGrant:
        """Parse NIH API response into NIHGrant object"""
        # Handle award_amount which can be None
        award_amount = data.get('award_amount', 0)
        if award_amount is None:
            award_amount = 0
        award_amount = float(award_amount)

        return NIHGrant(
            project_num=data.get('project_num', ''),
            project_title=data.get('project_title', ''),
            principal_investigator=self._format_pi_name(data.get('principal_investigators', [])),
            organization=data.get('organization', {}).get('org_name', ''),
            fiscal_year=data.get('fiscal_year', 0),
            award_amount=award_amount,
            project_start_date=data.get('project_start_date', ''),
            project_end_date=data.get('project_end_date', ''),
            abstract=data.get('abstract_text', ''),
            keywords=data.get('keywords', []),
            publications=[],  # Would need separate API call to get publications
            contact_pi=data.get('contact_pi_name', '')
        )

    def _format_pi_name(self, pi_list: List[Dict]) -> str:
        """Format principal investigator name from API data"""
        if not pi_list:
            return ''
        pi = pi_list[0]  # Take first PI
        first = pi.get('first_name', '')
        last = pi.get('last_name', '')
        return f"{first} {last}".strip()

    def _interpret_trend(
        self,
        grants_by_year: Dict[int, int],
        funding_by_year: Dict[int, float],
        chemical: str,
        disease: str
    ) -> tuple[str, str]:
        """
        Interpret funding trend

        Returns: (trend_category, interpretation_text)
        """
        if not grants_by_year:
            return 'NO_DATA', f"No NIH funding found for {chemical} → {disease} research"

        years = sorted(grants_by_year.keys())
        if len(years) < 3:
            total_grants = sum(grants_by_year.values())
            return 'EMERGING', f"Limited data ({total_grants} grants) - may be emerging research area"

        # Calculate trend (compare first 3 years to last 3 years)
        early_years = years[:3]
        recent_years = years[-3:]

        early_grants = sum(grants_by_year.get(y, 0) for y in early_years)
        recent_grants = sum(grants_by_year.get(y, 0) for y in recent_years)

        if recent_grants == 0 and early_grants > 0:
            trend = 'DECREASING'
            interpretation = f"NIH funding declining - research interest waning (was {early_grants} grants, now 0)"
        elif early_grants == 0 and recent_grants > 0:
            trend = 'EMERGING'
            interpretation = f"NEW research area - {recent_grants} grants in last 3 years (strong signal of emerging concern)"
        elif recent_grants > early_grants * 1.5:
            trend = 'INCREASING'
            percent_increase = ((recent_grants - early_grants) / early_grants) * 100
            interpretation = f"Growing research interest - grants increased {percent_increase:.0f}% (from {early_grants} to {recent_grants})"
        elif recent_grants < early_grants * 0.5:
            trend = 'DECREASING'
            percent_decrease = ((early_grants - recent_grants) / early_grants) * 100
            interpretation = f"Declining research interest - grants decreased {percent_decrease:.0f}% (from {early_grants} to {recent_grants})"
        else:
            trend = 'STABLE'
            interpretation = f"Steady research activity - ~{recent_grants} grants per year (sustained interest)"

        return trend, interpretation


def main():
    """Test NIH RePORTER integration"""
    print("=" * 80)
    print("NIH RePORTER INTEGRATION TEST")
    print("=" * 80)

    api = NIHReporterAPI()

    # Test 1: Search for TiO2 → IBD grants
    print("\n[TEST 1] TiO2 → IBD research grants")
    tio2_ibd_analysis = api.analyze_research_trend(
        chemical='titanium dioxide',
        disease='inflammatory bowel disease',
        years_back=10
    )

    print(f"\n  Total grants: {tio2_ibd_analysis.total_grants}")
    print(f"  Total funding: ${tio2_ibd_analysis.total_funding:,.0f}")
    print(f"  Trend: {tio2_ibd_analysis.trend}")
    print(f"  Interpretation: {tio2_ibd_analysis.interpretation}")

    if tio2_ibd_analysis.key_investigators:
        print(f"\n  Key Investigators:")
        for pi in tio2_ibd_analysis.key_investigators[:5]:
            print(f"    - {pi}")

    if tio2_ibd_analysis.recent_projects:
        print(f"\n  Recent Projects:")
        for project in tio2_ibd_analysis.recent_projects[:3]:
            print(f"    - [{project.fiscal_year}] {project.project_title[:80]}")
            print(f"      PI: {project.principal_investigator}, ${project.award_amount:,.0f}")

    # Test 2: Search for nanoparticle toxicity (broader search)
    print("\n\n[TEST 2] Nanoparticle + IBD research")
    nano_ibd_analysis = api.analyze_research_trend(
        chemical='nanoparticle',
        disease='colitis',
        years_back=10
    )

    print(f"\n  Total grants: {nano_ibd_analysis.total_grants}")
    print(f"  Total funding: ${nano_ibd_analysis.total_funding:,.0f}")
    print(f"  Trend: {nano_ibd_analysis.trend}")

    # Test 3: Grants by year trend
    if tio2_ibd_analysis.grants_by_year:
        print("\n\n[TEST 3] Funding trend by year (TiO2 + IBD):")
        for year in sorted(tio2_ibd_analysis.grants_by_year.keys()):
            grants = tio2_ibd_analysis.grants_by_year[year]
            funding = tio2_ibd_analysis.funding_by_year.get(year, 0)
            print(f"  {year}: {grants} grants, ${funding:,.0f}")

    print("\n" + "=" * 80)
    print("NIH RePORTER INTEGRATION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
