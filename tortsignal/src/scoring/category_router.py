"""Category router - assigns tort categories to candidates."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Known pharmaceutical companies (add more as needed)
PHARMA_DEFENDANTS = {
    "pfizer", "merck", "johnson & johnson", "j&j", "bayer", "novartis",
    "roche", "sanofi", "glaxosmithkline", "gsk", "abbvie", "eli lilly",
    "bristol-myers squibb", "bms", "astrazeneca", "amgen", "gilead",
    "novo nordisk", "boehringer ingelheim", "takeda", "allergan", "viatris",
    "teva", "mylan", "purdue pharma", "endo", "mallinckrodt",
}

# Known device companies
DEVICE_DEFENDANTS = {
    "medtronic", "boston scientific", "abbott", "stryker", "zimmer biomet",
    "johnson & johnson", "j&j", "ethicon", "c.r. bard", "bard", "becton dickinson",
    "bd", "baxter", "philips", "ge healthcare", "siemens healthineers",
    "intuitive surgical", "edwards lifesciences", "dexcom", "resmed",
}

# Known chemical/agricultural companies
CHEMICAL_DEFENDANTS = {
    "monsanto", "bayer", "dow", "dupont", "basf", "syngenta", "corteva",
    "3m", "dupont de nemours", "chemours", "honeywell", "eastman chemical",
    "ppg industries", "sherwin-williams", "rpm international",
}

# Known government contractors (military products)
GOV_CONTRACTORS = {
    "3m", "aearo technologies", "lockheed martin", "raytheon", "northrop grumman",
    "general dynamics", "bae systems", "l3harris", "leidos", "booz allen",
}

# Product type keywords
DRUG_KEYWORDS = {
    "pill", "tablet", "capsule", "injection", "vaccine", "medication",
    "prescription", "drug", "pharmaceutical", "therapy", "treatment",
    "mg", "mcg", "dosage",
}

DEVICE_KEYWORDS = {
    "implant", "mesh", "stent", "pacemaker", "defibrillator", "pump",
    "catheter", "prosthetic", "joint replacement", "hip", "knee",
    "surgical", "medical device", "iud", "hernia",
}

CHEMICAL_KEYWORDS = {
    "herbicide", "pesticide", "insecticide", "roundup", "glyphosate",
    "pfas", "pfoa", "pfos", "foam", "contamination", "exposure",
    "asbestos", "benzene", "paraquat", "dioxin",
}


class CategoryRouter:
    """Routes candidates to appropriate tort categories."""

    # Category weight vectors (used by Scorer)
    CATEGORY_WEIGHTS = {
        "pharma": {
            "faers_trend": 0.40,
            "court_velocity": 0.25,
            "court_breadth": 0.10,
            "literature": 0.15,
            "sec_language": 0.10,
        },
        "device": {
            "maude_trend": 0.40,
            "court_velocity": 0.25,
            "court_breadth": 0.10,
            "literature": 0.15,
            "sec_language": 0.10,
        },
        "chemical": {
            "literature": 0.35,
            "court_velocity": 0.25,
            "court_breadth": 0.15,
            "iarc_classification": 0.15,
            "sec_language": 0.10,
        },
        "gov_contractor": {
            "court_velocity": 0.35,
            "fca_settlement": 0.25,
            "court_breadth": 0.20,
            "sec_language": 0.20,
        },
        "consumer": {
            "court_velocity": 0.30,
            "court_breadth": 0.20,
            "literature": 0.25,
            "cpsc_reports": 0.15,
            "sec_language": 0.10,
        },
        "other": {
            "court_velocity": 0.35,
            "court_breadth": 0.25,
            "literature": 0.20,
            "sec_language": 0.20,
        },
    }

    def __init__(self):
        # Normalize sets to lowercase
        self.pharma_defendants = {d.lower() for d in PHARMA_DEFENDANTS}
        self.device_defendants = {d.lower() for d in DEVICE_DEFENDANTS}
        self.chemical_defendants = {d.lower() for d in CHEMICAL_DEFENDANTS}
        self.gov_contractors = {d.lower() for d in GOV_CONTRACTORS}

    def assign_category(
        self,
        defendant: str,
        product: str,
        injury: str | None = None,
    ) -> str:
        """
        Assign a tort category based on defendant, product, and injury.

        Args:
            defendant: Defendant company name
            product: Product name
            injury: Optional injury description

        Returns:
            Category string: pharma, device, chemical, gov_contractor, consumer, or other
        """
        defendant_lower = (defendant or "").lower()
        product_lower = (product or "").lower()
        injury_lower = (injury or "").lower()
        combined_text = f"{defendant_lower} {product_lower} {injury_lower}"

        # Check defendant lists first (most reliable)
        if self._matches_any(defendant_lower, self.pharma_defendants):
            # But could be device if product suggests it
            if self._has_keywords(product_lower, DEVICE_KEYWORDS):
                return "device"
            return "pharma"

        if self._matches_any(defendant_lower, self.device_defendants):
            return "device"

        if self._matches_any(defendant_lower, self.chemical_defendants):
            # Chemical companies also make drugs sometimes
            if self._has_keywords(product_lower, DRUG_KEYWORDS):
                return "pharma"
            return "chemical"

        if self._matches_any(defendant_lower, self.gov_contractors):
            return "gov_contractor"

        # Fall back to product/injury keywords
        if self._has_keywords(combined_text, DRUG_KEYWORDS):
            return "pharma"

        if self._has_keywords(combined_text, DEVICE_KEYWORDS):
            return "device"

        if self._has_keywords(combined_text, CHEMICAL_KEYWORDS):
            return "chemical"

        # Default
        return "consumer"

    def _matches_any(self, text: str, target_set: set[str]) -> bool:
        """Check if text contains any item from the target set."""
        for target in target_set:
            if target in text:
                return True
        return False

    def _has_keywords(self, text: str, keywords: set[str]) -> bool:
        """Check if text contains any of the keywords."""
        for kw in keywords:
            if kw in text:
                return True
        return False

    def get_weights(self, category: str) -> dict[str, float]:
        """Get the weight vector for a category."""
        return self.CATEGORY_WEIGHTS.get(category, self.CATEGORY_WEIGHTS["other"])
