"""BranchIQ bank master — ported from the original BranchIQ `src/data/banks.js`.

Fields `branches / deposits / advances / growth` are OFFICIAL REPORTED figures
(FY2025 annual reports / RBI disclosures). `digitalReadiness` and
`geographicCoverage` are BRANCHIQ MODEL ESTIMATES, labelled in the UI.

`footprint_weight` (BranchIQ model input, 0-1) drives the DEMO branch-placement
density in seed.py — it is derived from reported network size, not invented data.
"""

BANKS_BASE = [
    {"short": "SBI", "name": "State Bank of India (SBI)", "sector": "Public", "reportingPeriod": "FY2025",
     "branches": 22542, "deposits": 5380000, "advances": 4235000, "depositGrowth": 9.2, "creditGrowth": 12.0,
     "digitalReadiness": 82, "geographicCoverage": 98, "footprint_weight": 1.00,
     "source": "SBI Annual Report FY2025",
     "sourceUrl": "https://www.sbi.co.in/web/investor-relations/annual-report"},
    {"short": "Bank of Baroda", "name": "Bank of Baroda (BOB)", "sector": "Public", "reportingPeriod": "FY2025",
     "branches": 8320, "deposits": 1385000, "advances": 1160000, "depositGrowth": 9.0, "creditGrowth": 13.7,
     "digitalReadiness": 74, "geographicCoverage": 90, "footprint_weight": 0.37,
     "source": "Bank of Baroda Annual Report FY2025",
     "sourceUrl": "https://www.bankofbaroda.in/shareholders-corner/financial-reports/annual-reports"},
    {"short": "PNB", "name": "Punjab National Bank (PNB)", "sector": "Public", "reportingPeriod": "FY2025",
     "branches": 10108, "deposits": 1560000, "advances": 1140000, "depositGrowth": 8.5, "creditGrowth": 13.0,
     "digitalReadiness": 70, "geographicCoverage": 88, "footprint_weight": 0.45,
     "source": "PNB Annual Report FY2025",
     "sourceUrl": "https://www.pnbindia.in/annual-reports.html"},
    {"short": "Canara Bank", "name": "Canara Bank", "sector": "Public", "reportingPeriod": "FY2025",
     "branches": 9816, "deposits": 1370000, "advances": 1050000, "depositGrowth": 11.0, "creditGrowth": 11.3,
     "digitalReadiness": 71, "geographicCoverage": 86, "footprint_weight": 0.44,
     "source": "Canara Bank Annual Report FY2025",
     "sourceUrl": "https://canarabank.com/pages/annual-report"},
    {"short": "HDFC Bank", "name": "HDFC Bank", "sector": "Private", "reportingPeriod": "FY2025",
     "branches": 9455, "deposits": 2790000, "advances": 2660000, "depositGrowth": 14.0, "creditGrowth": 8.0,
     "digitalReadiness": 88, "geographicCoverage": 82, "footprint_weight": 0.42,
     "source": "HDFC Bank Annual Report FY2025",
     "sourceUrl": "https://www.hdfcbank.com/personal/about-us/investor-relations/annual-reports"},
    {"short": "ICICI Bank", "name": "ICICI Bank", "sector": "Private", "reportingPeriod": "FY2025",
     "branches": 6742, "deposits": 1520000, "advances": 1300000, "depositGrowth": 14.0, "creditGrowth": 13.0,
     "digitalReadiness": 90, "geographicCoverage": 78, "footprint_weight": 0.30,
     "source": "ICICI Bank Annual Report FY2025",
     "sourceUrl": "https://www.icicibank.com/about-us/annual"},
    {"short": "Axis Bank", "name": "Axis Bank", "sector": "Private", "reportingPeriod": "FY2025",
     "branches": 5876, "deposits": 1120000, "advances": 1030000, "depositGrowth": 10.0, "creditGrowth": 8.0,
     "digitalReadiness": 84, "geographicCoverage": 76, "footprint_weight": 0.26,
     "source": "Axis Bank Annual Report FY2025",
     "sourceUrl": "https://www.axisbank.com/shareholders-corner/shareholders-information/annual-reports"},
    {"short": "Kotak Mahindra Bank", "name": "Kotak Mahindra Bank", "sector": "Private", "reportingPeriod": "FY2025",
     "branches": 2148, "deposits": 470000, "advances": 440000, "depositGrowth": 15.0, "creditGrowth": 13.0,
     "digitalReadiness": 86, "geographicCoverage": 60, "footprint_weight": 0.10,
     "source": "Kotak Mahindra Bank Annual Report FY2025",
     "sourceUrl": "https://www.kotak.com/en/investor-relations/financial-results/annual-reports.html"},
    {"short": "IndusInd Bank", "name": "IndusInd Bank", "sector": "Private", "reportingPeriod": "FY2025",
     "branches": 3063, "deposits": 410000, "advances": 375000, "depositGrowth": 11.0, "creditGrowth": 12.0,
     "digitalReadiness": 80, "geographicCoverage": 58, "footprint_weight": 0.14,
     "source": "IndusInd Bank Annual Report FY2025",
     "sourceUrl": "https://www.indusind.com/in/en/personal/regulatory-disclosures/annual-report.html"},
]

SECTOR_URBAN_BIAS = {  # BranchIQ model input — drives demo placement tilt, labelled model estimate
    "Private": {"urban_states_bonus": 10, "rural_states_penalty": -8},
    "Public": {"urban_states_bonus": -4, "rural_states_bonus": 10},
}

URBAN_STATES = {"Maharashtra", "Delhi NCR", "Karnataka", "Telangana", "Goa", "Kerala", "Puducherry", "Chandigarh"}
RURAL_HEAVY = {"Uttar Pradesh", "West Bengal", "Madhya Pradesh", "Rajasthan", "Bihar", "Jharkhand",
               "Chhattisgarh", "Odisha", "Assam", "Uttarakhand", "Himachal Pradesh", "Jammu & Kashmir", "Tripura"}
