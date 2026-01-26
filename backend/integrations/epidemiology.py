"""
Epidemiology Integration - SEER & CDC WONDER
Detects disease trends, anomalies, and temporal patterns for EDE Epidemiology-First methodology
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import csv
import io
from dataclasses import dataclass
import statistics

# Import improved CDC WONDER implementation
try:
    from integrations.cdc_wonder import CDCWonderAPI, DiseaseTrend
    CDC_WONDER_IMPORTED = True
except ImportError:
    # Fall back to local import if running from integrations directory
    try:
        from cdc_wonder import CDCWonderAPI, DiseaseTrend
        CDC_WONDER_IMPORTED = True
    except ImportError:
        CDC_WONDER_IMPORTED = False
        # Will define minimal stub below


# If import failed, define minimal stub
if not CDC_WONDER_IMPORTED:
    @dataclass
    class DiseaseTrend:
        """Disease incidence/mortality trend over time"""
        disease: str
        years: List[int]
        rates: List[float]
        counts: List[int]
        data_source: str
        anomalies_detected: List[Dict]
        trend_direction: str
        percent_change: float
        interpretation: str

    class CDCWonderAPI:
        """Stub CDC WONDER API"""
        def __init__(self):
            pass

        def query_disease_trend(self, disease_icd10_code: str, start_year: int = 1999,
                                end_year: int = 2020, dataset: str = "D76") -> DiseaseTrend:
            """Stub method"""
            return DiseaseTrend(
                disease=f"Disease ({disease_icd10_code})",
                years=list(range(start_year, end_year + 1)),
                rates=[1.0] * (end_year - start_year + 1),
                counts=[3300] * (end_year - start_year + 1),
                data_source='CDC_WONDER (stub)',
                anomalies_detected=[],
                trend_direction='STABLE',
                percent_change=0.0,
                interpretation="No data available"
            )


class SEERDataWrapper:
    """
    Wrapper for SEER cancer incidence data

    SEER provides cancer incidence and survival data
    Access methods:
    1. SEER*Stat software (desktop)
    2. SEER API (for staging/algorithms)
    3. CSV/ASCII data files (requires Research Data Agreement)

    For EDE, we'll support CSV file imports
    """

    def __init__(self):
        self.data_cache = {}

    def load_incidence_data(
        self,
        csv_path: Optional[str] = None,
        cancer_site: str = "Lung",
        start_year: int = 1975,
        end_year: int = 2022
    ) -> DiseaseTrend:
        """
        Load SEER cancer incidence data from CSV export

        Args:
            csv_path: Path to SEER*Stat CSV export (optional, uses mock if None)
            cancer_site: Cancer site (e.g., 'Lung', 'Breast', 'Colorectal')
            start_year: Start year
            end_year: End year

        Returns:
            DiseaseTrend object with cancer incidence trends
        """
        print(f"\n[SEER] Loading {cancer_site} cancer incidence data ({start_year}-{end_year})...")

        if csv_path:
            try:
                return self._parse_seer_csv(csv_path, cancer_site)
            except Exception as e:
                print(f"[SEER] Error loading CSV: {e}")
                print(f"[SEER] Falling back to mock data")

        # Use mock data for testing
        return self._mock_lung_cancer_data(start_year, end_year)

    def _parse_seer_csv(self, csv_path: str, cancer_site: str) -> DiseaseTrend:
        """Parse SEER*Stat CSV export"""
        # TODO: Implement CSV parsing when real SEER data is available
        # Expected columns: Year, Age Adjusted Rate, Count, Population
        pass

    def _mock_lung_cancer_data(self, start_year: int, end_year: int) -> DiseaseTrend:
        """
        Mock lung cancer incidence data for testing
        Based on real trends: Lung cancer declining ~2% per year since 1990s (smoking reduction)
        """
        years = list(range(start_year, min(end_year + 1, 2023)))

        # Simulate declining trend (peak in 1990s ~65 per 100k, declining to ~35 per 100k by 2022)
        peak_year = 1990
        peak_rate = 65.0
        decline_per_year = 0.6  # ~0.9% decline per year

        rates = []
        for year in years:
            if year <= peak_year:
                # Increasing before 1990
                years_from_1975 = year - 1975
                rate = 55.0 + (years_from_1975 * 0.7)
            else:
                # Declining after 1990
                years_since_peak = year - peak_year
                rate = peak_rate - (years_since_peak * decline_per_year)
            rates.append(max(rate, 20.0))  # Floor at 20

        # Calculate counts
        population = 320_000_000
        counts = [int(r * (population / 100_000)) for r in rates]

        # Detect anomalies
        anomalies = []

        # Overall trend
        if len(rates) >= 2:
            overall_change = ((rates[-1] - rates[0]) / rates[0]) * 100
        else:
            overall_change = 0

        if overall_change > 10:
            trend_direction = 'INCREASING'
        elif overall_change < -10:
            trend_direction = 'DECREASING'
        else:
            trend_direction = 'STABLE'

        interpretation = f"Lung cancer incidence {trend_direction.lower()} {overall_change:+.1f}% from {start_year} to {years[-1]}"

        return DiseaseTrend(
            disease="Lung Cancer",
            years=years,
            rates=rates,
            counts=counts,
            data_source='SEER (mock)',
            anomalies_detected=anomalies,
            trend_direction=trend_direction,
            percent_change=overall_change,
            interpretation=interpretation
        )


class DiseaseTrendAnalyzer:
    """
    Analyzes disease trends to detect anomalies and temporal patterns
    Used for Epidemiology-First methodology and Bradford Hill Temporality scoring
    """

    def __init__(self):
        pass

    def detect_anomalies(
        self,
        trend: DiseaseTrend,
        threshold_pct: float = 15.0
    ) -> List[Dict]:
        """
        Detect year-over-year anomalies (spikes or drops)

        Args:
            trend: DiseaseTrend object
            threshold_pct: Percent change threshold for anomaly (default 15%)

        Returns:
            List of anomalies with year, rate, and percent change
        """
        anomalies = []

        for i in range(1, len(trend.years)):
            if trend.rates[i-1] == 0:
                continue

            pct_change = ((trend.rates[i] - trend.rates[i-1]) / trend.rates[i-1]) * 100

            if abs(pct_change) >= threshold_pct:
                anomaly_type = 'SPIKE' if pct_change > 0 else 'DROP'

                anomalies.append({
                    'year': trend.years[i],
                    'rate': trend.rates[i],
                    'previous_rate': trend.rates[i-1],
                    'percent_change': pct_change,
                    'type': anomaly_type,
                    'significance': 'HIGH' if abs(pct_change) >= 25 else 'MODERATE'
                })

        return anomalies

    def calculate_trend_slope(self, trend: DiseaseTrend) -> Dict:
        """
        Calculate linear regression slope for trend

        Returns:
            Dictionary with slope, R², and interpretation
        """
        if len(trend.years) < 3:
            return {
                'slope': 0,
                'r_squared': 0,
                'interpretation': 'Insufficient data for trend analysis'
            }

        # Simple linear regression
        n = len(trend.years)
        x = list(range(n))  # Year index
        y = trend.rates

        # Calculate means
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        # Calculate slope
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        # Calculate R²
        ss_total = sum((y[i] - y_mean) ** 2 for i in range(n))
        y_pred = [y_mean + slope * (x[i] - x_mean) for i in range(n)]
        ss_residual = sum((y[i] - y_pred[i]) ** 2 for i in range(n))

        if ss_total == 0:
            r_squared = 0
        else:
            r_squared = 1 - (ss_residual / ss_total)

        # Interpretation
        if slope > 0.1:
            direction = "Strong increasing trend"
        elif slope > 0.01:
            direction = "Moderate increasing trend"
        elif slope < -0.1:
            direction = "Strong decreasing trend"
        elif slope < -0.01:
            direction = "Moderate decreasing trend"
        else:
            direction = "Stable (no significant trend)"

        return {
            'slope': slope,
            'r_squared': r_squared,
            'annual_change_rate': slope,  # Rate change per year
            'interpretation': f"{direction} (R² = {r_squared:.3f})"
        }

    def compare_with_exposure_timeline(
        self,
        disease_trend: DiseaseTrend,
        exposure_start_year: int,
        exposure_peak_year: int,
        expected_latency_years: int = 10
    ) -> Dict:
        """
        Compare disease trend with exposure timeline for Bradford Hill Temporality

        Args:
            disease_trend: DiseaseTrend object
            exposure_start_year: Year exposure began
            exposure_peak_year: Year exposure peaked
            expected_latency_years: Expected latency period

        Returns:
            Temporality assessment for Bradford Hill scoring
        """
        print(f"\n[TEMPORALITY] Comparing disease trend with exposure timeline...")
        print(f"  Exposure Start: {exposure_start_year}")
        print(f"  Exposure Peak: {exposure_peak_year}")
        print(f"  Expected Latency: {expected_latency_years} years")

        # Find when disease rate started increasing
        anomalies = self.detect_anomalies(disease_trend, threshold_pct=10)

        if not anomalies:
            # No clear increase, check overall trend
            trend_stats = self.calculate_trend_slope(disease_trend)

            if trend_stats['slope'] > 0:
                # Gradual increase
                disease_increase_year = disease_trend.years[0]
            else:
                return {
                    'temporality_valid': False,
                    'reason': 'No disease increase detected',
                    'exposure_precedes_disease': None,
                    'latency_period': None,
                    'bradford_hill_score': 0,
                    'interpretation': 'FATAL FLAW: No disease increase observed'
                }
        else:
            # Use first significant spike
            disease_increase_year = anomalies[0]['year']

        # Check if exposure precedes disease
        exposure_precedes = exposure_start_year < disease_increase_year

        # Calculate latency
        latency = disease_increase_year - exposure_peak_year

        # Temporality score (for Bradford Hill)
        if not exposure_precedes:
            score = 0
            interpretation = 'FATAL FLAW: Disease increase precedes exposure'
        elif latency < 0:
            score = 2
            interpretation = 'WEAK: Disease increased before exposure peak'
        elif 0 <= latency < (expected_latency_years - 5):
            score = 5
            interpretation = 'MODERATE: Latency shorter than expected'
        elif (expected_latency_years - 5) <= latency <= (expected_latency_years + 5):
            score = 10
            interpretation = 'STRONG: Latency matches expected biological mechanism'
        elif latency > (expected_latency_years + 10):
            score = 6
            interpretation = 'MODERATE: Latency longer than expected (other factors possible)'
        else:
            score = 8
            interpretation = 'GOOD: Latency within reasonable range'

        print(f"  Disease Increase Year: {disease_increase_year}")
        print(f"  Latency: {latency} years")
        print(f"  Temporality Score: {score}/10 - {interpretation}")

        return {
            'temporality_valid': exposure_precedes,
            'reason': interpretation,
            'exposure_precedes_disease': exposure_precedes,
            'exposure_start_year': exposure_start_year,
            'disease_increase_year': disease_increase_year,
            'latency_period': latency,
            'expected_latency': expected_latency_years,
            'bradford_hill_score': score,
            'interpretation': interpretation
        }

    def identify_changepoint(self, trend: DiseaseTrend) -> Optional[int]:
        """
        Identify the year when disease trend changed significantly
        Uses simple changepoint detection

        Returns:
            Year when changepoint occurred, or None if no changepoint
        """
        if len(trend.years) < 5:
            return None

        # Calculate year-over-year changes
        changes = []
        for i in range(1, len(trend.rates)):
            if trend.rates[i-1] != 0:
                pct_change = ((trend.rates[i] - trend.rates[i-1]) / trend.rates[i-1]) * 100
                changes.append((trend.years[i], pct_change))

        if not changes:
            return None

        # Find year with largest increase
        max_change = max(changes, key=lambda x: x[1])

        if max_change[1] >= 15:  # At least 15% increase
            return max_change[0]

        return None


# Main integration class
class EpidemiologyIntegration:
    """
    Main class combining CDC WONDER and SEER for comprehensive epidemiology analysis
    """

    def __init__(self):
        self.cdc = CDCWonderAPI()
        self.seer = SEERDataWrapper()
        self.analyzer = DiseaseTrendAnalyzer()

    def analyze_disease_signal(
        self,
        disease: str,
        disease_icd10_code: str,
        exposure_start_year: int,
        exposure_peak_year: int,
        expected_latency: int = 10,
        start_year: int = 1999,
        end_year: int = 2020
    ) -> Dict:
        """
        Complete epidemiological analysis for a disease-exposure pair

        Returns:
            Comprehensive analysis with trends, anomalies, and temporality assessment
        """
        print(f"\n{'='*80}")
        print(f"EPIDEMIOLOGY ANALYSIS: {disease}")
        print(f"{'='*80}")

        # Get disease trend
        trend = self.cdc.query_disease_trend(
            disease_icd10_code,
            start_year,
            end_year
        )

        # Detect anomalies
        anomalies = self.analyzer.detect_anomalies(trend)
        trend.anomalies_detected = anomalies

        # Calculate trend statistics
        trend_stats = self.analyzer.calculate_trend_slope(trend)

        # Assess temporality
        temporality = self.analyzer.compare_with_exposure_timeline(
            trend,
            exposure_start_year,
            exposure_peak_year,
            expected_latency
        )

        # Identify changepoint
        changepoint = self.analyzer.identify_changepoint(trend)

        return {
            'disease': disease,
            'trend': trend,
            'anomalies': anomalies,
            'trend_statistics': trend_stats,
            'temporality_assessment': temporality,
            'changepoint_year': changepoint,
            'bradford_hill_temporality_score': temporality['bradford_hill_score']
        }


if __name__ == "__main__":
    # Test the epidemiology integration
    epi = EpidemiologyIntegration()

    print("\n" + "="*80)
    print("EPIDEMIOLOGY INTEGRATION TEST")
    print("="*80 + "\n")

    # Test 1: TiO2 → IBD analysis
    print("Test 1: Titanium Dioxide → Inflammatory Bowel Disease")

    result = epi.analyze_disease_signal(
        disease="Inflammatory Bowel Disease",
        disease_icd10_code="K50-K51",  # Crohn's + Ulcerative Colitis
        exposure_start_year=1990,  # TiO2 food additive approval
        exposure_peak_year=2000,  # Widespread use in packaged foods
        expected_latency=10,  # IBD develops 5-15 years after exposure
        start_year=1999,
        end_year=2020
    )

    # Print results
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    print(f"\nDisease Trend:")
    print(f"  Direction: {result['trend'].trend_direction}")
    print(f"  Overall Change: {result['trend'].percent_change:+.1f}%")
    print(f"  Data Points: {len(result['trend'].years)} years")
    print(f"  Latest Rate: {result['trend'].rates[-1]:.2f} per 100,000")

    print(f"\nTrend Statistics:")
    print(f"  {result['trend_statistics']['interpretation']}")
    print(f"  Annual Change: {result['trend_statistics']['annual_change_rate']:.4f} per year")

    print(f"\nAnomalies Detected: {len(result['anomalies'])}")
    for anomaly in result['anomalies'][:3]:  # Show first 3
        print(f"  {anomaly['year']}: {anomaly['percent_change']:+.1f}% ({anomaly['type']})")

    print(f"\nTemporality Assessment:")
    print(f"  Exposure Precedes Disease: {result['temporality_assessment']['exposure_precedes_disease']}")
    print(f"  Latency Period: {result['temporality_assessment']['latency_period']} years")
    print(f"  Bradford Hill Score: {result['bradford_hill_temporality_score']}/10")
    print(f"  Interpretation: {result['temporality_assessment']['interpretation']}")

    if result['changepoint_year']:
        print(f"\nChangepoint Detected: {result['changepoint_year']}")

    print("\n✅ EPIDEMIOLOGY INTEGRATION TEST COMPLETE")
