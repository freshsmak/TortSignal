"""
PubMed Integration - Mechanistic and Epidemiological Evidence Gathering
Part of EDE Hazard-First methodology (Step 2: Mechanism Search) and Epidemiology-First (Step 1: Literature Search)
"""

from Bio import Entrez
from typing import List, Dict, Optional
import time
import re
from datetime import datetime


class PubMedIntegration:
    """
    Integrates with NCBI E-utilities API to search PubMed for:
    1. Mechanistic evidence (pathways, mechanisms of action)
    2. Epidemiological evidence (cohort studies, case-control studies)
    3. Case reports
    4. Review articles

    Automatically classifies papers and extracts key evidence
    """

    def __init__(self, email: str = "ede@example.com"):
        """
        Initialize PubMed integration

        Args:
            email: Required by NCBI for E-utilities API (identifies your application)
        """
        Entrez.email = email
        self.rate_limit_delay = 0.34  # NCBI allows 3 requests/second with API key, 10/sec with key

    def search_all(self, chemical: str, disease: str, max_results: int = 200) -> Dict[str, List[Dict]]:
        """
        Comprehensive search for all evidence types

        Args:
            chemical: Chemical name (e.g., "Titanium Dioxide")
            disease: Disease name (e.g., "Inflammatory Bowel Disease")
            max_results: Maximum papers per category

        Returns:
            Dictionary with categorized papers
        """
        results = {
            'mechanistic': self.search_mechanistic(chemical, disease, max_results),
            'epidemiology': self.search_epidemiology(chemical, disease, max_results),
            'case_reports': self.search_case_reports(chemical, disease, max_results),
            'reviews': self.search_reviews(chemical, disease, max_results)
        }

        # Summary statistics
        results['summary'] = {
            'total_papers': sum(len(papers) for papers in results.values() if isinstance(papers, list)),
            'mechanistic_count': len(results['mechanistic']),
            'epidemiology_count': len(results['epidemiology']),
            'case_reports_count': len(results['case_reports']),
            'reviews_count': len(results['reviews'])
        }

        print(f"\n[PUBMED] Search complete: {results['summary']['total_papers']} papers found")
        print(f"  Mechanistic: {results['summary']['mechanistic_count']}")
        print(f"  Epidemiology: {results['summary']['epidemiology_count']}")
        print(f"  Case Reports: {results['summary']['case_reports_count']}")
        print(f"  Reviews: {results['summary']['reviews_count']}")

        return results

    def search_mechanistic(self, chemical: str, disease: str, max_results: int = 200) -> List[Dict]:
        """
        Search for mechanistic papers (pathways, mechanisms of action)

        Query strategy:
        - Include terms: pathway, mechanism, molecular, cellular, inflammatory, oxidative stress, etc.
        - Exclude: human studies, epidemiology, cohort, case-control

        Returns: List of mechanistic papers with extracted evidence
        """
        print(f"\n[PUBMED] Searching mechanistic papers: {chemical} + {disease}")

        # Build query
        query_parts = [
            f'"{chemical}"[Title/Abstract]',
            f'"{disease}"[Title/Abstract]',
            '(',
            'pathway[Title/Abstract] OR',
            'mechanism[Title/Abstract] OR',
            'molecular[Title/Abstract] OR',
            'cellular[Title/Abstract] OR',
            'inflammation[Title/Abstract] OR',
            '"oxidative stress"[Title/Abstract] OR',
            'cytokine[Title/Abstract] OR',
            '"gut microbiome"[Title/Abstract] OR',
            'intestinal[Title/Abstract] OR',
            '"animal model"[Title/Abstract] OR',
            'mice[Title/Abstract] OR',
            'rat[Title/Abstract]',
            ')',
            'NOT (',
            'epidemiology[Title/Abstract] OR',
            'cohort[Title/Abstract] OR',
            '"case-control"[Title/Abstract] OR',
            'cross-sectional[Title/Abstract]',
            ')'
        ]

        query = ' '.join(query_parts)

        papers = self._search_and_fetch(query, max_results)

        # Classify and extract mechanistic evidence
        mechanistic_papers = []
        for paper in papers:
            classification = self._classify_paper(paper)
            if classification == 'MECHANISTIC':
                # Extract mechanistic evidence
                evidence = self._extract_mechanistic_evidence(paper)
                mechanistic_papers.append({
                    **paper,
                    'evidence_type': 'MECHANISTIC',
                    'extracted_evidence': evidence
                })

        print(f"[PUBMED] Found {len(mechanistic_papers)} mechanistic papers")
        return mechanistic_papers

    def search_epidemiology(self, chemical: str, disease: str, max_results: int = 100) -> List[Dict]:
        """
        Search for epidemiological studies (cohort, case-control, cross-sectional)

        Query strategy:
        - Include: cohort, case-control, cross-sectional, risk, odds ratio, hazard ratio
        - Focus on human studies

        Returns: List of epi papers with extracted effect sizes
        """
        print(f"\n[PUBMED] Searching epidemiology papers: {chemical} + {disease}")

        query_parts = [
            f'"{chemical}"[Title/Abstract]',
            f'"{disease}"[Title/Abstract]',
            '(',
            'cohort[Title/Abstract] OR',
            '"case-control"[Title/Abstract] OR',
            'cross-sectional[Title/Abstract] OR',
            '"odds ratio"[Title/Abstract] OR',
            '"hazard ratio"[Title/Abstract] OR',
            '"relative risk"[Title/Abstract] OR',
            'epidemiology[Title/Abstract] OR',
            'incidence[Title/Abstract] OR',
            'prevalence[Title/Abstract]',
            ')',
            'AND humans[MeSH]'
        ]

        query = ' '.join(query_parts)

        papers = self._search_and_fetch(query, max_results)

        # Extract epidemiological evidence
        epi_papers = []
        for paper in papers:
            classification = self._classify_paper(paper)
            if classification in ['EPIDEMIOLOGY', 'CASE_CONTROL', 'COHORT']:
                evidence = self._extract_epidemiological_evidence(paper)
                epi_papers.append({
                    **paper,
                    'evidence_type': classification,
                    'extracted_evidence': evidence
                })

        print(f"[PUBMED] Found {len(epi_papers)} epidemiology papers")
        return epi_papers

    def search_case_reports(self, chemical: str, disease: str, max_results: int = 50) -> List[Dict]:
        """
        Search for case reports (individual patient cases)

        Returns: List of case reports
        """
        print(f"\n[PUBMED] Searching case reports: {chemical} + {disease}")

        query_parts = [
            f'"{chemical}"[Title/Abstract]',
            f'"{disease}"[Title/Abstract]',
            '(',
            '"case report"[Title] OR',
            '"case reports"[Publication Type] OR',
            '"case series"[Title]',
            ')'
        ]

        query = ' '.join(query_parts)

        papers = self._search_and_fetch(query, max_results)

        case_reports = []
        for paper in papers:
            case_reports.append({
                **paper,
                'evidence_type': 'CASE_REPORT'
            })

        print(f"[PUBMED] Found {len(case_reports)} case reports")
        return case_reports

    def search_reviews(self, chemical: str, disease: str, max_results: int = 20) -> List[Dict]:
        """
        Search for systematic reviews and meta-analyses

        Returns: List of review papers
        """
        print(f"\n[PUBMED] Searching reviews: {chemical} + {disease}")

        query_parts = [
            f'"{chemical}"[Title/Abstract]',
            f'"{disease}"[Title/Abstract]',
            '(',
            '"systematic review"[Publication Type] OR',
            '"meta-analysis"[Publication Type] OR',
            'review[Publication Type]',
            ')'
        ]

        query = ' '.join(query_parts)

        papers = self._search_and_fetch(query, max_results)

        reviews = []
        for paper in papers:
            reviews.append({
                **paper,
                'evidence_type': 'REVIEW'
            })

        print(f"[PUBMED] Found {len(reviews)} review papers")
        return reviews

    # ============================================================================
    # Internal Methods
    # ============================================================================

    def _search_and_fetch(self, query: str, max_results: int) -> List[Dict]:
        """
        Execute PubMed search and fetch paper details

        Returns: List of papers with metadata and abstracts
        """
        try:
            # Step 1: Search for PMIDs
            time.sleep(self.rate_limit_delay)
            handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance")
            search_results = Entrez.read(handle)
            handle.close()

            pmids = search_results['IdList']

            if not pmids:
                print(f"[PUBMED] No results found for query")
                return []

            print(f"[PUBMED] Found {len(pmids)} PMIDs, fetching details...")

            # Step 2: Fetch paper details in batches (NCBI recommends batches of 500)
            papers = []
            batch_size = 100

            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i+batch_size]

                time.sleep(self.rate_limit_delay)
                handle = Entrez.efetch(
                    db="pubmed",
                    id=batch_pmids,
                    rettype="medline",
                    retmode="xml"
                )

                records = Entrez.read(handle)
                handle.close()

                # Parse each record
                for record in records['PubmedArticle']:
                    paper = self._parse_pubmed_record(record)
                    if paper:
                        papers.append(paper)

            return papers

        except Exception as e:
            print(f"[PUBMED] Error searching: {e}")
            return []

    def _parse_pubmed_record(self, record: Dict) -> Optional[Dict]:
        """
        Parse PubMed XML record into structured dictionary

        Returns: Paper metadata and abstract
        """
        try:
            article = record['MedlineCitation']['Article']

            # Extract PMID
            pmid = str(record['MedlineCitation']['PMID'])

            # Extract title
            title = article.get('ArticleTitle', '')

            # Extract abstract
            abstract_parts = article.get('Abstract', {}).get('AbstractText', [])
            if isinstance(abstract_parts, list):
                abstract = ' '.join(str(part) for part in abstract_parts)
            else:
                abstract = str(abstract_parts)

            # Extract authors
            authors = []
            author_list = article.get('AuthorList', [])
            for author in author_list[:3]:  # First 3 authors
                if 'LastName' in author and 'Initials' in author:
                    authors.append(f"{author['LastName']} {author['Initials']}")

            # Extract journal and date
            journal = article.get('Journal', {})
            journal_title = journal.get('Title', '')

            pub_date = journal.get('JournalIssue', {}).get('PubDate', {})
            year = pub_date.get('Year', '')

            # Extract DOI if available
            doi = None
            article_ids = record['PubmedData'].get('ArticleIdList', [])
            for article_id in article_ids:
                if article_id.attributes.get('IdType') == 'doi':
                    doi = str(article_id)
                    break

            return {
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'journal': journal_title,
                'year': year,
                'doi': doi,
                'pubmed_url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }

        except Exception as e:
            print(f"[PUBMED] Error parsing record: {e}")
            return None

    def _classify_paper(self, paper: Dict) -> str:
        """
        Automatically classify paper type based on title/abstract

        Returns: MECHANISTIC, EPIDEMIOLOGY, COHORT, CASE_CONTROL, CASE_REPORT, REVIEW
        """
        text = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()

        # Case report
        if 'case report' in text or 'case series' in text:
            return 'CASE_REPORT'

        # Review
        if 'systematic review' in text or 'meta-analysis' in text or 'review' in text:
            return 'REVIEW'

        # Epidemiology subtypes
        if 'cohort' in text:
            return 'COHORT'
        if 'case-control' in text or 'case control' in text:
            return 'CASE_CONTROL'
        if any(term in text for term in ['epidemiology', 'odds ratio', 'hazard ratio', 'relative risk', 'incidence', 'prevalence']):
            return 'EPIDEMIOLOGY'

        # Mechanistic (default for lab studies)
        if any(term in text for term in ['mechanism', 'pathway', 'molecular', 'cellular', 'mice', 'rat', 'animal model', 'in vitro', 'cell culture']):
            return 'MECHANISTIC'

        return 'UNKNOWN'

    def _extract_mechanistic_evidence(self, paper: Dict) -> Dict:
        """
        Extract mechanistic evidence from abstract

        Looks for:
        - Pathways mentioned (inflammation, oxidative stress, etc.)
        - Model system (mice, rats, cell culture)
        - Effect direction (increased, decreased)
        """
        abstract = paper.get('abstract', '').lower()
        title = paper.get('title', '').lower()
        text = title + ' ' + abstract

        evidence = {
            'pathways': [],
            'model_system': None,
            'effect_direction': None,
            'key_findings': []
        }

        # Detect pathways
        pathway_keywords = {
            'inflammation': ['inflammation', 'inflammatory', 'cytokine', 'il-6', 'tnf', 'nf-kb'],
            'oxidative_stress': ['oxidative stress', 'ros', 'reactive oxygen', 'lipid peroxidation'],
            'microbiome': ['microbiome', 'gut bacteria', 'dysbiosis', 'microbiota'],
            'barrier_dysfunction': ['barrier', 'permeability', 'tight junction', 'intestinal barrier'],
            'immune_dysregulation': ['immune', 'lymphocyte', 't cell', 'macrophage']
        }

        for pathway, keywords in pathway_keywords.items():
            if any(kw in text for kw in keywords):
                evidence['pathways'].append(pathway)

        # Detect model system
        if 'mice' in text or 'mouse' in text:
            evidence['model_system'] = 'mice'
        elif 'rat' in text:
            evidence['model_system'] = 'rat'
        elif 'cell culture' in text or 'in vitro' in text:
            evidence['model_system'] = 'in_vitro'
        elif 'human' in text:
            evidence['model_system'] = 'human'

        # Detect effect direction
        if any(term in text for term in ['increased', 'elevated', 'higher', 'enhanced', 'induced']):
            evidence['effect_direction'] = 'increased'
        elif any(term in text for term in ['decreased', 'reduced', 'lower', 'inhibited']):
            evidence['effect_direction'] = 'decreased'

        # Extract key findings (sentences with chemical + disease + effect)
        sentences = abstract.split('.')
        for sentence in sentences[:5]:  # First 5 sentences
            if len(sentence) > 50 and any(term in sentence.lower() for term in ['caused', 'induced', 'associated', 'resulted', 'led to']):
                evidence['key_findings'].append(sentence.strip())

        return evidence

    def _extract_epidemiological_evidence(self, paper: Dict) -> Dict:
        """
        Extract epidemiological evidence from abstract

        Looks for:
        - Effect size (OR, RR, HR)
        - Sample size
        - Study design
        - Confidence interval
        """
        abstract = paper.get('abstract', '').lower()
        title = paper.get('title', '').lower()
        text = title + ' ' + abstract

        evidence = {
            'study_design': None,
            'sample_size': None,
            'effect_size': None,
            'effect_size_type': None,
            'confidence_interval': None,
            'p_value': None
        }

        # Detect study design
        if 'cohort' in text:
            evidence['study_design'] = 'cohort'
        elif 'case-control' in text or 'case control' in text:
            evidence['study_design'] = 'case-control'
        elif 'cross-sectional' in text:
            evidence['study_design'] = 'cross-sectional'
        elif 'randomized' in text:
            evidence['study_design'] = 'RCT'

        # Extract sample size (look for "n = 1234" or "1234 participants")
        sample_patterns = [
            r'n\s*=\s*(\d+(?:,\d+)?)',
            r'(\d+(?:,\d+)?)\s+(?:participants|patients|subjects|individuals)'
        ]

        for pattern in sample_patterns:
            match = re.search(pattern, text)
            if match:
                sample_str = match.group(1).replace(',', '')
                evidence['sample_size'] = int(sample_str)
                break

        # Extract effect size (OR, RR, HR)
        effect_patterns = [
            (r'odds ratio[:\s]+(\d+\.?\d*)', 'OR'),
            (r'or[:\s]=?\s*(\d+\.?\d*)', 'OR'),
            (r'relative risk[:\s]+(\d+\.?\d*)', 'RR'),
            (r'rr[:\s]=?\s*(\d+\.?\d*)', 'RR'),
            (r'hazard ratio[:\s]+(\d+\.?\d*)', 'HR'),
            (r'hr[:\s]=?\s*(\d+\.?\d*)', 'HR')
        ]

        for pattern, effect_type in effect_patterns:
            match = re.search(pattern, text)
            if match:
                evidence['effect_size'] = float(match.group(1))
                evidence['effect_size_type'] = effect_type
                break

        # Extract confidence interval
        ci_pattern = r'(\d+\.?\d*)%\s+ci[:\s]+(\d+\.?\d*)[–-](\d+\.?\d*)'
        ci_match = re.search(ci_pattern, text)
        if ci_match:
            evidence['confidence_interval'] = {
                'level': f"{ci_match.group(1)}%",
                'lower': float(ci_match.group(2)),
                'upper': float(ci_match.group(3))
            }

        # Extract p-value
        p_pattern = r'p\s*[<>=]\s*(\d+\.?\d*(?:e-?\d+)?)'
        p_match = re.search(p_pattern, text)
        if p_match:
            evidence['p_value'] = p_match.group(1)

        return evidence


if __name__ == "__main__":
    # Test the PubMed integration
    pubmed = PubMedIntegration()

    print("\n" + "="*80)
    print("PUBMED INTEGRATION TEST")
    print("="*80 + "\n")

    # Test with TiO2 → IBD
    results = pubmed.search_all(
        chemical="Titanium Dioxide",
        disease="Inflammatory Bowel Disease",
        max_results=50  # Limit for testing
    )

    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    print(f"Total Papers: {results['summary']['total_papers']}")
    print(f"  Mechanistic: {results['summary']['mechanistic_count']}")
    print(f"  Epidemiology: {results['summary']['epidemiology_count']}")
    print(f"  Case Reports: {results['summary']['case_reports_count']}")
    print(f"  Reviews: {results['summary']['reviews_count']}")

    # Show sample mechanistic paper
    if results['mechanistic']:
        print("\n" + "="*80)
        print("SAMPLE MECHANISTIC PAPER")
        print("="*80)
        paper = results['mechanistic'][0]
        print(f"\nTitle: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'])}")
        print(f"Journal: {paper['journal']} ({paper['year']})")
        print(f"PMID: {paper['pmid']}")
        print(f"\nExtracted Evidence:")
        print(f"  Pathways: {', '.join(paper['extracted_evidence']['pathways'])}")
        print(f"  Model: {paper['extracted_evidence']['model_system']}")
        print(f"  Effect: {paper['extracted_evidence']['effect_direction']}")

    # Show sample epidemiology paper
    if results['epidemiology']:
        print("\n" + "="*80)
        print("SAMPLE EPIDEMIOLOGY PAPER")
        print("="*80)
        paper = results['epidemiology'][0]
        print(f"\nTitle: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'])}")
        print(f"Journal: {paper['journal']} ({paper['year']})")
        print(f"PMID: {paper['pmid']}")
        print(f"\nExtracted Evidence:")
        print(f"  Study Design: {paper['extracted_evidence']['study_design']}")
        print(f"  Sample Size: {paper['extracted_evidence']['sample_size']}")
        print(f"  Effect Size: {paper['extracted_evidence']['effect_size']} ({paper['extracted_evidence']['effect_size_type']})")
