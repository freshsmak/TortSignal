"""Pytest configuration and shared fixtures."""

import os
import pytest

# Set test environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "postgres://test:test@localhost:5432/tortsignal_test")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("UNICOURT_API_KEY", "test-key")
os.environ.setdefault("UNICOURT_BASE_URL", "https://test.unicourt.com/api/v2")


@pytest.fixture
def sample_case_data():
    """Sample court case data for testing."""
    return {
        "case_id": "UC123456",
        "title": "Smith v. Bayer Corporation - Roundup Herbicide Exposure",
        "filed_date": "2024-06-15",
        "court": {
            "name": "U.S. District Court for the Northern District of California",
            "jurisdiction": "federal",
            "state": "CA",
        },
        "parties": [
            {"name": "John Smith", "side": "plaintiff", "party_type": "individual"},
            {"name": "Bayer Corporation", "side": "defendant", "party_type": "company"},
        ],
        "attorneys": [
            {"name": "Jane Lawyer", "side": "plaintiff", "firm": "Morgan & Morgan"},
        ],
        "claims_text": "Plaintiff alleges exposure to Roundup herbicide caused Non-Hodgkin Lymphoma...",
    }


@pytest.fixture
def sample_faers_data():
    """Sample FAERS adverse event data for testing."""
    return {
        "safetyreportid": "12345678",
        "receivedate": "20240615",
        "patient": {
            "patientsex": "2",
            "patientonsetage": "45",
            "patientonsetageunit": "801",
            "drug": [
                {
                    "drugcharacterization": "1",
                    "medicinalproduct": "OZEMPIC",
                    "openfda": {
                        "brand_name": ["OZEMPIC"],
                        "generic_name": ["SEMAGLUTIDE"],
                    },
                }
            ],
            "reaction": [
                {"reactionmeddrapt": "Gastroparesis"},
                {"reactionmeddrapt": "Nausea"},
            ],
        },
    }


@pytest.fixture
def sample_pubmed_data():
    """Sample PubMed article data for testing."""
    return {
        "pmid": "12345678",
        "title": "Association between glyphosate exposure and non-Hodgkin lymphoma: a meta-analysis",
        "abstract": "Background: Several epidemiological studies have examined...",
        "journal": "International Journal of Cancer",
        "pub_date": "2024-03-15",
        "publication_types": ["Meta-Analysis", "Review"],
        "authors": [{"name": "Smith J", "affiliation": "University of California"}],
        "mesh_terms": ["Glyphosate/adverse effects", "Lymphoma, Non-Hodgkin/chemically induced"],
        "chemicals": ["Glyphosate"],
    }
