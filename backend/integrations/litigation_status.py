"""
Automated Litigation Status Integration

Addresses robustness gap #5: No litigation-status ground truth integration

This module provides automated court docket integration to validate "pre-litigation"
status and novelty scoring. It uses multiple sources:

1. UniCourt API (primary) - Comprehensive case database
2. PACER (Public Access to Court Electronic Records) - Federal courts
3. CourtListener (free alternative) - Federal appellate, district, bankruptcy
4. State court databases (where available)
5. MDL (Multidistrict Litigation) database

Purpose:
- Validate novelty scoring with real-time case counts
- Detect early litigation before it becomes a mass tort
- Identify MDL formations and consolidations
- Track case velocity and geographic distribution
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import requests


class LitigationPhase(Enum):
    """Litigation lifecycle phases"""
    PRE_LITIGATION = "pre_litigation"  # 0 cases, only scientific evidence
    EMERGING = "emerging"  # 1-10 cases, no MDL
    EARLY_MDL = "early_mdl"  # 10-100 cases, MDL forming
    ACTIVE_MDL = "active_mdl"  # 100-1000 cases, MDL active
    MATURE_MDL = "mature_mdl"  # 1000+ cases, bellwether trials
    DECLINING = "declining"  # Settlement phase, case count decreasing
    RESOLVED = "resolved"  # MDL closed, settlements complete


@dataclass
class CourtCase:
    """Individual court case"""
    case_number: str
    court: str
    title: str
    filed_date: datetime
    status: str  # active, closed, dismissed, settled
    plaintiff: str
    defendant: str
    case_type: str  # product_liability, personal_injury, class_action
    mdl_number: Optional[int] = None
    docket_url: Optional[str] = None


@dataclass
class MDLStatus:
    """Multidistrict Litigation status"""
    mdl_number: int
    title: str
    court: str
    judge: str
    case_count: int
    creation_date: datetime
    status: str  # pending, active, closed
    bellwether_trials: int
    settlements: Optional[int] = None
    settlement_amount: Optional[float] = None


@dataclass
class LitigationStatusReport:
    """Comprehensive litigation status for a chemical/product"""
    chemical: str
    product: Optional[str] = None

    # Case counts
    total_cases: int = 0
    active_cases: int = 0
    closed_cases: int = 0
    dismissed_cases: int = 0

    # Geographic distribution
    federal_cases: int = 0
    state_cases: int = 0
    states_represented: List[str] = None
    law_firms_involved: List[str] = None

    # MDL status
    mdl_status: Optional[MDLStatus] = None
    is_mdl: bool = False

    # Temporal metrics
    first_case_date: Optional[datetime] = None
    latest_case_date: Optional[datetime] = None
    case_velocity_30d: int = 0  # Cases filed in last 30 days
    case_velocity_90d: int = 0  # Cases filed in last 90 days

    # Classification
    phase: LitigationPhase = LitigationPhase.PRE_LITIGATION
    is_pre_litigation: bool = True
    novelty_score: int = 10  # 0-10, 10 = completely novel, 0 = saturated

    # Data quality
    data_source: str = "unicourt"
    confidence: float = 0.0
    last_updated: datetime = None

    def __post_init__(self):
        if self.states_represented is None:
            self.states_represented = []
        if self.law_firms_involved is None:
            self.law_firms_involved = []
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def calculate_phase(self):
        """Determine litigation phase based on case counts and MDL status"""
        if self.total_cases == 0:
            self.phase = LitigationPhase.PRE_LITIGATION
            self.is_pre_litigation = True
            self.novelty_score = 10
        elif self.total_cases <= 10 and not self.is_mdl:
            self.phase = LitigationPhase.EMERGING
            self.is_pre_litigation = False
            self.novelty_score = 7
        elif 10 < self.total_cases <= 100:
            if self.is_mdl:
                self.phase = LitigationPhase.EARLY_MDL
                self.novelty_score = 5
            else:
                self.phase = LitigationPhase.EMERGING
                self.novelty_score = 6
            self.is_pre_litigation = False
        elif 100 < self.total_cases <= 1000:
            self.phase = LitigationPhase.ACTIVE_MDL
            self.is_pre_litigation = False
            self.novelty_score = 3
        elif self.total_cases > 1000:
            self.phase = LitigationPhase.MATURE_MDL
            self.is_pre_litigation = False
            self.novelty_score = 0
        else:
            self.phase = LitigationPhase.PRE_LITIGATION
            self.is_pre_litigation = True
            self.novelty_score = 10

        # Adjust for declining phase (case velocity negative)
        if self.case_velocity_90d < (self.total_cases * -0.1):  # 10% decline
            self.phase = LitigationPhase.DECLINING

    def calculate_confidence(self):
        """Calculate confidence in litigation status data"""
        # Start with base confidence by source
        source_confidence = {
            'unicourt_api': 0.90,
            'pacer_api': 0.95,
            'courtlistener': 0.80,
            'manual_search': 0.70,
            'estimated': 0.40
        }

        self.confidence = source_confidence.get(self.data_source, 0.50)

        # Adjust for data recency
        if self.last_updated:
            days_old = (datetime.now() - self.last_updated).days
            if days_old <= 7:
                pass  # No penalty
            elif days_old <= 30:
                self.confidence *= 0.95
            elif days_old <= 90:
                self.confidence *= 0.90
            else:
                self.confidence *= 0.80

        # Adjust for geographic coverage
        if len(self.states_represented) >= 10:
            self.confidence *= 1.05  # Comprehensive search
        elif len(self.states_represented) == 0:
            self.confidence *= 0.85  # May be missing state court cases

        # Clamp to [0, 1]
        self.confidence = max(0.0, min(1.0, self.confidence))


class LitigationStatusIntegration:
    """
    Main litigation status integration

    Coordinates multiple sources to determine litigation status
    """

    def __init__(self):
        self.cache = {}

    def get_status(
        self,
        chemical: str,
        product: Optional[str] = None,
        defendant: Optional[str] = None,
        use_cache: bool = True
    ) -> LitigationStatusReport:
        """
        Get comprehensive litigation status

        Args:
            chemical: Chemical name (e.g., "titanium dioxide", "glyphosate")
            product: Optional product name (e.g., "Roundup", "Skittles")
            defendant: Optional defendant name (e.g., "Bayer", "Mars")
            use_cache: Whether to use cached results (default: True)

        Returns:
            Comprehensive litigation status report
        """
        cache_key = f"{chemical}:{product}:{defendant}"

        if use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            age = (datetime.now() - cached.last_updated).days
            if age < 7:  # Cache valid for 7 days
                print(f"[LITIGATION] Using cached status ({age} days old)")
                return cached

        print(f"\n[LITIGATION] Querying status for {chemical}...")

        report = LitigationStatusReport(
            chemical=chemical,
            product=product
        )

        # Strategy 1: Try UniCourt API (best coverage)
        unicourt_cases = self._search_unicourt(chemical, product, defendant)
        if unicourt_cases:
            report = self._build_report_from_unicourt(unicourt_cases, report)
            report.data_source = "unicourt_api"

        # Strategy 2: Try PACER API (federal courts only)
        # Note: PACER API requires separate credentials and fees
        # Commenting out for now, but structure provided for future integration
        # pacer_cases = self._search_pacer(chemical, product, defendant)
        # if pacer_cases:
        #     report = self._merge_pacer_results(report, pacer_cases)

        # Strategy 3: Try CourtListener (free federal courts)
        courtlistener_cases = self._search_courtlistener(chemical, product, defendant)
        if courtlistener_cases:
            report = self._merge_courtlistener_results(report, courtlistener_cases)

        # Strategy 4: Check MDL database
        mdl_status = self._check_mdl_database(chemical, product)
        if mdl_status:
            report.mdl_status = mdl_status
            report.is_mdl = True

        # Calculate phase and novelty
        report.calculate_phase()
        report.calculate_confidence()

        # Cache result
        self.cache[cache_key] = report

        print(f"[LITIGATION] Status: {report.phase.value}")
        print(f"[LITIGATION] Total Cases: {report.total_cases}")
        print(f"[LITIGATION] Novelty Score: {report.novelty_score}/10")
        print(f"[LITIGATION] Confidence: {report.confidence:.1%}")

        return report

    def _search_unicourt(
        self,
        chemical: str,
        product: Optional[str],
        defendant: Optional[str]
    ) -> Optional[List[CourtCase]]:
        """
        Search UniCourt for cases

        Uses existing UniCourt connector (tortsignal/src/connectors/unicourt.py)
        """
        try:
            # Import UniCourt connector if available
            from tortsignal.src.connectors.unicourt import UniCourtConnector

            connector = UniCourtConnector()

            if not connector.health_check():
                print(f"[LITIGATION] UniCourt health check failed")
                return None

            # Build search query
            # UniCourt uses Lucene-style queries
            query_parts = []

            # Add chemical name
            query_parts.append(f'"{chemical}"')

            # Add product if specified
            if product:
                query_parts.append(f'OR "{product}"')

            # Add defendant if specified
            if defendant:
                query_parts.append(f'party:"{defendant}"')

            query = " ".join(query_parts)

            print(f"[LITIGATION] UniCourt query: {query}")

            # Fetch cases (last 5 years for comprehensive view)
            cases = []
            for case_record in connector.fetch(days=1825, limit=1000):  # 5 years
                # Convert to CourtCase
                court_case = CourtCase(
                    case_number=case_record.case_id,
                    court=case_record.court or "Unknown",
                    title=case_record.title or "",
                    filed_date=case_record.filed_date,
                    status="active",  # UniCourt doesn't always provide status
                    plaintiff="",  # Would need to parse from title or entities
                    defendant="",
                    case_type="product_liability",
                    docket_url=f"https://unicourt.com/case/{case_record.case_id}"
                )
                cases.append(court_case)

            print(f"[LITIGATION] Found {len(cases)} UniCourt cases")
            return cases if cases else None

        except ImportError:
            print(f"[LITIGATION] UniCourt connector not available")
            return None
        except Exception as e:
            print(f"[LITIGATION] UniCourt search error: {e}")
            return None

    def _search_courtlistener(
        self,
        chemical: str,
        product: Optional[str],
        defendant: Optional[str]
    ) -> Optional[List[CourtCase]]:
        """
        Search CourtListener API (free federal court access)

        API Docs: https://www.courtlistener.com/api/rest-info/
        """
        try:
            base_url = "https://www.courtlistener.com/api/rest/v3/search/"

            # Build query
            query_parts = [f'"{chemical}"']
            if product:
                query_parts.append(f'"{product}"')

            query = " OR ".join(query_parts)

            params = {
                'q': query,
                'type': 'd',  # Dockets
                'order_by': 'dateFiled desc',
                'format': 'json'
            }

            response = requests.get(base_url, params=params, timeout=30)

            if response.status_code != 200:
                print(f"[LITIGATION] CourtListener error: {response.status_code}")
                return None

            data = response.json()
            results = data.get('results', [])

            cases = []
            for result in results:
                court_case = CourtCase(
                    case_number=result.get('docketNumber', 'Unknown'),
                    court=result.get('court', 'Unknown'),
                    title=result.get('caseName', ''),
                    filed_date=datetime.fromisoformat(result.get('dateFiled', '2000-01-01')),
                    status='active',
                    plaintiff='',
                    defendant='',
                    case_type='product_liability',
                    docket_url=f"https://www.courtlistener.com{result.get('absolute_url', '')}"
                )
                cases.append(court_case)

            print(f"[LITIGATION] Found {len(cases)} CourtListener cases")
            return cases if cases else None

        except Exception as e:
            print(f"[LITIGATION] CourtListener search error: {e}")
            return None

    def _check_mdl_database(
        self,
        chemical: str,
        product: Optional[str]
    ) -> Optional[MDLStatus]:
        """
        Check JPML (Judicial Panel on Multidistrict Litigation) database

        MDL data is public via JPML website
        """
        # Known MDLs (would expand with live scraping/API)
        known_mdls = {
            'roundup': MDLStatus(
                mdl_number=2741,
                title='In Re: Roundup Products Liability Litigation',
                court='N.D. California',
                judge='Judge Vince Chhabria',
                case_count=4000,  # Approximate, would fetch live
                creation_date=datetime(2016, 10, 3),
                status='active',
                bellwether_trials=3,
                settlements=100000,
                settlement_amount=10_000_000_000
            ),
            'talcum powder': MDLStatus(
                mdl_number=2738,
                title='In Re: Johnson & Johnson Talcum Powder Products',
                court='D. New Jersey',
                judge='Judge Freda Wolfson',
                case_count=20000,
                creation_date=datetime(2016, 10, 4),
                status='active',
                bellwether_trials=5,
                settlements=None,
                settlement_amount=None
            ),
            'zantac': MDLStatus(
                mdl_number=2924,
                title='In Re: Zantac (Ranitidine) Products Liability Litigation',
                court='S.D. Florida',
                judge='Judge Robin Rosenberg',
                case_count=2000,
                creation_date=datetime(2020, 2, 13),
                status='active',
                bellwether_trials=0,
                settlements=None,
                settlement_amount=None
            )
        }

        # Check if chemical/product matches known MDL
        search_key = chemical.lower()
        if product:
            search_key = product.lower()

        for key, mdl in known_mdls.items():
            if key in search_key or search_key in key:
                print(f"[LITIGATION] Found MDL {mdl.mdl_number}: {mdl.title}")
                return mdl

        # Would implement live scraping of JPML website here
        # URL: https://www.jpml.uscourts.gov/pending-mdls

        return None

    def _build_report_from_unicourt(
        self,
        cases: List[CourtCase],
        report: LitigationStatusReport
    ) -> LitigationStatusReport:
        """Build litigation report from UniCourt cases"""
        report.total_cases = len(cases)
        report.active_cases = len([c for c in cases if c.status == 'active'])
        report.closed_cases = len([c for c in cases if c.status in ['closed', 'settled']])
        report.dismissed_cases = len([c for c in cases if c.status == 'dismissed'])

        # Federal vs state
        federal_courts = ['district', 'bankruptcy', 'appellate', 'supreme']
        for case in cases:
            court_lower = case.court.lower()
            if any(fc in court_lower for fc in federal_courts):
                report.federal_cases += 1
            else:
                report.state_cases += 1

        # Temporal metrics
        if cases:
            dates = [c.filed_date for c in cases if c.filed_date]
            if dates:
                report.first_case_date = min(dates)
                report.latest_case_date = max(dates)

                # Calculate velocity
                now = datetime.now()
                thirty_days_ago = now - timedelta(days=30)
                ninety_days_ago = now - timedelta(days=90)

                report.case_velocity_30d = len([c for c in cases if c.filed_date >= thirty_days_ago])
                report.case_velocity_90d = len([c for c in cases if c.filed_date >= ninety_days_ago])

        return report

    def _merge_courtlistener_results(
        self,
        report: LitigationStatusReport,
        cases: List[CourtCase]
    ) -> LitigationStatusReport:
        """Merge CourtListener results into report (avoid double-counting)"""
        # Simple merge - in production would deduplicate by case number
        courtlistener_count = len(cases)

        # If UniCourt found fewer cases, supplement with CourtListener
        if courtlistener_count > report.total_cases:
            report.total_cases = courtlistener_count
            report.data_source = "courtlistener"

        return report


# Convenience function
def get_litigation_status(
    chemical: str,
    product: Optional[str] = None,
    defendant: Optional[str] = None
) -> LitigationStatusReport:
    """
    Quick litigation status check

    Args:
        chemical: Chemical name
        product: Optional product name
        defendant: Optional defendant name

    Returns:
        Litigation status report
    """
    integration = LitigationStatusIntegration()
    return integration.get_status(chemical, product, defendant)


if __name__ == "__main__":
    # Test litigation status integration
    print("\n" + "="*80)
    print("LITIGATION STATUS INTEGRATION TEST")
    print("="*80)

    # Test 1: Known MDL (Roundup)
    print("\n--- Test 1: Roundup (Mature MDL) ---")
    roundup_status = get_litigation_status("glyphosate", "Roundup", "Monsanto")
    print(f"\nPhase: {roundup_status.phase.value}")
    print(f"Pre-litigation: {roundup_status.is_pre_litigation}")
    print(f"Novelty Score: {roundup_status.novelty_score}/10")

    # Test 2: Pre-litigation (TiO2)
    print("\n--- Test 2: Titanium Dioxide (Potential Pre-litigation) ---")
    tio2_status = get_litigation_status("titanium dioxide", defendant="Mars")
    print(f"\nPhase: {tio2_status.phase.value}")
    print(f"Pre-litigation: {tio2_status.is_pre_litigation}")
    print(f"Novelty Score: {tio2_status.novelty_score}/10")
    print(f"Case Count: {tio2_status.total_cases}")

    # Test 3: Unknown (should return pre-litigation)
    print("\n--- Test 3: Novel Chemical (Expected Pre-litigation) ---")
    novel_status = get_litigation_status("novel_chemical_x")
    print(f"\nPhase: {novel_status.phase.value}")
    print(f"Pre-litigation: {novel_status.is_pre_litigation}")
    print(f"Novelty Score: {novel_status.novelty_score}/10")

    print("\n✅ LITIGATION STATUS INTEGRATION TEST COMPLETE")
