"""
Comprehensive Disease Epidemiology Database

Sources:
- SEER Cancer Statistics Review (cancer incidence by age group)
- CDC WONDER (mortality data)
- Global Burden of Disease Study 2021
- Published epidemiological studies (cited per disease)

This module provides incidence/prevalence data for:
- Cancers (with age stratification)
- Inflammatory bowel disease (IBD)
- Autoimmune diseases
- Neurological conditions
- Other chronic diseases relevant to tort litigation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class TrendDirection(Enum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    VARIABLE = "VARIABLE"


@dataclass
class AgeStratifiedRate:
    """Incidence/prevalence rate for a specific age group."""
    age_group: str  # e.g., "20-34", "35-49", "50-64"
    rate: float     # per 100,000
    trend: TrendDirection
    annual_percent_change: float  # APC


@dataclass
class DiseaseEpidemiology:
    """Epidemiological data for a disease."""
    disease_name: str
    icd10_codes: List[str]
    overall_incidence: float  # per 100,000, age-adjusted
    overall_prevalence: Optional[float]  # per 100,000
    age_stratified_rates: List[AgeStratifiedRate]
    trend_direction: TrendDirection
    percent_change_10yr: float
    data_years: str  # e.g., "2010-2020"
    data_source: str
    citation: str
    notes: str
    potential_exposures: List[str]  # Known/suspected exposures


# =============================================================================
# CANCER DATA WITH AGE STRATIFICATION
# =============================================================================

# Colorectal Cancer - THE KEY EPIDEMIOLOGICAL SIGNAL
# Young adults (under 50) showing ALARMING increase
COLORECTAL_CANCER = DiseaseEpidemiology(
    disease_name="Colorectal Cancer",
    icd10_codes=["C18", "C19", "C20"],
    overall_incidence=35.3,  # per 100k, 2020
    overall_prevalence=None,
    age_stratified_rates=[
        AgeStratifiedRate("20-34", 4.1, TrendDirection.INCREASING, 2.2),   # +2.2%/year
        AgeStratifiedRate("35-49", 15.8, TrendDirection.INCREASING, 1.9),  # +1.9%/year
        AgeStratifiedRate("50-64", 58.3, TrendDirection.DECREASING, -2.1),
        AgeStratifiedRate("65-74", 114.2, TrendDirection.DECREASING, -3.2),
        AgeStratifiedRate("75+", 168.5, TrendDirection.DECREASING, -3.5),
    ],
    trend_direction=TrendDirection.VARIABLE,
    percent_change_10yr=-14.5,  # Overall decline (driven by older adults)
    data_years="2010-2020",
    data_source="SEER Cancer Statistics Review",
    citation="Siegel RL et al. CA Cancer J Clin 2024; SEER*Stat 2020",
    notes="CRITICAL SIGNAL: Under-50 CRC increasing 2%/year since mid-1990s. "
          "Birth cohort effect suggests environmental exposure around 1960s-1990s. "
          "Screening explains decline in 50+, but NOT the young adult increase.",
    potential_exposures=[
        "Ultra-processed foods",
        "Obesity epidemic",
        "Sedentary lifestyle",
        "Microbiome disruption",
        "Artificial sweeteners",
        "Antibiotics (early life)",
        "Red/processed meat",
        "Environmental chemicals (unknown)",
    ]
)

# Thyroid Cancer - Was overdiagnosis, now declining
THYROID_CANCER = DiseaseEpidemiology(
    disease_name="Thyroid Cancer",
    icd10_codes=["C73"],
    overall_incidence=12.6,
    overall_prevalence=None,
    age_stratified_rates=[
        AgeStratifiedRate("20-34", 9.8, TrendDirection.STABLE, -0.5),
        AgeStratifiedRate("35-49", 20.2, TrendDirection.DECREASING, -2.1),
        AgeStratifiedRate("50-64", 24.8, TrendDirection.DECREASING, -3.2),
        AgeStratifiedRate("65-74", 24.5, TrendDirection.DECREASING, -2.8),
        AgeStratifiedRate("75+", 18.2, TrendDirection.STABLE, -0.3),
    ],
    trend_direction=TrendDirection.DECREASING,
    percent_change_10yr=-10.0,
    data_years="2010-2020",
    data_source="SEER Cancer Statistics Review",
    citation="SEER*Stat 2020; Lim H et al. JAMA 2017",
    notes="Peaked 2013-2015 due to overdiagnosis (incidental detection). "
          "Now declining after guideline changes. Not a true environmental signal.",
    potential_exposures=["Radiation (historical)", "Overdiagnosis (imaging)"]
)

# Liver Cancer - Rising due to Hepatitis C cohort
LIVER_CANCER = DiseaseEpidemiology(
    disease_name="Liver and Intrahepatic Bile Duct Cancer",
    icd10_codes=["C22"],
    overall_incidence=8.4,
    overall_prevalence=None,
    age_stratified_rates=[
        AgeStratifiedRate("20-34", 0.5, TrendDirection.STABLE, 0.2),
        AgeStratifiedRate("35-49", 4.2, TrendDirection.STABLE, 0.5),
        AgeStratifiedRate("50-64", 14.8, TrendDirection.INCREASING, 1.2),
        AgeStratifiedRate("65-74", 20.2, TrendDirection.STABLE, 0.3),
        AgeStratifiedRate("75+", 16.8, TrendDirection.DECREASING, -1.1),
    ],
    trend_direction=TrendDirection.STABLE,
    percent_change_10yr=7.7,
    data_years="2010-2020",
    data_source="SEER Cancer Statistics Review",
    citation="SEER*Stat 2020",
    notes="Baby boomer cohort effect from Hepatitis C infection. "
          "Now stabilizing as HCV treatment (DAAs) and hepatitis prevention improve.",
    potential_exposures=["Hepatitis B/C", "Alcohol", "NAFLD/Obesity", "Aflatoxins"]
)

# Melanoma - Continuing to rise
MELANOMA = DiseaseEpidemiology(
    disease_name="Melanoma of the Skin",
    icd10_codes=["C43"],
    overall_incidence=22.4,
    overall_prevalence=None,
    age_stratified_rates=[
        AgeStratifiedRate("20-34", 7.2, TrendDirection.STABLE, 0.3),
        AgeStratifiedRate("35-49", 18.5, TrendDirection.INCREASING, 1.2),
        AgeStratifiedRate("50-64", 35.2, TrendDirection.INCREASING, 1.5),
        AgeStratifiedRate("65-74", 58.8, TrendDirection.INCREASING, 2.1),
        AgeStratifiedRate("75+", 72.5, TrendDirection.INCREASING, 2.8),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=6.7,
    data_years="2010-2020",
    data_source="SEER Cancer Statistics Review",
    citation="SEER*Stat 2020",
    notes="Continuing increase, especially in older adults. "
          "UV exposure, tanning bed use, ozone depletion.",
    potential_exposures=["UV radiation", "Tanning beds", "Sun exposure (historical)"]
)


# =============================================================================
# INFLAMMATORY BOWEL DISEASE (IBD)
# =============================================================================

IBD_CROHNS = DiseaseEpidemiology(
    disease_name="Crohn's Disease",
    icd10_codes=["K50"],
    overall_incidence=10.7,  # per 100k
    overall_prevalence=201,   # per 100k
    age_stratified_rates=[
        AgeStratifiedRate("0-17", 4.8, TrendDirection.INCREASING, 2.5),
        AgeStratifiedRate("18-34", 15.2, TrendDirection.INCREASING, 2.1),
        AgeStratifiedRate("35-49", 12.8, TrendDirection.INCREASING, 1.8),
        AgeStratifiedRate("50-64", 9.5, TrendDirection.INCREASING, 1.5),
        AgeStratifiedRate("65+", 6.2, TrendDirection.STABLE, 0.5),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=35.0,  # Significant increase
    data_years="2010-2020",
    data_source="Global Burden of Disease Study 2021; NHDS",
    citation="GBD 2021 IBD Collaborators. Lancet Gastroenterol Hepatol 2024",
    notes="SIGNIFICANT INCREASE especially in children and young adults. "
          "Strongest in Western countries but now rising globally. "
          "Microbiome disruption suspected as major factor.",
    potential_exposures=[
        "Ultra-processed foods",
        "Food additives (emulsifiers, carrageenan)",
        "Titanium dioxide (E171)",
        "Antibiotics (early life)",
        "Microbiome disruption",
        "Western diet",
        "Environmental chemicals",
    ]
)

IBD_ULCERATIVE_COLITIS = DiseaseEpidemiology(
    disease_name="Ulcerative Colitis",
    icd10_codes=["K51"],
    overall_incidence=9.2,
    overall_prevalence=286,
    age_stratified_rates=[
        AgeStratifiedRate("0-17", 3.2, TrendDirection.INCREASING, 2.0),
        AgeStratifiedRate("18-34", 12.8, TrendDirection.INCREASING, 1.8),
        AgeStratifiedRate("35-49", 11.5, TrendDirection.INCREASING, 1.5),
        AgeStratifiedRate("50-64", 9.8, TrendDirection.STABLE, 0.8),
        AgeStratifiedRate("65+", 7.2, TrendDirection.STABLE, 0.3),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=28.0,
    data_years="2010-2020",
    data_source="Global Burden of Disease Study 2021",
    citation="GBD 2021 IBD Collaborators. Lancet Gastroenterol Hepatol 2024",
    notes="Similar pattern to Crohn's - increasing in young populations. "
          "Strong association with Western lifestyle adoption.",
    potential_exposures=[
        "Ultra-processed foods",
        "Food additives",
        "NSAIDs",
        "Microbiome disruption",
    ]
)


# =============================================================================
# AUTOIMMUNE DISEASES
# =============================================================================

MULTIPLE_SCLEROSIS = DiseaseEpidemiology(
    disease_name="Multiple Sclerosis",
    icd10_codes=["G35"],
    overall_incidence=3.2,
    overall_prevalence=165,
    age_stratified_rates=[
        AgeStratifiedRate("15-24", 2.8, TrendDirection.INCREASING, 1.5),
        AgeStratifiedRate("25-34", 5.2, TrendDirection.INCREASING, 1.8),
        AgeStratifiedRate("35-44", 4.5, TrendDirection.STABLE, 0.5),
        AgeStratifiedRate("45-54", 3.2, TrendDirection.STABLE, 0.2),
        AgeStratifiedRate("55+", 1.8, TrendDirection.STABLE, 0.1),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=18.0,
    data_years="2010-2021",
    data_source="Global Burden of Disease Study 2021",
    citation="GBD 2021 Neurological Disorders Collaborators",
    notes="Steadily increasing globally. Strong latitude gradient (more common "
          "further from equator). Vitamin D, EBV virus, and environmental factors suspected.",
    potential_exposures=[
        "EBV infection",
        "Vitamin D deficiency",
        "Smoking",
        "Organic solvents",
        "Geographic latitude",
    ]
)

RHEUMATOID_ARTHRITIS = DiseaseEpidemiology(
    disease_name="Rheumatoid Arthritis",
    icd10_codes=["M05", "M06"],
    overall_incidence=9.5,
    overall_prevalence=510,
    age_stratified_rates=[
        AgeStratifiedRate("15-39", 4.2, TrendDirection.INCREASING, 1.2),
        AgeStratifiedRate("40-54", 12.5, TrendDirection.STABLE, 0.5),
        AgeStratifiedRate("55-69", 18.2, TrendDirection.STABLE, 0.2),
        AgeStratifiedRate("70+", 15.8, TrendDirection.STABLE, -0.1),
    ],
    trend_direction=TrendDirection.STABLE,
    percent_change_10yr=8.0,
    data_years="2010-2021",
    data_source="Global Burden of Disease Study 2021",
    citation="GBD 2021",
    notes="Relatively stable but slight increase in younger adults.",
    potential_exposures=[
        "Smoking",
        "Silica dust",
        "Genetics",
        "Periodontal disease",
    ]
)

SYSTEMIC_LUPUS = DiseaseEpidemiology(
    disease_name="Systemic Lupus Erythematosus (SLE)",
    icd10_codes=["M32"],
    overall_incidence=5.1,
    overall_prevalence=72,
    age_stratified_rates=[
        AgeStratifiedRate("15-24", 6.2, TrendDirection.INCREASING, 1.5),
        AgeStratifiedRate("25-44", 8.5, TrendDirection.STABLE, 0.8),
        AgeStratifiedRate("45-64", 4.8, TrendDirection.STABLE, 0.3),
        AgeStratifiedRate("65+", 2.2, TrendDirection.STABLE, 0.1),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=12.0,
    data_years="2010-2021",
    data_source="Global Burden of Disease Study 2021",
    citation="GBD 2021; Rees F et al. Nat Rev Rheumatol 2017",
    notes="More common in women (9:1). Increasing incidence in young adults. "
          "Disproportionately affects Black and Hispanic populations.",
    potential_exposures=[
        "UV light",
        "Silica dust",
        "Infections (EBV)",
        "Drugs (hydralazine, procainamide)",
    ]
)

TYPE_1_DIABETES = DiseaseEpidemiology(
    disease_name="Type 1 Diabetes",
    icd10_codes=["E10"],
    overall_incidence=22.0,  # per 100k in under-20s
    overall_prevalence=520,
    age_stratified_rates=[
        AgeStratifiedRate("0-4", 18.5, TrendDirection.INCREASING, 3.2),
        AgeStratifiedRate("5-9", 28.5, TrendDirection.INCREASING, 3.5),
        AgeStratifiedRate("10-14", 32.8, TrendDirection.INCREASING, 3.8),
        AgeStratifiedRate("15-19", 18.2, TrendDirection.INCREASING, 2.5),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=40.0,
    data_years="2010-2020",
    data_source="SEARCH for Diabetes in Youth Study",
    citation="Lawrence JM et al. JAMA 2021; Mayer-Davis EJ et al. N Engl J Med 2017",
    notes="ALARMING 3-4% annual increase globally for 30+ years. "
          "One of the clearest signals of environmental change. "
          "'Accelerator hypothesis' suggests environmental triggers.",
    potential_exposures=[
        "Viral infections",
        "Gut microbiome disruption",
        "Vitamin D deficiency",
        "Early dietary factors",
        "Enteroviruses",
        "Environmental chemicals (unknown)",
    ]
)


# =============================================================================
# NEUROLOGICAL CONDITIONS
# =============================================================================

PARKINSONS_DISEASE = DiseaseEpidemiology(
    disease_name="Parkinson's Disease",
    icd10_codes=["G20"],
    overall_incidence=12.5,
    overall_prevalence=160,
    age_stratified_rates=[
        AgeStratifiedRate("40-49", 1.2, TrendDirection.STABLE, 0.5),
        AgeStratifiedRate("50-59", 5.8, TrendDirection.STABLE, 0.8),
        AgeStratifiedRate("60-69", 18.5, TrendDirection.INCREASING, 1.2),
        AgeStratifiedRate("70-79", 52.8, TrendDirection.INCREASING, 1.5),
        AgeStratifiedRate("80+", 82.5, TrendDirection.INCREASING, 2.0),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=22.0,
    data_years="2010-2021",
    data_source="Global Burden of Disease Study 2021",
    citation="GBD 2021; Dorsey ER et al. JAMA Neurol 2018",
    notes="Fastest growing neurological disorder. 'Parkinson Pandemic' predicted. "
          "Strong associations with pesticide exposure, especially paraquat.",
    potential_exposures=[
        "Paraquat (herbicide)",
        "Rotenone (pesticide)",
        "MPTP",
        "Head trauma",
        "Rural living/well water",
        "Trichloroethylene (TCE)",
    ]
)

AUTISM_SPECTRUM = DiseaseEpidemiology(
    disease_name="Autism Spectrum Disorder",
    icd10_codes=["F84"],
    overall_incidence=None,  # Usually measured as prevalence
    overall_prevalence=2760,  # 1 in 36 children (2023 CDC)
    age_stratified_rates=[
        AgeStratifiedRate("8 years old", 2760, TrendDirection.INCREASING, 8.0),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=150.0,  # 1 in 150 (2002) to 1 in 36 (2023)
    data_years="2002-2023",
    data_source="CDC ADDM Network",
    citation="Maenner MJ et al. MMWR 2023",
    notes="DRAMATIC increase from 1 in 150 (2002) to 1 in 36 (2023). "
          "Debate on true increase vs diagnostic expansion. "
          "Some increase likely real based on birth cohort analyses.",
    potential_exposures=[
        "Prenatal acetaminophen",
        "Air pollution",
        "Pesticides",
        "Advanced parental age",
        "Diagnostic changes (partial)",
    ]
)

ADHD = DiseaseEpidemiology(
    disease_name="Attention-Deficit/Hyperactivity Disorder",
    icd10_codes=["F90"],
    overall_incidence=None,
    overall_prevalence=9400,  # 9.4% of children
    age_stratified_rates=[
        AgeStratifiedRate("3-5", 2400, TrendDirection.INCREASING, 3.0),
        AgeStratifiedRate("6-11", 10500, TrendDirection.INCREASING, 2.5),
        AgeStratifiedRate("12-17", 13200, TrendDirection.INCREASING, 2.0),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=42.0,
    data_years="2003-2020",
    data_source="National Survey of Children's Health",
    citation="Danielson ML et al. J Clin Child Adolesc Psychol 2018",
    notes="Substantial increase in diagnosis. Combination of increased "
          "awareness/diagnosis AND potential environmental factors.",
    potential_exposures=[
        "Lead exposure",
        "Prenatal smoking",
        "Artificial food dyes",
        "Pesticides (organophosphates)",
        "Prenatal alcohol",
    ]
)


# =============================================================================
# OTHER RELEVANT CONDITIONS
# =============================================================================

GASTROPARESIS = DiseaseEpidemiology(
    disease_name="Gastroparesis (Stomach Paralysis)",
    icd10_codes=["K31.84"],
    overall_incidence=6.3,  # per 100k
    overall_prevalence=37.8,
    age_stratified_rates=[
        AgeStratifiedRate("18-34", 8.5, TrendDirection.INCREASING, 5.0),
        AgeStratifiedRate("35-49", 12.2, TrendDirection.INCREASING, 4.2),
        AgeStratifiedRate("50-64", 10.8, TrendDirection.INCREASING, 3.5),
        AgeStratifiedRate("65+", 7.5, TrendDirection.STABLE, 1.0),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=85.0,  # Significant increase, especially with GLP-1 drugs
    data_years="2015-2024",
    data_source="Healthcare utilization data; FAERS",
    citation="Waghray A et al. Dig Dis Sci 2024; FDA FAERS analysis",
    notes="EMERGING SIGNAL with GLP-1 agonists (Ozempic, Wegovy, Zepbound). "
          "Litigation beginning. FDA investigating.",
    potential_exposures=[
        "GLP-1 agonists (semaglutide, tirzepatide)",
        "Diabetes",
        "Post-surgical",
        "Idiopathic",
    ]
)

UTERINE_CANCER = DiseaseEpidemiology(
    disease_name="Uterine Cancer (Endometrial)",
    icd10_codes=["C54", "C55"],
    overall_incidence=28.1,
    overall_prevalence=None,
    age_stratified_rates=[
        AgeStratifiedRate("40-49", 14.2, TrendDirection.INCREASING, 1.8),
        AgeStratifiedRate("50-59", 35.8, TrendDirection.INCREASING, 1.5),
        AgeStratifiedRate("60-69", 52.5, TrendDirection.INCREASING, 1.2),
        AgeStratifiedRate("70+", 48.2, TrendDirection.STABLE, 0.5),
    ],
    trend_direction=TrendDirection.INCREASING,
    percent_change_10yr=15.0,
    data_years="2010-2020",
    data_source="SEER Cancer Statistics Review",
    citation="SEER*Stat 2020; Clarke MA et al. JNCI 2022",
    notes="Increasing, especially in younger women. "
          "Hair relaxer litigation (Black women 40% elevated risk per NIH study).",
    potential_exposures=[
        "Hair relaxer chemicals",
        "Obesity",
        "Estrogen therapy",
        "Tamoxifen",
    ]
)


# =============================================================================
# DATABASE CLASS
# =============================================================================

class DiseaseEpidemiologyDatabase:
    """Database of comprehensive disease epidemiology."""

    def __init__(self):
        self.diseases = {
            # Cancers
            "colorectal_cancer": COLORECTAL_CANCER,
            "thyroid_cancer": THYROID_CANCER,
            "liver_cancer": LIVER_CANCER,
            "melanoma": MELANOMA,
            "uterine_cancer": UTERINE_CANCER,

            # IBD
            "crohns_disease": IBD_CROHNS,
            "ulcerative_colitis": IBD_ULCERATIVE_COLITIS,

            # Autoimmune
            "multiple_sclerosis": MULTIPLE_SCLEROSIS,
            "rheumatoid_arthritis": RHEUMATOID_ARTHRITIS,
            "systemic_lupus": SYSTEMIC_LUPUS,
            "type_1_diabetes": TYPE_1_DIABETES,

            # Neurological
            "parkinsons": PARKINSONS_DISEASE,
            "autism": AUTISM_SPECTRUM,
            "adhd": ADHD,

            # Other
            "gastroparesis": GASTROPARESIS,
        }

    def get_disease(self, name: str) -> Optional[DiseaseEpidemiology]:
        """Get epidemiology data for a specific disease."""
        return self.diseases.get(name.lower().replace(" ", "_").replace("'", ""))

    def get_increasing_diseases(self) -> List[DiseaseEpidemiology]:
        """Get all diseases with increasing trends."""
        return [d for d in self.diseases.values()
                if d.trend_direction == TrendDirection.INCREASING]

    def get_young_adult_signals(self) -> List[Tuple[DiseaseEpidemiology, AgeStratifiedRate]]:
        """Get diseases with increasing rates in young adults (under 50)."""
        signals = []
        young_age_groups = ["0-17", "18-34", "20-34", "35-49", "15-24", "25-34",
                           "0-4", "5-9", "10-14", "15-19", "15-39", "3-5", "6-11", "12-17"]

        for disease in self.diseases.values():
            for rate in disease.age_stratified_rates:
                if (rate.age_group in young_age_groups and
                    rate.trend == TrendDirection.INCREASING and
                    rate.annual_percent_change >= 1.5):
                    signals.append((disease, rate))

        return signals

    def search_by_exposure(self, exposure: str) -> List[DiseaseEpidemiology]:
        """Find diseases associated with a specific exposure."""
        exposure_lower = exposure.lower()
        return [d for d in self.diseases.values()
                if any(exposure_lower in e.lower() for e in d.potential_exposures)]

    def get_litigation_relevant(self) -> List[DiseaseEpidemiology]:
        """Get diseases with potential litigation relevance."""
        # Keywords that suggest litigation potential
        keywords = ["litigation", "lawsuit", "emerged", "signal", "alarming"]
        return [d for d in self.diseases.values()
                if any(kw in d.notes.lower() for kw in keywords)]

    def get_stats(self) -> Dict:
        """Get database statistics."""
        increasing = len(self.get_increasing_diseases())
        return {
            "total_diseases": len(self.diseases),
            "increasing_trend": increasing,
            "decreasing_trend": len([d for d in self.diseases.values()
                                    if d.trend_direction == TrendDirection.DECREASING]),
            "stable_trend": len([d for d in self.diseases.values()
                                if d.trend_direction == TrendDirection.STABLE]),
            "young_adult_signals": len(self.get_young_adult_signals()),
        }


def main():
    """Test the disease epidemiology database."""
    db = DiseaseEpidemiologyDatabase()

    print("=" * 70)
    print("DISEASE EPIDEMIOLOGY DATABASE")
    print("=" * 70)

    stats = db.get_stats()
    print(f"\nDatabase Statistics:")
    print(f"  Total diseases: {stats['total_diseases']}")
    print(f"  Increasing trend: {stats['increasing_trend']}")
    print(f"  Young adult signals: {stats['young_adult_signals']}")

    print("\n" + "-" * 70)
    print("CRITICAL: Young Adult Disease Signals")
    print("-" * 70)
    for disease, rate in db.get_young_adult_signals():
        print(f"  {disease.disease_name} ({rate.age_group}): "
              f"+{rate.annual_percent_change}%/year")

    print("\n" + "-" * 70)
    print("Diseases Associated with Food Additives")
    print("-" * 70)
    for disease in db.search_by_exposure("food"):
        print(f"  - {disease.disease_name}: {disease.percent_change_10yr:+.0f}% (10yr)")

    print("\n" + "-" * 70)
    print("Diseases Associated with Pesticides")
    print("-" * 70)
    for disease in db.search_by_exposure("pesticide"):
        print(f"  - {disease.disease_name}: {disease.percent_change_10yr:+.0f}% (10yr)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
