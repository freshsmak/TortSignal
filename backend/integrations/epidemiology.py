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
    SEER (Surveillance, Epidemiology, and End Results) Data Integration

    SEER collects cancer incidence and survival data from population-based cancer registries
    covering ~48% of the US population.

    API Access:
    - SEER Data API: https://api.seer.cancer.gov/rest/
    - Requires API key (set via SEER_API_KEY environment variable)
    - Rate limits: 1000 requests/hour per key

    Data Coverage:
    - Years: 1975-2020 (varies by registry)
    - Cancer sites: All primary cancer sites
    - Metrics: Incidence rates (age-adjusted), counts, survival
    """

    BASE_URL = "https://api.seer.cancer.gov/rest"

    # SEER site recode mappings (subset of most common sites)
    SITE_CODES = {
        'lung': '22030',
        'breast': '26000',
        'prostate': '28010',
        'colorectal': '21041-21049',
        'bladder': '29010',
        'melanoma': '25010',
        'kidney': '29020',
        'leukemia': '35011-35043',
        'liver': '21071',
        'pancreas': '21100',
        'thyroid': '32010',
        'stomach': '21020',
        'esophagus': '21010',
        'ovary': '27040',
        'brain': '31010'
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SEER API wrapper

        Args:
            api_key: SEER API key (if None, reads from SEER_API_KEY environment variable)
        """
        import os
        self.api_key = api_key or os.getenv('SEER_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TortSignal/1.0 (Mass Tort Discovery System)',
            'Accept': 'application/json'
        })
        self.data_cache = {}

        if self.api_key:
            print(f"[SEER] Initialized with API key: {self.api_key[:8]}...")
        else:
            print(f"[SEER] WARNING: No API key provided - will use fallback data only")

    def load_incidence_data(
        self,
        cancer_site: str = "Lung",
        start_year: int = 1975,
        end_year: int = 2020,
        csv_path: Optional[str] = None,
        confidence_threshold: str = 'MODERATE'
    ) -> DiseaseTrend:
        """
        Load SEER cancer incidence data

        Data Source Priority:
        1. SEER REST API (real-time, requires API key)
        2. Local CSV export (if csv_path provided)
        3. Literature-based estimates (fallback only)

        Args:
            cancer_site: Cancer site (e.g., 'Lung', 'Breast', 'Colorectal')
            start_year: Start year (1975-2020)
            end_year: End year (1975-2020)
            csv_path: Optional path to SEER*Stat CSV export
            confidence_threshold: Minimum confidence level ('HIGH', 'MODERATE', 'LOW')

        Returns:
            DiseaseTrend object with cancer incidence trends and confidence metrics
        """
        print(f"\n[SEER] Querying {cancer_site} cancer incidence ({start_year}-{end_year})...")

        # Strategy 1: Try SEER REST API (highest confidence)
        if self.api_key:
            try:
                trend = self._query_seer_api(cancer_site, start_year, end_year)
                if trend:
                    print(f"[SEER] ✓ Retrieved {len(trend.years)} years from API")
                    return trend
            except Exception as e:
                print(f"[SEER] API query failed: {e}")
        else:
            print(f"[SEER] Skipping API (no key provided)")

        # Strategy 2: Try local CSV export (moderate confidence)
        if csv_path:
            try:
                trend = self._parse_seer_csv(csv_path, cancer_site, start_year, end_year)
                if trend:
                    print(f"[SEER] ✓ Loaded {len(trend.years)} years from CSV")
                    return trend
            except Exception as e:
                print(f"[SEER] CSV parsing failed: {e}")

        # Strategy 3: Literature-based estimates (low confidence)
        print(f"[SEER] WARNING: Falling back to literature estimates (low confidence)")
        return self._estimate_from_literature(cancer_site, start_year, end_year)

    def _query_seer_api(
        self,
        cancer_site: str,
        start_year: int,
        end_year: int
    ) -> Optional[DiseaseTrend]:
        """
        Query SEER REST API for cancer incidence data

        SEER API Endpoints:
        - /incidence: Get incidence rates by site, year, demographics
        - /survival: Get survival statistics
        - /population: Get population denominators

        Returns:
            DiseaseTrend if successful, None if API unavailable
        """
        site_key = cancer_site.lower()
        site_code = self.SITE_CODES.get(site_key)

        if not site_code:
            print(f"[SEER] Unknown cancer site: {cancer_site}")
            print(f"[SEER] Available sites: {', '.join(self.SITE_CODES.keys())}")
            return None

        # Build API request
        params = {
            'api_key': self.api_key,
            'site': site_code,
            'year_start': start_year,
            'year_end': end_year,
            'race': 'all',
            'sex': 'all',
            'age': 'all',
            'statistic': 'incidence',
            'rate_type': 'age_adjusted',  # Age-adjusted rate per 100,000
            'format': 'json'
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/incidence",
                params=params,
                timeout=30
            )

            if response.status_code == 401:
                print(f"[SEER] Authentication failed - invalid API key")
                return None
            elif response.status_code == 429:
                print(f"[SEER] Rate limit exceeded (1000 req/hour)")
                return None
            elif response.status_code != 200:
                print(f"[SEER] API error: {response.status_code}")
                return None

            data = response.json()

            # Parse API response
            return self._parse_api_response(data, cancer_site, start_year, end_year)

        except requests.RequestException as e:
            print(f"[SEER] Network error: {e}")
            return None
        except Exception as e:
            print(f"[SEER] Unexpected error: {e}")
            return None

    def _parse_api_response(
        self,
        data: Dict,
        cancer_site: str,
        start_year: int,
        end_year: int
    ) -> Optional[DiseaseTrend]:
        """
        Parse SEER API JSON response

        Expected structure:
        {
            "results": [
                {"year": 1975, "rate": 42.3, "count": 123456, "population": 290000000},
                {"year": 1976, "rate": 43.1, "count": 125678, "population": 295000000},
                ...
            ],
            "metadata": {...}
        }
        """
        if 'results' not in data or not data['results']:
            print(f"[SEER] No results in API response")
            return None

        results = data['results']

        years = []
        rates = []
        counts = []

        for record in results:
            try:
                year = int(record.get('year', 0))
                rate = float(record.get('rate', 0))
                count = int(record.get('count', 0))

                if start_year <= year <= end_year:
                    years.append(year)
                    rates.append(rate)
                    counts.append(count)
            except (ValueError, KeyError) as e:
                continue

        if not years:
            return None

        # Calculate trend metrics
        percent_change = ((rates[-1] - rates[0]) / rates[0] * 100) if rates[0] > 0 else 0

        if percent_change > 10:
            trend_direction = 'INCREASING'
        elif percent_change < -10:
            trend_direction = 'DECREASING'
        else:
            trend_direction = 'STABLE'

        interpretation = (
            f"{cancer_site} cancer incidence {trend_direction.lower()} "
            f"{percent_change:+.1f}% from {years[0]} ({rates[0]:.1f}/100k) "
            f"to {years[-1]} ({rates[-1]:.1f}/100k). "
            f"Source: SEER API (high confidence, n={len(years)} years)"
        )

        return DiseaseTrend(
            disease=f"{cancer_site} Cancer",
            years=years,
            rates=rates,
            counts=counts,
            data_source='SEER API (real-time)',
            anomalies_detected=[],
            trend_direction=trend_direction,
            percent_change=percent_change,
            interpretation=interpretation
        )

    def _parse_seer_csv(
        self,
        csv_path: str,
        cancer_site: str,
        start_year: int,
        end_year: int
    ) -> Optional[DiseaseTrend]:
        """
        Parse SEER*Stat CSV export

        SEER*Stat CSV format (example):
        Year,Age Adjusted Rate,Count,Population
        1975,42.3,123456,290000000
        1976,43.1,125678,295000000
        ...

        Alternative format:
        Site,Year,Rate,Cases,Population
        Lung and Bronchus,1975,42.3,123456,290000000
        """
        import csv

        print(f"[SEER] Parsing CSV: {csv_path}")

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)

            years = []
            rates = []
            counts = []

            for row in reader:
                try:
                    # Try to extract year
                    year = None
                    for col in ['Year', 'year', 'YEAR']:
                        if col in row:
                            year = int(row[col])
                            break

                    if not year or year < start_year or year > end_year:
                        continue

                    # Extract rate
                    rate = None
                    for col in ['Age Adjusted Rate', 'Rate', 'rate', 'AGE_ADJUSTED_RATE']:
                        if col in row and row[col]:
                            rate = float(row[col].replace(',', ''))
                            break

                    # Extract count
                    count = None
                    for col in ['Count', 'count', 'Cases', 'cases', 'COUNT']:
                        if col in row and row[col]:
                            count = int(row[col].replace(',', ''))
                            break

                    if rate is not None:
                        years.append(year)
                        rates.append(rate)
                        counts.append(count if count is not None else 0)

                except (ValueError, KeyError) as e:
                    continue

        if not years:
            raise Exception("No valid data found in CSV")

        # Calculate trend
        percent_change = ((rates[-1] - rates[0]) / rates[0] * 100) if rates[0] > 0 else 0

        if percent_change > 10:
            trend_direction = 'INCREASING'
        elif percent_change < -10:
            trend_direction = 'DECREASING'
        else:
            trend_direction = 'STABLE'

        interpretation = (
            f"{cancer_site} cancer incidence {trend_direction.lower()} "
            f"{percent_change:+.1f}% from {years[0]} to {years[-1]}. "
            f"Source: SEER CSV export (moderate confidence, n={len(years)} years)"
        )

        return DiseaseTrend(
            disease=f"{cancer_site} Cancer",
            years=years,
            rates=rates,
            counts=counts,
            data_source='SEER CSV Export',
            anomalies_detected=[],
            trend_direction=trend_direction,
            percent_change=percent_change,
            interpretation=interpretation
        )

    def _estimate_from_literature(
        self,
        cancer_site: str,
        start_year: int,
        end_year: int
    ) -> DiseaseTrend:
        """
        Literature-based cancer incidence estimates (LOW CONFIDENCE)

        Uses published cancer statistics when API/CSV unavailable.
        Sources:
        - NCI SEER Cancer Statistics Review (annual)
        - American Cancer Society Cancer Facts & Figures
        - Siegel et al. CA Cancer J Clin (annual projections)
        """
        site_key = cancer_site.lower()

        # Literature-based estimates for major cancer types
        literature_trends = {
            'lung': {
                'baseline_rate': 65.0,  # per 100k in 1990
                'annual_change': -0.02,  # 2% annual decline (smoking reduction)
                'peak_year': 1990,
                'interpretation': 'Lung cancer declining since 1990s due to smoking reduction (Jemal et al. 2018)'
            },
            'breast': {
                'baseline_rate': 140.0,  # per 100k women in 2000
                'annual_change': -0.004,  # 0.4% annual decline post-2000
                'peak_year': 2000,
                'interpretation': 'Breast cancer stabilized/slight decline post-2000 (Berry et al. 2005)'
            },
            'colorectal': {
                'baseline_rate': 60.0,  # per 100k in 1985
                'annual_change': -0.03,  # 3% annual decline (screening impact)
                'peak_year': 1985,
                'interpretation': 'Colorectal cancer declining since 1985 due to screening (Siegel et al. 2020)'
            },
            'prostate': {
                'baseline_rate': 180.0,  # per 100k men in 1992
                'annual_change': -0.01,  # 1% annual decline post-PSA peak
                'peak_year': 1992,
                'interpretation': 'Prostate cancer declined after PSA screening peak (Jemal et al. 2010)'
            },
            'melanoma': {
                'baseline_rate': 20.0,  # per 100k in 2000
                'annual_change': 0.02,  # 2% annual increase (UV exposure)
                'peak_year': 2000,
                'interpretation': 'Melanoma rising steadily due to UV exposure (Linos et al. 2009)'
            }
        }

        trend_params = literature_trends.get(site_key, {
            'baseline_rate': 50.0,
            'annual_change': 0.0,
            'peak_year': 2000,
            'interpretation': f'Generic trend estimate for {cancer_site}'
        })

        years = list(range(start_year, end_year + 1))
        rates = []

        baseline = trend_params['baseline_rate']
        peak_year = trend_params['peak_year']
        annual_change = trend_params['annual_change']

        for year in years:
            years_from_peak = year - peak_year
            rate = baseline * (1 + annual_change) ** years_from_peak
            rates.append(max(rate, 5.0))  # Floor at 5/100k

        # Calculate counts (US population ~330M)
        population = 330_000_000
        counts = [int(r * (population / 100_000)) for r in rates]

        # Calculate trend
        percent_change = ((rates[-1] - rates[0]) / rates[0] * 100) if rates[0] > 0 else 0

        if percent_change > 10:
            trend_direction = 'INCREASING'
        elif percent_change < -10:
            trend_direction = 'DECREASING'
        else:
            trend_direction = 'STABLE'

        interpretation = (
            f"{cancer_site} cancer incidence {trend_direction.lower()} "
            f"{percent_change:+.1f}% (literature estimate). "
            f"{trend_params['interpretation']}. "
            f"⚠️ LOW CONFIDENCE: Real SEER data unavailable"
        )

        return DiseaseTrend(
            disease=f"{cancer_site} Cancer",
            years=years,
            rates=rates,
            counts=counts,
            data_source='Literature Estimates (LOW CONFIDENCE)',
            anomalies_detected=[],
            trend_direction=trend_direction,
            percent_change=percent_change,
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
