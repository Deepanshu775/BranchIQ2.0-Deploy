"""BranchIQ source registry — every data input is registered here with type & confidence.

A. OFFICIAL / REPORTED DATA — bank annual reports, RBI disclosures (audited)
B. PUBLIC MARKET DATA — Census, government statistics (public, not audited per-bank)
C. BRANCHIQ DERIVED METRIC — computed by BranchIQ engines from A+B
D. MODEL ESTIMATE — BranchIQ analytical/model-generated scores
E. ML PREDICTION — BranchIQ predictive layer (heuristic model until real training data exists)

DEMO layer: synthetic branch placement & PIN-locality economics used for development only.
Never mixed with official figures — every demo record carries source_type="demo".
"""

SOURCES_REGISTRY = [
    {"source_id": "bank-annual-reports", "source_name": "Official Bank Annual Reports",
     "organization": "Individual banks (SBI, HDFC, ICICI, Axis, BoB, PNB, Canara, Kotak, IndusInd)",
     "dataset": "FY2025 annual reports / investor presentations", "period": "FY2025",
     "url": "https://www.rbi.org.in/Scripts/PublicationsView.aspx (index of bank disclosures)",
     "data_type": "official", "confidence": "high",
     "used_for": ["Bank branch totals", "Deposits", "Advances", "Growth rates"]},
    {"source_id": "rbi-dbie", "source_name": "RBI Database on Indian Economy (DBIE)",
     "organization": "Reserve Bank of India", "dataset": "State/district banking statistics", "period": "FY2025",
     "url": "https://dbie.rbi.org.in", "data_type": "official", "confidence": "high",
     "used_for": ["District deposit/credit aggregates (schema ready)", "CD ratio"]},
    {"source_id": "rbi-banking", "source_name": "RBI Basic Statistical Returns (BSR)",
     "organization": "Reserve Bank of India", "dataset": "Branch-level banking statistics", "period": "FY2025",
     "url": "https://www.rbi.org.in", "data_type": "official", "confidence": "high",
     "used_for": ["Branch counts by centre (schema ready)"]},
    {"source_id": "census", "source_name": "Census of India 2011 + 2026 projections",
     "organization": "Office of the Registrar General & Census Commissioner, India",
     "dataset": "Population, urbanization, towns", "period": "2011 / projected 2026",
     "url": "https://censusindia.gov.in", "data_type": "market", "confidence": "high",
     "used_for": ["District & town population", "Urbanization"]},
    {"source_id": "gov-economic", "source_name": "Government Economic Datasets (MoSPI / state GSDP)",
     "organization": "Ministry of Statistics & Programme Implementation", "dataset": "GSDP growth, MSME",
     "period": "FY2024-25", "url": "https://mospi.gov.in", "data_type": "market", "confidence": "medium",
     "used_for": ["Economic activity indicators"]},
    {"source_id": "osm", "source_name": "OpenStreetMap",
     "organization": "OSM Foundation", "dataset": "Coordinates, transport & commercial POIs", "period": "2026",
     "url": "https://www.openstreetmap.org", "data_type": "market", "confidence": "medium",
     "used_for": ["Approximate coordinates for towns & candidate sites"]},
    {"source_id": "branchiq-engine", "source_name": "BranchIQ Analytical Engine",
     "organization": "BranchIQ", "dataset": "Opportunity, whitespace, cannibalization & catchment models",
     "period": "current", "url": "", "data_type": "analytical", "confidence": "medium",
     "used_for": ["Opportunity scores", "Whitespace", "Cannibalization risk", "Decision bands"]},
    {"source_id": "branchiq-ml", "source_name": "BranchIQ Prediction Layer (heuristic ML)",
     "organization": "BranchIQ", "dataset": "Transparent feature-weighted high-potential-market model",
     "period": "current", "url": "", "data_type": "model", "confidence": "low",
     "used_for": ["High-potential probability", "Feature contribution explanations"]},
    {"source_id": "branchiq-demo", "source_name": "BranchIQ DEMO DATA LAYER",
     "organization": "BranchIQ (synthetic, for development)", "dataset":
     "Deterministic demo branch placement, PIN-locality economics & candidate sites", "period": "dev",
     "url": "", "data_type": "demo", "confidence": "low",
     "used_for": ["Demo branch records", "Demo PIN-locality catchments", "Candidate locations"]},
]

DEMO_DISCLAIMER = (
    "DEMO DATA NOTICE: District/town names, populations and coordinates are public geography "
    "(Census/OpenStreetMap, approximate). Branch placement, PIN-locality economics and candidate "
    "sites are SYNTHETIC demo data generated deterministically for development. They are never "
    "official bank data. Real deployment should ingest RBI/DBIE and bank locator files through "
    "backend/data_pipeline."
)

PIN_LEVEL_NOTE = (
    "PIN-level banking indicators are not published by RBI. PIN/locality recommendations are "
    "DERIVED from district/city indicators and geospatial branch data."
)

TRANSPARENCY_NOTES = [
    "BranchIQ does not use confidential customer or internal bank data.",
    "Official figures come only from audited annual reports / RBI disclosures and are labelled OFFICIAL REPORTED DATA.",
    "Opportunity, whitespace and cannibalization scores are BranchIQ analytical/model-generated estimates.",
    "Branch placement and PIN-locality economics are demo data for development, labelled DEMO DATA.",
    "BranchIQ never says a regulator recommends opening a branch — recommendations are BranchIQ's own analytical output.",
]

METHODOLOGY_NOTE = (
    "BranchIQ combines publicly available banking, geographic and market indicators with its own "
    "transparent analytical framework. Strategic scores are model-generated estimates, not official "
    "bank forecasts; demo records are labelled as such."
)

METHODOLOGY_FLOW = [
    {"step": "Public Data", "desc": "RBI, DBIE, annual reports, government datasets"},
    {"step": "Data Standardization", "desc": "Normalize periods, units & geographies"},
    {"step": "Market Analysis", "desc": "Demand, demographics & economic activity"},
    {"step": "Bank Network Analysis", "desc": "Presence, coverage & network scale"},
    {"step": "Competitive Analysis", "desc": "Relative positioning & intensity"},
    {"step": "Opportunity Score", "desc": "Weighted analytical scoring model"},
    {"step": "AI Consulting Recommendation", "desc": "Strategy synthesis & priority action"},
]
