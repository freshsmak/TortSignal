"""LLM-based entity extraction for court cases and other documents."""

import json
import logging
from typing import Any

import requests

from src.config import get_config
from src.models import ExtractedEntities

logger = logging.getLogger(__name__)

# OpenAI API endpoint
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# JSON schema for structured output
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "product": {
            "type": "string",
            "description": "The product, drug, device, or chemical mentioned. Use 'unknown' if not found.",
        },
        "defendant": {
            "type": "string",
            "description": "The company or manufacturer being sued. Use 'unknown' if not found.",
        },
        "injury": {
            "type": "string",
            "description": "The alleged harm, injury, or disease. Use 'unknown' if not found.",
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score from 0.0 to 1.0",
        },
        "notes": {
            "type": "string",
            "description": "Any relevant notes about the extraction",
        },
        "is_product_liability": {
            "type": "boolean",
            "description": "True if this appears to be a product liability case",
        },
    },
    "required": ["product", "defendant", "injury", "confidence", "is_product_liability", "notes"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are an expert legal analyst specializing in product liability and mass tort litigation.

Your task is to extract structured information from court case titles and documents.

Rules:
1. Focus on identifying the PRODUCT (drug, device, chemical, consumer product) and the DEFENDANT (manufacturer/company).
2. Identify the alleged INJURY or harm.
3. Ignore plaintiff names - they are not relevant.
4. If information is not clearly stated, use "unknown" rather than guessing.
5. Set is_product_liability=false if this doesn't appear to be a product liability case.
6. Confidence should reflect how certain you are about the extraction:
   - 0.9-1.0: Clear, explicit mentions
   - 0.7-0.9: Implied or partially stated
   - 0.5-0.7: Inferred from context
   - <0.5: Guessing

Examples of product liability cases:
- "Smith v. Bayer Corp" (defendant: Bayer, product: likely pharmaceutical)
- "Johnson v. 3M Company - Combat Earplugs" (defendant: 3M, product: Combat Earplugs)
- Drug injury cases, medical device failures, toxic exposure, etc."""


class EntityExtractor:
    """Extract entities from text using OpenAI's API."""

    def __init__(self):
        config = get_config()
        self.api_key = config.openai.api_key
        self.model = config.openai.model
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def extract(self, text: str) -> ExtractedEntities:
        """
        Extract entities from text (e.g., case title + complaint snippet).

        Args:
            text: The text to extract entities from

        Returns:
            ExtractedEntities object

        Raises:
            Exception if API call fails
        """
        # Truncate very long text
        if len(text) > 4000:
            text = text[:4000] + "..."

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract entities from this text:\n\n{text}"},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "tort_entities",
                    "strict": True,
                    "schema": EXTRACTION_SCHEMA,
                },
            },
            "temperature": 0.1,  # Low temperature for consistent extraction
        }

        response = self.session.post(
            OPENAI_API_URL,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        return ExtractedEntities(
            product=parsed["product"],
            defendant=parsed["defendant"],
            injury=parsed["injury"],
            confidence=float(parsed["confidence"]),
            notes=parsed["notes"],
            is_product_liability=bool(parsed["is_product_liability"]),
        )

    def extract_batch(
        self,
        texts: list[str],
        skip_on_error: bool = True,
    ) -> list[ExtractedEntities | None]:
        """
        Extract entities from multiple texts.

        Args:
            texts: List of texts to extract from
            skip_on_error: If True, return None for failed extractions

        Returns:
            List of ExtractedEntities (or None for failures if skip_on_error)
        """
        results = []
        for i, text in enumerate(texts):
            try:
                result = self.extract(text)
                results.append(result)
            except Exception as e:
                logger.warning(f"Extraction failed for text {i}: {e}")
                if skip_on_error:
                    results.append(None)
                else:
                    raise

        return results
