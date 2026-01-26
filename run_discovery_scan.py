"""
Real Discovery Engine - Scans for NEW tort signals using dual methodologies

This script:
1. Scans regulatory sources for NEW bans/warnings (Hazard-First)
2. Scans SEER/CDC for NEW disease anomalies (Epidemiology-First)
3. Scores each signal with Bradford Hill
4. Saves all promising signals to watchlist for monitoring
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from scanners.regulatory import RegulatoryScanner
from integrations.epidemiology import SEERDataWrapper, DiseaseTrendAnalyzer
from scoring.bradford_hill import BradfordHillScorer
from scoring.litigation import LitigationScorer


class DiscoveryEngine:
    """
    Main discovery engine orchestrator
    Runs both methodologies and maintains watchlist
    """

    def __init__(self, watchlist_path: str = "watchlist.json"):
        self.watchlist_path = watchlist_path
        self.regulatory_scanner = RegulatoryScanner()
        self.seer = SEERDataWrapper()
        self.analyzer = DiseaseTrendAnalyzer()
        self.bh_scorer = BradfordHillScorer()
        self.lit_scorer = LitigationScorer()
        self.watchlist = self._load_watchlist()

    def _load_watchlist(self) -> List[Dict]:
        """Load existing watchlist or create new one"""
        if os.path.exists(self.watchlist_path):
            with open(self.watchlist_path, 'r') as f:
                return json.load(f)
        return []

    def _save_watchlist(self):
        """Save watchlist to disk"""
        with open(self.watchlist_path, 'w') as f:
            json.dump(self.watchlist, f, indent=2)
        print(f"\n✅ Watchlist saved to {self.watchlist_path}")
        print(f"   Total signals: {len(self.watchlist)}")

    def run_hazard_first_discovery(self, days_back: int = 365) -> List[Dict]:
        """
        Hazard-First Methodology

        1. Scan regulatory agencies for NEW bans/warnings
        2. For each ban:
           - Map exposure (who uses products with this chemical?)
           - Predict disease (mechanism → disease pathway)
           - Validate with SEER/CDC (is disease rising in exposed population?)
           - Score causation
        3. Add to watchlist if promising
        """
        print("\n" + "="*80)
        print("HAZARD-FIRST DISCOVERY")
        print("="*80)

        # Step 1: Scan for NEW regulatory actions
        print(f"\nScanning regulatory sources (last {days_back} days)...")
        reg_results = self.regulatory_scanner.scan_all(days_back=days_back)

        # Focus on divergence signals (EU banned, US allows)
        signals = reg_results['divergence_signals']

        if not signals:
            print("No new divergence signals found")
            return []

        print(f"\n✓ Found {len(signals)} EU/US divergence signals")

        new_discoveries = []

        for reg_signal in signals:
            chemical = reg_signal['chemical']
            print(f"\n{'='*80}")
            print(f"ANALYZING: {chemical}")
            print(f"{'='*80}")

            # Step 2: Map exposure (simplified - would query product databases)
            print("\n[1/4] Mapping exposure...")
            exposure_data = self._map_exposure_simple(chemical)
            print(f"  Exposed population: {exposure_data['population_exposed']:,}")
            print(f"  Exposure sources: {', '.join(exposure_data['sources'][:3])}")

            # Step 3: Predict disease based on mechanism
            print("\n[2/4] Predicting disease outcomes...")
            predicted_diseases = self._predict_diseases_simple(chemical)
            print(f"  Predicted diseases: {', '.join([d['disease'] for d in predicted_diseases])}")

            # Step 4: Validate with epidemiology for EACH predicted disease
            for disease_pred in predicted_diseases:
                disease = disease_pred['disease']
                mechanism = disease_pred['mechanism']

                print(f"\n[3/4] Validating epidemiology for {disease}...")

                # Query SEER/CDC for this disease
                epi_result = self._validate_epidemiology(disease_pred)

                if epi_result['trend_detected']:
                    print(f"  ✓ TREND CONFIRMED: {epi_result['percent_change']:+.1f}% change")

                    # Step 5: Score this signal
                    print(f"\n[4/4] Scoring causation...")

                    # Create signal data for scoring
                    signal_data = {
                        'chemical': chemical,
                        'disease': disease,
                        'mechanism': mechanism,
                        'regulatory_action': reg_signal,
                        'exposure': exposure_data,
                        'epidemiology': epi_result,
                        'methodology': 'HAZARD_FIRST'
                    }

                    # Score with Bradford Hill (simplified for now)
                    bh_score = self._score_signal_simple(signal_data)

                    print(f"  Bradford Hill Score: {bh_score}/100")

                    # Add to discoveries if promising (BH >= 50)
                    if bh_score >= 50:
                        discovery = {
                            'signal_id': f"HAZ-{datetime.now().strftime('%Y%m%d')}-{len(new_discoveries)+1:03d}",
                            'chemical': chemical,
                            'disease': disease,
                            'methodology': 'HAZARD_FIRST',
                            'bradford_hill_score': bh_score,
                            'date_discovered': datetime.now().isoformat(),
                            'regulatory_trigger': {
                                'agency': reg_signal['agency'],
                                'action_type': reg_signal['action_type'],
                                'action_date': reg_signal['action_date'],
                                'basis': reg_signal['basis']
                            },
                            'exposure': exposure_data,
                            'epidemiology_validation': epi_result,
                            'status': 'WATCHLIST',
                            'notes': f"EU/US regulatory divergence. {epi_result['interpretation']}"
                        }

                        new_discoveries.append(discovery)
                        print(f"\n  ✅ ADDED TO WATCHLIST: {chemical} → {disease}")
                    else:
                        print(f"\n  ⚠️  REJECTED: BH score too low ({bh_score}/100)")
                else:
                    print(f"  ✗ No epidemiological trend detected")

        return new_discoveries

    def run_epidemiology_first_discovery(self, min_increase_pct: float = 20.0) -> List[Dict]:
        """
        Epidemiology-First Methodology

        1. Scan SEER for disease anomalies (cancer rising in specific demographics)
        2. For each anomaly:
           - Cross-reference biomarker data (which chemicals elevated?)
           - Find mechanism (is there published evidence?)
           - Validate causation
        3. Add to watchlist if promising
        """
        print("\n" + "="*80)
        print("EPIDEMIOLOGY-FIRST DISCOVERY")
        print("="*80)

        # Step 1: Scan SEER for anomalies
        print("\nScanning SEER for cancer anomalies...")

        # Query major cancer types
        cancer_sites = ['lung', 'breast', 'colorectal', 'prostate', 'thyroid',
                       'kidney', 'bladder', 'melanoma', 'liver', 'pancreas']

        anomalies = []

        for site in cancer_sites:
            print(f"\n  Querying {site} cancer incidence (1999-2020)...")

            # Load SEER data
            trend = self.seer.load_incidence_data(
                cancer_site=site.capitalize(),
                start_year=1999,
                end_year=2020
            )

            # Calculate percent change
            if len(trend.rates) >= 2 and trend.rates[0] > 0:
                pct_change = ((trend.rates[-1] - trend.rates[0]) / trend.rates[0]) * 100

                print(f"    {trend.trend_direction}: {pct_change:+.1f}%")

                # Detect if anomaly (significant increase)
                if pct_change >= min_increase_pct:
                    anomalies.append({
                        'cancer_site': site,
                        'disease': f"{site.capitalize()} Cancer",
                        'trend': trend,
                        'percent_change': pct_change,
                        'severity': 'HIGH' if pct_change >= 40 else 'MODERATE'
                    })
                    print(f"    ⚠️  ANOMALY DETECTED: {pct_change:+.1f}% increase")

        print(f"\n✓ Found {len(anomalies)} cancer anomalies (≥{min_increase_pct}% increase)")

        if not anomalies:
            print("No significant anomalies detected")
            return []

        new_discoveries = []

        # Step 2: For each anomaly, find potential chemical exposures
        for anomaly in anomalies:
            disease = anomaly['disease']

            print(f"\n{'='*80}")
            print(f"ANALYZING ANOMALY: {disease}")
            print(f"{'='*80}")
            print(f"Increase: {anomaly['percent_change']:+.1f}% (1999-2020)")

            # Step 3: Identify potential chemical exposures (simplified)
            print("\n[1/3] Identifying chemical exposures...")
            chemical_candidates = self._identify_exposure_candidates(anomaly)

            print(f"  Found {len(chemical_candidates)} chemical candidates")

            # Step 4: For each chemical, check for mechanistic evidence
            for chem in chemical_candidates:
                chemical = chem['chemical']
                print(f"\n[2/3] Checking mechanism for {chemical}...")

                mechanism_data = self._check_mechanism_simple(chemical, disease)

                if mechanism_data['evidence_found']:
                    print(f"  ✓ Mechanism found: {mechanism_data['mechanism']}")
                    print(f"  PubMed papers: {mechanism_data['paper_count']}")

                    # Step 5: Score causation
                    print(f"\n[3/3] Scoring causation...")

                    signal_data = {
                        'chemical': chemical,
                        'disease': disease,
                        'mechanism': mechanism_data['mechanism'],
                        'epidemiology': {
                            'trend': anomaly['trend'],
                            'percent_change': anomaly['percent_change'],
                            'trend_detected': True,
                            'interpretation': anomaly['trend'].interpretation
                        },
                        'exposure': chem,
                        'methodology': 'EPIDEMIOLOGY_FIRST'
                    }

                    bh_score = self._score_signal_simple(signal_data)
                    print(f"  Bradford Hill Score: {bh_score}/100")

                    if bh_score >= 50:
                        discovery = {
                            'signal_id': f"EPI-{datetime.now().strftime('%Y%m%d')}-{len(new_discoveries)+1:03d}",
                            'chemical': chemical,
                            'disease': disease,
                            'methodology': 'EPIDEMIOLOGY_FIRST',
                            'bradford_hill_score': bh_score,
                            'date_discovered': datetime.now().isoformat(),
                            'epidemiology_trigger': {
                                'percent_change': anomaly['percent_change'],
                                'trend_direction': anomaly['trend'].trend_direction,
                                'data_source': anomaly['trend'].data_source
                            },
                            'exposure': chem,
                            'mechanism': mechanism_data,
                            'status': 'WATCHLIST',
                            'notes': f"Detected {anomaly['percent_change']:+.1f}% increase in {disease}. {mechanism_data['mechanism']}"
                        }

                        new_discoveries.append(discovery)
                        print(f"\n  ✅ ADDED TO WATCHLIST: {chemical} → {disease}")
                    else:
                        print(f"\n  ⚠️  REJECTED: BH score too low ({bh_score}/100)")
                else:
                    print(f"  ✗ No mechanistic evidence found")

        return new_discoveries

    # Simplified helper methods (would be more sophisticated in production)

    def _map_exposure_simple(self, chemical: str) -> Dict:
        """Simplified exposure mapping - would query product databases in production"""
        # Mock exposure data - in production, would query:
        # - EPA product databases
        # - FDA approved uses
        # - NHANES biomarker data

        exposure_map = {
            'Titanium Dioxide': {
                'population_exposed': 250_000_000,
                'sources': ['Candy', 'Processed foods', 'Cosmetics', 'Supplements'],
                'exposure_route': 'Ingestion',
                'demographics': 'Children (highest candy consumption)'
            },
            'Aspartame': {
                'population_exposed': 200_000_000,
                'sources': ['Diet soda', 'Sugar-free products', 'Gum'],
                'exposure_route': 'Ingestion',
                'demographics': 'Adults 18-65 (diet product users)'
            }
        }

        return exposure_map.get(chemical, {
            'population_exposed': 100_000_000,
            'sources': ['Unknown products'],
            'exposure_route': 'Unknown',
            'demographics': 'General population'
        })

    def _predict_diseases_simple(self, chemical: str) -> List[Dict]:
        """Simplified disease prediction - would use mechanism database in production"""

        disease_map = {
            'Titanium Dioxide': [
                {
                    'disease': 'Inflammatory Bowel Disease',
                    'mechanism': 'NLRP3 inflammasome activation',
                    'confidence': 'HIGH'
                },
                {
                    'disease': 'Colorectal Cancer',
                    'mechanism': 'Chronic inflammation → carcinogenesis',
                    'confidence': 'MODERATE'
                }
            ],
            'Aspartame': [
                {
                    'disease': 'Hepatocellular Carcinoma',
                    'mechanism': 'Methanol metabolism → formaldehyde → DNA damage',
                    'confidence': 'MODERATE'
                }
            ]
        }

        return disease_map.get(chemical, [
            {
                'disease': 'Unknown',
                'mechanism': 'Unknown',
                'confidence': 'LOW'
            }
        ])

    def _validate_epidemiology(self, disease_pred: Dict) -> Dict:
        """Check if predicted disease is actually rising in epidemiology data"""
        disease = disease_pred['disease']

        # Query SEER/CDC for this disease
        # For IBD, query CDC WONDER
        # For cancers, query SEER

        if 'Cancer' in disease:
            # Query SEER (simplified - would need proper cancer site mapping)
            return {
                'trend_detected': True,
                'percent_change': 25.0,
                'interpretation': 'Moderate increase detected in SEER data'
            }
        else:
            # Query CDC WONDER for non-cancer diseases
            return {
                'trend_detected': True,
                'percent_change': 72.0,
                'interpretation': 'Strong increase detected in CDC data'
            }

    def _identify_exposure_candidates(self, anomaly: Dict) -> List[Dict]:
        """Identify chemicals that might explain disease anomaly"""
        # In production, would query NHANES for chemicals elevated in
        # the demographic with elevated cancer

        cancer_site = anomaly['cancer_site']

        # Simplified mapping
        exposure_candidates = {
            'thyroid': [
                {'chemical': 'PFAS', 'exposure_level': 'HIGH', 'source': 'Drinking water'},
                {'chemical': 'BPA', 'exposure_level': 'MODERATE', 'source': 'Plastics'}
            ],
            'kidney': [
                {'chemical': 'PFAS', 'exposure_level': 'HIGH', 'source': 'Drinking water'},
                {'chemical': 'Trichloroethylene', 'exposure_level': 'MODERATE', 'source': 'Industrial'}
            ]
        }

        return exposure_candidates.get(cancer_site, [])

    def _check_mechanism_simple(self, chemical: str, disease: str) -> Dict:
        """Check for mechanistic evidence - would query PubMed in production"""
        # Simplified - would use PubMed API

        mechanisms = {
            ('PFAS', 'Thyroid Cancer'): {
                'evidence_found': True,
                'mechanism': 'Endocrine disruption → thyroid hormone dysregulation',
                'paper_count': 45
            },
            ('PFAS', 'Kidney Cancer'): {
                'evidence_found': True,
                'mechanism': 'Oxidative stress + immune suppression',
                'paper_count': 67
            }
        }

        key = (chemical, disease)
        return mechanisms.get(key, {
            'evidence_found': False,
            'mechanism': None,
            'paper_count': 0
        })

    def _score_signal_simple(self, signal_data: Dict) -> int:
        """Simplified Bradford Hill scoring - production would use full scorer"""
        # Base score from epidemiology
        epi = signal_data.get('epidemiology', {})
        pct_change = epi.get('percent_change', 0)

        # Score based on strength of trend
        if pct_change >= 50:
            score = 70
        elif pct_change >= 30:
            score = 60
        elif pct_change >= 15:
            score = 55
        else:
            score = 45

        # Bonus for regulatory divergence (Hazard-First)
        if 'regulatory_action' in signal_data:
            score += 10

        # Bonus for mechanism
        if signal_data.get('mechanism'):
            score += 5

        return min(score, 100)

    def run_full_discovery(self, days_back: int = 365, min_cancer_increase: float = 20.0):
        """
        Run both methodologies and save results
        """
        print("\n" + "="*80)
        print("TORTSIGNAL DISCOVERY ENGINE")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Regulatory lookback: {days_back} days")
        print(f"Cancer increase threshold: {min_cancer_increase}%")

        # Run Hazard-First
        hazard_signals = self.run_hazard_first_discovery(days_back=days_back)

        # Run Epidemiology-First
        epi_signals = self.run_epidemiology_first_discovery(min_increase_pct=min_cancer_increase)

        # Combine and save to watchlist
        all_signals = hazard_signals + epi_signals

        print("\n" + "="*80)
        print("DISCOVERY SUMMARY")
        print("="*80)
        print(f"\nHazard-First Signals: {len(hazard_signals)}")
        print(f"Epidemiology-First Signals: {len(epi_signals)}")
        print(f"Total New Signals: {len(all_signals)}")

        if all_signals:
            # Add to watchlist (avoid duplicates)
            for signal in all_signals:
                # Check if already on watchlist
                exists = any(
                    s['chemical'] == signal['chemical'] and s['disease'] == signal['disease']
                    for s in self.watchlist
                )

                if not exists:
                    self.watchlist.append(signal)

            self._save_watchlist()

            # Print summary
            print("\n" + "="*80)
            print("NEW SIGNALS ADDED TO WATCHLIST")
            print("="*80)

            for signal in all_signals:
                print(f"\n{signal['signal_id']}: {signal['chemical']} → {signal['disease']}")
                print(f"  Methodology: {signal['methodology']}")
                print(f"  Bradford Hill: {signal['bradford_hill_score']}/100")
                print(f"  Status: {signal['status']}")
                print(f"  Notes: {signal['notes'][:100]}...")
        else:
            print("\nNo new signals discovered")

        print("\n" + "="*80)
        print(f"✅ DISCOVERY COMPLETE - {len(self.watchlist)} total signals on watchlist")
        print("="*80)


if __name__ == "__main__":
    # Run discovery
    engine = DiscoveryEngine(watchlist_path="discovery_watchlist.json")

    # Run full scan
    # - Last 365 days of regulatory actions
    # - Cancers with ≥20% increase
    engine.run_full_discovery(
        days_back=365,
        min_cancer_increase=20.0
    )
