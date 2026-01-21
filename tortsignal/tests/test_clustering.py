"""Tests for the candidate builder / clustering module."""

import pytest
from datetime import datetime, timezone

from src.clustering.candidate_builder import (
    CandidateBuilder,
    normalize_text,
    make_candidate_key,
)
from src.models import CaseRecord, ExtractedEntities


class TestNormalization:
    """Test text normalization functions."""

    def test_normalize_text_lowercase(self):
        assert normalize_text("BAYER CORPORATION") == "bayer corporation"

    def test_normalize_text_special_chars(self):
        assert normalize_text("Johnson & Johnson") == "johnson johnson"

    def test_normalize_text_whitespace(self):
        assert normalize_text("  Multiple   Spaces  ") == "multiple spaces"

    def test_normalize_text_empty(self):
        assert normalize_text("") == ""
        assert normalize_text(None) == ""


class TestCandidateKey:
    """Test candidate key generation."""

    def test_make_candidate_key(self):
        key = make_candidate_key("Bayer Corporation", "Roundup")
        assert key == "bayer corporation|roundup"

    def test_make_candidate_key_special_chars(self):
        key = make_candidate_key("Johnson & Johnson", "Tylenol (500mg)")
        assert key == "johnson johnson|tylenol 500mg"


class TestCandidateBuilder:
    """Test the candidate builder."""

    @pytest.fixture
    def builder(self):
        return CandidateBuilder()

    @pytest.fixture
    def sample_case(self):
        return CaseRecord(
            source_uid="TEST-001",
            title="Smith v. Bayer Corp - Roundup Exposure",
            filed_date="2024-06-15",
            jurisdiction="federal",
            state="CA",
            plaintiff_firm="Morgan & Morgan",
            url="https://example.com/case/1",
        )

    @pytest.fixture
    def sample_entities(self):
        return ExtractedEntities(
            product="Roundup",
            defendant="Bayer Corporation",
            injury="Non-Hodgkin Lymphoma",
            confidence=0.95,
            notes="Clear product liability case",
            is_product_liability=True,
        )

    def test_add_case_creates_cluster(self, builder, sample_case, sample_entities):
        key = builder.add_case(sample_case, sample_entities)
        assert key is not None
        assert key == "bayer corporation|roundup"
        assert len(builder.clusters) == 1

    def test_add_case_skips_non_pl(self, builder, sample_case):
        non_pl_entities = ExtractedEntities(
            product="N/A",
            defendant="Unknown",
            injury="Unknown",
            confidence=0.3,
            notes="Not a product liability case",
            is_product_liability=False,
        )
        key = builder.add_case(sample_case, non_pl_entities)
        assert key is None
        assert len(builder.clusters) == 0

    def test_add_multiple_cases_same_cluster(self, builder, sample_entities):
        case1 = CaseRecord(
            source_uid="TEST-001",
            title="Case 1",
            filed_date="2024-06-15",
            jurisdiction="federal",
            state="CA",
            plaintiff_firm="Firm A",
        )
        case2 = CaseRecord(
            source_uid="TEST-002",
            title="Case 2",
            filed_date="2024-06-16",
            jurisdiction="federal",
            state="TX",
            plaintiff_firm="Firm B",
        )

        builder.add_case(case1, sample_entities)
        builder.add_case(case2, sample_entities)

        assert len(builder.clusters) == 1
        cluster = list(builder.clusters.values())[0]
        assert cluster["count"] == 2
        assert len(cluster["states"]) == 2
        assert len(cluster["firms"]) == 2

    def test_build_candidates_scoring(self, builder, sample_case, sample_entities):
        # Add the same case pattern from multiple states/firms
        for i, (state, firm) in enumerate([
            ("CA", "Firm A"),
            ("TX", "Firm B"),
            ("FL", "Firm C"),
            ("NY", "Firm A"),
        ]):
            case = CaseRecord(
                source_uid=f"TEST-{i:03d}",
                title=f"Case {i}",
                filed_date=f"2024-06-{15+i}",
                jurisdiction="federal",
                state=state,
                plaintiff_firm=firm,
            )
            builder.add_case(case, sample_entities)

        candidates = builder.build_candidates()
        assert len(candidates) == 1

        candidate = candidates[0]
        assert candidate.count == 4
        assert candidate.breadth_states == 4
        assert candidate.breadth_firms == 3
        # Score = count * (1 + states) * (1 + firms) = 4 * 5 * 4 = 80
        assert candidate.score_total == 80.0

    def test_injury_label_dominant(self, builder):
        """Test that dominant injury becomes the label."""
        case = CaseRecord(
            source_uid="TEST",
            title="Test",
            filed_date="2024-06-15",
            jurisdiction="federal",
        )

        # Add 5 cases with NHL, 2 with other injuries
        for i in range(5):
            entities = ExtractedEntities(
                product="Roundup",
                defendant="Bayer",
                injury="Non-Hodgkin Lymphoma",
                confidence=0.9,
                notes="",
                is_product_liability=True,
            )
            case.source_uid = f"TEST-NHL-{i}"
            builder.add_case(case, entities)

        for i in range(2):
            entities = ExtractedEntities(
                product="Roundup",
                defendant="Bayer",
                injury="Leukemia",
                confidence=0.9,
                notes="",
                is_product_liability=True,
            )
            case.source_uid = f"TEST-LEU-{i}"
            builder.add_case(case, entities)

        candidates = builder.build_candidates()
        # NHL is 5/7 = 71% > 60% threshold
        assert candidates[0].injury_label == "Non-Hodgkin Lymphoma"

    def test_injury_label_mixed(self, builder):
        """Test that mixed injuries get 'mixed' label."""
        case = CaseRecord(
            source_uid="TEST",
            title="Test",
            filed_date="2024-06-15",
            jurisdiction="federal",
        )

        injuries = ["Cancer A", "Cancer B", "Cancer C", "Cancer D"]
        for i, injury in enumerate(injuries):
            entities = ExtractedEntities(
                product="Product X",
                defendant="Company Y",
                injury=injury,
                confidence=0.9,
                notes="",
                is_product_liability=True,
            )
            case.source_uid = f"TEST-{i}"
            builder.add_case(case, entities)

        candidates = builder.build_candidates()
        # No injury > 60%, should be "mixed"
        assert candidates[0].injury_label == "mixed"
