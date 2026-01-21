"""PubMed / NCBI E-utilities connector for scientific literature."""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Generator
from xml.etree import ElementTree

import requests

from src.connectors.base import BaseConnector
from src.models import PubMedArticle

logger = logging.getLogger(__name__)

# NCBI E-utilities endpoints
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Rate limiting: 3 requests/second without API key, 10 with key
REQUEST_DELAY = 0.35  # seconds between requests


class PubMedConnector(BaseConnector):
    """Connector for PubMed scientific literature via NCBI E-utilities."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize PubMed connector.

        Args:
            api_key: Optional NCBI API key for higher rate limits.
        """
        self.api_key = api_key
        self.session = requests.Session()
        self._last_request_time = 0.0

    @property
    def source_name(self) -> str:
        return "pubmed"

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def health_check(self) -> bool:
        """Check if PubMed E-utilities is reachable."""
        try:
            self._rate_limit()
            response = self.session.get(
                ESEARCH_URL,
                params={"db": "pubmed", "term": "test", "retmax": 1},
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"PubMed health check failed: {e}")
            return False

    def fetch(
        self,
        query: str,
        days: int | None = None,
        limit: int = 100,
    ) -> Generator[PubMedArticle, None, None]:
        """
        Search PubMed and fetch article details.

        Args:
            query: Search query (e.g., "glyphosate AND non-hodgkin lymphoma")
            days: Optional - limit to articles from last N days
            limit: Maximum number of articles to return

        Yields:
            PubMedArticle objects
        """
        # Build query with optional date filter
        full_query = query
        if days:
            date_filter = f'("{days}"[PDat])'
            full_query = f"({query}) AND {date_filter}"

        # Search for PMIDs
        pmids = self._search(full_query, limit)
        if not pmids:
            return

        # Fetch article details in batches
        batch_size = 50
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i : i + batch_size]
            articles = self._fetch_details(batch)
            for article in articles:
                yield article

    def _search(self, query: str, limit: int) -> list[str]:
        """Search PubMed and return list of PMIDs."""
        self._rate_limit()

        params = {
            "db": "pubmed",
            "term": query,
            "retmax": limit,
            "retmode": "json",
            "sort": "relevance",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self.session.get(ESEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []

    def _fetch_details(self, pmids: list[str]) -> list[PubMedArticle]:
        """Fetch article details for a list of PMIDs."""
        if not pmids:
            return []

        self._rate_limit()

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self.session.get(EFETCH_URL, params=params, timeout=30)
            response.raise_for_status()
            return self._parse_xml(response.text)
        except Exception as e:
            logger.error(f"PubMed fetch failed: {e}")
            return []

    def _parse_xml(self, xml_text: str) -> list[PubMedArticle]:
        """Parse PubMed XML response into PubMedArticle objects."""
        articles = []

        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError as e:
            logger.error(f"Failed to parse PubMed XML: {e}")
            return []

        for article_elem in root.findall(".//PubmedArticle"):
            try:
                article = self._parse_article(article_elem)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"Failed to parse article: {e}")

        return articles

    def _parse_article(self, elem: ElementTree.Element) -> PubMedArticle | None:
        """Parse a single PubmedArticle XML element."""
        medline = elem.find("MedlineCitation")
        if medline is None:
            return None

        # PMID
        pmid_elem = medline.find("PMID")
        pmid = pmid_elem.text if pmid_elem is not None else None
        if not pmid:
            return None

        article = medline.find("Article")
        if article is None:
            return None

        # Title
        title_elem = article.find("ArticleTitle")
        title = self._get_text(title_elem) or "No title"

        # Abstract
        abstract_elem = article.find("Abstract/AbstractText")
        abstract = self._get_text(abstract_elem)

        # Journal
        journal_elem = article.find("Journal/Title")
        journal = self._get_text(journal_elem) or "Unknown"

        # Publication date
        pub_date = self._parse_pub_date(article)

        # Publication types
        pub_types = []
        for pt in article.findall("PublicationTypeList/PublicationType"):
            if pt.text:
                pub_types.append(pt.text)

        # Authors
        authors = []
        for author in article.findall("AuthorList/Author"):
            name_parts = []
            lastname = author.find("LastName")
            forename = author.find("ForeName")
            if lastname is not None and lastname.text:
                name_parts.append(lastname.text)
            if forename is not None and forename.text:
                name_parts.insert(0, forename.text)
            if name_parts:
                affil_elem = author.find("AffiliationInfo/Affiliation")
                authors.append({
                    "name": " ".join(name_parts),
                    "affiliation": self._get_text(affil_elem),
                })

        # MeSH terms
        mesh_terms = []
        for mesh in medline.findall("MeshHeadingList/MeshHeading/DescriptorName"):
            if mesh.text:
                mesh_terms.append(mesh.text)

        # Chemicals
        chemicals = []
        for chem in medline.findall("ChemicalList/Chemical/NameOfSubstance"):
            if chem.text:
                chemicals.append(chem.text)

        # DOI
        doi = None
        for id_elem in elem.findall("PubmedData/ArticleIdList/ArticleId"):
            if id_elem.get("IdType") == "doi":
                doi = id_elem.text
                break

        # PMC ID
        pmc_id = None
        for id_elem in elem.findall("PubmedData/ArticleIdList/ArticleId"):
            if id_elem.get("IdType") == "pmc":
                pmc_id = id_elem.text
                break

        return PubMedArticle(
            pmid=pmid,
            title=title,
            abstract=abstract,
            journal=journal,
            pub_date=pub_date,
            publication_types=pub_types,
            authors=authors,
            mesh_terms=mesh_terms,
            chemicals=chemicals,
            doi=doi,
            pmc_id=pmc_id,
        )

    def _get_text(self, elem: ElementTree.Element | None) -> str | None:
        """Extract text content from an XML element."""
        if elem is None:
            return None
        # Handle mixed content (text + child elements)
        text_parts = []
        if elem.text:
            text_parts.append(elem.text)
        for child in elem:
            if child.text:
                text_parts.append(child.text)
            if child.tail:
                text_parts.append(child.tail)
        return "".join(text_parts).strip() if text_parts else None

    def _parse_pub_date(self, article: ElementTree.Element) -> str:
        """Extract publication date as YYYY-MM-DD string."""
        # Try ArticleDate first
        article_date = article.find("ArticleDate")
        if article_date is not None:
            year = article_date.findtext("Year", "")
            month = article_date.findtext("Month", "01")
            day = article_date.findtext("Day", "01")
            if year:
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Fall back to Journal PubDate
        pub_date = article.find("Journal/JournalIssue/PubDate")
        if pub_date is not None:
            year = pub_date.findtext("Year", "")
            month = pub_date.findtext("Month", "01")
            day = pub_date.findtext("Day", "01")
            # Month might be text like "Jan"
            if month and not month.isdigit():
                month_map = {
                    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
                    "may": "05", "jun": "06", "jul": "07", "aug": "08",
                    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
                }
                month = month_map.get(month.lower()[:3], "01")
            if year:
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        return ""

    def search_product_injury(
        self,
        product: str,
        injury: str,
        limit: int = 50,
    ) -> list[PubMedArticle]:
        """
        Search for studies linking a product to an injury.

        Args:
            product: Product/drug/chemical name
            injury: Injury/disease name
            limit: Maximum results

        Returns:
            List of PubMedArticle objects, prioritizing meta-analyses
        """
        query = f'("{product}"[Title/Abstract]) AND ("{injury}"[Title/Abstract])'
        articles = list(self.fetch(query, limit=limit))

        # Sort to prioritize meta-analyses and systematic reviews
        def sort_key(a: PubMedArticle) -> tuple:
            is_meta = a.is_meta_analysis
            is_review = any("review" in pt.lower() for pt in a.publication_types)
            return (not is_meta, not is_review, a.pub_date or "")

        articles.sort(key=sort_key)
        return articles

    def count_publications(
        self,
        product: str,
        injury: str,
    ) -> int:
        """Count publications linking a product to an injury."""
        query = f'("{product}"[Title/Abstract]) AND ("{injury}"[Title/Abstract])'
        
        self._rate_limit()
        params = {
            "db": "pubmed",
            "term": query,
            "rettype": "count",
            "retmode": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self.session.get(ESEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return int(data.get("esearchresult", {}).get("count", 0))
        except Exception as e:
            logger.error(f"PubMed count failed: {e}")
            return 0
