"""
LLM-Enhanced PubMed Extraction

Addresses robustness gap #4: Evidence extraction improvements

Enhances the existing PubMed integration with LLM-based analysis for:
1. Accurate paper classification (RCT, cohort, case-control, mechanistic, review)
2. Structured extraction of effect sizes, confidence intervals, p-values
3. Mechanistic pathway extraction
4. Study quality assessment
5. Key findings and limitations identification

Uses Claude API (Anthropic) for structured extraction from abstracts and full text.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
import anthropic


class StudyType(Enum):
    """Study design types (evidence hierarchy)"""
    SYSTEMATIC_REVIEW = "systematic_review"  # Highest
    META_ANALYSIS = "meta_analysis"
    RCT = "randomized_controlled_trial"
    COHORT = "cohort"
    CASE_CONTROL = "case_control"
    CROSS_SECTIONAL = "cross_sectional"
    MECHANISTIC = "mechanistic"
    ANIMAL_MODEL = "animal_model"
    IN_VITRO = "in_vitro"
    CASE_REPORT = "case_report"  # Lowest
    REVIEW = "review"
    OTHER = "other"


@dataclass
class EffectSize:
    """Extracted effect size measurement"""
    measure_type: str  # "OR", "RR", "HR", "SMD", "beta"
    point_estimate: float
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    p_value: Optional[float] = None
    sample_size: Optional[int] = None
    adjustment: str = "unadjusted"  # "unadjusted", "adjusted", "fully_adjusted"


@dataclass
class MechanisticPathway:
    """Extracted mechanistic pathway"""
    pathway_name: str  # e.g., "NLRP3 inflammasome activation"
    molecules_involved: List[str]  # e.g., ["IL-1β", "caspase-1", "ASC"]
    upstream_triggers: List[str]  # e.g., ["TiO2 nanoparticles", "ROS"]
    downstream_effects: List[str]  # e.g., ["pyroptosis", "IL-1β release"]
    evidence_strength: str = "moderate"  # "weak", "moderate", "strong"


@dataclass
class StudyQuality:
    """Study quality assessment"""
    sample_size_adequate: bool
    confounding_addressed: bool
    exposure_assessment: str  # "poor", "fair", "good", "excellent"
    outcome_assessment: str
    follow_up_adequate: bool
    bias_risk: str  # "low", "moderate", "high", "unclear"
    overall_quality: str  # "poor", "fair", "good", "excellent"


@dataclass
class EnhancedPubMedPaper:
    """PubMed paper with LLM-enhanced extraction"""
    pmid: str
    title: str
    abstract: str
    authors: List[str]
    journal: str
    year: int

    # LLM-extracted fields
    study_type: StudyType
    study_type_confidence: float  # 0-1

    # Effect sizes (for epidemiology papers)
    effect_sizes: List[EffectSize]

    # Mechanistic evidence (for mechanistic papers)
    mechanistic_pathways: List[MechanisticPathway]

    # Quality assessment
    study_quality: Optional[StudyQuality] = None

    # Key findings
    key_findings: List[str] = None
    limitations: List[str] = None

    # Bradford Hill relevance
    relevance_to_bh_criteria: Dict[str, str] = None  # criterion -> evidence

    def __post_init__(self):
        if self.key_findings is None:
            self.key_findings = []
        if self.limitations is None:
            self.limitations = []
        if self.relevance_to_bh_criteria is None:
            self.relevance_to_bh_criteria = {}


class LLMPubMedExtractor:
    """
    LLM-powered PubMed evidence extractor

    Uses Claude to extract structured data from abstracts and full text
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM extractor

        Args:
            api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def enhance_paper(
        self,
        paper: Dict,
        chemical: str,
        disease: str
    ) -> EnhancedPubMedPaper:
        """
        Enhance PubMed paper with LLM-based extraction

        Args:
            paper: Basic PubMed paper data (from existing integration)
            chemical: Chemical name (for context)
            disease: Disease name (for context)

        Returns:
            Enhanced paper with structured extraction
        """
        # Step 1: Classify study type
        study_type, type_confidence = self._classify_study_type(paper)

        # Step 2: Extract based on study type
        if study_type in [StudyType.COHORT, StudyType.CASE_CONTROL, StudyType.CROSS_SECTIONAL, StudyType.RCT]:
            effect_sizes = self._extract_effect_sizes(paper)
        else:
            effect_sizes = []

        if study_type in [StudyType.MECHANISTIC, StudyType.ANIMAL_MODEL, StudyType.IN_VITRO]:
            pathways = self._extract_mechanistic_pathways(paper, chemical, disease)
        else:
            pathways = []

        # Step 3: Assess study quality
        quality = self._assess_study_quality(paper, study_type)

        # Step 4: Extract key findings and limitations
        findings, limitations = self._extract_findings_and_limitations(paper)

        # Step 5: Map to Bradford Hill criteria
        bh_relevance = self._map_to_bradford_hill(paper, study_type, chemical, disease)

        return EnhancedPubMedPaper(
            pmid=paper.get('pmid', 'unknown'),
            title=paper.get('title', ''),
            abstract=paper.get('abstract', ''),
            authors=paper.get('authors', []),
            journal=paper.get('journal', ''),
            year=paper.get('year', 2024),
            study_type=study_type,
            study_type_confidence=type_confidence,
            effect_sizes=effect_sizes,
            mechanistic_pathways=pathways,
            study_quality=quality,
            key_findings=findings,
            limitations=limitations,
            relevance_to_bh_criteria=bh_relevance
        )

    def _classify_study_type(self, paper: Dict) -> Tuple[StudyType, float]:
        """
        Classify study design using LLM

        Returns: (StudyType, confidence_score)
        """
        prompt = f"""Classify the study design of this research paper.

Title: {paper.get('title', '')}

Abstract: {paper.get('abstract', '')}

Classify as one of:
- systematic_review: Systematic review or meta-analysis
- randomized_controlled_trial: RCT with randomization
- cohort: Prospective or retrospective cohort study
- case_control: Case-control study
- cross_sectional: Cross-sectional study
- mechanistic: Mechanistic study (pathway analysis)
- animal_model: Animal model study
- in_vitro: In vitro / cell culture study
- case_report: Single case or case series
- review: Narrative review (not systematic)
- other: Other study type

Return JSON:
{{
  "study_type": "...",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON from response
            json_match = content[content.find('{'):content.rfind('}')+1]
            result = json.loads(json_match)

            study_type_str = result['study_type']
            confidence = float(result.get('confidence', 0.7))

            # Map to enum
            type_map = {
                'systematic_review': StudyType.SYSTEMATIC_REVIEW,
                'meta_analysis': StudyType.META_ANALYSIS,
                'randomized_controlled_trial': StudyType.RCT,
                'cohort': StudyType.COHORT,
                'case_control': StudyType.CASE_CONTROL,
                'cross_sectional': StudyType.CROSS_SECTIONAL,
                'mechanistic': StudyType.MECHANISTIC,
                'animal_model': StudyType.ANIMAL_MODEL,
                'in_vitro': StudyType.IN_VITRO,
                'case_report': StudyType.CASE_REPORT,
                'review': StudyType.REVIEW,
                'other': StudyType.OTHER
            }

            study_type = type_map.get(study_type_str, StudyType.OTHER)

            return study_type, confidence

        except Exception as e:
            print(f"[LLM] Classification error: {e}")
            # Fallback to heuristic
            return self._heuristic_classify(paper), 0.5

    def _extract_effect_sizes(self, paper: Dict) -> List[EffectSize]:
        """
        Extract effect sizes using LLM

        Returns: List of EffectSize objects
        """
        prompt = f"""Extract all effect size measurements from this epidemiology paper.

Title: {paper.get('title', '')}

Abstract: {paper.get('abstract', '')}

Extract all reported effect sizes (odds ratios, relative risks, hazard ratios, etc.)

Return JSON array:
[
  {{
    "measure_type": "OR" or "RR" or "HR" or "SMD",
    "point_estimate": float,
    "ci_lower": float or null,
    "ci_upper": float or null,
    "p_value": float or null,
    "sample_size": int or null,
    "adjustment": "unadjusted" or "adjusted" or "fully_adjusted",
    "context": "brief description of what this measures"
  }},
  ...
]

If no effect sizes found, return []"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON array
            json_match = content[content.find('['):content.rfind(']')+1]
            results = json.loads(json_match)

            effect_sizes = []
            for item in results:
                effect_size = EffectSize(
                    measure_type=item['measure_type'],
                    point_estimate=float(item['point_estimate']),
                    confidence_interval_lower=float(item['ci_lower']) if item.get('ci_lower') else None,
                    confidence_interval_upper=float(item['ci_upper']) if item.get('ci_upper') else None,
                    p_value=float(item['p_value']) if item.get('p_value') else None,
                    sample_size=int(item['sample_size']) if item.get('sample_size') else None,
                    adjustment=item.get('adjustment', 'unadjusted')
                )
                effect_sizes.append(effect_size)

            return effect_sizes

        except Exception as e:
            print(f"[LLM] Effect size extraction error: {e}")
            return []

    def _extract_mechanistic_pathways(
        self,
        paper: Dict,
        chemical: str,
        disease: str
    ) -> List[MechanisticPathway]:
        """
        Extract mechanistic pathways using LLM

        Returns: List of MechanisticPathway objects
        """
        prompt = f"""Extract mechanistic pathways linking {chemical} to {disease} from this paper.

Title: {paper.get('title', '')}

Abstract: {paper.get('abstract', '')}

Extract all mechanistic pathways described. For each pathway:
- Pathway name (e.g., "NLRP3 inflammasome activation")
- Key molecules involved
- Upstream triggers
- Downstream effects
- Evidence strength (weak, moderate, strong)

Return JSON array:
[
  {{
    "pathway_name": "...",
    "molecules": ["...", "..."],
    "upstream_triggers": ["...", "..."],
    "downstream_effects": ["...", "..."],
    "evidence_strength": "weak" or "moderate" or "strong"
  }},
  ...
]

If no clear mechanistic pathways, return []"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON array
            json_match = content[content.find('['):content.rfind(']')+1]
            results = json.loads(json_match)

            pathways = []
            for item in results:
                pathway = MechanisticPathway(
                    pathway_name=item['pathway_name'],
                    molecules_involved=item.get('molecules', []),
                    upstream_triggers=item.get('upstream_triggers', []),
                    downstream_effects=item.get('downstream_effects', []),
                    evidence_strength=item.get('evidence_strength', 'moderate')
                )
                pathways.append(pathway)

            return pathways

        except Exception as e:
            print(f"[LLM] Pathway extraction error: {e}")
            return []

    def _assess_study_quality(
        self,
        paper: Dict,
        study_type: StudyType
    ) -> Optional[StudyQuality]:
        """
        Assess study quality using LLM

        Returns: StudyQuality assessment
        """
        if study_type == StudyType.CASE_REPORT:
            # Skip quality assessment for case reports
            return None

        prompt = f"""Assess the quality of this research study.

Title: {paper.get('title', '')}

Abstract: {paper.get('abstract', '')}

Study Type: {study_type.value}

Assess:
1. Sample size adequate for study type
2. Confounding addressed (adjusted analysis)
3. Exposure assessment quality (poor/fair/good/excellent)
4. Outcome assessment quality (poor/fair/good/excellent)
5. Follow-up adequate (if applicable)
6. Risk of bias (low/moderate/high/unclear)
7. Overall quality (poor/fair/good/excellent)

Return JSON:
{{
  "sample_size_adequate": true/false,
  "confounding_addressed": true/false,
  "exposure_assessment": "...",
  "outcome_assessment": "...",
  "follow_up_adequate": true/false,
  "bias_risk": "...",
  "overall_quality": "...",
  "reasoning": "brief explanation"
}}"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON
            json_match = content[content.find('{'):content.rfind('}')+1]
            result = json.loads(json_match)

            return StudyQuality(
                sample_size_adequate=result['sample_size_adequate'],
                confounding_addressed=result['confounding_addressed'],
                exposure_assessment=result['exposure_assessment'],
                outcome_assessment=result['outcome_assessment'],
                follow_up_adequate=result['follow_up_adequate'],
                bias_risk=result['bias_risk'],
                overall_quality=result['overall_quality']
            )

        except Exception as e:
            print(f"[LLM] Quality assessment error: {e}")
            return None

    def _extract_findings_and_limitations(
        self,
        paper: Dict
    ) -> Tuple[List[str], List[str]]:
        """
        Extract key findings and limitations

        Returns: (findings, limitations)
        """
        prompt = f"""Summarize the key findings and limitations of this paper.

Title: {paper.get('title', '')}

Abstract: {paper.get('abstract', '')}

Return JSON:
{{
  "key_findings": ["finding 1", "finding 2", ...],
  "limitations": ["limitation 1", "limitation 2", ...]
}}"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON
            json_match = content[content.find('{'):content.rfind('}')+1]
            result = json.loads(json_match)

            findings = result.get('key_findings', [])
            limitations = result.get('limitations', [])

            return findings, limitations

        except Exception as e:
            print(f"[LLM] Findings extraction error: {e}")
            return [], []

    def _map_to_bradford_hill(
        self,
        paper: Dict,
        study_type: StudyType,
        chemical: str,
        disease: str
    ) -> Dict[str, str]:
        """
        Map paper evidence to Bradford Hill criteria

        Returns: Dictionary mapping criteria to evidence
        """
        prompt = f"""Map the evidence in this paper to Bradford Hill criteria for causation.

Paper Title: {paper.get('title', '')}
Abstract: {paper.get('abstract', '')}

Chemical: {chemical}
Disease: {disease}
Study Type: {study_type.value}

Bradford Hill Criteria:
1. Strength (effect size)
2. Consistency (replicates other studies)
3. Specificity (specific exposure-disease link)
4. Temporality (exposure precedes disease)
5. Biological Gradient (dose-response)
6. Plausibility (biological mechanism)
7. Coherence (fits with existing knowledge)
8. Experiment (intervention/removal reduces disease)
9. Analogy (similar exposures cause similar diseases)

For each criterion where this paper provides evidence, return:
{{
  "criterion_name": "brief description of evidence from this paper",
  ...
}}

Only include criteria where paper provides relevant evidence.
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON
            json_match = content[content.find('{'):content.rfind('}')+1]
            result = json.loads(json_match)

            return result

        except Exception as e:
            print(f"[LLM] BH mapping error: {e}")
            return {}

    def _heuristic_classify(self, paper: Dict) -> StudyType:
        """Fallback heuristic classification"""
        title_lower = paper.get('title', '').lower()
        abstract_lower = paper.get('abstract', '').lower()

        if 'systematic review' in title_lower or 'meta-analysis' in title_lower:
            return StudyType.SYSTEMATIC_REVIEW
        elif 'randomized' in abstract_lower or 'placebo' in abstract_lower:
            return StudyType.RCT
        elif 'cohort' in abstract_lower:
            return StudyType.COHORT
        elif 'case-control' in abstract_lower:
            return StudyType.CASE_CONTROL
        elif 'cross-sectional' in abstract_lower:
            return StudyType.CROSS_SECTIONAL
        elif any(word in abstract_lower for word in ['pathway', 'mechanism', 'molecular']):
            return StudyType.MECHANISTIC
        elif 'mice' in abstract_lower or 'rats' in abstract_lower:
            return StudyType.ANIMAL_MODEL
        elif 'case report' in title_lower:
            return StudyType.CASE_REPORT
        elif 'review' in title_lower:
            return StudyType.REVIEW
        else:
            return StudyType.OTHER


# Convenience function
def enhance_pubmed_results(
    papers: List[Dict],
    chemical: str,
    disease: str,
    api_key: Optional[str] = None
) -> List[EnhancedPubMedPaper]:
    """
    Enhance a list of PubMed papers with LLM extraction

    Args:
        papers: List of basic PubMed papers
        chemical: Chemical name
        disease: Disease name
        api_key: Optional Anthropic API key

    Returns:
        List of enhanced papers
    """
    extractor = LLMPubMedExtractor(api_key)

    enhanced = []
    for paper in papers:
        try:
            enhanced_paper = extractor.enhance_paper(paper, chemical, disease)
            enhanced.append(enhanced_paper)
        except Exception as e:
            print(f"[LLM] Error enhancing paper {paper.get('pmid', 'unknown')}: {e}")
            continue

    return enhanced


if __name__ == "__main__":
    # Test LLM-enhanced extraction
    print("\n" + "="*80)
    print("LLM-ENHANCED PUBMED EXTRACTION TEST")
    print("="*80)

    # Mock paper for testing
    test_paper = {
        'pmid': '12345678',
        'title': 'Association between titanium dioxide exposure and inflammatory bowel disease: a cohort study',
        'abstract': '''
        Background: Titanium dioxide (TiO2) nanoparticles are widely used as food additives.
        Recent mechanistic studies suggest TiO2 may trigger intestinal inflammation.

        Methods: We conducted a prospective cohort study of 50,000 adults over 10 years.
        Dietary TiO2 exposure was assessed via food frequency questionnaires.

        Results: We identified 500 incident IBD cases. After adjusting for age, sex, smoking,
        and diet, high TiO2 exposure (>10mg/day) was associated with increased IBD risk
        (HR 1.65, 95% CI 1.32-2.05, p<0.001). A dose-response relationship was observed.

        Limitations: Self-reported dietary data. No biomarker measurements.

        Conclusions: TiO2 exposure may increase IBD risk. Mechanistic studies needed.
        ''',
        'authors': ['Smith J', 'Jones A', 'Brown B'],
        'journal': 'Gut',
        'year': 2023
    }

    try:
        extractor = LLMPubMedExtractor()

        print("\n--- Enhancing Paper ---")
        enhanced = extractor.enhance_paper(test_paper, "titanium dioxide", "inflammatory bowel disease")

        print(f"\nStudy Type: {enhanced.study_type.value} (confidence: {enhanced.study_type_confidence:.1%})")
        print(f"\nEffect Sizes: {len(enhanced.effect_sizes)}")
        for es in enhanced.effect_sizes:
            print(f"  - {es.measure_type} {es.point_estimate:.2f} ({es.confidence_interval_lower:.2f}-{es.confidence_interval_upper:.2f})")

        print(f"\nKey Findings: {len(enhanced.key_findings)}")
        for finding in enhanced.key_findings[:3]:
            print(f"  - {finding}")

        print(f"\nBradford Hill Evidence:")
        for criterion, evidence in enhanced.relevance_to_bh_criteria.items():
            print(f"  {criterion}: {evidence}")

        print("\n✅ LLM-ENHANCED EXTRACTION TEST COMPLETE")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Note: Requires ANTHROPIC_API_KEY environment variable")
