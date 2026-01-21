"""Data models for TortSignal."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CaseRecord:
    """A court case record from UniCourt or PACER."""

    source_uid: str
    title: str
    filed_date: str  # YYYY-MM-DD
    jurisdiction: str
    plaintiff_firm: str | None = None
    state: str | None = None
    url: str | None = None
    complaint_snippet: str | None = None
    defendant_text: str | None = None
    product_text: str | None = None
    injury_text: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedEntities:
    """Entities extracted from case text via LLM."""

    product: str
    defendant: str
    injury: str
    confidence: float
    notes: str
    is_product_liability: bool


@dataclass
class FAERSReport:
    """An FDA FAERS adverse event report."""

    primaryid: str
    caseid: str
    receivedate: str
    event_dt: str | None
    drugs: list[dict[str, Any]]
    reactions: list[dict[str, Any]]
    outcomes: list[dict[str, Any]]
    patient_sex: str | None = None
    patient_age: float | None = None
    reporter_country: str | None = None
    narrative: str | None = None


@dataclass
class MAUDEReport:
    """An FDA MAUDE device adverse event report."""

    mdr_report_key: str
    event_type: str
    report_date: str
    manufacturer: str | None
    brand_name: str | None
    device_problem_codes: list[str]
    event_description: str | None = None
    patient_sex: str | None = None
    patient_age: str | None = None


@dataclass
class PubMedArticle:
    """A PubMed article record."""

    pmid: str
    title: str
    abstract: str | None
    journal: str
    pub_date: str
    publication_types: list[str]
    authors: list[dict[str, str]]
    mesh_terms: list[str]
    chemicals: list[str]
    doi: str | None = None
    pmc_id: str | None = None

    @property
    def is_meta_analysis(self) -> bool:
        """Check if this is a meta-analysis."""
        return any("meta-analysis" in pt.lower() for pt in self.publication_types)


@dataclass
class CandidateCluster:
    """A cluster of cases forming an emerging tort candidate."""

    defendant: str
    product: str
    injury_label: str  # Most common injury or "mixed"
    injury_counts: dict[str, int]
    count: int
    states: list[str]
    firms: list[str]
    breadth_states: int
    breadth_firms: int
    score_total: float
    score_components: dict[str, Any]
    why_now: str
    first_seen: datetime | None
    last_seen: datetime | None
    members: list[dict[str, Any]]  # Individual case records


@dataclass
class SignalEvent:
    """A typed signal event derived from a source document."""

    event_type: str  # filing_new, filing_spike, adverse_trend, paper_published, etc.
    event_time: datetime
    weight: float
    features: dict[str, Any]
    excerpt: str | None
    doc_source_uid: str | None = None


@dataclass
class AdverseTrend:
    """An adverse event trend signal from FAERS or MAUDE (product-first discovery)."""

    source: str  # "faers" or "maude"
    product_name: str
    window_days: int
    reports_current: int
    reports_baseline: int
    delta_pct: float
    top_reactions: list[str]
    prr_proxy: float | None = None
    is_new_entrant: bool = False  # True if product wasn't in baseline top list


@dataclass
class ReactionTrend:
    """An adverse reaction trend across all products (reaction-first discovery).
    
    This is the key to catching signals that product-first discovery misses.
    Example: "Gastroparesis is spiking" → trace back → "driven by GLP-1 drugs"
    """

    source: str  # "faers" or "maude"
    reaction: str  # The adverse reaction / injury
    window_days: int
    reports_current: int
    reports_baseline: int
    delta_pct: float
    top_drugs: list[dict[str, Any]]  # [{drug_name, count}, ...] - the trace-back


@dataclass
class DrugReactionSignal:
    """A specific drug+reaction pair signal (most granular discovery).
    
    More specific than product-level or reaction-level analysis.
    "Ozempic + Gastroparesis" might spike even if overall Ozempic
    and overall Gastroparesis look normal individually.
    """

    drug_name: str
    reaction: str
    reports_current: int
    reports_baseline: int
    delta_pct: float
    window_days: int


@dataclass
class DeviceTrend:
    """A device adverse event trend from MAUDE (product-first discovery)."""

    source: str  # "maude"
    device_name: str
    product_code: str | None  # FDA product code (e.g., "OTN" for mesh)
    manufacturer: str | None
    window_days: int
    reports_current: int
    reports_baseline: int
    delta_pct: float
    top_problems: list[str]  # Device problem codes
    is_new_entrant: bool = False


@dataclass
class DeviceCategoryTrend:
    """A device category trend from MAUDE (category-first discovery).
    
    Catches whole classes of devices failing, not just individual brands.
    Example: All surgical mesh (product code OTN) spiking, across manufacturers.
    """

    source: str  # "maude"
    product_code: str  # FDA device product code
    product_code_name: str | None  # Human-readable name
    window_days: int
    reports_current: int
    reports_baseline: int
    delta_pct: float
    top_manufacturers: list[dict[str, Any]]  # [{manufacturer, count}, ...]
    top_brands: list[dict[str, Any]]  # [{brand_name, count}, ...]


@dataclass 
class ManufacturerTrend:
    """A manufacturer-level trend (systemic quality issues).
    
    Catches companies with problems across their entire portfolio,
    not just individual products.
    """

    source: str  # "faers" or "maude"
    manufacturer: str
    window_days: int
    reports_current: int
    reports_baseline: int
    delta_pct: float
    top_products: list[dict[str, Any]]  # [{product_name, count}, ...]
