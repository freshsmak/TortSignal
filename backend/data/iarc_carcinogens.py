"""
IARC Carcinogen Classifications Database

Source: IARC Monographs on the Identification of Carcinogenic Hazards to Humans
        Volumes 1-140 (as of November 2025)
URL: https://monographs.iarc.who.int/agents-classified-by-the-iarc/

Classifications:
- Group 1: Carcinogenic to humans (135 agents)
- Group 2A: Probably carcinogenic to humans (97 agents)
- Group 2B: Possibly carcinogenic to humans (324 agents)
- Group 3: Not classifiable (499 agents)

This module focuses on Group 1 and 2A agents as they are most relevant for litigation.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class IARCAgent:
    """IARC classified carcinogenic agent."""
    name: str
    group: str  # "1", "2A", "2B", "3"
    cas_number: Optional[str]
    volume: Optional[int]
    year: Optional[int]
    cancer_sites: List[str]  # Associated cancer types
    exposure_sources: List[str]  # How people are exposed
    notes: str = ""


# IARC GROUP 1 - CARCINOGENIC TO HUMANS (135 agents)
# These have SUFFICIENT evidence of carcinogenicity in humans
GROUP_1_CARCINOGENS = [
    # Chemicals
    IARCAgent("Acetaldehyde associated with alcohol consumption", "1", "75-07-0", 100, 2012, ["Esophageal"], ["Alcohol consumption"], ""),
    IARCAgent("Aflatoxins", "1", None, 100, 2012, ["Liver"], ["Contaminated food, peanuts, corn"], "Naturally occurring mycotoxins"),
    IARCAgent("Arsenic and inorganic arsenic compounds", "1", "7440-38-2", 100, 2012, ["Lung", "Skin", "Bladder", "Kidney"], ["Drinking water", "Occupational", "Pesticides"], ""),
    IARCAgent("Asbestos (all forms)", "1", None, 100, 2012, ["Lung", "Mesothelioma", "Larynx", "Ovary"], ["Construction", "Insulation", "Brake pads"], "Major litigation target"),
    IARCAgent("Benzene", "1", "71-43-2", 120, 2018, ["Leukemia (AML)"], ["Gasoline", "Petrochemical", "Cigarette smoke"], ""),
    IARCAgent("Benzidine", "1", "92-87-5", 100, 2012, ["Bladder"], ["Dye manufacturing"], ""),
    IARCAgent("Benzo[a]pyrene", "1", "50-32-8", 100, 2012, ["Lung", "Skin"], ["Combustion", "Grilled food", "Tobacco smoke"], "PAH"),
    IARCAgent("Beryllium and compounds", "1", "7440-41-7", 100, 2012, ["Lung"], ["Aerospace", "Electronics", "Nuclear"], ""),
    IARCAgent("1,3-Butadiene", "1", "106-99-0", 100, 2012, ["Leukemia", "Lymphoma"], ["Rubber manufacturing", "Petrochemical"], ""),
    IARCAgent("Cadmium and compounds", "1", "7440-43-9", 100, 2012, ["Lung", "Kidney"], ["Batteries", "Pigments", "Electroplating"], ""),
    IARCAgent("Chromium (VI) compounds", "1", None, 100, 2012, ["Lung", "Sinonasal"], ["Chrome plating", "Stainless steel welding"], ""),
    IARCAgent("Coal tar and coal-tar pitch", "1", "65996-93-2", 100, 2012, ["Skin", "Lung", "Bladder"], ["Roofing", "Paving", "Aluminum production"], ""),
    IARCAgent("Ethylene oxide", "1", "75-21-8", 100, 2012, ["Lymphoma", "Leukemia", "Breast"], ["Medical sterilization", "Chemical manufacturing"], ""),
    IARCAgent("Formaldehyde", "1", "50-00-0", 100, 2012, ["Nasopharyngeal", "Leukemia"], ["Pressed wood", "Textiles", "Healthcare"], "Major litigation target"),
    IARCAgent("Nickel compounds", "1", None, 100, 2012, ["Lung", "Sinonasal"], ["Stainless steel", "Batteries", "Plating"], ""),
    IARCAgent("Plutonium", "1", "7440-07-5", 100, 2012, ["Lung", "Liver", "Bone"], ["Nuclear workers"], ""),
    IARCAgent("Radon-222", "1", "14859-67-7", 100, 2012, ["Lung"], ["Indoor air", "Mining"], "Second leading cause of lung cancer"),
    IARCAgent("Silica dust, crystalline", "1", "14808-60-7", 100, 2012, ["Lung"], ["Mining", "Construction", "Sandblasting"], "Major litigation target"),
    IARCAgent("Sulfur mustard", "1", "505-60-2", 100, 2012, ["Lung", "Larynx"], ["Chemical warfare"], ""),
    IARCAgent("2,3,7,8-TCDD (Dioxin)", "1", "1746-01-6", 100, 2012, ["All cancers combined"], ["Herbicide contamination", "Incineration"], "Agent Orange component"),
    IARCAgent("Trichloroethylene", "1", "79-01-6", 106, 2014, ["Kidney", "Liver", "NHL"], ["Degreasing", "Dry cleaning"], ""),
    IARCAgent("Vinyl chloride", "1", "75-01-4", 100, 2012, ["Liver (angiosarcoma)", "Liver"], ["PVC manufacturing"], ""),

    # Biological agents
    IARCAgent("Epstein-Barr virus", "1", None, 100, 2012, ["Nasopharyngeal", "Lymphoma", "Gastric"], ["Ubiquitous infection"], ""),
    IARCAgent("Helicobacter pylori", "1", None, 100, 2012, ["Gastric", "MALT lymphoma"], ["Infection"], ""),
    IARCAgent("Hepatitis B virus", "1", None, 100, 2012, ["Liver"], ["Blood/sexual transmission"], ""),
    IARCAgent("Hepatitis C virus", "1", None, 100, 2012, ["Liver", "NHL"], ["Blood transmission"], ""),
    IARCAgent("HIV-1", "1", None, 100, 2012, ["Kaposi sarcoma", "NHL", "Cervix", "Others"], ["Blood/sexual transmission"], ""),
    IARCAgent("HPV types 16, 18, 31, 33, 35, 39, 45, 51, 52, 56, 58, 59", "1", None, 100, 2012, ["Cervix", "Anal", "Oropharyngeal", "Vulva", "Vagina", "Penis"], ["Sexual transmission"], ""),

    # Physical agents
    IARCAgent("Ionizing radiation (all types)", "1", None, 100, 2012, ["Multiple cancers"], ["Medical imaging", "Nuclear", "Radon"], ""),
    IARCAgent("Solar radiation", "1", None, 100, 2012, ["Skin (melanoma, BCC, SCC)", "Lip"], ["Sun exposure"], ""),
    IARCAgent("UV radiation (including tanning devices)", "1", None, 100, 2012, ["Skin (melanoma, BCC, SCC)"], ["Sun", "Tanning beds"], ""),

    # Lifestyle/Occupational
    IARCAgent("Alcoholic beverages", "1", None, 100, 2012, ["Oral", "Pharynx", "Larynx", "Esophagus", "Liver", "Colorectal", "Breast"], ["Drinking"], ""),
    IARCAgent("Tobacco smoking", "1", None, 100, 2012, ["Lung", "Oral", "Pharynx", "Larynx", "Esophagus", "Stomach", "Pancreas", "Kidney", "Bladder", "Cervix", "Colorectal", "Liver", "AML"], ["Smoking"], ""),
    IARCAgent("Smokeless tobacco", "1", None, 100, 2012, ["Oral", "Esophagus", "Pancreas"], ["Chewing tobacco, snuff"], ""),
    IARCAgent("Secondhand tobacco smoke", "1", None, 100, 2012, ["Lung"], ["Environmental exposure"], ""),
    IARCAgent("Processed meat", "1", None, 114, 2015, ["Colorectal"], ["Diet"], "Hot dogs, bacon, ham, sausages"),

    # Occupational exposures
    IARCAgent("Aluminum production", "1", None, 100, 2012, ["Lung", "Bladder"], ["Occupational"], ""),
    IARCAgent("Coal gasification", "1", None, 100, 2012, ["Lung", "Bladder", "Skin"], ["Occupational"], ""),
    IARCAgent("Coke production", "1", None, 100, 2012, ["Lung"], ["Occupational"], ""),
    IARCAgent("Iron and steel founding", "1", None, 100, 2012, ["Lung"], ["Occupational"], ""),
    IARCAgent("Leather dust", "1", None, 100, 2012, ["Sinonasal"], ["Shoe manufacturing"], ""),
    IARCAgent("Painting (occupational)", "1", None, 100, 2012, ["Lung", "Bladder", "Mesothelioma"], ["Occupational"], ""),
    IARCAgent("Rubber manufacturing industry", "1", None, 100, 2012, ["Bladder", "Lung", "Leukemia"], ["Occupational"], ""),
    IARCAgent("Wood dust", "1", None, 100, 2012, ["Sinonasal", "Nasopharyngeal"], ["Carpentry", "Furniture making"], ""),

    # Pharmaceuticals
    IARCAgent("Azathioprine", "1", "446-86-6", 100, 2012, ["Skin (SCC)", "NHL", "Liver"], ["Immunosuppressant drug"], ""),
    IARCAgent("Busulfan", "1", "55-98-1", 100, 2012, ["Leukemia"], ["Chemotherapy"], ""),
    IARCAgent("Chlorambucil", "1", "305-03-3", 100, 2012, ["Leukemia"], ["Chemotherapy"], ""),
    IARCAgent("Cyclophosphamide", "1", "50-18-0", 100, 2012, ["Bladder", "Leukemia"], ["Chemotherapy", "Immunosuppressant"], ""),
    IARCAgent("Cyclosporine", "1", "59865-13-3", 100, 2012, ["NHL", "Skin"], ["Immunosuppressant"], ""),
    IARCAgent("Diethylstilbestrol (DES)", "1", "56-53-1", 100, 2012, ["Breast", "Vagina/Cervix (clear cell)"], ["Historical pregnancy drug"], "Major litigation target"),
    IARCAgent("Estrogen-progestogen menopausal therapy", "1", None, 100, 2012, ["Breast", "Endometrium"], ["HRT"], ""),
    IARCAgent("Estrogen menopausal therapy", "1", None, 100, 2012, ["Endometrium", "Ovary"], ["HRT"], ""),
    IARCAgent("Melphalan", "1", "148-82-3", 100, 2012, ["Leukemia"], ["Chemotherapy"], ""),
    IARCAgent("MOPP chemotherapy", "1", None, 100, 2012, ["Leukemia", "Lung"], ["Hodgkin lymphoma treatment"], ""),
    IARCAgent("Tamoxifen", "1", "10540-29-1", 100, 2012, ["Endometrium"], ["Breast cancer treatment"], ""),
    IARCAgent("Thiotepa", "1", "52-24-4", 100, 2012, ["Leukemia"], ["Chemotherapy"], ""),

    # Recent additions (post-2020)
    IARCAgent("Opium consumption", "1", None, 126, 2020, ["Larynx", "Lung", "Pharynx", "Esophagus", "Bladder", "Pancreas"], ["Drug use"], ""),
    IARCAgent("Welding fumes", "1", None, 118, 2018, ["Lung"], ["Welding"], ""),
    IARCAgent("Lindane", "1", "58-89-9", 113, 2015, ["NHL"], ["Pesticide", "Lice treatment"], "Banned in many countries"),
    IARCAgent("Pentachlorophenol", "1", "87-86-5", 117, 2017, ["NHL"], ["Wood preservative"], ""),
    IARCAgent("PCBs (polychlorinated biphenyls)", "1", None, 107, 2016, ["Melanoma"], ["Electrical equipment", "Plasticizers"], "Banned but persistent"),
]

# IARC GROUP 2A - PROBABLY CARCINOGENIC (97 agents)
# These have LIMITED evidence in humans but SUFFICIENT in animals
GROUP_2A_CARCINOGENS = [
    # High-priority chemicals (high exposure potential)
    IARCAgent("Acrylamide", "2A", "79-06-1", 116, 2016, ["Kidney", "Endometrium"], ["Fried/baked starchy foods", "Coffee"], "Forms during high-heat cooking"),
    IARCAgent("Adriamycin (doxorubicin)", "2A", "23214-92-8", 100, 2012, ["Leukemia", "Breast"], ["Chemotherapy"], ""),
    IARCAgent("Androgenic steroids", "2A", None, 100, 2012, ["Liver"], ["Performance enhancement"], ""),
    IARCAgent("Bitumens (oxidized)", "2A", None, 103, 2013, ["Lung"], ["Roofing", "Paving"], ""),
    IARCAgent("Captafol", "2A", "2425-06-1", 53, 1991, ["Leukemia"], ["Fungicide"], ""),
    IARCAgent("Chloral and chloral hydrate", "2A", "302-17-0", 106, 2014, ["Thyroid"], ["Sedative"], ""),
    IARCAgent("Cobalt metal with tungsten carbide", "2A", None, 86, 2006, ["Lung"], ["Hard metal industry"], ""),
    IARCAgent("Creosotes", "2A", "8001-58-9", 92, 2010, ["Skin"], ["Wood preservation"], ""),
    IARCAgent("Dibenz[a,h]anthracene", "2A", "53-70-3", 92, 2010, ["Multiple"], ["Combustion products"], "PAH"),
    IARCAgent("DDT", "2A", "50-29-3", 113, 2015, ["Liver", "NHL"], ["Pesticide (historical)"], "Banned but persistent"),
    IARCAgent("Diazinon", "2A", "333-41-5", 112, 2015, ["NHL", "Leukemia"], ["Pesticide"], ""),
    IARCAgent("Epichlorohydrin", "2A", "106-89-8", 71, 1999, ["Lung", "NHL"], ["Chemical intermediate"], ""),
    IARCAgent("Ethyl carbamate (urethane)", "2A", "51-79-6", 96, 2010, ["Multiple"], ["Fermented foods/drinks"], ""),
    IARCAgent("Glyphosate", "2A", "1071-83-6", 112, 2015, ["NHL"], ["Herbicide (Roundup)"], "Major litigation target - Monsanto/Bayer"),
    IARCAgent("Glycidol", "2A", "556-52-5", 77, 2000, ["Multiple"], ["Food contaminant", "Chemical intermediate"], ""),
    IARCAgent("Hot beverages above 65°C", "2A", None, 116, 2016, ["Esophagus"], ["Very hot drinks"], ""),
    IARCAgent("Lead compounds, inorganic", "2A", None, 87, 2006, ["Lung", "Stomach", "Brain"], ["Batteries", "Paint (historical)", "Plumbing"], ""),
    IARCAgent("Malathion", "2A", "121-75-5", 112, 2015, ["NHL"], ["Pesticide"], ""),
    IARCAgent("Methyl bromide", "2A", "74-83-9", 71, 1999, ["Prostate"], ["Fumigant"], ""),
    IARCAgent("Night shift work", "2A", None, 124, 2019, ["Breast"], ["Circadian disruption"], ""),
    IARCAgent("Nitrate/nitrite (ingested under conditions that result in endogenous nitrosation)", "2A", None, 114, 2015, ["Colorectal", "Stomach"], ["Processed meat", "Water"], ""),
    IARCAgent("Non-arsenical insecticides (occupational)", "2A", None, 112, 2015, ["Lung", "NHL"], ["Occupational"], ""),
    IARCAgent("Petroleum refining (occupational)", "2A", None, 45, 1989, ["Leukemia", "Skin"], ["Occupational"], ""),
    IARCAgent("Red meat", "2A", None, 114, 2015, ["Colorectal"], ["Diet"], "Beef, pork, lamb, goat"),
    IARCAgent("Shiftwork involving circadian disruption", "2A", None, 124, 2019, ["Breast"], ["Night work"], ""),
    IARCAgent("Silicon carbide whiskers", "2A", None, 111, 2017, ["Lung"], ["Industrial abrasives"], ""),
    IARCAgent("Styrene", "2A", "100-42-5", 121, 2019, ["Lymphohematopoietic"], ["Plastics", "Rubber"], ""),
    IARCAgent("Tris(2,3-dibromopropyl) phosphate", "2A", "126-72-7", 71, 1999, ["Multiple"], ["Flame retardant (historical)"], ""),
    IARCAgent("Vinyl bromide", "2A", "593-60-2", 97, 2008, ["Liver"], ["Chemical intermediate"], ""),
    IARCAgent("Vinyl fluoride", "2A", "75-02-5", 97, 2008, ["Liver"], ["Polymer production"], ""),

    # PFAS compounds (emerging concern)
    IARCAgent("PFOA (perfluorooctanoic acid)", "2A", "335-67-1", 135, 2024, ["Kidney", "Testicular"], ["Teflon manufacturing", "Firefighting foam", "Stain resistance"], "Major litigation target - 3M, DuPont"),
    IARCAgent("PFOS (perfluorooctane sulfonic acid)", "2A", "1763-23-1", 135, 2024, ["Kidney", "Liver"], ["Firefighting foam", "Stain resistance"], "Major litigation target"),
]

# High-exposure chemicals requiring monitoring
HIGH_PRIORITY_EXPOSURE_CHEMICALS = [
    # Food additives and contaminants
    {"name": "Titanium dioxide (E171)", "concern": "Genotoxicity", "exposure": "Food, cosmetics, pharmaceuticals", "status": "Banned EU 2022, allowed US", "regulatory_divergence": True},
    {"name": "BPA (Bisphenol A)", "concern": "Endocrine disruption", "exposure": "Plastics, can linings, receipts", "status": "Restricted", "regulatory_divergence": False},
    {"name": "BPS (Bisphenol S)", "concern": "Endocrine disruption", "exposure": "BPA replacement", "status": "Prop 65 listed 2025", "regulatory_divergence": False},
    {"name": "Artificial food dyes (Red 40, Yellow 5, Yellow 6)", "concern": "Behavioral effects", "exposure": "Processed foods", "status": "Banned EU, allowed US", "regulatory_divergence": True},
    {"name": "Brominated vegetable oil (BVO)", "concern": "Organ damage", "exposure": "Citrus sodas", "status": "Banned 2024", "regulatory_divergence": False},
    {"name": "Potassium bromate", "concern": "Carcinogenicity", "exposure": "Bread flour", "status": "Banned EU/UK/Canada, allowed US", "regulatory_divergence": True},

    # Personal care
    {"name": "Parabens (methylparaben, propylparaben)", "concern": "Endocrine disruption", "exposure": "Cosmetics, lotions", "status": "Restricted EU", "regulatory_divergence": True},
    {"name": "Phthalates (DEHP, DBP, BBP)", "concern": "Endocrine disruption, reproductive", "exposure": "Plastics, cosmetics, flooring", "status": "Restricted varying", "regulatory_divergence": True},
    {"name": "Formaldehyde-releasing preservatives", "concern": "Carcinogenicity", "exposure": "Hair products (Brazilian blowout)", "status": "Restricted", "regulatory_divergence": False},
    {"name": "Talc (with asbestos contamination)", "concern": "Mesothelioma, ovarian cancer", "exposure": "Baby powder, cosmetics", "status": "Major litigation (J&J)", "regulatory_divergence": False},

    # Environmental/Industrial
    {"name": "PFAS (forever chemicals)", "concern": "Cancer, immune, thyroid", "exposure": "Water, nonstick, textiles, firefighting foam", "status": "Emerging regulation", "regulatory_divergence": False},
    {"name": "Microplastics", "concern": "Unknown long-term", "exposure": "Ubiquitous", "status": "Unregulated", "regulatory_divergence": False},
    {"name": "Glyphosate (Roundup)", "concern": "NHL (IARC 2A)", "exposure": "Food residues, occupational", "status": "Major litigation ongoing", "regulatory_divergence": True},
    {"name": "Paraquat", "concern": "Parkinson's disease", "exposure": "Agricultural workers", "status": "Banned EU, allowed US", "regulatory_divergence": True},
    {"name": "Chlorpyrifos", "concern": "Neurodevelopmental", "exposure": "Food residues", "status": "Banned 2022", "regulatory_divergence": False},

    # Pharmaceutical
    {"name": "Ranitidine (Zantac)", "concern": "NDMA contamination", "exposure": "Heartburn medication", "status": "Recalled 2020, major litigation", "regulatory_divergence": False},
    {"name": "Valsartan/Losartan (ARBs)", "concern": "NDMA/NDEA contamination", "exposure": "Blood pressure medication", "status": "Recalls ongoing", "regulatory_divergence": False},
    {"name": "Acetaminophen (prenatal)", "concern": "ADHD, autism", "exposure": "OTC pain reliever during pregnancy", "status": "Litigation emerging", "regulatory_divergence": False},
    {"name": "Proton pump inhibitors (PPIs)", "concern": "Kidney disease, dementia", "exposure": "Heartburn medication", "status": "Litigation ongoing", "regulatory_divergence": False},

    # Occupational
    {"name": "Benzene (occupational)", "concern": "Leukemia (IARC 1)", "exposure": "Petrochemical, gasoline", "status": "Regulated but litigation ongoing", "regulatory_divergence": False},
    {"name": "Asbestos (continuing exposure)", "concern": "Mesothelioma (IARC 1)", "exposure": "Renovation, brake pads, gaskets", "status": "Banned most uses but legacy exposure", "regulatory_divergence": True},
]


class IARCDatabase:
    """Database of IARC carcinogen classifications."""

    def __init__(self):
        self.group_1 = GROUP_1_CARCINOGENS
        self.group_2a = GROUP_2A_CARCINOGENS
        self.high_priority = HIGH_PRIORITY_EXPOSURE_CHEMICALS

    def get_all_group_1(self) -> List[IARCAgent]:
        """Get all Group 1 (carcinogenic) agents."""
        return self.group_1

    def get_all_group_2a(self) -> List[IARCAgent]:
        """Get all Group 2A (probably carcinogenic) agents."""
        return self.group_2a

    def search_by_cancer_site(self, cancer_site: str) -> List[IARCAgent]:
        """Find agents associated with a specific cancer site."""
        results = []
        cancer_lower = cancer_site.lower()

        for agent in self.group_1 + self.group_2a:
            for site in agent.cancer_sites:
                if cancer_lower in site.lower():
                    results.append(agent)
                    break

        return results

    def search_by_exposure(self, exposure_keyword: str) -> List[IARCAgent]:
        """Find agents by exposure source."""
        results = []
        keyword_lower = exposure_keyword.lower()

        for agent in self.group_1 + self.group_2a:
            for source in agent.exposure_sources:
                if keyword_lower in source.lower():
                    results.append(agent)
                    break

        return results

    def get_litigation_targets(self) -> List[IARCAgent]:
        """Get agents that are/were major litigation targets."""
        targets = []
        keywords = ["litigation", "major", "target"]

        for agent in self.group_1 + self.group_2a:
            if any(kw in agent.notes.lower() for kw in keywords):
                targets.append(agent)

        return targets

    def get_regulatory_divergence(self) -> List[Dict]:
        """Get chemicals with EU/US regulatory divergence."""
        return [c for c in self.high_priority if c.get("regulatory_divergence")]

    def get_stats(self) -> Dict:
        """Get database statistics."""
        return {
            "group_1_count": len(self.group_1),
            "group_2a_count": len(self.group_2a),
            "high_priority_count": len(self.high_priority),
            "total_agents": len(self.group_1) + len(self.group_2a),
            "cancer_sites_covered": len(set(
                site for agent in self.group_1 + self.group_2a
                for site in agent.cancer_sites
            )),
        }


def main():
    """Test the IARC database."""
    db = IARCDatabase()

    print("=" * 70)
    print("IARC CARCINOGEN DATABASE")
    print("=" * 70)

    stats = db.get_stats()
    print(f"\nDatabase Statistics:")
    print(f"  Group 1 agents: {stats['group_1_count']}")
    print(f"  Group 2A agents: {stats['group_2a_count']}")
    print(f"  High-priority chemicals: {stats['high_priority_count']}")
    print(f"  Cancer sites covered: {stats['cancer_sites_covered']}")

    print("\n" + "-" * 70)
    print("Known Litigation Targets:")
    for agent in db.get_litigation_targets():
        print(f"  - {agent.name} ({agent.group}): {', '.join(agent.cancer_sites)}")

    print("\n" + "-" * 70)
    print("EU/US Regulatory Divergence Chemicals:")
    for chem in db.get_regulatory_divergence():
        print(f"  - {chem['name']}: {chem['status']}")

    print("\n" + "-" * 70)
    print("Agents Associated with Lung Cancer:")
    for agent in db.search_by_cancer_site("lung")[:10]:
        print(f"  - {agent.name} (Group {agent.group})")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
