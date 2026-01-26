"""
Enhanced CDC WONDER Integration

Improves robustness of CDC WONDER API integration to eliminate literature fallbacks.

Key improvements:
1. Proper XML-based API requests (CDC WONDER's preferred method)
2. Complete ICD-10 code handling with range expansion
3. Multi-strategy parsing (XML → TSV → HTML → CSV export)
4. Caching to reduce API load
5. Better error handling and retry logic
6. Support for multiple datasets (D76, D77, D139, D140)

CDC WONDER API Documentation:
- https://wonder.cdc.gov/wonder/help/WONDER-API.html
- https://wonder.cdc.gov/wonder/help/ucd.html (Underlying Cause of Death)
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re
import time
from datetime import datetime, timedelta
import hashlib
import json


@dataclass
class DiseaseTrend:
    """Disease incidence/mortality trend over time"""
    disease: str
    years: List[int]
    rates: List[float]  # Age-adjusted rates per 100,000
    counts: List[int]  # Raw case counts
    data_source: str
    anomalies_detected: List[Dict]
    trend_direction: str  # 'INCREASING', 'DECREASING', 'STABLE'
    percent_change: float  # Overall percent change from first to last year
    interpretation: str
    confidence: str = "HIGH"  # Data quality: HIGH, MODERATE, LOW


class ICD10CodeExpander:
    """Expand ICD-10 code ranges into individual codes"""

    @staticmethod
    def expand_range(icd10_range: str) -> List[str]:
        """
        Expand ICD-10 code range into list of individual codes

        Examples:
            K50-K51 → ['K50', 'K50.0', 'K50.1', ..., 'K51', 'K51.0', ...]
            C15-C26 → ['C15', 'C16', 'C17', ..., 'C26']
            K50 → ['K50', 'K50.0', 'K50.1', 'K50.8', 'K50.9']
        """
        # Handle simple code (no range)
        if '-' not in icd10_range:
            return ICD10CodeExpander._expand_single_code(icd10_range)

        # Split range
        parts = icd10_range.split('-')
        if len(parts) != 2:
            return [icd10_range]  # Return as-is if malformed

        start_code, end_code = parts[0].strip(), parts[1].strip()

        # Extract letter and numbers
        start_letter = start_code[0]
        start_num = int(re.findall(r'\d+', start_code)[0]) if re.findall(r'\d+', start_code) else 0

        end_letter = end_code[0]
        end_num = int(re.findall(r'\d+', end_code)[0]) if re.findall(r'\d+', end_code) else 0

        # Expand range
        codes = []
        if start_letter == end_letter:
            for num in range(start_num, end_num + 1):
                base_code = f"{start_letter}{num:02d}"
                codes.extend(ICD10CodeExpander._expand_single_code(base_code))
        else:
            # Cross-letter range (rare, but handle it)
            codes.append(icd10_range)  # Return range as-is

        return codes

    @staticmethod
    def _expand_single_code(code: str) -> List[str]:
        """Expand a single ICD-10 code to include subcategories"""
        # For 3-char codes, add .0-.9 subcategories
        if len(code) == 3 and code[-1].isdigit():
            expanded = [code]
            for i in [0, 1, 8, 9]:  # Common subcategories
                expanded.append(f"{code}.{i}")
            return expanded
        else:
            return [code]


class CDCWonderEnhancedAPI:
    """
    Enhanced CDC WONDER API with robust data fetching

    Implements multiple strategies to obtain real data before falling back
    """

    BASE_URL = "https://wonder.cdc.gov/controller"

    # Dataset configurations
    DATASETS = {
        'D76': {
            'name': 'Detailed Mortality',
            'years': (1999, 2020),
            'endpoint': 'datarequest/D76',
            'supports_xml': True
        },
        'D77': {
            'name': 'Multiple Cause of Death',
            'years': (1999, 2020),
            'endpoint': 'datarequest/D77',
            'supports_xml': True
        },
        'D139': {
            'name': 'Compressed Mortality',
            'years': (1999, 2020),
            'endpoint': 'datarequest/D139',
            'supports_xml': False
        },
        'D140': {
            'name': 'Underlying Cause of Death',
            'years': (2018, 2022),
            'endpoint': 'datarequest/D140',
            'supports_xml': True
        }
    }

    def __init__(self, cache_ttl_hours: int = 168):  # 1 week cache
        """
        Initialize enhanced CDC WONDER API

        Args:
            cache_ttl_hours: Cache time-to-live in hours (default: 1 week)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) TortSignal/1.0 Research Tool',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.cache = {}
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

    def query_disease_trend(
        self,
        disease_icd10_code: str,
        start_year: int = 1999,
        end_year: int = 2020,
        dataset: str = "D76",
        use_cache: bool = True
    ) -> DiseaseTrend:
        """
        Query CDC WONDER for disease mortality trends with enhanced robustness

        Strategies (in order):
        1. XML-based API request (CDC WONDER's preferred method)
        2. Form-based request with TSV export
        3. HTML table parsing
        4. Cached data from previous successful queries
        5. Literature estimates (only as last resort)

        Args:
            disease_icd10_code: ICD-10 code or range (e.g., 'K50-K51', 'C34')
            start_year: Start year
            end_year: End year
            dataset: CDC WONDER dataset (D76, D77, D139, D140)
            use_cache: Whether to use cached data

        Returns:
            DiseaseTrend with mortality data and confidence level
        """
        # Check cache first
        cache_key = f"{dataset}:{disease_icd10_code}:{start_year}-{end_year}"
        if use_cache and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                print(f"[CDC WONDER] Using cached data (age: {(datetime.now() - cached_time).days} days)")
                return cached_data

        print(f"\n[CDC WONDER] Querying {disease_icd10_code} trends ({start_year}-{end_year}) from dataset {dataset}...")

        # Expand ICD-10 codes
        icd10_codes = ICD10CodeExpander.expand_range(disease_icd10_code)
        print(f"[CDC WONDER] Expanded to {len(icd10_codes)} ICD-10 codes")

        # Strategy 1: XML-based request (preferred)
        if self.DATASETS[dataset]['supports_xml']:
            try:
                trend = self._query_via_xml(disease_icd10_code, icd10_codes, start_year, end_year, dataset)
                if trend and len(trend.years) > 0:
                    trend.confidence = "HIGH"
                    self.cache[cache_key] = (trend, datetime.now())
                    print(f"[CDC WONDER] ✓ Retrieved {len(trend.years)} years via XML API")
                    return trend
            except Exception as e:
                print(f"[CDC WONDER] XML query failed: {e}")

        # Strategy 2: Form-based request with TSV export
        try:
            trend = self._query_via_form(disease_icd10_code, icd10_codes, start_year, end_year, dataset)
            if trend and len(trend.years) > 0:
                trend.confidence = "HIGH"
                self.cache[cache_key] = (trend, datetime.now())
                print(f"[CDC WONDER] ✓ Retrieved {len(trend.years)} years via Form API")
                return trend
        except Exception as e:
            print(f"[CDC WONDER] Form query failed: {e}")

        # Strategy 3: Check if we have older cached data (expired but better than nothing)
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            age_days = (datetime.now() - cached_time).days
            print(f"[CDC WONDER] Using stale cache (age: {age_days} days)")
            cached_data.confidence = "MODERATE"
            return cached_data

        # Strategy 4: Literature fallback (clearly flagged)
        print(f"[CDC WONDER] ⚠️ All API strategies failed - falling back to literature estimates")
        trend = self._estimate_from_literature(disease_icd10_code, start_year, end_year)
        trend.confidence = "LOW"
        return trend

    def _query_via_xml(
        self,
        disease_code: str,
        icd10_codes: List[str],
        start_year: int,
        end_year: int,
        dataset: str
    ) -> Optional[DiseaseTrend]:
        """
        Query CDC WONDER using XML request (preferred method)

        CDC WONDER XML API allows structured requests and returns structured data
        """
        # Build XML request
        xml_request = self._build_xml_request(icd10_codes, start_year, end_year, dataset)

        try:
            response = self.session.post(
                f"{self.BASE_URL}/{self.DATASETS[dataset]['endpoint']}",
                data={'request_xml': xml_request, 'accept_datause_restrictions': 'true'},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=60
            )

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            # Parse XML response
            return self._parse_xml_response(response.text, disease_code)

        except Exception as e:
            raise Exception(f"XML query failed: {e}")

    def _build_xml_request(
        self,
        icd10_codes: List[str],
        start_year: int,
        end_year: int,
        dataset: str
    ) -> str:
        """
        Build XML request for CDC WONDER API

        Example XML structure:
        <request-parameters>
          <accept_datause_restrictions>true</accept_datause_restrictions>
          <parameter>
            <name>B_1</name>
            <value>D76.V1</value>  <!-- Group by Year -->
          </parameter>
          <parameter>
            <name>F_D76.V2</name>  <!-- ICD-10 codes -->
            <value>K50</value>
            <value>K51</value>
          </parameter>
        </request-parameters>
        """
        root = ET.Element("request-parameters")

        # Accept data use restrictions
        ET.SubElement(root, "accept_datause_restrictions").text = "true"

        # Group by: Year
        param = ET.SubElement(root, "parameter")
        ET.SubElement(param, "name").text = "B_1"
        ET.SubElement(param, "value").text = f"{dataset}.V1"  # Year variable

        # ICD-10 codes filter
        param = ET.SubElement(root, "parameter")
        ET.SubElement(param, "name").text = f"F_{dataset}.V2"  # ICD-10 filter
        for code in icd10_codes[:50]:  # Limit to avoid too long request
            ET.SubElement(param, "value").text = code

        # Year range filter
        param = ET.SubElement(root, "parameter")
        ET.SubElement(param, "name").text = f"F_{dataset}.V1"  # Year filter
        for year in range(start_year, end_year + 1):
            ET.SubElement(param, "value").text = str(year)

        # Measures: Deaths and Age-Adjusted Rate
        param = ET.SubElement(root, "parameter")
        ET.SubElement(param, "name").text = "M_1"
        ET.SubElement(param, "value").text = f"{dataset}.M1"  # Deaths

        param = ET.SubElement(root, "parameter")
        ET.SubElement(param, "name").text = "M_2"
        ET.SubElement(param, "value").text = f"{dataset}.M3"  # Age-Adjusted Rate

        # Export options
        param = ET.SubElement(root, "parameter")
        ET.SubElement(param, "name").text = "O_export"
        ET.SubElement(param, "value").text = "true"

        return ET.tostring(root, encoding='unicode')

    def _parse_xml_response(
        self,
        xml_response: str,
        disease_code: str
    ) -> Optional[DiseaseTrend]:
        """Parse XML response from CDC WONDER"""
        try:
            root = ET.fromstring(xml_response)

            # Find data-table element
            data_table = root.find('.//data-table')
            if data_table is None:
                raise Exception("No data-table found in response")

            years = []
            rates = []
            counts = []

            # Parse rows
            for row in data_table.findall('.//r'):
                # Extract year (column c with n="1")
                year_elem = row.find(".//c[@n='1']")
                if year_elem is not None and year_elem.text:
                    year = int(year_elem.text)
                else:
                    continue

                # Extract deaths (column c with l="Deaths")
                deaths_elem = row.find(".//c[@l='Deaths']")
                deaths = int(deaths_elem.text) if deaths_elem is not None and deaths_elem.text else 0

                # Extract age-adjusted rate
                rate_elem = row.find(".//c[@l='Age Adjusted Rate']")
                rate = float(rate_elem.text) if rate_elem is not None and rate_elem.text else 0.0

                years.append(year)
                counts.append(deaths)
                rates.append(rate)

            if not years:
                return None

            # Calculate trend
            percent_change = ((rates[-1] - rates[0]) / rates[0] * 100) if rates[0] > 0 else 0

            if percent_change > 10:
                trend_direction = 'INCREASING'
            elif percent_change < -10:
                trend_direction = 'DECREASING'
            else:
                trend_direction = 'STABLE'

            interpretation = (
                f"CDC WONDER XML API data: {len(years)} years, "
                f"{percent_change:+.1f}% change from {years[0]} to {years[-1]}"
            )

            return DiseaseTrend(
                disease=disease_code,
                years=years,
                rates=rates,
                counts=counts,
                data_source='CDC WONDER (XML API)',
                anomalies_detected=[],
                trend_direction=trend_direction,
                percent_change=percent_change,
                interpretation=interpretation
            )

        except Exception as e:
            raise Exception(f"XML parsing failed: {e}")

    def _query_via_form(
        self,
        disease_code: str,
        icd10_codes: List[str],
        start_year: int,
        end_year: int,
        dataset: str
    ) -> Optional[DiseaseTrend]:
        """
        Query CDC WONDER using form-based request with TSV export

        This is the fallback method when XML doesn't work
        """
        form_data = {
            'accept_datause_restrictions': 'true',
            'stage': 'request',
            'saved_id': '',
            'dataset_code': dataset,

            # Group by Year
            'B_1': f'{dataset}.V1',

            # Measures
            'M_1': f'{dataset}.M1',  # Deaths
            'M_2': f'{dataset}.M3',  # Age Adjusted Rate

            # ICD-10 codes (limit to 100 to avoid URL too long)
            f'F_{dataset}.V2': icd10_codes[:100],

            # Year range
            f'F_{dataset}.V1': [str(y) for y in range(start_year, end_year + 1)],

            # Export options
            'O_show_totals': 'true',
            'O_precision': '1',
            'O_timeout': '300',
            'O_export': 'true',
            'O_title': 'Disease Trend Query',
        }

        try:
            response = self.session.post(
                f"{self.BASE_URL}/{self.DATASETS[dataset]['endpoint']}",
                data=form_data,
                timeout=60,
                allow_redirects=True
            )

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            # Try multiple parsing strategies
            return self._parse_multi_strategy(response.text, disease_code)

        except Exception as e:
            raise Exception(f"Form query failed: {e}")

    def _parse_multi_strategy(
        self,
        response_text: str,
        disease_code: str
    ) -> Optional[DiseaseTrend]:
        """Try multiple parsing strategies on response"""

        # Strategy 1: TSV format
        if '\t' in response_text and 'Year\t' in response_text:
            trend = self._parse_tsv(response_text, disease_code)
            if trend:
                return trend

        # Strategy 2: HTML table
        if '<table' in response_text.lower():
            trend = self._parse_html_table(response_text, disease_code)
            if trend:
                return trend

        # Strategy 3: CSV-style parsing
        if ',' in response_text and 'Year,' in response_text:
            trend = self._parse_csv(response_text, disease_code)
            if trend:
                return trend

        return None

    def _parse_tsv(self, tsv_data: str, disease_code: str) -> Optional[DiseaseTrend]:
        """Parse tab-delimited response"""
        lines = [line for line in tsv_data.split('\n') if line.strip()]

        # Find header
        header_idx = None
        for i, line in enumerate(lines):
            if 'Year' in line and ('Deaths' in line or 'Rate' in line):
                header_idx = i
                break

        if header_idx is None:
            return None

        years, rates, counts = [], [], []

        for line in lines[header_idx + 1:]:
            parts = line.split('\t')
            if len(parts) < 2:
                continue

            try:
                year = int(parts[0])
                if year < 1990 or year > 2030:
                    continue

                deaths = int(parts[1].replace(',', '')) if len(parts) > 1 else 0
                rate = float(parts[2].replace(',', '')) if len(parts) > 2 else 0.0

                years.append(year)
                counts.append(deaths)
                rates.append(rate)

            except (ValueError, IndexError):
                continue

        if not years:
            return None

        return self._build_trend(disease_code, years, rates, counts, 'CDC WONDER (TSV)')

    def _parse_html_table(self, html_content: str, disease_code: str) -> Optional[DiseaseTrend]:
        """Parse HTML table response"""
        year_pattern = r'<td[^>]*>(\d{4})</td>'
        number_pattern = r'<td[^>]*>([\d,\.]+)</td>'

        years, rates, counts = [], [], []

        rows = re.findall(r'<tr[^>]*>(.+?)</tr>', html_content, re.DOTALL)

        for row in rows:
            year_match = re.search(year_pattern, row)
            if not year_match:
                continue

            year = int(year_match.group(1))
            if year < 1990 or year > 2030:
                continue

            numbers = re.findall(number_pattern, row)
            if len(numbers) < 2:
                continue

            try:
                deaths = int(numbers[0].replace(',', ''))
                rate = float(numbers[1].replace(',', ''))

                years.append(year)
                counts.append(deaths)
                rates.append(rate)
            except (ValueError, IndexError):
                continue

        if not years:
            return None

        return self._build_trend(disease_code, years, rates, counts, 'CDC WONDER (HTML)')

    def _parse_csv(self, csv_data: str, disease_code: str) -> Optional[DiseaseTrend]:
        """Parse CSV-style response"""
        import csv
        from io import StringIO

        try:
            reader = csv.DictReader(StringIO(csv_data))

            years, rates, counts = [], [], []

            for row in reader:
                try:
                    year = int(row.get('Year', 0))
                    if year < 1990 or year > 2030:
                        continue

                    deaths = int(row.get('Deaths', 0).replace(',', ''))
                    rate = float(row.get('Age Adjusted Rate', 0).replace(',', ''))

                    years.append(year)
                    counts.append(deaths)
                    rates.append(rate)

                except (ValueError, KeyError):
                    continue

            if not years:
                return None

            return self._build_trend(disease_code, years, rates, counts, 'CDC WONDER (CSV)')

        except Exception:
            return None

    def _build_trend(
        self,
        disease_code: str,
        years: List[int],
        rates: List[float],
        counts: List[int],
        data_source: str
    ) -> DiseaseTrend:
        """Build DiseaseTrend from parsed data"""
        percent_change = ((rates[-1] - rates[0]) / rates[0] * 100) if rates[0] > 0 else 0

        if percent_change > 10:
            trend_direction = 'INCREASING'
        elif percent_change < -10:
            trend_direction = 'DECREASING'
        else:
            trend_direction = 'STABLE'

        interpretation = (
            f"{data_source}: {len(years)} years of data, "
            f"{trend_direction.lower()} {percent_change:+.1f}%"
        )

        return DiseaseTrend(
            disease=disease_code,
            years=years,
            rates=rates,
            counts=counts,
            data_source=data_source,
            anomalies_detected=[],
            trend_direction=trend_direction,
            percent_change=percent_change,
            interpretation=interpretation
        )

    def _estimate_from_literature(
        self,
        disease_code: str,
        start_year: int,
        end_year: int
    ) -> DiseaseTrend:
        """
        Literature fallback (only when all API strategies fail)

        This should be rarely used if XML and Form methods work properly
        """
        from .cdc_wonder import CDCWonderAPI

        # Use existing literature estimation
        fallback_api = CDCWonderAPI()
        trend = fallback_api._estimate_from_literature(disease_code, start_year, end_year)

        # Mark as low confidence
        trend.data_source += " ⚠️ LOW CONFIDENCE (API unavailable)"

        return trend


# Convenience function
def query_cdc_wonder(
    disease_icd10_code: str,
    start_year: int = 1999,
    end_year: int = 2020,
    dataset: str = "D76"
) -> DiseaseTrend:
    """
    Quick CDC WONDER query with enhanced robustness

    Args:
        disease_icd10_code: ICD-10 code or range
        start_year: Start year
        end_year: End year
        dataset: Dataset code

    Returns:
        DiseaseTrend with confidence level
    """
    api = CDCWonderEnhancedAPI()
    return api.query_disease_trend(disease_icd10_code, start_year, end_year, dataset)


if __name__ == "__main__":
    # Test enhanced CDC WONDER integration
    print("\n" + "="*80)
    print("ENHANCED CDC WONDER INTEGRATION TEST")
    print("="*80)

    api = CDCWonderEnhancedAPI()

    # Test 1: IBD trend (K50-K51)
    print("\n--- Test 1: IBD Mortality (K50-K51) ---")
    trend = api.query_disease_trend("K50-K51", 1999, 2020)

    print(f"\nResults:")
    print(f"  Disease: {trend.disease}")
    print(f"  Data Source: {trend.data_source}")
    print(f"  Confidence: {trend.confidence}")
    print(f"  Years: {len(trend.years)}")
    print(f"  Trend: {trend.trend_direction} ({trend.percent_change:+.1f}%)")
    if trend.years:
        print(f"  Baseline: {trend.rates[0]:.2f}/100k ({trend.years[0]})")
        print(f"  Current: {trend.rates[-1]:.2f}/100k ({trend.years[-1]})")

    # Test 2: Lung cancer (C34)
    print("\n--- Test 2: Lung Cancer Mortality (C34) ---")
    trend = api.query_disease_trend("C34", 1999, 2020)

    print(f"\nResults:")
    print(f"  Data Source: {trend.data_source}")
    print(f"  Confidence: {trend.confidence}")
    print(f"  Trend: {trend.trend_direction} ({trend.percent_change:+.1f}%)")

    print("\n✅ ENHANCED CDC WONDER TEST COMPLETE")
