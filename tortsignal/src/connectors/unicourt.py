"""UniCourt connector for court filings data."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Generator

import requests

from src.config import get_config
from src.connectors.base import BaseConnector
from src.models import CaseRecord

logger = logging.getLogger(__name__)

# Nature of Suit codes for Product Liability
# 365 = Personal Injury - Product Liability
# 367 = Personal Injury - Health Care/Pharmaceutical Personal Injury Product Liability
NOS_CODES = [365, 367]


class UniCourtConnector(BaseConnector):
    """Connector for UniCourt court filings API."""

    def __init__(self):
        config = get_config()
        self.api_key = config.unicourt.api_key
        self.base_url = config.unicourt.base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    @property
    def source_name(self) -> str:
        return "unicourt"

    def health_check(self) -> bool:
        """Check if UniCourt API is reachable."""
        try:
            # TODO: Replace with actual health check endpoint
            # response = self.session.get(f"{self.base_url}/health", timeout=10)
            # return response.status_code == 200
            logger.warning("UniCourt health_check not implemented - returning True")
            return True
        except Exception as e:
            logger.error(f"UniCourt health check failed: {e}")
            return False

    def fetch(
        self,
        days: int = 7,
        limit: int = 100,
        nos_codes: list[int] | None = None,
    ) -> Generator[CaseRecord, None, None]:
        """
        Fetch recent product liability cases.

        Args:
            days: Number of days to look back
            limit: Maximum number of cases to return
            nos_codes: Nature of Suit codes to filter (default: [365, 367])

        Yields:
            CaseRecord objects
        """
        nos_codes = nos_codes or NOS_CODES
        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).date()

        # =================================================================
        # TODO: IMPLEMENT YOUR UNICOURT API CALL HERE
        # =================================================================
        # 
        # Your UniCourt sandbox should have an endpoint like:
        #   GET /search/cases or GET /cases
        #
        # Example implementation:
        #
        # params = {
        #     "filed_after": since_date.isoformat(),
        #     "nature_of_suit": ",".join(map(str, nos_codes)),
        #     "page_size": min(limit, 100),
        # }
        # 
        # response = self.session.get(
        #     f"{self.base_url}/search/cases",
        #     params=params,
        #     timeout=30,
        # )
        # response.raise_for_status()
        # data = response.json()
        #
        # for item in data.get("cases", []):
        #     yield self._parse_case(item)
        #
        # =================================================================

        logger.warning(
            "UniCourt fetch() not implemented - returning empty results. "
            "See src/connectors/unicourt.py for implementation instructions."
        )
        return
        yield  # Make this a generator

    def _parse_case(self, raw: dict[str, Any]) -> CaseRecord:
        """
        Parse a raw UniCourt API response into a CaseRecord.

        TODO: Adjust field names based on your actual API response structure.
        """
        # Extract parties
        parties = raw.get("parties", [])
        defendants = [p for p in parties if p.get("side", "").lower() == "defendant"]
        defendant_names = [d.get("name", "") for d in defendants]

        # Extract attorneys/firms
        attorneys = raw.get("attorneys", [])
        plaintiff_attorneys = [a for a in attorneys if a.get("side", "").lower() == "plaintiff"]
        plaintiff_firms = list(set(a.get("firm", "") for a in plaintiff_attorneys if a.get("firm")))

        # Extract court info
        court = raw.get("court", {})

        return CaseRecord(
            source_uid=str(raw.get("case_id", raw.get("id", ""))),
            title=raw.get("title", raw.get("case_title", "")),
            filed_date=raw.get("filed_date", raw.get("filing_date", "")),
            jurisdiction=court.get("jurisdiction", "federal"),
            state=court.get("state", raw.get("state")),
            plaintiff_firm=plaintiff_firms[0] if plaintiff_firms else None,
            url=raw.get("url", raw.get("docket_url")),
            complaint_snippet=raw.get("complaint_text", raw.get("claims_text")),
            defendant_text=", ".join(defendant_names) if defendant_names else None,
            raw_data=raw,
        )

    def fetch_case_details(self, case_id: str) -> dict[str, Any] | None:
        """
        Fetch detailed information for a specific case.

        TODO: Implement based on your UniCourt API.
        """
        logger.warning(f"fetch_case_details not implemented for case_id={case_id}")
        return None


# =============================================================================
# USAGE EXAMPLE (for reference)
# =============================================================================
#
# from src.connectors.unicourt import UniCourtConnector
#
# connector = UniCourtConnector()
#
# if connector.health_check():
#     for case in connector.fetch(days=7, limit=100):
#         print(f"Case: {case.title}")
#         print(f"  Filed: {case.filed_date}")
#         print(f"  Defendant: {case.defendant_text}")
#         print()
