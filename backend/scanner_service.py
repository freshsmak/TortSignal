"""
Scanner Service - Orchestrates all scanning operations
Runs regulatory, PubMed, and epidemiology scans, then saves to database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanners.regulatory import RegulatoryScanner
from integrations.pubmed import PubMedIntegration
from integrations.epidemiology import EpidemiologyIntegration
from scoring.bradford_hill import BradfordHillScorer
from scoring.litigation import LitigationScorer
from persistence import DataPersistence
from datetime import datetime
from typing import Dict, List, Optional


class ScannerService:
    """
    Orchestrates all EDE scanning operations
    """

    def __init__(self):
        self.regulatory_scanner = RegulatoryScanner()
        self.pubmed = PubMedIntegration()
        self.epidemiology = EpidemiologyIntegration()
        self.bradford_hill_scorer = BradfordHillScorer()
        self.litigation_scorer = LitigationScorer()
        self.db = DataPersistence()

    def scan_regulatory(self, days_back: int = 30) -> Dict:
        """
        Run regulatory scan and save results to database

        Returns:
            Summary of scan results
        """
        print(f"\n{'='*80}")
        print(f"REGULATORY SCAN (last {days_back} days)")
        print(f"{'='*80}\n")

        results = self.regulatory_scanner.scan_all(days_back)

        # Process divergence signals (EU banned but US allows = HIGH PRIORITY)
        signals_created = 0
        actions_saved = 0

        for signal in results.get('divergence_signals', []):
            # Generate signal ID
            chemical_slug = signal['chemical'].replace(' ', '').replace(',', '')[:15]
            signal_id = f"HAZ-{datetime.now().year}-{chemical_slug}"

            # Create signal in database
            self.db.create_or_update_signal(
                signal_id=signal_id,
                chemical=signal['chemical'],
                disease="Unknown",  # Will be determined via PubMed/epidemiology
                methodology='HAZARD_FIRST',
                status='DETECTED'
            )
            signals_created += 1

            # Save regulatory action
            self.db.save_regulatory_actions(signal_id, [signal])
            actions_saved += 1

        print(f"\n[SCAN COMPLETE]")
        print(f"  Signals Created: {signals_created}")
        print(f"  Regulatory Actions Saved: {actions_saved}")

        return {
            'signals_created': signals_created,
            'actions_saved': actions_saved,
            'total_actions': len(results.get('eu_echa', [])) + len(results.get('iarc', [])) + len(results.get('fda', [])) + len(results.get('niosh', []))
        }

    def scan_signal_evidence(
        self,
        signal_id: str,
        chemical: str,
        disease: str,
        max_papers: int = 50
    ) -> Dict:
        """
        Scan PubMed for evidence for a specific signal

        Args:
            signal_id: Signal ID
            chemical: Chemical name
            disease: Disease name
            max_papers: Maximum papers to retrieve

        Returns:
            Summary of papers found and saved
        """
        print(f"\n{'='*80}")
        print(f"PUBMED EVIDENCE SCAN: {chemical} → {disease}")
        print(f"{'='*80}\n")

        # Search PubMed
        results = self.pubmed.search_all(chemical, disease, max_papers)

        # Save papers to database
        all_papers = (
            results.get('mechanistic', []) +
            results.get('epidemiology', []) +
            results.get('case_reports', []) +
            results.get('reviews', [])
        )

        papers_saved = self.db.save_pubmed_papers(signal_id, all_papers)

        print(f"\n[SCAN COMPLETE]")
        print(f"  Papers Found: {results['summary']['total_papers']}")
        print(f"  Papers Saved: {papers_saved}")

        return {
            'papers_found': results['summary']['total_papers'],
            'papers_saved': papers_saved,
            'mechanistic': results['summary']['mechanistic_count'],
            'epidemiology': results['summary']['epidemiology_count']
        }

    def scan_signal_epidemiology(
        self,
        signal_id: str,
        chemical: str,
        disease: str,
        disease_icd10: str,
        exposure_start_year: int,
        exposure_peak_year: int,
        expected_latency: int = 10
    ) -> Dict:
        """
        Run epidemiology scan and validation for a signal

        Args:
            signal_id: Signal ID
            chemical: Chemical name
            disease: Disease name
            disease_icd10: ICD-10 code for disease
            exposure_start_year: When exposure began
            exposure_peak_year: When exposure was widespread
            expected_latency: Expected disease latency (years)

        Returns:
            Epidemiology results with temporality assessment
        """
        print(f"\n{'='*80}")
        print(f"EPIDEMIOLOGY VALIDATION: {chemical} → {disease}")
        print(f"{'='*80}\n")

        # Run epidemiology analysis
        result = self.epidemiology.analyze_disease_signal(
            disease=disease,
            disease_icd10_code=disease_icd10,
            exposure_start_year=exposure_start_year,
            exposure_peak_year=exposure_peak_year,
            expected_latency=expected_latency
        )

        # Convert trend object to dict for database
        trend = result['trend']
        trend_dict = {
            'disease': trend.disease,
            'years': trend.years,
            'rates': trend.rates,
            'counts': trend.counts,
            'data_source': trend.data_source,
            'trend_direction': trend.trend_direction,
            'percent_change': trend.percent_change
        }

        # Save to database
        self.db.save_epidemiology_validation(
            signal_id=signal_id,
            data_source='CDC_WONDER',
            disease=disease,
            disease_trend=trend_dict,
            temporality_assessment=result['temporality_assessment']
        )

        print(f"\n[SCAN COMPLETE]")
        print(f"  Temporality Score: {result['bradford_hill_temporality_score']}/10")
        print(f"  Validation: {result['temporality_assessment']['interpretation']}")

        return {
            'temporality_score': result['bradford_hill_temporality_score'],
            'temporality_valid': result['temporality_assessment']['temporality_valid'],
            'trend_direction': trend.trend_direction,
            'percent_change': trend.percent_change
        }

    def scan_full_signal(
        self,
        signal_id: str,
        chemical: str,
        disease: str,
        disease_icd10: str,
        exposure_start_year: int,
        exposure_peak_year: int
    ) -> Dict:
        """
        Complete signal scan: evidence + epidemiology + scoring

        Returns:
            Complete signal analysis
        """
        print(f"\n{'='*80}")
        print(f"FULL SIGNAL SCAN: {signal_id}")
        print(f"{'='*80}\n")

        # 1. Scan evidence
        evidence_results = self.scan_signal_evidence(signal_id, chemical, disease)

        # 2. Scan epidemiology
        epi_results = self.scan_signal_epidemiology(
            signal_id,
            chemical,
            disease,
            disease_icd10,
            exposure_start_year,
            exposure_peak_year
        )

        print(f"\n✅ FULL SIGNAL SCAN COMPLETE: {signal_id}")

        return {
            'evidence': evidence_results,
            'epidemiology': epi_results
        }


if __name__ == "__main__":
    # Test the scanner service
    print("\n" + "="*80)
    print("SCANNER SERVICE TEST")
    print("="*80)

    scanner = ScannerService()

    # Test 1: Regulatory scan
    print("\n\nTest 1: Regulatory Scan")
    reg_results = scanner.scan_regulatory(days_back=365)

    # Test 2: Full signal scan (using HAZ-2026-001 from seed data)
    print("\n\nTest 2: Full Signal Scan (TiO2 → IBD)")
    signal_results = scanner.scan_full_signal(
        signal_id="HAZ-2026-001",
        chemical="Titanium Dioxide",
        disease="Inflammatory Bowel Disease",
        disease_icd10="K50-K51",
        exposure_start_year=1990,
        exposure_peak_year=2000
    )

    print("\n✅ SCANNER SERVICE TEST COMPLETE")
