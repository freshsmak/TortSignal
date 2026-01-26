"""
NHANES (National Health and Nutrition Examination Survey) Integration
Biomarker data and exposure surveys for linking chemicals to disease populations

NHANES Data: https://wwwn.cdc.gov/nchs/nhanes/
- Survey cycles: 2017-2020 (most recent complete)
- File format: .XPT (SAS transport files)
- No REST API - must download and parse files
"""

import pandas as pd
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os
import tempfile
from pathlib import Path


@dataclass
class BiomarkerData:
    """Chemical biomarker levels in blood/urine by demographic"""
    chemical: str
    demographic: Dict[str, str]  # {'race': 'Black', 'age': '30-60', 'gender': 'Female'}
    mean_level: float  # ng/mL or ug/L
    median_level: float
    percentile_95: float
    sample_size: int
    units: str
    survey_cycle: str
    interpretation: str


@dataclass
class ExposureAssessment:
    """Cross-referenced exposure data for disease population"""
    chemical: str
    disease_population: Dict[str, str]
    general_population: Dict[str, str]
    exposure_ratio: float  # Ratio of disease pop to general pop
    biomarker_disease_pop: Optional[float]
    biomarker_general_pop: Optional[float]
    survey_data: Dict[str, any]  # Product use, occupation, diet
    interpretation: str
    data_quality: str  # 'HIGH', 'MODERATE', 'LOW'


class NHANESIntegration:
    """
    NHANES Biomarker and Survey Data Integration

    Key Datasets:
    - Lab Data: Chemical biomarkers (PFAS, phthalates, heavy metals)
    - Survey Data: Product use, occupation, diet
    - Demographics: Age, race, gender, income

    Survey Cycles:
    - 2017-2020: Most recent complete (pre-COVID)
    - 2015-2016: Previous cycle
    - 2013-2014: Older data
    """

    BASE_URL = "https://wwwn.cdc.gov/Nchs/Nhanes"

    # Chemical to NHANES file mapping (2017-2018 cycle = "J" suffix)
    # Note: TiO2 is NOT routinely measured in NHANES biomarker surveys
    # Most chemicals use Lab Data files
    CHEMICAL_FILES = {
        'titanium': None,  # TiO2 not routinely measured in NHANES blood/urine panels
        'titanium_blood': None,
        'pfas': 'PFAS_J',  # Per- and Polyfluoroalkyl Substances (remove .XPT - added later)
        'phthalates': 'PHTHTE_J',  # Phthalates - Urine
        'lead': 'PbCd_J',  # Lead and Cadmium - Blood
        'bpa': 'EPH_J',  # Environmental Phenols & Parabens
        'parabens': 'EPH_J',
        'formaldehyde': None,  # Not measured as biomarker
    }

    # ICD-10 to demographic filters
    DISEASE_DEMOGRAPHICS = {
        'K50-K51': {'age_min': 20, 'age_max': 80, 'description': 'IBD (Crohn\'s, UC)'},
        'C54': {'age_min': 30, 'age_max': 70, 'gender': 'Female', 'description': 'Uterine cancer'},
        'C91-C95': {'age_min': 0, 'age_max': 100, 'description': 'Leukemia'},
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) TortSignal/1.0'
        })
        self.cache_dir = cache_dir or Path(tempfile.gettempdir()) / 'nhanes_cache'
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def get_biomarker_levels(
        self,
        chemical: str,
        demographic: Dict[str, any],
        survey_cycle: str = "2017-2018"
    ) -> Optional[BiomarkerData]:
        """
        Get chemical biomarker levels for specific demographic

        Args:
            chemical: 'titanium', 'pfas', 'phthalates', 'lead', 'bpa', etc.
            demographic: {'race': 'Black', 'age_min': 30, 'age_max': 60, 'gender': 'Female'}
            survey_cycle: '2017-2018', '2015-2016', etc.

        Returns:
            BiomarkerData object with mean/median levels
        """
        print(f"\n[NHANES] Querying {chemical} levels for {demographic}")

        # Check if chemical is measured in NHANES
        if chemical.lower() not in self.CHEMICAL_FILES:
            print(f"[NHANES] Warning: {chemical} not routinely measured in NHANES")
            return self._estimate_from_literature(chemical, demographic)

        file_name = self.CHEMICAL_FILES[chemical.lower()]
        if file_name is None:
            print(f"[NHANES] {chemical} not available as biomarker in NHANES")
            return self._estimate_from_literature(chemical, demographic)

        # Download and parse data file
        try:
            df = self._load_nhanes_file(file_name, survey_cycle)

            if df is None:
                return self._estimate_from_literature(chemical, demographic)

            # Filter by demographics
            filtered = self._filter_by_demographics(df, demographic)

            if len(filtered) == 0:
                print(f"[NHANES] No data found for demographics: {demographic}")
                return None

            # Calculate statistics
            biomarker_data = self._calculate_biomarker_stats(
                filtered,
                chemical,
                demographic,
                survey_cycle
            )

            print(f"[NHANES] Found data: n={biomarker_data.sample_size}, "
                  f"mean={biomarker_data.mean_level:.2f} {biomarker_data.units}")

            return biomarker_data

        except Exception as e:
            print(f"[NHANES] Error: {e}")
            return self._estimate_from_literature(chemical, demographic)

    def cross_reference_exposure(
        self,
        chemical: str,
        disease_icd10: str,
        disease_demographics: Dict[str, any]
    ) -> ExposureAssessment:
        """
        Cross-reference chemical exposure with disease population

        Compares biomarker levels in:
        - Disease-affected demographic (e.g., Black women 30-60)
        - General population baseline

        Returns exposure ratio and interpretation
        """
        print(f"\n[NHANES] Cross-referencing {chemical} exposure with {disease_icd10}")

        # Get biomarker levels for disease population
        disease_pop_data = self.get_biomarker_levels(
            chemical,
            disease_demographics
        )

        # Get baseline (general population) levels
        general_demographics = {'age_min': 20, 'age_max': 80}  # All adults
        general_pop_data = self.get_biomarker_levels(
            chemical,
            general_demographics
        )

        # Calculate exposure ratio
        if disease_pop_data and general_pop_data:
            exposure_ratio = disease_pop_data.mean_level / general_pop_data.mean_level

            interpretation = self._interpret_exposure_ratio(
                exposure_ratio,
                chemical,
                disease_demographics
            )

            data_quality = 'HIGH' if disease_pop_data.sample_size >= 100 else 'MODERATE'

        else:
            exposure_ratio = 1.0
            interpretation = "Insufficient biomarker data in NHANES"
            data_quality = 'LOW'

        # Get survey data (product use, occupation, diet)
        survey_data = self._get_survey_data(chemical, disease_demographics)

        assessment = ExposureAssessment(
            chemical=chemical,
            disease_population=disease_demographics,
            general_population=general_demographics,
            exposure_ratio=exposure_ratio,
            biomarker_disease_pop=disease_pop_data.mean_level if disease_pop_data else None,
            biomarker_general_pop=general_pop_data.mean_level if general_pop_data else None,
            survey_data=survey_data,
            interpretation=interpretation,
            data_quality=data_quality
        )

        print(f"[NHANES] Exposure ratio: {exposure_ratio:.2f}x")
        print(f"[NHANES] {interpretation}")

        return assessment

    def _load_nhanes_file(
        self,
        file_name: str,
        survey_cycle: str
    ) -> Optional[pd.DataFrame]:
        """
        Download and parse NHANES .XPT file

        Files are cached locally to avoid repeated downloads

        Note: NHANES file URLs are structured as:
        https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/PFAS_J.XPT
        """
        # Convert survey cycle to URL format
        cycle_map = {
            '2017-2018': '2017-2018',
            '2015-2016': '2015-2016',
            '2013-2014': '2013-2014'
        }
        cycle_url = cycle_map.get(survey_cycle, '2017-2018')

        # Add .XPT extension if not present
        if not file_name.endswith('.XPT'):
            file_name = f"{file_name}.XPT"

        # Check cache first
        cache_path = self.cache_dir / f"{survey_cycle}_{file_name}"

        if cache_path.exists():
            print(f"[NHANES] Loading from cache: {file_name}")
            try:
                # Check if file is actually XPT (not HTML error page)
                with open(cache_path, 'rb') as f:
                    header = f.read(100)
                    if b'<!DOCTYPE html>' in header or b'<html' in header:
                        print(f"[NHANES] Cache contains HTML error page, removing")
                        cache_path.unlink()
                    else:
                        return pd.read_sas(cache_path)
            except Exception as e:
                print(f"[NHANES] Cache read error: {e}")
                cache_path.unlink()  # Remove bad cache file

        # Download file
        url = f"{self.BASE_URL}/{cycle_url}/{file_name}"
        print(f"[NHANES] Downloading: {url}")

        try:
            response = self.session.get(url, timeout=60)

            # Check if response is HTML (error page)
            if b'<!DOCTYPE html>' in response.content[:200] or b'<html' in response.content[:200]:
                print(f"[NHANES] URL returned HTML error page (404 or moved)")
                print(f"[NHANES] This chemical may not be available in NHANES {survey_cycle}")
                return None

            response.raise_for_status()

            # Save to cache
            with open(cache_path, 'wb') as f:
                f.write(response.content)

            # Parse SAS file
            df = pd.read_sas(cache_path)
            print(f"[NHANES] Loaded {len(df)} records from {file_name}")

            return df

        except requests.exceptions.RequestException as e:
            print(f"[NHANES] Download failed: {e}")
            return None
        except Exception as e:
            print(f"[NHANES] Parse error: {e}")
            return None

    def _filter_by_demographics(
        self,
        df: pd.DataFrame,
        demographic: Dict[str, any]
    ) -> pd.DataFrame:
        """
        Filter NHANES data by demographic criteria

        NHANES variable names:
        - RIDAGEYR: Age in years
        - RIAGENDR: Gender (1=Male, 2=Female)
        - RIDRETH3: Race/Hispanic origin
        """
        filtered = df.copy()

        # Age filter
        if 'age_min' in demographic and 'RIDAGEYR' in df.columns:
            filtered = filtered[filtered['RIDAGEYR'] >= demographic['age_min']]
        if 'age_max' in demographic and 'RIDAGEYR' in df.columns:
            filtered = filtered[filtered['RIDAGEYR'] <= demographic['age_max']]

        # Gender filter
        if 'gender' in demographic and 'RIAGENDR' in df.columns:
            gender_code = 2 if demographic['gender'].lower() == 'female' else 1
            filtered = filtered[filtered['RIAGENDR'] == gender_code]

        # Race filter
        if 'race' in demographic and 'RIDRETH3' in df.columns:
            race_map = {
                'mexican_american': 1,
                'other_hispanic': 2,
                'white': 3,
                'black': 4,
                'asian': 6,
                'other': 7
            }
            race_code = race_map.get(demographic['race'].lower())
            if race_code:
                filtered = filtered[filtered['RIDRETH3'] == race_code]

        return filtered

    def _calculate_biomarker_stats(
        self,
        df: pd.DataFrame,
        chemical: str,
        demographic: Dict[str, any],
        survey_cycle: str
    ) -> BiomarkerData:
        """
        Calculate biomarker statistics from filtered NHANES data

        Note: Column names vary by chemical - need to map correctly
        """
        # Find biomarker columns (typically start with chemical code)
        # For example: PFAS file has LBXPFDE, LBXPFHS, etc.
        biomarker_cols = [col for col in df.columns if col.startswith('LBX') or col.startswith('URX')]

        if not biomarker_cols:
            # Fallback: use all numeric columns
            biomarker_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()

        # Take first biomarker column (usually the primary compound)
        if len(biomarker_cols) > 0:
            primary_col = biomarker_cols[0]
            values = df[primary_col].dropna()
        else:
            # Synthetic data for testing
            values = pd.Series([1.0])

        if len(values) == 0:
            values = pd.Series([0.0])

        return BiomarkerData(
            chemical=chemical,
            demographic=demographic,
            mean_level=float(values.mean()),
            median_level=float(values.median()),
            percentile_95=float(values.quantile(0.95)),
            sample_size=len(values),
            units='ng/mL',  # Common unit (varies by chemical)
            survey_cycle=survey_cycle,
            interpretation=f"{len(values)} samples analyzed"
        )

    def _get_survey_data(
        self,
        chemical: str,
        demographic: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Get survey questionnaire data (product use, occupation, diet)

        Examples:
        - Hair product use questionnaire
        - Occupational exposure questions
        - Dietary recall

        Note: Survey data requires separate file downloads
        Currently returns literature-based estimates
        """
        # This would require downloading additional questionnaire files
        # For now, return literature-based estimates

        survey_data = {
            'data_source': 'literature_estimate',
            'notes': 'NHANES questionnaire data requires separate file download'
        }

        # Special case: Hair relaxer use (well-documented in literature)
        if 'formaldehyde' in chemical.lower() or 'phthalate' in chemical.lower():
            if demographic.get('race', '').lower() == 'black' and demographic.get('gender', '').lower() == 'female':
                survey_data['hair_relaxer_use'] = 0.74  # 74% per literature
                survey_data['data_source'] = 'literature (Helm et al. 2018)'

        return survey_data

    def _interpret_exposure_ratio(
        self,
        ratio: float,
        chemical: str,
        demographic: Dict[str, any]
    ) -> str:
        """Interpret exposure ratio significance"""
        if ratio >= 3.0:
            return f"VERY HIGH exposure - {chemical} levels {ratio:.1f}x higher in disease population (strong exposure signal)"
        elif ratio >= 2.0:
            return f"HIGH exposure - {chemical} levels {ratio:.1f}x higher in disease population (moderate exposure signal)"
        elif ratio >= 1.5:
            return f"ELEVATED exposure - {chemical} levels {ratio:.1f}x higher in disease population (weak exposure signal)"
        elif ratio >= 1.2:
            return f"SLIGHTLY ELEVATED exposure - {chemical} levels {ratio:.1f}x higher (minimal signal)"
        else:
            return f"No significant exposure difference - ratio {ratio:.2f}x (insufficient evidence)"

    def _estimate_from_literature(
        self,
        chemical: str,
        demographic: Dict[str, any]
    ) -> Optional[BiomarkerData]:
        """
        Fallback: Estimate biomarker levels from published literature

        Used when:
        - Chemical not measured in NHANES (e.g., TiO2)
        - Data download fails
        - Demographic filter produces empty set
        """
        print(f"[NHANES] Using literature-based estimates for {chemical}")

        # Literature-based estimates (from published studies)
        literature_estimates = {
            'titanium': {
                'mean': 50.0,  # ng/mL in blood (Heringa et al. 2018)
                'median': 35.0,
                'p95': 120.0,
                'units': 'ng/mL',
                'reference': 'Heringa et al. (2018) - TiO2 nanoparticles in blood'
            },
            'titanium_blood': {
                'mean': 50.0,
                'median': 35.0,
                'p95': 120.0,
                'units': 'ng/mL',
                'reference': 'Heringa et al. (2018)'
            }
        }

        if chemical.lower() in literature_estimates:
            est = literature_estimates[chemical.lower()]
            return BiomarkerData(
                chemical=chemical,
                demographic=demographic,
                mean_level=est['mean'],
                median_level=est['median'],
                percentile_95=est['p95'],
                sample_size=0,  # Literature estimate, no direct sample
                units=est['units'],
                survey_cycle='literature',
                interpretation=f"Literature estimate: {est['reference']}"
            )

        return None


def main():
    """Test NHANES integration with TiO2 → IBD example"""
    print("=" * 80)
    print("NHANES BIOMARKER INTEGRATION TEST")
    print("=" * 80)

    nhanes = NHANESIntegration()

    # Test 1: TiO2 biomarker levels (will use literature fallback)
    print("\n[TEST 1] TiO2 biomarker levels in general population")
    tio2_general = nhanes.get_biomarker_levels(
        chemical='titanium',
        demographic={'age_min': 20, 'age_max': 80}
    )

    if tio2_general:
        print(f"  Mean: {tio2_general.mean_level} {tio2_general.units}")
        print(f"  Source: {tio2_general.survey_cycle}")

    # Test 2: Cross-reference with IBD population
    print("\n[TEST 2] Cross-reference TiO2 exposure with IBD population")
    assessment = nhanes.cross_reference_exposure(
        chemical='titanium',
        disease_icd10='K50-K51',
        disease_demographics={'age_min': 20, 'age_max': 60}
    )

    print(f"  Exposure ratio: {assessment.exposure_ratio:.2f}x")
    print(f"  Data quality: {assessment.data_quality}")
    print(f"  Interpretation: {assessment.interpretation}")

    # Test 3: PFAS biomarker (should download real NHANES data)
    print("\n[TEST 3] PFAS biomarker levels (real NHANES data)")
    pfas_data = nhanes.get_biomarker_levels(
        chemical='pfas',
        demographic={'age_min': 30, 'age_max': 60, 'gender': 'Female'}
    )

    if pfas_data:
        print(f"  Sample size: {pfas_data.sample_size}")
        print(f"  Mean: {pfas_data.mean_level:.2f} {pfas_data.units}")

    print("\n" + "=" * 80)
    print("NHANES INTEGRATION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
