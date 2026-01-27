"""
IARC Carcinogen Classifications Database - Comprehensive Edition

Source: IARC Monographs on the Identification of Carcinogenic Hazards to Humans
        Volumes 1-140 (as of January 2026)
URL: https://monographs.iarc.who.int/agents-classified-by-the-iarc/

Classifications:
- Group 1: Carcinogenic to humans (135 agents)
- Group 2A: Probably carcinogenic to humans (97 agents)
- Group 2B: Possibly carcinogenic to humans (324 agents)
- Group 3: Not classifiable (499 agents)

Total: ~1,055 evaluated agents
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum


class IARCGroup(Enum):
    """IARC carcinogenicity classification groups."""
    GROUP_1 = "1"      # Carcinogenic to humans
    GROUP_2A = "2A"    # Probably carcinogenic to humans
    GROUP_2B = "2B"    # Possibly carcinogenic to humans
    GROUP_3 = "3"      # Not classifiable


@dataclass
class IARCAgent:
    """IARC classified carcinogenic agent."""
    name: str
    group: str  # "1", "2A", "2B", "3"
    cas_number: Optional[str] = None
    volume: Optional[int] = None
    year: Optional[int] = None
    cancer_sites: List[str] = field(default_factory=list)
    exposure_sources: List[str] = field(default_factory=list)
    notes: str = ""
    category: str = ""  # Chemical, Biological, Physical, Occupational, Lifestyle, Pharmaceutical


# =============================================================================
# IARC GROUP 1 - CARCINOGENIC TO HUMANS (135 agents)
# Sufficient evidence of carcinogenicity in humans
# =============================================================================

GROUP_1_CARCINOGENS = [
    # --- CHEMICALS (Alphabetical) ---
    IARCAgent("Acetaldehyde associated with alcohol consumption", "1", "75-07-0", 100, 2012,
              ["Esophagus", "Head and neck"], ["Alcohol consumption"], "", "Chemical"),
    IARCAgent("Aflatoxins (naturally occurring mixtures)", "1", None, 100, 2012,
              ["Liver (hepatocellular carcinoma)"], ["Contaminated food", "Peanuts", "Corn", "Tree nuts"],
              "Mycotoxin from Aspergillus", "Chemical"),
    IARCAgent("4-Aminobiphenyl", "1", "92-67-1", 100, 2012,
              ["Bladder"], ["Rubber industry", "Dye manufacturing"], "", "Chemical"),
    IARCAgent("Aristolochic acid", "1", None, 100, 2012,
              ["Renal pelvis", "Ureter", "Bladder"], ["Herbal medicines", "Dietary supplements"],
              "Found in Aristolochia plants", "Chemical"),
    IARCAgent("Arsenic and inorganic arsenic compounds", "1", "7440-38-2", 100, 2012,
              ["Lung", "Skin", "Bladder", "Kidney", "Liver"],
              ["Drinking water", "Occupational exposure", "Pesticides", "Wood preservatives"],
              "Major global health issue", "Chemical"),
    IARCAgent("Asbestos (all forms including actinolite, amosite, anthophyllite, chrysotile, crocidolite, tremolite)", "1", None, 100, 2012,
              ["Lung", "Mesothelioma", "Larynx", "Ovary"],
              ["Construction", "Insulation", "Brake pads", "Shipbuilding", "Mining"],
              "MAJOR LITIGATION TARGET", "Chemical"),
    IARCAgent("Benzene", "1", "71-43-2", 120, 2018,
              ["Acute myeloid leukemia (AML)", "Acute lymphocytic leukemia (ALL)"],
              ["Petroleum industry", "Gasoline", "Chemical manufacturing", "Cigarette smoke"],
              "MAJOR LITIGATION TARGET", "Chemical"),
    IARCAgent("Benzidine", "1", "92-87-5", 100, 2012,
              ["Bladder"], ["Dye manufacturing", "Rubber industry"], "", "Chemical"),
    IARCAgent("Benzo[a]pyrene", "1", "50-32-8", 100, 2012,
              ["Lung", "Skin"], ["Combustion products", "Grilled/smoked food", "Tobacco smoke", "Coal tar"],
              "Prototypical PAH", "Chemical"),
    IARCAgent("Beryllium and beryllium compounds", "1", "7440-41-7", 100, 2012,
              ["Lung"], ["Aerospace", "Electronics", "Nuclear industry", "Ceramics"], "", "Chemical"),
    IARCAgent("Bis(chloromethyl)ether and chloromethyl methyl ether", "1", "542-88-1", 100, 2012,
              ["Lung"], ["Chemical manufacturing"], "", "Chemical"),
    IARCAgent("1,3-Butadiene", "1", "106-99-0", 100, 2012,
              ["Hematolymphatic cancers"], ["Rubber manufacturing", "Petrochemical industry"], "", "Chemical"),
    IARCAgent("Cadmium and cadmium compounds", "1", "7440-43-9", 100, 2012,
              ["Lung", "Kidney"], ["Battery manufacturing", "Pigments", "Electroplating", "Plastics stabilizers"],
              "", "Chemical"),
    IARCAgent("Chlorambucil", "1", "305-03-3", 100, 2012,
              ["Leukemia"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Chlornaphazine", "1", "494-03-1", 100, 2012,
              ["Bladder"], ["Historical cancer treatment"], "Withdrawn", "Pharmaceutical"),
    IARCAgent("Chromium (VI) compounds", "1", None, 100, 2012,
              ["Lung", "Sinonasal cavity"], ["Chrome plating", "Stainless steel welding", "Pigments", "Leather tanning"],
              "", "Chemical"),
    IARCAgent("Coal gasification", "1", None, 100, 2012,
              ["Lung", "Bladder", "Skin"], ["Occupational exposure"], "", "Occupational"),
    IARCAgent("Coal-tar distillation", "1", None, 100, 2012,
              ["Skin", "Lung", "Bladder"], ["Occupational exposure"], "", "Occupational"),
    IARCAgent("Coal-tar pitch", "1", "65996-93-2", 100, 2012,
              ["Skin", "Lung", "Bladder"], ["Roofing", "Paving", "Aluminum production"], "", "Chemical"),
    IARCAgent("Coke production", "1", None, 100, 2012,
              ["Lung", "Kidney"], ["Steel industry"], "", "Occupational"),
    IARCAgent("Cyclophosphamide", "1", "50-18-0", 100, 2012,
              ["Bladder", "Leukemia", "Skin"], ["Chemotherapy", "Immunosuppression"], "", "Pharmaceutical"),
    IARCAgent("Cyclosporine", "1", "59865-13-3", 100, 2012,
              ["Non-Hodgkin lymphoma", "Skin"], ["Immunosuppressant drug"], "", "Pharmaceutical"),
    IARCAgent("1,2-Dichloropropane", "1", "78-87-5", 110, 2017,
              ["Bile duct (cholangiocarcinoma)"], ["Printing industry", "Solvent"], "", "Chemical"),
    IARCAgent("Diethylstilbestrol (DES)", "1", "56-53-1", 100, 2012,
              ["Breast", "Vagina (clear cell adenocarcinoma)", "Cervix"],
              ["Historical pregnancy drug"], "MAJOR LITIGATION TARGET - in utero exposure", "Pharmaceutical"),
    IARCAgent("Engine exhaust, diesel", "1", None, 105, 2012,
              ["Lung", "Bladder"], ["Transportation", "Mining", "Construction equipment"],
              "MAJOR LITIGATION TARGET", "Chemical"),
    IARCAgent("Epstein-Barr virus (EBV)", "1", None, 100, 2012,
              ["Nasopharyngeal carcinoma", "Burkitt lymphoma", "Hodgkin lymphoma", "Gastric carcinoma"],
              ["Ubiquitous infection"], "", "Biological"),
    IARCAgent("Erionite", "1", "66733-21-9", 100, 2012,
              ["Mesothelioma"], ["Natural mineral in volcanic rock"], "Found in Turkey, North Dakota", "Chemical"),
    IARCAgent("Estrogen-only menopausal therapy", "1", None, 100, 2012,
              ["Endometrium", "Ovary"], ["Hormone replacement therapy"], "", "Pharmaceutical"),
    IARCAgent("Estrogen-progestogen menopausal therapy", "1", None, 100, 2012,
              ["Breast", "Endometrium"], ["Hormone replacement therapy"], "", "Pharmaceutical"),
    IARCAgent("Estrogen-progestogen oral contraceptives", "1", None, 100, 2012,
              ["Breast", "Cervix", "Liver"], ["Birth control"], "Also protective for ovary, endometrium", "Pharmaceutical"),
    IARCAgent("Ethanol in alcoholic beverages", "1", "64-17-5", 100, 2012,
              ["Oral cavity", "Pharynx", "Larynx", "Esophagus", "Liver", "Colorectum", "Breast"],
              ["Alcohol consumption"], "", "Lifestyle"),
    IARCAgent("Ethylene oxide", "1", "75-21-8", 100, 2012,
              ["Lymphoid tumors", "Breast"], ["Medical device sterilization", "Chemical manufacturing"],
              "", "Chemical"),
    IARCAgent("Etoposide", "1", "33419-42-0", 100, 2012,
              ["Leukemia (secondary)"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Fission products including strontium-90", "1", None, 100, 2012,
              ["Leukemia", "Solid tumors"], ["Nuclear accidents", "Fallout"], "", "Physical"),
    IARCAgent("Fluoro-edenite fibrous amphibole", "1", None, 111, 2017,
              ["Mesothelioma"], ["Natural mineral exposure in Sicily"], "", "Chemical"),
    IARCAgent("Formaldehyde", "1", "50-00-0", 100, 2012,
              ["Nasopharyngeal carcinoma", "Leukemia (myeloid)"],
              ["Pressed wood products", "Textiles", "Healthcare", "Embalming"],
              "MAJOR LITIGATION TARGET", "Chemical"),
    IARCAgent("Haematite mining (underground)", "1", None, 100, 2012,
              ["Lung"], ["Iron ore mining"], "", "Occupational"),
    IARCAgent("Helicobacter pylori infection", "1", None, 100, 2012,
              ["Stomach (non-cardia)", "Gastric MALT lymphoma"], ["Bacterial infection"], "", "Biological"),
    IARCAgent("Hepatitis B virus (chronic infection)", "1", None, 100, 2012,
              ["Liver (hepatocellular carcinoma)", "Bile duct"], ["Blood/body fluid transmission"],
              "", "Biological"),
    IARCAgent("Hepatitis C virus (chronic infection)", "1", None, 100, 2012,
              ["Liver (hepatocellular carcinoma)", "Non-Hodgkin lymphoma"], ["Blood transmission"],
              "", "Biological"),
    IARCAgent("Human immunodeficiency virus type 1 (HIV-1)", "1", None, 100, 2012,
              ["Kaposi sarcoma", "Non-Hodgkin lymphoma", "Hodgkin lymphoma", "Cervix", "Anus", "Conjunctiva"],
              ["Blood/sexual transmission"], "", "Biological"),
    IARCAgent("Human papillomavirus (HPV) types 16, 18, 31, 33, 35, 39, 45, 51, 52, 56, 58, 59", "1", None, 100, 2012,
              ["Cervix", "Vulva", "Vagina", "Penis", "Anus", "Oropharynx"],
              ["Sexual transmission"], "", "Biological"),
    IARCAgent("Human T-cell lymphotropic virus type 1 (HTLV-1)", "1", None, 100, 2012,
              ["Adult T-cell leukemia/lymphoma"], ["Blood/sexual/mother-to-child transmission"], "", "Biological"),
    IARCAgent("Ionizing radiation (all types)", "1", None, 100, 2012,
              ["Leukemia", "Thyroid", "Breast", "Lung", "Stomach", "Colon", "Bladder", "Ovary", "Skin", "Brain", "Bone"],
              ["Medical imaging", "Nuclear industry", "Radon", "Cosmic rays"], "", "Physical"),
    IARCAgent("Iron and steel founding", "1", None, 100, 2012,
              ["Lung"], ["Foundry work"], "", "Occupational"),
    IARCAgent("Isopropyl alcohol manufacture using strong acids", "1", None, 100, 2012,
              ["Sinonasal cavity"], ["Chemical manufacturing"], "", "Occupational"),
    IARCAgent("Kaposi sarcoma herpesvirus (KSHV/HHV8)", "1", None, 100, 2012,
              ["Kaposi sarcoma", "Primary effusion lymphoma"], ["Transmission routes unclear"], "", "Biological"),
    IARCAgent("Leather dust", "1", None, 100, 2012,
              ["Sinonasal cavity"], ["Shoe manufacturing", "Leather goods"], "", "Occupational"),
    IARCAgent("Lindane", "1", "58-89-9", 113, 2015,
              ["Non-Hodgkin lymphoma"], ["Pesticide", "Lice treatment"], "Banned in many countries", "Chemical"),
    IARCAgent("Magenta production", "1", None, 100, 2012,
              ["Bladder"], ["Dye manufacturing"], "", "Occupational"),
    IARCAgent("Melphalan", "1", "148-82-3", 100, 2012,
              ["Leukemia (secondary)"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Methoxsalen (8-Methoxypsoralen) plus UVA radiation", "1", "298-81-7", 100, 2012,
              ["Skin"], ["PUVA therapy for psoriasis"], "", "Pharmaceutical"),
    IARCAgent("4,4'-Methylenebis(2-chloroaniline) (MOCA)", "1", "101-14-4", 100, 2012,
              ["Bladder"], ["Polyurethane production"], "", "Chemical"),
    IARCAgent("Mineral oils, untreated or mildly treated", "1", None, 100, 2012,
              ["Skin (scrotal)", "Sinonasal"], ["Metalworking", "Textile industry"], "", "Chemical"),
    IARCAgent("MOPP and other combined chemotherapy including alkylating agents", "1", None, 100, 2012,
              ["Leukemia"], ["Hodgkin lymphoma treatment"], "", "Pharmaceutical"),
    IARCAgent("2-Naphthylamine", "1", "91-59-8", 100, 2012,
              ["Bladder"], ["Dye manufacturing", "Rubber industry"], "", "Chemical"),
    IARCAgent("Nickel compounds", "1", None, 100, 2012,
              ["Lung", "Sinonasal cavity"], ["Nickel refining", "Stainless steel", "Batteries", "Plating"],
              "", "Chemical"),
    IARCAgent("N'-Nitrosonornicotine (NNN) and 4-(N-Nitrosomethylamino)-1-(3-pyridyl)-1-butanone (NNK)", "1", None, 100, 2012,
              ["Lung", "Esophagus", "Pancreas"], ["Tobacco products"], "Tobacco-specific nitrosamines", "Chemical"),
    IARCAgent("Opium consumption", "1", None, 126, 2020,
              ["Larynx", "Lung", "Pharynx", "Esophagus", "Bladder", "Pancreas"],
              ["Drug use"], "", "Lifestyle"),
    IARCAgent("Outdoor air pollution", "1", None, 109, 2013,
              ["Lung"], ["Ambient exposure"], "", "Physical"),
    IARCAgent("Outdoor air pollution, particulate matter", "1", None, 109, 2013,
              ["Lung"], ["Ambient exposure"], "", "Physical"),
    IARCAgent("Painter (occupational exposure)", "1", None, 100, 2012,
              ["Lung", "Bladder", "Mesothelioma"], ["Painting occupation"], "", "Occupational"),
    IARCAgent("Pentachlorophenol", "1", "87-86-5", 117, 2017,
              ["Non-Hodgkin lymphoma"], ["Wood preservative"], "", "Chemical"),
    IARCAgent("Phosphorus-32 as phosphate", "1", "7723-14-0", 100, 2012,
              ["Leukemia"], ["Medical treatment"], "", "Physical"),
    IARCAgent("Plutonium", "1", "7440-07-5", 100, 2012,
              ["Lung", "Liver", "Bone"], ["Nuclear workers", "Weapons production"], "", "Physical"),
    IARCAgent("Polychlorinated biphenyls (PCBs)", "1", None, 107, 2016,
              ["Melanoma"], ["Electrical equipment", "Plasticizers"], "Banned but persistent", "Chemical"),
    IARCAgent("Processed meat (consumption of)", "1", None, 114, 2015,
              ["Colorectum"], ["Diet"], "Hot dogs, bacon, ham, sausages, salami", "Lifestyle"),
    IARCAgent("Radioiodines, short-lived, including iodine-131", "1", None, 100, 2012,
              ["Thyroid"], ["Nuclear accidents", "Medical treatment"], "", "Physical"),
    IARCAgent("Radionuclides, alpha-particle-emitting, internally deposited", "1", None, 100, 2012,
              ["Various depending on target organ"], ["Nuclear exposure"], "", "Physical"),
    IARCAgent("Radionuclides, beta-particle-emitting, internally deposited", "1", None, 100, 2012,
              ["Various depending on target organ"], ["Nuclear exposure"], "", "Physical"),
    IARCAgent("Radium-224 and its decay products", "1", None, 100, 2012,
              ["Bone"], ["Historical medical use"], "", "Physical"),
    IARCAgent("Radium-226 and its decay products", "1", None, 100, 2012,
              ["Bone", "Mastoid"], ["Historical medical/industrial use"], "Radium girls", "Physical"),
    IARCAgent("Radium-228 and its decay products", "1", None, 100, 2012,
              ["Bone"], ["Historical medical use"], "", "Physical"),
    IARCAgent("Radon-222 and its decay products", "1", "14859-67-7", 100, 2012,
              ["Lung"], ["Indoor air", "Mining", "Groundwater"], "Second leading cause of lung cancer", "Physical"),
    IARCAgent("Rubber manufacturing industry", "1", None, 100, 2012,
              ["Bladder", "Lung", "Leukemia", "Stomach"], ["Rubber factory work"], "", "Occupational"),
    IARCAgent("Salted fish (Chinese-style)", "1", None, 100, 2012,
              ["Nasopharynx"], ["Diet"], "", "Lifestyle"),
    IARCAgent("Schistosoma haematobium infection", "1", None, 100, 2012,
              ["Bladder"], ["Parasitic infection"], "", "Biological"),
    IARCAgent("Semustine (methyl-CCNU)", "1", "13909-09-6", 100, 2012,
              ["Leukemia"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Shale oils", "1", None, 100, 2012,
              ["Skin"], ["Historical industrial use"], "", "Chemical"),
    IARCAgent("Silica dust, crystalline (quartz, cristobalite)", "1", "14808-60-7", 100, 2012,
              ["Lung"], ["Mining", "Construction", "Sandblasting", "Foundries"],
              "MAJOR LITIGATION TARGET", "Chemical"),
    IARCAgent("Solar radiation", "1", None, 100, 2012,
              ["Skin (melanoma, BCC, SCC)", "Lip"], ["Sun exposure"], "", "Physical"),
    IARCAgent("Soot (as found in occupational exposure of chimney sweeps)", "1", None, 100, 2012,
              ["Skin (scrotal)", "Lung"], ["Chimney sweeping"], "Historical significance", "Occupational"),
    IARCAgent("Sulfur mustard", "1", "505-60-2", 100, 2012,
              ["Lung", "Larynx", "Pharynx"], ["Chemical warfare"], "", "Chemical"),
    IARCAgent("Tamoxifen", "1", "10540-29-1", 100, 2012,
              ["Endometrium"], ["Breast cancer treatment/prevention"], "Also protective for breast", "Pharmaceutical"),
    IARCAgent("2,3,7,8-Tetrachlorodibenzo-para-dioxin (TCDD)", "1", "1746-01-6", 100, 2012,
              ["All sites combined"], ["Herbicide contamination", "Incineration"],
              "Agent Orange component - MAJOR LITIGATION TARGET", "Chemical"),
    IARCAgent("Thiotepa", "1", "52-24-4", 100, 2012,
              ["Leukemia"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Thorium-232 and its decay products", "1", None, 100, 2012,
              ["Liver (hemangiosarcoma)", "Leukemia", "Bile duct"], ["Thorotrast contrast agent"], "", "Physical"),
    IARCAgent("Tobacco smoke, secondhand", "1", None, 100, 2012,
              ["Lung"], ["Passive smoking exposure"], "", "Lifestyle"),
    IARCAgent("Tobacco smoking", "1", None, 100, 2012,
              ["Lung", "Oral cavity", "Pharynx", "Larynx", "Esophagus", "Stomach", "Pancreas",
               "Kidney", "Bladder", "Cervix", "Colorectum", "Liver", "AML", "Ovary (mucinous)"],
              ["Active smoking"], "", "Lifestyle"),
    IARCAgent("Tobacco, smokeless", "1", None, 100, 2012,
              ["Oral cavity", "Esophagus", "Pancreas"], ["Chewing tobacco", "Snuff"], "", "Lifestyle"),
    IARCAgent("ortho-Toluidine", "1", "95-53-4", 100, 2012,
              ["Bladder"], ["Dye manufacturing"], "", "Chemical"),
    IARCAgent("Treosulfan", "1", "299-75-2", 100, 2012,
              ["Leukemia"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Trichloroethylene", "1", "79-01-6", 106, 2014,
              ["Kidney", "Liver", "Non-Hodgkin lymphoma"], ["Metal degreasing", "Dry cleaning"],
              "", "Chemical"),
    IARCAgent("Ultraviolet radiation (UVA, UVB, UVC)", "1", None, 100, 2012,
              ["Skin (melanoma, SCC, BCC)"], ["Sun exposure", "Tanning beds", "Welding arcs"],
              "", "Physical"),
    IARCAgent("Ultraviolet-emitting tanning devices", "1", None, 100, 2012,
              ["Skin (melanoma)"], ["Indoor tanning"], "", "Physical"),
    IARCAgent("Vinyl chloride", "1", "75-01-4", 100, 2012,
              ["Liver (angiosarcoma)", "Hepatocellular carcinoma"],
              ["PVC manufacturing"], "", "Chemical"),
    IARCAgent("Welding fumes", "1", None, 118, 2018,
              ["Lung"], ["Welding"], "", "Occupational"),
    IARCAgent("Wood dust", "1", None, 100, 2012,
              ["Sinonasal cavity (adenocarcinoma)", "Nasopharynx"],
              ["Carpentry", "Furniture making", "Sawmills"], "", "Occupational"),
    IARCAgent("X-radiation and gamma radiation", "1", None, 100, 2012,
              ["Many sites"], ["Medical imaging", "Radiotherapy", "Nuclear industry"], "", "Physical"),
]


# =============================================================================
# IARC GROUP 2A - PROBABLY CARCINOGENIC TO HUMANS (97 agents)
# Limited evidence in humans but sufficient in animals, or strong mechanistic evidence
# =============================================================================

GROUP_2A_CARCINOGENS = [
    # --- HIGH-PRIORITY CHEMICALS ---
    IARCAgent("Acrylamide", "2A", "79-06-1", 116, 2016,
              ["Kidney", "Endometrium"], ["Fried/baked starchy foods", "Coffee", "Cigarettes"],
              "Forms during high-heat cooking", "Chemical"),
    IARCAgent("Adriamycin (doxorubicin)", "2A", "23214-92-8", 100, 2012,
              ["Secondary cancers"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Androgenic (anabolic) steroids", "2A", None, 100, 2012,
              ["Liver"], ["Performance enhancement", "Medical use"], "", "Pharmaceutical"),
    IARCAgent("Art glass, glass containers and pressed ware (manufacture of)", "2A", None, 58, 1993,
              ["Lung"], ["Glass industry"], "", "Occupational"),
    IARCAgent("Azacitidine", "2A", "320-67-2", 100, 2012,
              ["Secondary cancers"], ["Cancer treatment"], "", "Pharmaceutical"),
    IARCAgent("Biomass fuel (primarily wood), indoor emissions from household combustion", "2A", None, 95, 2010,
              ["Lung"], ["Cooking/heating in developing countries"], "", "Physical"),
    IARCAgent("Bitumens, oxidized, and their emissions during roofing", "2A", None, 103, 2013,
              ["Lung"], ["Roofing work"], "", "Occupational"),
    IARCAgent("Carbon electrode manufacture", "2A", None, 92, 2010,
              ["Lung", "Bladder"], ["Electrode production"], "", "Occupational"),
    IARCAgent("Chloral and chloral hydrate", "2A", "302-17-0", 106, 2014,
              ["Thyroid"], ["Sedative (historical)"], "", "Pharmaceutical"),
    IARCAgent("alpha-Chlorinated toluenes (benzal chloride, benzotrichloride, benzyl chloride)", "2A", None, 100, 2012,
              ["Lung"], ["Chemical manufacturing"], "", "Chemical"),
    IARCAgent("4-Chloro-ortho-toluidine", "2A", "95-69-2", 99, 2010,
              ["Bladder"], ["Dye manufacturing"], "", "Chemical"),
    IARCAgent("Chlorozotocin", "2A", "54749-90-5", 100, 2012,
              ["Secondary cancers"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Cisplatin", "2A", "15663-27-1", 100, 2012,
              ["Secondary cancers"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Cobalt metal with tungsten carbide", "2A", None, 86, 2006,
              ["Lung"], ["Hard metal industry"], "", "Chemical"),
    IARCAgent("Creosotes", "2A", "8001-58-9", 92, 2010,
              ["Skin"], ["Wood preservation"], "", "Chemical"),
    IARCAgent("Cyclopenta[cd]pyrene", "2A", "27208-37-3", 92, 2010,
              ["Multiple sites"], ["Combustion products"], "PAH", "Chemical"),
    IARCAgent("DDT (p,p'-DDT)", "2A", "50-29-3", 113, 2015,
              ["Liver", "Non-Hodgkin lymphoma"], ["Pesticide (historical)"], "Banned but persistent", "Chemical"),
    IARCAgent("Diazinon", "2A", "333-41-5", 112, 2015,
              ["Non-Hodgkin lymphoma", "Leukemia"], ["Pesticide"], "", "Chemical"),
    IARCAgent("Dibenz[a,h]anthracene", "2A", "53-70-3", 92, 2010,
              ["Multiple sites"], ["Combustion products"], "PAH", "Chemical"),
    IARCAgent("Dichloromethane (methylene chloride)", "2A", "75-09-2", 110, 2017,
              ["Biliary tract", "Non-Hodgkin lymphoma"], ["Solvent", "Paint stripper"], "", "Chemical"),
    IARCAgent("Dieldrin", "2A", "60-57-1", 130, 2022,
              ["Breast", "Liver"], ["Pesticide (historical)"], "Banned", "Chemical"),
    IARCAgent("Diethyl sulfate", "2A", "64-67-5", 54, 1992,
              ["Multiple sites"], ["Chemical manufacturing"], "", "Chemical"),
    IARCAgent("Dimethylcarbamoyl chloride", "2A", "79-44-7", 100, 2012,
              ["Multiple sites"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("1,2-Dimethylhydrazine", "2A", "540-73-8", 100, 2012,
              ["Colon"], ["Laboratory chemical"], "", "Chemical"),
    IARCAgent("Dimethyl sulfate", "2A", "77-78-1", 100, 2012,
              ["Multiple sites"], ["Chemical manufacturing"], "", "Chemical"),
    IARCAgent("Epichlorohydrin", "2A", "106-89-8", 71, 1999,
              ["Lung", "NHL"], ["Epoxy resin production"], "", "Chemical"),
    IARCAgent("Ethyl carbamate (urethane)", "2A", "51-79-6", 96, 2010,
              ["Multiple sites"], ["Fermented foods/drinks"], "", "Chemical"),
    IARCAgent("Glycidol", "2A", "556-52-5", 77, 2000,
              ["Multiple sites"], ["Food contaminant", "Chemical intermediate"], "", "Chemical"),
    IARCAgent("Glyphosate", "2A", "1071-83-6", 112, 2015,
              ["Non-Hodgkin lymphoma"], ["Herbicide (Roundup)"],
              "MAJOR LITIGATION TARGET - Monsanto/Bayer", "Chemical"),
    IARCAgent("Hairdresser or barber (occupational exposure)", "2A", None, 99, 2010,
              ["Bladder", "Lung", "Larynx"], ["Salon work"], "", "Occupational"),
    IARCAgent("Hot beverages at very high temperature (above 65°C)", "2A", None, 116, 2016,
              ["Esophagus"], ["Drinking very hot liquids"], "", "Lifestyle"),
    IARCAgent("Human papillomavirus type 68", "2A", None, 100, 2012,
              ["Cervix"], ["Sexual transmission"], "", "Biological"),
    IARCAgent("Indium phosphide", "2A", "22398-80-7", 86, 2006,
              ["Lung"], ["Electronics industry"], "", "Chemical"),
    IARCAgent("IQ (2-Amino-3-methylimidazo[4,5-f]quinoline)", "2A", "76180-96-6", 56, 1993,
              ["Multiple sites"], ["Cooked meat"], "Heterocyclic amine", "Chemical"),
    IARCAgent("Lead compounds, inorganic", "2A", None, 87, 2006,
              ["Stomach", "Lung", "Brain (glioma)"], ["Batteries", "Paint (historical)", "Plumbing"],
              "", "Chemical"),
    IARCAgent("Malaria (caused by infection with Plasmodium falciparum)", "2A", None, 104, 2014,
              ["Burkitt lymphoma"], ["Parasitic infection"], "In endemic areas", "Biological"),
    IARCAgent("Malathion", "2A", "121-75-5", 112, 2015,
              ["Non-Hodgkin lymphoma"], ["Pesticide"], "", "Chemical"),
    IARCAgent("5-Methoxypsoralen", "2A", "484-20-8", 40, 1986,
              ["Skin"], ["Tanning accelerator"], "", "Chemical"),
    IARCAgent("Methyl bromide", "2A", "74-83-9", 71, 1999,
              ["Prostate"], ["Fumigant"], "", "Chemical"),
    IARCAgent("Methyl methanesulfonate", "2A", "66-27-3", 100, 2012,
              ["Multiple sites"], ["Laboratory chemical"], "", "Chemical"),
    IARCAgent("N-Methyl-N'-nitro-N-nitrosoguanidine (MNNG)", "2A", "70-25-7", 100, 2012,
              ["Stomach"], ["Laboratory chemical"], "", "Chemical"),
    IARCAgent("N-Methyl-N-nitrosourea", "2A", "684-93-5", 100, 2012,
              ["Multiple sites"], ["Laboratory chemical"], "", "Chemical"),
    IARCAgent("Nitrogen mustard", "2A", "51-75-2", 100, 2012,
              ["Secondary cancers"], ["Chemotherapy (historical)"], "", "Pharmaceutical"),
    IARCAgent("N-Nitrosodiethylamine", "2A", "55-18-5", 100, 2012,
              ["Multiple sites"], ["Industrial contaminant", "Tobacco smoke"], "", "Chemical"),
    IARCAgent("N-Nitrosodimethylamine (NDMA)", "2A", "62-75-9", 100, 2012,
              ["Liver"], ["Food/water contaminant", "Drug impurity"],
              "Zantac/Valsartan recall trigger", "Chemical"),
    IARCAgent("Night shift work", "2A", None, 124, 2019,
              ["Breast", "Prostate", "Colorectum"], ["Circadian disruption"], "", "Occupational"),
    IARCAgent("Nitrate or nitrite (ingested) under conditions that result in endogenous nitrosation", "2A", None, 114, 2015,
              ["Colorectum", "Stomach"], ["Processed meat", "Drinking water"], "", "Chemical"),
    IARCAgent("Non-arsenical insecticides (occupational exposures in spraying and application)", "2A", None, 112, 2015,
              ["Lung", "Non-Hodgkin lymphoma"], ["Agricultural work"], "", "Occupational"),
    IARCAgent("PFOA (perfluorooctanoic acid)", "2A", "335-67-1", 135, 2024,
              ["Kidney", "Testicular"], ["Teflon manufacturing", "Firefighting foam", "Water contamination"],
              "MAJOR LITIGATION TARGET - 3M, DuPont", "Chemical"),
    IARCAgent("PFOS (perfluorooctane sulfonic acid)", "2A", "1763-23-1", 135, 2024,
              ["Kidney", "Liver"], ["Firefighting foam", "Stain resistance"],
              "MAJOR LITIGATION TARGET", "Chemical"),
    IARCAgent("Petroleum refining (occupational exposures)", "2A", None, 45, 1989,
              ["Leukemia", "Skin"], ["Refinery work"], "", "Occupational"),
    IARCAgent("Pioglitazone", "2A", "111025-46-8", 108, 2016,
              ["Bladder"], ["Diabetes drug"], "", "Pharmaceutical"),
    IARCAgent("Polybrominated biphenyls", "2A", None, 107, 2016,
              ["Multiple sites"], ["Flame retardants"], "Banned but persistent", "Chemical"),
    IARCAgent("Procarbazine hydrochloride", "2A", "366-70-1", 100, 2012,
              ["Secondary cancers"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("1,3-Propane sultone", "2A", "1120-71-4", 100, 2012,
              ["Multiple sites"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Red meat (consumption of)", "2A", None, 114, 2015,
              ["Colorectum"], ["Diet"], "Beef, pork, lamb, goat", "Lifestyle"),
    IARCAgent("Shiftwork that involves circadian disruption", "2A", None, 124, 2019,
              ["Breast"], ["Night work"], "", "Occupational"),
    IARCAgent("Silicon carbide whiskers", "2A", None, 111, 2017,
              ["Lung"], ["Abrasives", "Ceramics"], "", "Chemical"),
    IARCAgent("Styrene", "2A", "100-42-5", 121, 2019,
              ["Lymphohematopoietic malignancies"], ["Plastics", "Rubber", "Fiberglass"],
              "", "Chemical"),
    IARCAgent("Styrene-7,8-oxide", "2A", "96-09-3", 100, 2012,
              ["Multiple sites"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Teniposide", "2A", "29767-20-2", 100, 2012,
              ["Secondary cancers"], ["Chemotherapy drug"], "", "Pharmaceutical"),
    IARCAgent("Tetrachloroethylene (perchloroethylene)", "2A", "127-18-4", 106, 2014,
              ["Bladder", "Non-Hodgkin lymphoma"], ["Dry cleaning", "Metal degreasing"],
              "", "Chemical"),
    IARCAgent("Tris(2,3-dibromopropyl) phosphate", "2A", "126-72-7", 71, 1999,
              ["Multiple sites"], ["Flame retardant (historical)"], "Children's sleepwear", "Chemical"),
    IARCAgent("Ultraviolet radiation A", "2A", None, 100, 2012,
              ["Skin melanoma"], ["Sun exposure", "Tanning beds"], "", "Physical"),
    IARCAgent("Ultraviolet radiation B", "2A", None, 100, 2012,
              ["Skin melanoma"], ["Sun exposure"], "", "Physical"),
    IARCAgent("Ultraviolet radiation C", "2A", None, 100, 2012,
              ["Skin"], ["Germicidal lamps", "Welding"], "", "Physical"),
    IARCAgent("Vinyl bromide", "2A", "593-60-2", 97, 2008,
              ["Liver"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Vinyl fluoride", "2A", "75-02-5", 97, 2008,
              ["Liver"], ["Polymer production"], "", "Chemical"),
    IARCAgent("4-Vinylcyclohexene diepoxide", "2A", "106-87-6", 60, 1994,
              ["Ovary", "Skin"], ["Chemical intermediate"], "", "Chemical"),
]


# =============================================================================
# IARC GROUP 2B - POSSIBLY CARCINOGENIC TO HUMANS (324 agents - key selections)
# Limited evidence in humans and less than sufficient in animals
# =============================================================================

GROUP_2B_CARCINOGENS = [
    # High-exposure or litigation-relevant agents
    IARCAgent("Acetaldehyde", "2B", "75-07-0", 71, 1999, ["Multiple"], ["Industrial"], "", "Chemical"),
    IARCAgent("Acetamide", "2B", "60-35-5", 71, 1999, ["Multiple"], ["Industrial"], "", "Chemical"),
    IARCAgent("AF-2 (furylframide)", "2B", "3688-53-7", 31, 1983, ["Multiple"], ["Food preservative"], "", "Chemical"),
    IARCAgent("Aflatoxin M1", "2B", "6795-23-9", 56, 1993, ["Liver"], ["Dairy products"], "", "Chemical"),
    IARCAgent("Aloe vera, whole leaf extract", "2B", None, 108, 2016, ["Colon"], ["Supplements"], "", "Chemical"),
    IARCAgent("Amsacrine", "2B", "51264-14-3", 76, 2000, ["Secondary cancers"], ["Chemotherapy"], "", "Pharmaceutical"),
    IARCAgent("ortho-Anisidine", "2B", "90-04-0", 127, 2021, ["Bladder"], ["Dye manufacturing"], "", "Chemical"),
    IARCAgent("Antimony trioxide", "2B", "1309-64-4", 47, 1989, ["Lung"], ["Flame retardants"], "", "Chemical"),
    IARCAgent("Acrylonitrile", "2B", "107-13-1", 71, 1999, ["Lung", "Prostate"], ["Plastics manufacturing"], "", "Chemical"),
    IARCAgent("Auramine (technical-grade)", "2B", "492-80-8", 100, 2012, ["Bladder"], ["Dye"], "", "Chemical"),
    IARCAgent("Benz[a]anthracene", "2B", "56-55-3", 92, 2010, ["Multiple"], ["Combustion"], "PAH", "Chemical"),
    IARCAgent("Benzofuran", "2B", "271-89-6", 63, 1995, ["Multiple"], ["Coal tar"], "", "Chemical"),
    IARCAgent("Beta-carotene supplements", "2B", None, 100, 2012, ["Lung"], ["Supplements in smokers"], "", "Chemical"),
    IARCAgent("Bracken fern", "2B", None, 40, 1986, ["Bladder", "Esophagus"], ["Food"], "", "Chemical"),
    IARCAgent("Bromochloroacetic acid", "2B", "5589-96-8", 140, 2025, ["Multiple"], ["Drinking water"], "", "Chemical"),
    IARCAgent("Bromodichloromethane", "2B", "75-27-4", 140, 2025, ["Bladder", "Colorectum"], ["Drinking water"], "", "Chemical"),
    IARCAgent("1,3-Butadiene diepoxide", "2B", "1464-53-5", 71, 1999, ["Multiple"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Butylated hydroxyanisole (BHA)", "2B", "25013-16-5", 40, 1986, ["Forestomach"], ["Food preservative"], "", "Chemical"),
    IARCAgent("Caffeic acid", "2B", "331-39-5", 56, 1993, ["Multiple"], ["Coffee", "Fruits", "Vegetables"], "", "Chemical"),
    IARCAgent("Carbon black", "2B", "1333-86-4", 93, 2010, ["Lung"], ["Tires", "Pigments"], "", "Chemical"),
    IARCAgent("Carbon tetrachloride", "2B", "56-23-5", 71, 1999, ["Liver"], ["Solvent"], "", "Chemical"),
    IARCAgent("Carrageenan (degraded)", "2B", None, 31, 1983, ["Colon"], ["Food additive"], "", "Chemical"),
    IARCAgent("Catechol", "2B", "120-80-9", 71, 1999, ["Multiple"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Chlordane", "2B", "57-74-9", 79, 2001, ["Multiple"], ["Pesticide"], "Banned", "Chemical"),
    IARCAgent("Chlordecone (Kepone)", "2B", "143-50-0", 79, 2001, ["Prostate"], ["Pesticide"], "Banned", "Chemical"),
    IARCAgent("Chloroform", "2B", "67-66-3", 73, 1999, ["Liver", "Kidney"], ["Solvent", "Drinking water"], "", "Chemical"),
    IARCAgent("Chrysene", "2B", "218-01-9", 92, 2010, ["Multiple"], ["Combustion"], "PAH", "Chemical"),
    IARCAgent("Citrus Red No. 2", "2B", "6358-53-8", 8, 1975, ["Bladder"], ["Food dye"], "", "Chemical"),
    IARCAgent("Cobalt and cobalt compounds", "2B", "7440-48-4", 86, 2006, ["Lung"], ["Alloys", "Batteries"], "", "Chemical"),
    IARCAgent("Coconut oil diethanolamine condensate", "2B", "68603-42-9", 101, 2013, ["Multiple"], ["Cosmetics"], "", "Chemical"),
    IARCAgent("para-Cresidine", "2B", "120-71-8", 57, 1993, ["Bladder"], ["Dye manufacturing"], "", "Chemical"),
    IARCAgent("Dacarbazine", "2B", "4342-03-4", 26, 1981, ["Secondary cancers"], ["Chemotherapy"], "", "Pharmaceutical"),
    IARCAgent("Dibenz[a,j]acridine", "2B", "224-42-0", 32, 1983, ["Multiple"], ["Combustion"], "", "Chemical"),
    IARCAgent("Dibenzo[a,l]pyrene", "2B", "191-30-0", 92, 2010, ["Multiple"], ["Combustion"], "Most potent PAH", "Chemical"),
    IARCAgent("1,2-Dibromoethane (EDB)", "2B", "106-93-4", 71, 1999, ["Multiple"], ["Fumigant"], "", "Chemical"),
    IARCAgent("2,3-Dibromo-1-propanol", "2B", "96-13-9", 77, 2000, ["Multiple"], ["Flame retardant"], "", "Chemical"),
    IARCAgent("1,4-Dichlorobenzene", "2B", "106-46-7", 73, 1999, ["Multiple"], ["Mothballs", "Deodorizers"], "", "Chemical"),
    IARCAgent("3,3'-Dichlorobenzidine", "2B", "91-94-1", 29, 1982, ["Bladder"], ["Dye manufacturing"], "", "Chemical"),
    IARCAgent("1,2-Dichloroethane", "2B", "107-06-2", 71, 1999, ["Multiple"], ["Solvent", "PVC production"], "", "Chemical"),
    IARCAgent("Diesel fuel, marine", "2B", None, 45, 1989, ["Multiple"], ["Marine fuel"], "", "Chemical"),
    IARCAgent("Di(2-ethylhexyl) phthalate (DEHP)", "2B", "117-81-7", 101, 2013, ["Multiple"], ["Plasticizer"], "", "Chemical"),
    IARCAgent("1,2-Diethylhydrazine", "2B", "1615-80-1", 4, 1974, ["Multiple"], ["Laboratory"], "", "Chemical"),
    IARCAgent("Diglycidyl resorcinol ether", "2B", "101-90-6", 71, 1999, ["Multiple"], ["Epoxy resin"], "", "Chemical"),
    IARCAgent("Diisopropyl sulfate", "2B", "2973-10-6", 54, 1992, ["Multiple"], ["Chemical"], "", "Chemical"),
    IARCAgent("3,3'-Dimethoxybenzidine (ortho-Dianisidine)", "2B", "119-90-4", 99, 2010, ["Multiple"], ["Dye manufacturing"], "", "Chemical"),
    IARCAgent("para-Dimethylaminoazobenzene", "2B", "60-11-7", 8, 1975, ["Liver"], ["Dye"], "", "Chemical"),
    IARCAgent("3,3'-Dimethylbenzidine (ortho-Tolidine)", "2B", "119-93-7", 119, 2018, ["Bladder"], ["Dye manufacturing"], "", "Chemical"),
    IARCAgent("1,1-Dimethylhydrazine", "2B", "57-14-7", 71, 1999, ["Multiple"], ["Rocket fuel"], "", "Chemical"),
    IARCAgent("1,6-Dinitropyrene", "2B", "42397-64-8", 46, 1989, ["Multiple"], ["Diesel exhaust"], "", "Chemical"),
    IARCAgent("1,8-Dinitropyrene", "2B", "42397-65-9", 46, 1989, ["Multiple"], ["Diesel exhaust"], "", "Chemical"),
    IARCAgent("2,4-Dinitrotoluene", "2B", "121-14-2", 65, 1996, ["Liver"], ["Explosives"], "", "Chemical"),
    IARCAgent("2,6-Dinitrotoluene", "2B", "606-20-2", 65, 1996, ["Liver"], ["Explosives"], "", "Chemical"),
    IARCAgent("1,4-Dioxane", "2B", "123-91-1", 71, 1999, ["Liver", "Nasal"], ["Solvent", "Cosmetics contaminant"], "", "Chemical"),
    IARCAgent("Disperse Blue 1", "2B", "2475-45-8", 48, 1990, ["Bladder"], ["Textile dye"], "", "Chemical"),
    IARCAgent("Doxifluridine", "2B", "3094-09-5", 76, 2000, ["Secondary cancers"], ["Chemotherapy"], "", "Pharmaceutical"),
    IARCAgent("Dry cleaning (occupational)", "2B", None, 63, 1995, ["Multiple"], ["Dry cleaning work"], "", "Occupational"),
    IARCAgent("Electromagnetic fields (ELF)", "2B", None, 80, 2002, ["Childhood leukemia"], ["Power lines", "Electrical devices"], "", "Physical"),
    IARCAgent("Ethyl acrylate", "2B", "140-88-5", 71, 1999, ["Forestomach"], ["Plastics"], "", "Chemical"),
    IARCAgent("Ethylbenzene", "2B", "100-41-4", 77, 2000, ["Multiple"], ["Styrene production", "Solvent"], "", "Chemical"),
    IARCAgent("Fumonisin B1", "2B", "116355-83-0", 82, 2002, ["Esophagus", "Liver"], ["Corn contamination"], "Mycotoxin", "Chemical"),
    IARCAgent("Gasoline", "2B", None, 45, 1989, ["Leukemia", "Kidney"], ["Vehicle fuel"], "", "Chemical"),
    IARCAgent("Gasoline engine exhaust", "2B", None, 105, 2013, ["Bladder"], ["Vehicle emissions"], "", "Chemical"),
    IARCAgent("Ginkgo biloba extract", "2B", None, 108, 2016, ["Thyroid", "Liver"], ["Supplements"], "", "Chemical"),
    IARCAgent("Goldenseal root powder", "2B", None, 108, 2016, ["Liver"], ["Supplements"], "", "Chemical"),
    IARCAgent("HC Blue No. 1", "2B", "2784-94-3", 57, 1993, ["Multiple"], ["Hair dye"], "", "Chemical"),
    IARCAgent("Heptachlor", "2B", "76-44-8", 79, 2001, ["Liver"], ["Pesticide"], "Banned", "Chemical"),
    IARCAgent("Hexachlorobenzene", "2B", "118-74-1", 79, 2001, ["Liver", "Thyroid"], ["Fungicide"], "", "Chemical"),
    IARCAgent("Hexachloroethane", "2B", "67-72-1", 73, 1999, ["Kidney"], ["Solvent"], "", "Chemical"),
    IARCAgent("Hexachlorocyclohexanes (including lindane)", "2B", "608-73-1", 53, 1991, ["Multiple"], ["Pesticide"], "", "Chemical"),
    IARCAgent("Hydrazine", "2B", "302-01-2", 71, 1999, ["Lung", "Liver"], ["Rocket fuel", "Chemical intermediate"], "", "Chemical"),
    IARCAgent("1-Hydroxy-2-methylanthraquinone", "2B", "82-47-3", 101, 2013, ["Multiple"], ["Dye"], "", "Chemical"),
    IARCAgent("Indeno[1,2,3-cd]pyrene", "2B", "193-39-5", 92, 2010, ["Multiple"], ["Combustion"], "PAH", "Chemical"),
    IARCAgent("Iron-dextran complex", "2B", "9004-66-4", 2, 1973, ["Multiple"], ["Iron supplement"], "", "Pharmaceutical"),
    IARCAgent("Isoprene", "2B", "78-79-5", 60, 1994, ["Multiple"], ["Rubber production"], "", "Chemical"),
    IARCAgent("Kava extract", "2B", None, 108, 2016, ["Liver"], ["Supplements"], "", "Chemical"),
    IARCAgent("Lasiocarpine", "2B", "303-34-4", 10, 1976, ["Liver"], ["Herbal plants"], "Pyrrolizidine alkaloid", "Chemical"),
    IARCAgent("Magnetic fields (ELF)", "2B", None, 80, 2002, ["Childhood leukemia"], ["Power lines"], "", "Physical"),
    IARCAgent("Melamine", "2B", "108-78-1", 119, 2018, ["Bladder"], ["Plastics", "Food adulteration"], "", "Chemical"),
    IARCAgent("Merphalan", "2B", "531-76-0", 9, 1975, ["Secondary cancers"], ["Chemotherapy"], "", "Pharmaceutical"),
    IARCAgent("2-Methylaziridine (propyleneimine)", "2B", "75-55-8", 9, 1975, ["Multiple"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Methylazoxymethanol acetate", "2B", "592-62-1", 10, 1976, ["Multiple"], ["Laboratory"], "", "Chemical"),
    IARCAgent("5-Methylchrysene", "2B", "3697-24-3", 92, 2010, ["Multiple"], ["Combustion"], "PAH", "Chemical"),
    IARCAgent("4,4'-Methylene bis(2-methylaniline)", "2B", "838-88-0", 57, 1993, ["Multiple"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Methylmercury compounds", "2B", None, 58, 1993, ["Multiple"], ["Fish", "Dental amalgam"], "", "Chemical"),
    IARCAgent("2-Methyl-1-nitroanthraquinone", "2B", "129-15-7", 27, 1982, ["Liver"], ["Dye"], "", "Chemical"),
    IARCAgent("N-Methyl-N-nitrosourethane", "2B", "615-53-2", 100, 2012, ["Multiple"], ["Laboratory"], "", "Chemical"),
    IARCAgent("Methylthiouracil", "2B", "56-04-2", 79, 2001, ["Thyroid"], ["Antithyroid drug"], "", "Pharmaceutical"),
    IARCAgent("Metronidazole", "2B", "443-48-1", 50, 1990, ["Multiple"], ["Antibiotic"], "", "Pharmaceutical"),
    IARCAgent("Mirex", "2B", "2385-85-5", 20, 1979, ["Liver"], ["Pesticide"], "Banned", "Chemical"),
    IARCAgent("Mitomycin C", "2B", "50-07-7", 10, 1976, ["Secondary cancers"], ["Chemotherapy"], "", "Pharmaceutical"),
    IARCAgent("Mitoxantrone", "2B", "65271-80-9", 76, 2000, ["Secondary cancers"], ["Chemotherapy"], "", "Pharmaceutical"),
    IARCAgent("Monocrotaline", "2B", "315-22-0", 10, 1976, ["Liver"], ["Herbal plants"], "", "Chemical"),
    IARCAgent("5-(Morpholinomethyl)-3-[(5-nitrofurfurylidene)amino]-2-oxazolidinone", "2B", "3795-88-8", 50, 1990, ["Multiple"], ["Antibacterial"], "", "Pharmaceutical"),
    IARCAgent("Nafenopin", "2B", "3771-19-5", 24, 1980, ["Liver"], ["Lipid-lowering drug"], "", "Pharmaceutical"),
    IARCAgent("Naphthalene", "2B", "91-20-3", 82, 2002, ["Multiple"], ["Mothballs", "Industrial"], "", "Chemical"),
    IARCAgent("Nickel, metallic and alloys", "2B", "7440-02-0", 49, 1990, ["Lung"], ["Metal industry"], "", "Chemical"),
    IARCAgent("Niridazole", "2B", "61-57-4", 13, 1977, ["Multiple"], ["Antiparasitic drug"], "", "Pharmaceutical"),
    IARCAgent("Nitrilotriacetic acid and its salts", "2B", "139-13-9", 73, 1999, ["Kidney", "Bladder"], ["Detergents", "Chelating agent"], "", "Chemical"),
    IARCAgent("2-Nitrofluorene", "2B", "607-57-8", 46, 1989, ["Multiple"], ["Diesel exhaust"], "", "Chemical"),
    IARCAgent("Nitromethane", "2B", "75-52-5", 77, 2000, ["Multiple"], ["Racing fuel", "Solvent"], "", "Chemical"),
    IARCAgent("2-Nitropropane", "2B", "79-46-9", 71, 1999, ["Liver"], ["Solvent"], "", "Chemical"),
    IARCAgent("N-Nitrosodi-n-butylamine", "2B", "924-16-3", 100, 2012, ["Bladder", "Liver"], ["Rubber", "Tobacco"], "", "Chemical"),
    IARCAgent("N-Nitrosodiethanolamine", "2B", "1116-54-7", 100, 2012, ["Liver"], ["Cosmetics contaminant"], "", "Chemical"),
    IARCAgent("N-Nitrosodi-n-propylamine", "2B", "621-64-7", 100, 2012, ["Liver"], ["Rubber"], "", "Chemical"),
    IARCAgent("N-Nitroso-N-methylurea", "2B", "684-93-5", 100, 2012, ["Multiple"], ["Laboratory"], "", "Chemical"),
    IARCAgent("Ochratoxin A", "2B", "303-47-9", 56, 1993, ["Kidney"], ["Food contamination"], "Mycotoxin", "Chemical"),
    IARCAgent("Oxazepam", "2B", "604-75-1", 66, 1996, ["Multiple"], ["Benzodiazepine"], "", "Pharmaceutical"),
    IARCAgent("Phenazopyridine hydrochloride", "2B", "136-40-3", 24, 1980, ["Bladder"], ["Urinary analgesic"], "", "Pharmaceutical"),
    IARCAgent("Phenobarbital", "2B", "50-06-6", 79, 2001, ["Liver"], ["Anticonvulsant"], "", "Pharmaceutical"),
    IARCAgent("Phenoxybenzamine hydrochloride", "2B", "63-92-3", 24, 1980, ["Multiple"], ["Antihypertensive"], "", "Pharmaceutical"),
    IARCAgent("Phenyl glycidyl ether", "2B", "122-60-1", 71, 1999, ["Multiple"], ["Epoxy resin"], "", "Chemical"),
    IARCAgent("Phenylhydrazine", "2B", "100-63-0", 71, 1999, ["Multiple"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Phenytoin", "2B", "57-41-0", 66, 1996, ["Multiple"], ["Anticonvulsant"], "", "Pharmaceutical"),
    IARCAgent("Pickled vegetables (traditional Asian)", "2B", None, 56, 1993, ["Esophagus", "Stomach"], ["Diet"], "", "Lifestyle"),
    IARCAgent("Polychlorophenols and their sodium salts (mixed)", "2B", None, 71, 1999, ["Multiple"], ["Wood preservatives"], "", "Chemical"),
    IARCAgent("Ponceau 3R", "2B", "3564-09-8", 8, 1975, ["Multiple"], ["Food dye"], "", "Chemical"),
    IARCAgent("Potassium bromate", "2B", "7758-01-2", 73, 1999, ["Kidney", "Thyroid"], ["Bread flour additive"], "Banned EU/UK", "Chemical"),
    IARCAgent("Printing processes", "2B", None, 65, 1996, ["Lung", "Bladder"], ["Printing industry"], "", "Occupational"),
    IARCAgent("Progestins (combined)", "2B", None, 100, 2012, ["Breast", "Endometrium"], ["Contraceptives", "HRT"], "", "Pharmaceutical"),
    IARCAgent("Propylene oxide", "2B", "75-56-9", 60, 1994, ["Multiple"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Propylthiouracil", "2B", "51-52-5", 79, 2001, ["Thyroid"], ["Antithyroid drug"], "", "Pharmaceutical"),
    IARCAgent("Radiofrequency electromagnetic fields", "2B", None, 102, 2013, ["Glioma"], ["Mobile phones", "Wireless devices"], "", "Physical"),
    IARCAgent("Riddelliine", "2B", "23246-96-0", 10, 1976, ["Liver"], ["Herbal plants"], "Pyrrolizidine alkaloid", "Chemical"),
    IARCAgent("Safrole", "2B", "94-59-7", 10, 1976, ["Liver"], ["Sassafras oil", "Spices"], "", "Chemical"),
    IARCAgent("Streptozotocin", "2B", "18883-66-4", 17, 1978, ["Multiple"], ["Chemotherapy"], "", "Pharmaceutical"),
    IARCAgent("Sulfallate", "2B", "95-06-7", 30, 1983, ["Multiple"], ["Herbicide"], "", "Chemical"),
    IARCAgent("Talc not containing asbestiform fibres", "2B", "14807-96-6", 93, 2010, ["Ovary"], ["Cosmetics", "Baby powder"],
              "Litigation: J&J", "Chemical"),
    IARCAgent("Tetrabromobisphenol A", "2B", "79-94-7", 115, 2016, ["Multiple"], ["Flame retardant"], "", "Chemical"),
    IARCAgent("Textile manufacturing industry", "2B", None, 48, 1990, ["Multiple"], ["Textile work"], "", "Occupational"),
    IARCAgent("Thioacetamide", "2B", "62-55-5", 7, 1974, ["Liver"], ["Laboratory chemical"], "", "Chemical"),
    IARCAgent("Thiourea", "2B", "62-56-6", 79, 2001, ["Thyroid"], ["Chemical intermediate"], "", "Chemical"),
    IARCAgent("Titanium dioxide", "2B", "13463-67-7", 93, 2010, ["Lung"], ["Paint", "Food (E171)", "Sunscreen", "Cosmetics"],
              "Banned EU food 2022; US permitted", "Chemical"),
    IARCAgent("Toluene diisocyanates", "2B", "26471-62-5", 71, 1999, ["Lung"], ["Polyurethane manufacturing"], "", "Chemical"),
    IARCAgent("Toxaphene (polychlorinated camphenes)", "2B", "8001-35-2", 79, 2001, ["Multiple"], ["Pesticide"], "Banned", "Chemical"),
    IARCAgent("1,2,3-Trichloropropane", "2B", "96-18-4", 63, 1995, ["Multiple"], ["Solvent", "Pesticide intermediate"], "", "Chemical"),
    IARCAgent("Trp-P-1", "2B", "62450-06-0", 31, 1983, ["Multiple"], ["Cooked food"], "Heterocyclic amine", "Chemical"),
    IARCAgent("Trp-P-2", "2B", "62450-07-1", 31, 1983, ["Multiple"], ["Cooked food"], "Heterocyclic amine", "Chemical"),
    IARCAgent("Trypan blue", "2B", "72-57-1", 8, 1975, ["Multiple"], ["Laboratory dye"], "", "Chemical"),
    IARCAgent("Uracil mustard", "2B", "66-75-1", 9, 1975, ["Secondary cancers"], ["Chemotherapy"], "", "Pharmaceutical"),
    IARCAgent("Urethane (ethyl carbamate)", "2B", "51-79-6", 7, 1974, ["Multiple"], ["Fermented beverages"], "", "Chemical"),
    IARCAgent("Vanadium pentoxide", "2B", "1314-62-1", 86, 2006, ["Lung"], ["Metal industry", "Catalyst"], "", "Chemical"),
    IARCAgent("Very hot beverages at temperatures above 65°C", "2B", None, 116, 2016, ["Esophagus"], ["Hot drinks"], "", "Lifestyle"),
    IARCAgent("Welding fumes (excluding Group 1)", "2B", None, 49, 1990, ["Lung"], ["Welding"], "", "Occupational"),
    IARCAgent("Wood creosote", "2B", "8021-39-4", 92, 2010, ["Skin"], ["Wood preservation"], "", "Chemical"),
    IARCAgent("Zalcitabine", "2B", "7481-89-2", 76, 2000, ["Multiple"], ["HIV treatment"], "", "Pharmaceutical"),
    IARCAgent("Zidovudine (AZT)", "2B", "30516-87-1", 76, 2000, ["Multiple"], ["HIV treatment"], "", "Pharmaceutical"),
]


# =============================================================================
# HIGH-PRIORITY CHEMICALS FOR MONITORING (EU/US Regulatory Divergence & Emerging)
# =============================================================================

HIGH_PRIORITY_CHEMICALS = [
    # Food additives with regulatory divergence
    {"name": "Titanium dioxide (E171)", "concern": "Genotoxicity", "exposure": "Food, cosmetics, pharmaceuticals",
     "status": "Banned EU 2022, allowed US", "regulatory_divergence": True, "iarc_group": "2B"},
    {"name": "BPA (Bisphenol A)", "concern": "Endocrine disruption", "exposure": "Plastics, can linings, receipts",
     "status": "Restricted EU, limited US action", "regulatory_divergence": True, "iarc_group": None},
    {"name": "BPS (Bisphenol S)", "concern": "Endocrine disruption", "exposure": "BPA replacement",
     "status": "California Prop 65 listed 2025", "regulatory_divergence": False, "iarc_group": None},
    {"name": "Red 40 (Allura Red)", "concern": "Behavioral effects, hypersensitivity", "exposure": "Processed foods, candy",
     "status": "Warning label EU, no action US", "regulatory_divergence": True, "iarc_group": None},
    {"name": "Yellow 5 (Tartrazine)", "concern": "Behavioral effects, hypersensitivity", "exposure": "Processed foods",
     "status": "Warning label EU, no action US", "regulatory_divergence": True, "iarc_group": None},
    {"name": "Yellow 6 (Sunset Yellow)", "concern": "Behavioral effects", "exposure": "Processed foods",
     "status": "Warning label EU, no action US", "regulatory_divergence": True, "iarc_group": None},
    {"name": "Red 3 (Erythrosine)", "concern": "Thyroid tumors", "exposure": "Maraschino cherries, candy",
     "status": "FDA ban proposed 2024", "regulatory_divergence": False, "iarc_group": None},
    {"name": "Brominated vegetable oil (BVO)", "concern": "Organ damage, bromine accumulation", "exposure": "Citrus sodas",
     "status": "Banned US 2024, already banned EU", "regulatory_divergence": False, "iarc_group": None},
    {"name": "Potassium bromate", "concern": "Carcinogenicity (IARC 2B)", "exposure": "Bread flour",
     "status": "Banned EU/UK/Canada/Brazil, allowed US", "regulatory_divergence": True, "iarc_group": "2B"},
    {"name": "Azodicarbonamide", "concern": "Respiratory sensitizer", "exposure": "Bread flour, yoga mats",
     "status": "Banned EU/Australia, allowed US", "regulatory_divergence": True, "iarc_group": None},

    # PFAS - Forever Chemicals
    {"name": "PFOA", "concern": "Cancer, immune effects", "exposure": "Water, Teflon manufacturing",
     "status": "IARC 2A (2024), MCL 4 ppt (2024)", "regulatory_divergence": False, "iarc_group": "2A"},
    {"name": "PFOS", "concern": "Cancer, developmental", "exposure": "Firefighting foam, water",
     "status": "IARC 2A (2024), MCL 4 ppt (2024)", "regulatory_divergence": False, "iarc_group": "2A"},
    {"name": "GenX (HFPO-DA)", "concern": "Liver, kidney, thyroid", "exposure": "PFOA replacement",
     "status": "Emerging regulation", "regulatory_divergence": False, "iarc_group": None},
    {"name": "PFAS (class)", "concern": "Multiple endpoints", "exposure": "Ubiquitous",
     "status": "EPA MCLs 2024, EU REACH proposal", "regulatory_divergence": False, "iarc_group": None},

    # Pesticides
    {"name": "Glyphosate (Roundup)", "concern": "NHL (IARC 2A)", "exposure": "Food residues, occupational",
     "status": "Major litigation ongoing, EPA re-review", "regulatory_divergence": True, "iarc_group": "2A"},
    {"name": "Paraquat", "concern": "Parkinson's disease", "exposure": "Agricultural workers",
     "status": "Banned EU/UK/Brazil/China, allowed US", "regulatory_divergence": True, "iarc_group": None},
    {"name": "Chlorpyrifos", "concern": "Neurodevelopmental", "exposure": "Food residues",
     "status": "Banned food uses US 2022", "regulatory_divergence": False, "iarc_group": None},
    {"name": "Atrazine", "concern": "Endocrine disruption", "exposure": "Drinking water",
     "status": "Banned EU 2004, widely used US", "regulatory_divergence": True, "iarc_group": None},

    # Personal care
    {"name": "Talc (cosmetic grade)", "concern": "Ovarian cancer, mesothelioma (if asbestos-contaminated)",
     "exposure": "Baby powder, cosmetics", "status": "IARC 2B; Major litigation (J&J $9B+)",
     "regulatory_divergence": False, "iarc_group": "2B"},
    {"name": "Parabens", "concern": "Endocrine disruption", "exposure": "Cosmetics, lotions",
     "status": "Restricted EU, no FDA action", "regulatory_divergence": True, "iarc_group": None},
    {"name": "Phthalates (DEHP, DBP, BBP)", "concern": "Reproductive, endocrine", "exposure": "Plastics, cosmetics",
     "status": "Restricted EU, limited US action", "regulatory_divergence": True, "iarc_group": "2B"},
    {"name": "Formaldehyde-releasing preservatives", "concern": "Carcinogenicity",
     "exposure": "Hair straightening (Brazilian Blowout)", "status": "OSHA limits, state bans",
     "regulatory_divergence": False, "iarc_group": "1"},

    # Pharmaceuticals - Active Litigation
    {"name": "Ranitidine (Zantac)", "concern": "NDMA contamination", "exposure": "Heartburn medication",
     "status": "Recalled 2020, MDL litigation", "regulatory_divergence": False, "iarc_group": None},
    {"name": "Valsartan/Losartan (ARBs)", "concern": "NDMA/NDEA contamination", "exposure": "Blood pressure medication",
     "status": "Recalls since 2018", "regulatory_divergence": False, "iarc_group": None},
    {"name": "Acetaminophen (prenatal exposure)", "concern": "ADHD, autism spectrum", "exposure": "OTC pain reliever",
     "status": "MDL litigation ongoing", "regulatory_divergence": False, "iarc_group": None},
    {"name": "Proton pump inhibitors (PPIs)", "concern": "Kidney disease, dementia, infections",
     "exposure": "Heartburn medication (Nexium, Prilosec)", "status": "Litigation ongoing",
     "regulatory_divergence": False, "iarc_group": None},
    {"name": "Zantac (ranitidine)", "concern": "NDMA formation", "exposure": "Heartburn medication",
     "status": "Market withdrawal 2020, MDL bellwether trials", "regulatory_divergence": False, "iarc_group": None},

    # Environmental/Industrial
    {"name": "Microplastics", "concern": "Unknown long-term effects", "exposure": "Ubiquitous - food, water, air",
     "status": "Unregulated, research ongoing", "regulatory_divergence": False, "iarc_group": None},
    {"name": "Nanomaterials", "concern": "Unknown toxicity", "exposure": "Cosmetics, food packaging, medicine",
     "status": "Limited regulation", "regulatory_divergence": False, "iarc_group": None},
    {"name": "1,4-Dioxane", "concern": "Carcinogenicity", "exposure": "Cosmetics contaminant, drinking water",
     "status": "IARC 2B, NY limits 2 ppm in cosmetics", "regulatory_divergence": False, "iarc_group": "2B"},

    # Occupational
    {"name": "Benzene (occupational)", "concern": "Leukemia (IARC 1)", "exposure": "Petrochemical, gasoline",
     "status": "PEL 1 ppm, litigation ongoing", "regulatory_divergence": False, "iarc_group": "1"},
    {"name": "Asbestos (continuing exposure)", "concern": "Mesothelioma (IARC 1)",
     "exposure": "Renovation, brake pads, legacy buildings", "status": "Not fully banned US, major legacy litigation",
     "regulatory_divergence": True, "iarc_group": "1"},
]


# =============================================================================
# DATABASE CLASS
# =============================================================================

class IARCDatabase:
    """Database of IARC carcinogen classifications with search and analysis capabilities."""

    def __init__(self):
        self.group_1 = GROUP_1_CARCINOGENS
        self.group_2a = GROUP_2A_CARCINOGENS
        self.group_2b = GROUP_2B_CARCINOGENS
        self.high_priority = HIGH_PRIORITY_CHEMICALS

        # Build lookup indices
        self._cas_index: Dict[str, IARCAgent] = {}
        self._name_index: Dict[str, IARCAgent] = {}
        self._build_indices()

    def _build_indices(self):
        """Build lookup indices for fast searching."""
        for agent in self.get_all_agents():
            if agent.cas_number:
                self._cas_index[agent.cas_number] = agent
            self._name_index[agent.name.lower()] = agent

    def get_all_agents(self) -> List[IARCAgent]:
        """Get all classified agents."""
        return self.group_1 + self.group_2a + self.group_2b

    def get_all_group_1(self) -> List[IARCAgent]:
        """Get all Group 1 (carcinogenic to humans) agents."""
        return self.group_1

    def get_all_group_2a(self) -> List[IARCAgent]:
        """Get all Group 2A (probably carcinogenic) agents."""
        return self.group_2a

    def get_all_group_2b(self) -> List[IARCAgent]:
        """Get all Group 2B (possibly carcinogenic) agents."""
        return self.group_2b

    def get_by_cas(self, cas_number: str) -> Optional[IARCAgent]:
        """Look up agent by CAS number."""
        return self._cas_index.get(cas_number)

    def search_by_name(self, name: str) -> List[IARCAgent]:
        """Search agents by name (partial match)."""
        name_lower = name.lower()
        return [agent for agent in self.get_all_agents()
                if name_lower in agent.name.lower()]

    def search_by_cancer_site(self, cancer_site: str) -> List[IARCAgent]:
        """Find agents associated with a specific cancer site."""
        cancer_lower = cancer_site.lower()
        return [agent for agent in self.get_all_agents()
                for site in agent.cancer_sites
                if cancer_lower in site.lower()]

    def search_by_exposure(self, exposure_keyword: str) -> List[IARCAgent]:
        """Find agents by exposure source."""
        keyword_lower = exposure_keyword.lower()
        return [agent for agent in self.get_all_agents()
                for source in agent.exposure_sources
                if keyword_lower in source.lower()]

    def search_by_category(self, category: str) -> List[IARCAgent]:
        """Find agents by category (Chemical, Biological, Physical, Occupational, Lifestyle, Pharmaceutical)."""
        category_lower = category.lower()
        return [agent for agent in self.get_all_agents()
                if category_lower in agent.category.lower()]

    def get_litigation_targets(self) -> List[IARCAgent]:
        """Get agents that are/were major litigation targets."""
        keywords = ["litigation", "major"]
        return [agent for agent in self.get_all_agents()
                if any(kw in agent.notes.lower() for kw in keywords)]

    def get_regulatory_divergence(self) -> List[Dict]:
        """Get chemicals with EU/US regulatory divergence."""
        return [c for c in self.high_priority if c.get("regulatory_divergence")]

    def get_emerging_concerns(self) -> List[Dict]:
        """Get emerging chemicals of concern for potential future litigation."""
        keywords = ["emerging", "proposed", "2024", "2025", "litigation", "recall"]
        return [c for c in self.high_priority
                if any(kw in c.get("status", "").lower() for kw in keywords)]

    def get_by_group(self, group: str) -> List[IARCAgent]:
        """Get all agents in a specific IARC group."""
        group_map = {
            "1": self.group_1,
            "2A": self.group_2a,
            "2B": self.group_2b,
        }
        return group_map.get(group.upper(), [])

    def get_all_cancer_sites(self) -> Set[str]:
        """Get all unique cancer sites in the database."""
        sites = set()
        for agent in self.get_all_agents():
            sites.update(agent.cancer_sites)
        return sites

    def get_all_exposure_sources(self) -> Set[str]:
        """Get all unique exposure sources in the database."""
        sources = set()
        for agent in self.get_all_agents():
            sources.update(agent.exposure_sources)
        return sources

    def get_stats(self) -> Dict:
        """Get comprehensive database statistics."""
        all_agents = self.get_all_agents()
        return {
            "group_1_count": len(self.group_1),
            "group_2a_count": len(self.group_2a),
            "group_2b_count": len(self.group_2b),
            "total_agents": len(all_agents),
            "high_priority_count": len(self.high_priority),
            "agents_with_cas": len([a for a in all_agents if a.cas_number]),
            "cancer_sites_covered": len(self.get_all_cancer_sites()),
            "exposure_sources": len(self.get_all_exposure_sources()),
            "litigation_targets": len(self.get_litigation_targets()),
            "regulatory_divergence": len(self.get_regulatory_divergence()),
            "categories": {
                "Chemical": len(self.search_by_category("Chemical")),
                "Biological": len(self.search_by_category("Biological")),
                "Physical": len(self.search_by_category("Physical")),
                "Occupational": len(self.search_by_category("Occupational")),
                "Lifestyle": len(self.search_by_category("Lifestyle")),
                "Pharmaceutical": len(self.search_by_category("Pharmaceutical")),
            }
        }


def main():
    """Test and display database statistics."""
    db = IARCDatabase()

    print("=" * 80)
    print("IARC CARCINOGEN DATABASE - COMPREHENSIVE EDITION")
    print("=" * 80)

    stats = db.get_stats()
    print(f"\n📊 DATABASE STATISTICS:")
    print(f"   Group 1 (Carcinogenic):          {stats['group_1_count']:>4} agents")
    print(f"   Group 2A (Probably carcinogenic): {stats['group_2a_count']:>4} agents")
    print(f"   Group 2B (Possibly carcinogenic): {stats['group_2b_count']:>4} agents")
    print(f"   ─────────────────────────────────────────")
    print(f"   Total IARC Agents:               {stats['total_agents']:>4}")
    print(f"   High-Priority Monitoring:        {stats['high_priority_count']:>4}")
    print(f"   Agents with CAS Numbers:         {stats['agents_with_cas']:>4}")
    print(f"   Cancer Sites Covered:            {stats['cancer_sites_covered']:>4}")
    print(f"   Known Litigation Targets:        {stats['litigation_targets']:>4}")
    print(f"   EU/US Regulatory Divergence:     {stats['regulatory_divergence']:>4}")

    print(f"\n📁 BY CATEGORY:")
    for cat, count in stats['categories'].items():
        if count > 0:
            print(f"   {cat}: {count}")

    print("\n" + "-" * 80)
    print("⚖️  MAJOR LITIGATION TARGETS:")
    for agent in db.get_litigation_targets():
        print(f"   • {agent.name} (Group {agent.group})")
        print(f"     Cancer sites: {', '.join(agent.cancer_sites[:3])}")
        if agent.notes:
            print(f"     Note: {agent.notes}")

    print("\n" + "-" * 80)
    print("🌍 EU/US REGULATORY DIVERGENCE (Top 10):")
    for chem in db.get_regulatory_divergence()[:10]:
        print(f"   • {chem['name']}")
        print(f"     Status: {chem['status']}")

    print("\n" + "-" * 80)
    print("🔬 LUNG CANCER ASSOCIATED AGENTS (First 15):")
    for agent in db.search_by_cancer_site("lung")[:15]:
        print(f"   • {agent.name} (Group {agent.group})")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
