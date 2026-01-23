"""UniCourt connector for court filings data.

Uses the official UniCourt Python SDK to search for product liability cases.
Documentation: https://docs.unicourt.com/
SDK: https://github.com/UniCourt/enterprise-api-py-sdk
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Generator

logger = logging.getLogger(__name__)

try:
    import unicourt
    from unicourt import Authentication, CaseSearch
    UNICOURT_SDK_AVAILABLE = True
except ImportError:
    UNICOURT_SDK_AVAILABLE = False
    logger.warning(
        "UniCourt SDK not installed. Install with: pip install unicourt\n"
        "SDK documentation: https://github.com/UniCourt/enterprise-api-py-sdk"
    )

from src.config import get_config
from src.connectors.base import BaseConnector
from src.models import CaseRecord

logger = logging.getLogger(__name__)


class UniCourtConnector(BaseConnector):
    """
    Connector for UniCourt court filings API using the official SDK.

    Authentication:
        Uses CLIENT_ID and CLIENT_SECRET from environment variables.
        Automatically generates and manages OAuth tokens.

    Example:
        >>> connector = UniCourtConnector()
        >>> if connector.health_check():
        ...     for case in connector.fetch(days=30, limit=100):
        ...         print(case.title)
    """

    def __init__(self):
        if not UNICOURT_SDK_AVAILABLE:
            raise ImportError(
                "UniCourt SDK is required but not installed. "
                "Install with: pip install unicourt"
            )

        config = get_config()

        # Configure SDK with credentials
        unicourt.CLIENT_ID = config.unicourt.client_id
        unicourt.CLIENT_SECRET = config.unicourt.client_secret

        self.authenticated = False
        logger.info("UniCourt connector initialized")

    @property
    def source_name(self) -> str:
        return "unicourt"

    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token."""
        if self.authenticated:
            return True

        try:
            logger.info("Generating UniCourt authentication token...")
            auth_obj, status_code = Authentication.generate_new_token()

            if status_code == 200:
                self.authenticated = True
                logger.info("✓ UniCourt authentication successful")
                return True
            else:
                logger.error(f"UniCourt authentication failed with status {status_code}")
                return False

        except Exception as e:
            logger.error(f"UniCourt authentication error: {e}")
            return False

    def health_check(self) -> bool:
        """Check if UniCourt API is reachable and credentials are valid."""
        try:
            return self._ensure_authenticated()
        except Exception as e:
            logger.error(f"UniCourt health check failed: {e}")
            return False

    def __del__(self):
        """Cleanup: invalidate token when connector is destroyed."""
        if self.authenticated:
            try:
                Authentication.invalidate_token()
                logger.info("UniCourt authentication token invalidated")
            except Exception as e:
                logger.warning(f"Error invalidating UniCourt token: {e}")

    def fetch(
        self,
        days: int = 30,
        limit: int = 100,
        page_size: int = 100,
        strategy: str = "hybrid",
    ) -> Generator[CaseRecord, None, None]:
        """
        Fetch recent product liability cases using the UniCourt SDK.

        Uses a hybrid strategy combining:
        1. High-recall defendant query (structure-based)
        2. High-precision tort language query (content-based)

        Args:
            days: Number of days to look back (default: 30)
            limit: Maximum total number of cases to return (default: 100)
            page_size: Results per page (default: 100, max: 100)
            strategy: "hybrid" (default), "structure", or "language"

        Yields:
            CaseRecord objects for product liability cases

        Strategy Details:
            - "hybrid": Combines structure + language (recommended)
            - "structure": High recall - all defendant cases
            - "language": High precision - explicit tort language only

        Example:
            >>> connector = UniCourtConnector()
            >>> for case in connector.fetch(days=30, limit=50):
            ...     print(f"{case.title} - {case.filed_date}")
        """
        if not self._ensure_authenticated():
            logger.error("Authentication failed - cannot fetch cases")
            return

        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).date()
        date_str = since_date.strftime("%Y-%m-%d")

        logger.info(f"Searching UniCourt using '{strategy}' strategy for cases filed after {date_str}")

        # Run queries based on strategy
        if strategy == "hybrid":
            # Combine both high-recall and high-precision
            for case_record in self._fetch_hybrid(date_str, limit, page_size):
                yield case_record
        elif strategy == "structure":
            # High-recall: all cases with defendants
            query = f'filedDate:[{date_str} TO *] AND (Party:((PartyRole:(name:defendant))))'
            logger.debug(f"Structure query: {query}")
            for case_record in self._execute_query(query, limit, page_size):
                yield case_record
        elif strategy == "language":
            # High-precision: explicit tort language
            query = f'filedDate:[{date_str} TO *] AND ("product liability" OR "design defect" OR "failure to warn" OR "strict liability")'
            logger.debug(f"Language query: {query}")
            for case_record in self._execute_query(query, limit, page_size):
                yield case_record
        else:
            logger.error(f"Unknown strategy: {strategy}")
            return

    def _fetch_hybrid(
        self,
        date_str: str,
        limit: int,
        page_size: int,
    ) -> Generator[CaseRecord, None, None]:
        """
        Hybrid strategy: Combine structure-based and language-based queries.

        Returns unique cases from both approaches, language matches prioritized.
        """
        seen_case_ids = set()
        fetched_count = 0

        # First: High-precision tort language query
        language_query = f'filedDate:[{date_str} TO *] AND ("product liability" OR "design defect" OR "failure to warn" OR "strict liability")'
        logger.info("Phase 1: High-precision tort language search")
        logger.debug(f"Query: {language_query}")

        for case_record in self._execute_query(language_query, limit // 2, page_size):
            if fetched_count >= limit:
                break

            case_id = case_record.source_uid
            if case_id not in seen_case_ids:
                seen_case_ids.add(case_id)
                fetched_count += 1
                yield case_record

        # Second: High-recall structure query (if under limit)
        if fetched_count < limit:
            structure_query = f'filedDate:[{date_str} TO *] AND (Party:((PartyRole:(name:defendant))))'
            logger.info(f"Phase 2: High-recall structure search (need {limit - fetched_count} more)")
            logger.debug(f"Query: {structure_query}")

            for case_record in self._execute_query(structure_query, limit - fetched_count, page_size):
                if fetched_count >= limit:
                    break

                case_id = case_record.source_uid
                if case_id not in seen_case_ids:
                    seen_case_ids.add(case_id)
                    fetched_count += 1
                    yield case_record

        logger.info(f"Hybrid fetch complete: {fetched_count} unique cases")

    def _execute_query(
        self,
        query: str,
        limit: int,
        page_size: int,
    ) -> Generator[CaseRecord, None, None]:
        """
        Execute a single UniCourt query and yield results.

        Args:
            query: UniCourt query string
            limit: Maximum number of results
            page_size: Results per page

        Yields:
            CaseRecord objects
        """

        fetched_count = 0
        page_number = 1
        max_pages = (limit // page_size) + 1

        try:
            while fetched_count < limit and page_number <= max_pages:
                logger.debug(f"Fetching page {page_number} (page_size={page_size})")

                # Call SDK search method
                response, status_code = CaseSearch.search_cases(
                    q=query,
                    order='desc',
                    sort='filedDate',
                    page_number=page_number,
                    page_size=min(page_size, 100)  # API max is 100
                )

                if status_code != 200:
                    logger.error(f"UniCourt API returned status {status_code}")
                    break

                # Extract results from response
                if not hasattr(response, 'case_search_result_array'):
                    logger.warning("Response does not contain case_search_result_array")
                    break

                cases = response.case_search_result_array or []

                if len(cases) == 0:
                    logger.debug(f"No more cases found (page {page_number})")
                    break

                logger.debug(f"Retrieved {len(cases)} cases from page {page_number}")

                # Parse and yield each case
                for case_obj in cases:
                    if fetched_count >= limit:
                        break

                    try:
                        case_record = self._parse_case(case_obj)
                        fetched_count += 1
                        yield case_record
                    except Exception as e:
                        logger.warning(f"Failed to parse case: {e}")
                        continue

                page_number += 1

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            import traceback
            traceback.print_exc()

    def _parse_case(self, case_obj: Any) -> CaseRecord:
        """
        Parse a UniCourt SDK case object into a CaseRecord.

        Args:
            case_obj: Case object from unicourt SDK CaseSearch response

        Returns:
            CaseRecord with extracted fields

        Note:
            The SDK returns objects with attributes, not dictionaries.
            Use getattr() with defaults to safely extract fields.
        """
        # Helper to safely get attributes
        def get_attr(obj, *attrs, default=None):
            """Try multiple attribute names, return first found or default."""
            for attr in attrs:
                if hasattr(obj, attr):
                    val = getattr(obj, attr)
                    if val is not None:
                        return val
            return default

        # Extract basic case info
        case_id = get_attr(case_obj, 'case_id', 'id', 'case_number', default='')
        title = get_attr(case_obj, 'title', 'case_name', 'case_title', default='')
        filed_date = get_attr(case_obj, 'filed_date', 'filing_date', 'date_filed', default='')

        # Extract court info
        court_obj = get_attr(case_obj, 'court', default=None)
        if court_obj:
            jurisdiction = get_attr(court_obj, 'jurisdiction', default='federal')
            state = get_attr(court_obj, 'state', 'state_code', default=None)
            court_name = get_attr(court_obj, 'name', 'court_name', default=None)
        else:
            jurisdiction = 'federal'
            state = get_attr(case_obj, 'state', 'state_code', default=None)
            court_name = get_attr(case_obj, 'court_name', default=None)

        # Extract parties
        parties = get_attr(case_obj, 'parties', 'party_array', default=[]) or []
        defendant_names = []
        for party in parties:
            party_type = get_attr(party, 'party_type', 'type', 'role', default='').lower()
            if 'defendant' in party_type:
                name = get_attr(party, 'name', 'party_name', default='')
                if name:
                    defendant_names.append(name)

        # Extract attorneys/firms
        attorneys = get_attr(case_obj, 'attorneys', 'attorney_array', default=[]) or []
        plaintiff_firms = set()
        for attorney in attorneys:
            party_type = get_attr(attorney, 'party_type', 'type', 'representing', default='').lower()
            if 'plaintiff' in party_type:
                firm = get_attr(attorney, 'firm', 'firm_name', 'law_firm', default='')
                if firm:
                    plaintiff_firms.add(firm)

        # Extract URL
        url = get_attr(
            case_obj,
            'url',
            'docket_url',
            'case_url',
            'pacer_url',
            default=None
        )

        # Extract snippet/summary
        snippet = get_attr(
            case_obj,
            'complaint_text',
            'claims_text',
            'summary',
            'description',
            default=None
        )

        # Convert to string representation for raw_data
        # (SDK objects may not be JSON serializable)
        try:
            if hasattr(case_obj, '__dict__'):
                raw_data = {k: str(v) for k, v in case_obj.__dict__.items()
                           if not k.startswith('_')}
            else:
                raw_data = {'case_id': case_id, 'title': title}
        except Exception:
            raw_data = {'case_id': case_id}

        return CaseRecord(
            source_uid=str(case_id),
            title=title,
            filed_date=str(filed_date) if filed_date else None,
            jurisdiction=jurisdiction,
            state=state,
            plaintiff_firm=list(plaintiff_firms)[0] if plaintiff_firms else None,
            url=url,
            complaint_snippet=snippet,
            defendant_text=", ".join(defendant_names) if defendant_names else None,
            raw_data=raw_data,
        )

    def fetch_case_details(self, case_id: str) -> dict[str, Any] | None:
        """
        Fetch detailed information for a specific case using the UniCourt SDK.

        Args:
            case_id: The UniCourt case ID to fetch details for

        Returns:
            Dictionary with case details, or None if fetch fails

        Note:
            This method requires the CaseAnalytics or CaseDocket SDK modules.
            Not implemented yet - see UniCourt SDK documentation for details.
        """
        logger.warning(
            f"fetch_case_details not yet implemented for case_id={case_id}. "
            "See UniCourt SDK CaseAnalytics or CaseDocket modules."
        )
        return None


# =============================================================================
# USAGE EXAMPLE
# =============================================================================
#
# Example 1: Basic usage
# ----------------------
#
# from src.connectors.unicourt import UniCourtConnector
#
# connector = UniCourtConnector()
#
# if connector.health_check():
#     print("✓ UniCourt API is accessible")
#
#     # Fetch product liability cases from last 30 days
#     for case in connector.fetch(days=30, limit=50):
#         print(f"\nCase: {case.title}")
#         print(f"  Filed: {case.filed_date}")
#         print(f"  Defendant: {case.defendant_text}")
#         print(f"  Plaintiff Firm: {case.plaintiff_firm}")
#         print(f"  State: {case.state}")
#
# Example 2: Integration with discovery pipeline
# ----------------------------------------------
#
# from src.connectors.unicourt import UniCourtConnector
# from src.pipeline.discovery import process_cases
#
# connector = UniCourtConnector()
# cases = list(connector.fetch(days=7, limit=100))
# print(f"Found {len(cases)} new product liability cases")
# process_cases(cases)  # Feed into clustering/scoring pipeline
