"""
Configuration for the OPCS-4 neurosurgical workload decomposition.

All analytic choices that a reader might want to vary are declared here rather
than embedded in the analysis scripts.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data-raw"
DERIVED = ROOT / "derived"
FIGURES = ROOT / "outputs" / "figures"
TABLES = ROOT / "outputs" / "tables"

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

OPENCODECOUNTS_COMMIT = "a92a37bbfc3d670864fe6ae08edf1a61ed1d818e"
OPENCODECOUNTS_BASE = (
    "https://raw.githubusercontent.com/bennettoxford/opencodecounts/"
    f"{OPENCODECOUNTS_COMMIT}/data"
)
RDA_FILES = ["opcs4_usage", "opcs4_usage_breakdowns"]

# Nomis (ONS mid-year population estimates, England, single year of age)
NOMIS_URL = (
    "https://www.nomisweb.co.uk/api/v01/dataset/NM_2002_1.data.csv"
    "?geography=2092957699&date={dates}&gender=0&c_age=101...191"
    "&measures=20100&select=date_name,c_age_name,obs_value"
)
MYE_YEARS = list(range(2012, 2025))  # mid-year estimates 2012-2024

# ONS 2024-based national population projections, England, single year of age.
# Variants 11 and 13 differ in age composition but also in total size; the
# projection step decomposes the two rather than treating the variants as a
# pure age-structure contrast. Fertility and migration variants are not
# retrieved separately.
NPP_URL = (
    "https://www.nomisweb.co.uk/api/v01/dataset/NM_2403_1.data.csv"
    "?geography=2092957699&projected_year={years}&projvar=1,11,13&gender=0"
    "&c_age=0,1...105,223&measures=20100"
    "&select=projected_year_name,projvar_name,c_age_name,obs_value"
)
NPP_YEARS = list(range(2024, 2040))
PROJECTION_TARGET_FY = 2040   # financial year ending 2040
PROJECTION_BASE_FY = 2025     # financial year ending 2025

# ---------------------------------------------------------------------------
# Procedure groups
#
# Groups are defined at four-character OPCS-4 level. Each group is intended to
# be clinically coherent and to have a distinct a priori expectation about
# whether growth should be demographic or practice-driven. The expectations are
# recorded so that the analysis can be read against them rather than after them.
# ---------------------------------------------------------------------------

PROCEDURE_GROUPS = {
    "Extra-axial haematoma evacuation": {
        "codes": ["A401", "A411"],
        "prior": "demographic",
        "note": (
            "Evacuation of extradural and subdural haematoma. OPCS-4 does not "
            "distinguish acute from chronic subdural collections."
        ),
    },
    "Intracerebral haematoma evacuation": {
        "codes": ["A052", "A053", "A054"],
        "prior": "demographic",
        "note": "Evacuation of intraparenchymal haematoma.",
    },
    "Intracranial tumour resection and biopsy": {
        "codes": [
            "A021", "A022", "A023", "A024", "A025", "A026", "A027", "A028", "A029",
            "A041", "A042", "A043", "A044", "A045", "A046", "A048", "A049",
            "A081", "A082", "A083", "A084", "A085", "A086", "A088", "A089",
            "A171",
            "A381", "A382", "A383", "A384", "A385", "A386", "A388", "A389",
            "A431", "A432", "A438", "A439",
        ],
        "prior": "mixed",
        "note": "Excision and biopsy of intracranial parenchymal and meningeal lesions.",
    },
    "CSF diversion, primary": {
        "codes": ["A122", "A123", "A124", "A125", "A128", "A129", "A172"],
        "prior": "mixed",
        "note": "Creation of cerebroventricular shunts and endoscopic third ventriculostomy.",
    },
    "CSF diversion, revision and maintenance": {
        "codes": [
            "A131", "A132", "A133", "A134", "A138", "A139",
            "A141", "A142", "A143", "A144", "A145", "A148", "A149",
        ],
        "prior": "rate",
        "note": "Attention to, revision of and removal of existing shunt systems.",
    },
    "Peripheral nerve entrapment release": {
        "codes": ["A651", "A652", "A658", "A659", "A671", "A672", "A673", "A678", "A679"],
        "prior": "rate",
        "note": "Carpal tunnel, cubital tunnel and other entrapment releases.",
    },
    "Neuromodulation implantation": {
        "codes": ["A091", "A095", "A331", "A334", "A701", "A704"],
        "prior": "rate",
        "note": (
            "Implantation of brain, cranial nerve and peripheral nerve "
            "neurostimulators and electrodes. Excludes maintenance and removal."
        ),
    },
    "Spinal nerve root injection and denervation": {
        "codes": ["A573", "A574", "A577"],
        "prior": "rate",
        "note": (
            "Therapeutic and destructive interventions on spinal nerve roots. "
            "Included as a high-volume comparator with contested indications."
        ),
    },
    "Lumbar decompression without fusion": {
        "codes": [
            "V252", "V254", "V255", "V256", "V258", "V259",
            "V331", "V332", "V337", "V338", "V339",
        ],
        "prior": "demographic",
        "note": (
            "Primary lumbar decompression and discectomy without concurrent "
            "fusion. Lumbar canal stenosis is strongly age-related, so this is "
            "the clearest a priori demographic expectation outside the cranial "
            "emergency groups."
        ),
    },
    "Spinal fusion and instrumentation": {
        "codes": [
            "V221", "V224", "V225", "V251", "V253", "V294",
            "V333", "V335", "V336",
            "V381", "V382", "V383", "V384", "V385", "V386", "V388", "V389",
        ],
        "prior": "rate",
        "note": (
            "Degenerative cervical and lumbar fusion. Long-standing "
            "international practice variation makes a rate-driven expectation "
            "the default."
        ),
    },
    "Spinal deformity correction": {
        "codes": ["V411", "V412", "V414", "V415", "V417", "V418", "V419"],
        "prior": "rate",
        "note": (
            "Instrumental correction of spinal deformity, predominantly "
            "adolescent. Included as the group whose age profile is furthest "
            "from the cranial emergency groups; its age-structure component is "
            "expected to be negative."
        ),
    },
    "Spinal facet joint denervation": {
        "codes": [
            "V481", "V482", "V483", "V484", "V485", "V486", "V487", "V488",
            "V489",
        ],
        "prior": "rate",
        "note": (
            "Denervation of spinal facet joints. A second high-volume "
            "intervention with contested indications and explicit commissioning "
            "restriction during the study period."
        ),
    },
}

# ---------------------------------------------------------------------------
# Age bands
#
# opencodecounts reports single years for ages 15-19; these are collapsed to a
# 15-19 band so that all bands above age 4 are five-year bands.
# ---------------------------------------------------------------------------

AGE_BANDS = [
    "0", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
    "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79",
    "80-84", "85-89", "90+",
]

BREAKDOWN_TO_BAND = {
    "age_0": "0", "age_1_4": "1-4", "age_5_9": "5-9", "age_10_14": "10-14",
    "age_15": "15-19", "age_16": "15-19", "age_17": "15-19", "age_18": "15-19",
    "age_19": "15-19", "age_20_24": "20-24", "age_25_29": "25-29",
    "age_30_34": "30-34", "age_35_39": "35-39", "age_40_44": "40-44",
    "age_45_49": "45-49", "age_50_54": "50-54", "age_55_59": "55-59",
    "age_60_64": "60-64", "age_65_69": "65-69", "age_70_74": "70-74",
    "age_75_79": "75-79", "age_80_84": "80-84", "age_85_89": "85-89",
    "age_90plus": "90+",
}

# ---------------------------------------------------------------------------
# Comparison periods
#
# HES financial years are labelled by the year in which they end, so "2013"
# denotes 1 April 2012 to 31 March 2013. The pandemic makes a single
# start-to-end comparison uninterpretable, so the pre-pandemic and
# pandemic-and-recovery periods are the primary contrasts.
# ---------------------------------------------------------------------------

PERIODS = {
    "Pre-pandemic (2012/13 to 2018/19)": (2013, 2019),
    "Later period (2018/19 to 2024/25)": (2019, 2025),
    "Pandemic shock (2019/20 to 2020/21)": (2020, 2021),
    "Recovery (2020/21 to 2024/25)": (2021, 2025),
    "Whole period (2012/13 to 2024/25)": (2013, 2025),
    "Pre-pandemic, alternative endpoint (2012/13 to 2019/20)": (2013, 2020),
}
PRIMARY_PERIOD = "Pre-pandemic (2012/13 to 2018/19)"
ALT_ENDPOINT_PERIOD = "Pre-pandemic, alternative endpoint (2012/13 to 2019/20)"

# Periods shown in the main decomposition figure and table.
DISPLAY_PERIODS = [
    "Pre-pandemic (2012/13 to 2018/19)",
    "Later period (2018/19 to 2024/25)",
]
LATER_PERIOD = "Later period (2018/19 to 2024/25)"

# OPCS-4 revisions took effect in April 2014 (4.7), April 2017 (4.8),
# April 2020 (4.9) and April 2023 (4.10); the first financial years recorded
# under each new version end in 2015, 2018, 2021 and 2024. The code-level
# revision screen (s11) tests for level shifts at these boundaries. 2021 is
# confounded by the pandemic and is screened but not interpretable.
OPCS_REVISION_FYS = [2015, 2018, 2021, 2024]

# Endpoint-sensitivity contrast using three-year averages at either end of the
# pre-pandemic window. Averaging counts and populations over three financial
# years reduces the influence of any single unusually high or low endpoint
# year. 2019/20 is included in the closing average: it is predominantly
# pre-pandemic, with only its final weeks affected.
ENDPOINT_AVERAGES = {
    "label": "Three-year averages (2012/13-2014/15 to 2017/18-2019/20)",
    "start_fys": [2013, 2014, 2015],
    "end_fys": [2018, 2019, 2020],
}

# Consecutive-year decompositions are cumulated over this span to test whether
# the endpoint contrast is a stable feature of the period rather than an
# endpoint artefact.
CUMULATE_SPAN = (2013, 2020)

# Financial year ending in Y has its midpoint near 30 September Y-1; the
# closest mid-year population estimate is that for Y-1.
def fy_to_mye(fy_end_year: int) -> int:
    return fy_end_year - 1


# ---------------------------------------------------------------------------
# Analytic options
#
# The primary analysis uses all procedure positions with proportional
# redistribution of records whose age band is unallocated. All positions is
# primary because the age breakdowns are published on that basis only (the
# main-position variant is an approximation, see s02); proportional
# redistribution is primary because it preserves group-year totals without
# imposing an age on the unallocated remainder. The other five combinations
# are sensitivity analyses.
# ---------------------------------------------------------------------------

COUNT_BASIS = "all_procedures"   # primary; sensitivity uses "main_procedure"
UNKNOWN_AGE_HANDLING = "proportional"  # primary; sensitivity: "oldest", "drop"

# Age-standardisation: rates are directly standardised to the England mid-2012
# population in the twenty analysis age bands (open-ended top band 90+), the
# same standard throughout.
STANDARD_POP_MYE_YEAR = 2012

# ---------------------------------------------------------------------------
# Figure aesthetics (Nord palette, monospace)
# ---------------------------------------------------------------------------

NORD = {
    "bg": "#ECEFF4", "fg": "#2E3440", "grey": "#4C566A", "light": "#D8DEE9",
    "frost0": "#8FBCBB", "frost1": "#88C0D0", "frost2": "#81A1C1", "frost3": "#5E81AC",
    "red": "#BF616A", "orange": "#D08770", "yellow": "#EBCB8B",
    "green": "#A3BE8C", "purple": "#B48EAD",
}

GROUP_COLOURS = {
    "Extra-axial haematoma evacuation": NORD["red"],
    "Intracerebral haematoma evacuation": NORD["orange"],
    "Intracranial tumour resection and biopsy": NORD["frost3"],
    "CSF diversion, primary": NORD["frost1"],
    "CSF diversion, revision and maintenance": NORD["frost0"],
    "Peripheral nerve entrapment release": NORD["green"],
    "Neuromodulation implantation": NORD["purple"],
    "Spinal nerve root injection and denervation": NORD["yellow"],
    "Lumbar decompression without fusion": NORD["frost2"],
    "Spinal fusion and instrumentation": "#434C5E",
    "Spinal deformity correction": "#7E9B76",
    "Spinal facet joint denervation": "#C9A227",
}

COMPONENT_COLOURS = {
    "population_size": NORD["frost2"],
    "age_structure": NORD["frost3"],
    "age_specific_rate": NORD["orange"],
}
