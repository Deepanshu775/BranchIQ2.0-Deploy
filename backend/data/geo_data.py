"""BranchIQ geo base dataset — 25 states/UTs, districts, towns/localities.

PROVENANCE
- State names, district names and town names: public geography (Census of India 2011 / Survey of India).
- District populations: Census 2011 with 2026 projections (public, approx).
- Coordinates: approximate public coordinates (3 decimals) — APPROXIMATE, not survey-grade.
- PIN codes: real where confidently known; otherwise demo placeholder using the correct
  state-level PIN prefix — always labelled `pin_source: "demo"` when not verified.

Towns marked kind="locality" are generic urban localities (market/industrial/bus-stand areas).
More localities + PIN areas + candidate locations + demo branches are GENERATED deterministically
in seed.py from this base — never hand-edited in frontend code.
"""

# (state, region, lat, lng, population_mn, indicators{...}, districts)
# indicators: gsdpGrowth, marketGrowth, creditOpportunity, depositOpportunity,
#             customerPotential, digitalReadiness, marketConcentration, dataConfidence
# district: (name, lat, lng, pop_mn, tier, [(town, lat, lng, pop_k, pin, kind), ...])

IND = dict  # shorthand


def _s(name, region, lat, lng, pop_mn, ind, districts):
    return {"name": name, "region": region, "lat": lat, "lng": lng, "population_mn": pop_mn,
            "indicators": ind, "districts": districts}


def _d(name, lat, lng, pop_mn, tier, towns):
    return {"name": name, "lat": lat, "lng": lng, "population_mn": pop_mn, "tier": tier, "towns": towns}


def _t(name, lat, lng, pop_k, pin, kind="town"):
    return {"name": name, "lat": lat, "lng": lng, "population_k": pop_k, "pin": pin, "kind": kind}


STATES = [
    _s("Uttar Pradesh", "Central", 27.10, 78.50, 235,
       IND(gsdpGrowth=7.6, marketGrowth=74, creditOpportunity=72, depositOpportunity=71, customerPotential=88,
           digitalReadiness=62, marketConcentration=58, dataConfidence="MEDIUM"),
       [
           _d("Meerut", 28.98, 77.71, 3.4, "tier2", [
               _t("Meerut City", 28.98, 77.71, 1420, "250001", "city"),
               _t("Modipuram", 29.03, 77.68, 95, "250110", "town"),
               _t("Shastri Nagar", 28.99, 77.69, 120, "250004", "locality"),
           ]),
           _d("Gautam Buddha Nagar", 28.53, 77.39, 1.7, "tier1", [
               _t("Noida", 28.57, 77.32, 800, "201301", "city"),
               _t("Noida Sector 62", 28.62, 77.37, 150, "201309", "locality"),
               _t("Greater Noida", 28.47, 77.50, 250, "201310", "town"),
           ]),
           _d("Lucknow", 26.85, 80.95, 3.7, "tier1", [
               _t("Lucknow", 26.85, 80.95, 1200, "226001", "city"),
               _t("Hazratganj", 26.85, 80.94, 110, "226001", "locality"),
               _t("Gomti Nagar", 26.84, 81.00, 180, "226010", "locality"),
           ]),
           _d("Kanpur Nagar", 26.45, 80.33, 3.1, "tier1", [
               _t("Kanpur", 26.45, 80.33, 1050, "208001", "city"),
               _t("Swaroop Nagar", 26.48, 80.33, 90, "208002", "locality"),
           ]),
           _d("Varanasi", 25.32, 82.99, 1.7, "tier2", [
               _t("Varanasi", 25.32, 82.99, 620, "221001", "city"),
               _t("Lanka", 25.28, 83.00, 80, "221005", "locality"),
           ]),
           _d("Agra", 27.18, 78.01, 2.3, "tier2", [
               _t("Agra", 27.18, 78.01, 700, "282001", "city"),
               _t("Sanjay Place", 27.17, 78.01, 60, "282002", "locality"),
           ]),
           _d("Prayagraj", 25.44, 81.85, 1.6, "tier2", [
               _t("Prayagraj", 25.44, 81.85, 590, "211001", "city"),
               _t("Civil Lines", 25.45, 81.84, 70, "211001", "locality"),
           ]),
           _d("Ghaziabad", 28.67, 77.42, 2.7, "tier1", [
               _t("Ghaziabad", 28.67, 77.42, 760, "201001", "city"),
               _t("Vaishali", 28.65, 77.34, 130, "201010", "locality"),
               _t("Indirapuram", 28.64, 77.36, 120, "201014", "locality"),
           ]),
           _d("Gorakhpur", 26.76, 83.37, 1.4, "tier2", [
               _t("Gorakhpur", 26.76, 83.37, 480, "273001", "city"),
           ]),
           _d("Bareilly", 28.37, 79.43, 1.4, "tier2", [
               _t("Bareilly", 28.37, 79.43, 430, "243001", "city"),
           ]),
           _d("Aligarh", 27.90, 78.07, 1.3, "tier2", [
               _t("Aligarh", 27.90, 78.07, 400, "202001", "city"),
           ]),
           _d("Jhansi", 25.45, 78.57, 0.6, "tier3", [
               _t("Jhansi", 25.45, 78.57, 260, "284001", "city"),
           ]),
           _d("Saharanpur", 29.97, 77.55, 0.9, "tier3", [
               _t("Saharanpur", 29.97, 77.55, 340, "247001", "city"),
           ]),
           _d("Moradabad", 28.84, 78.78, 1.1, "tier3", [
               _t("Moradabad", 28.84, 78.78, 380, "244001", "city"),
           ]),
       ]),
    _s("Maharashtra", "West", 19.75, 75.71, 126,
       IND(gsdpGrowth=8.1, marketGrowth=84, creditOpportunity=90, depositOpportunity=88, customerPotential=86,
           digitalReadiness=85, marketConcentration=82, dataConfidence="HIGH"),
       [
           _d("Mumbai Suburban", 19.13, 72.85, 9.6, "tier1", [
               _t("Mumbai", 19.08, 72.88, 2100, "400001", "city"),
               _t("Andheri West", 19.12, 72.85, 700, "400053", "locality"),
               _t("Bandra West", 19.06, 72.83, 650, "400050", "locality"),
               _t("Borivali West", 19.23, 72.86, 590, "400066", "locality"),
           ]),
           _d("Pune", 18.52, 73.86, 9.4, "tier1", [
               _t("Pune", 18.52, 73.86, 1750, "411001", "city"),
               _t("Kothrud", 18.51, 73.80, 180, "411038", "locality"),
               _t("Hinjewadi", 18.59, 73.74, 95, "411057", "locality"),
               _t("Hadapsar", 18.50, 73.93, 210, "411028", "locality"),
           ]),
           _d("Nagpur", 21.15, 79.09, 3.0, "tier2", [
               _t("Nagpur", 21.15, 79.09, 1050, "440001", "city"),
               _t("Sitabuldi", 21.15, 79.09, 140, "440012", "locality"),
               _t("Dharampeth", 21.16, 79.06, 120, "440010", "locality"),
           ]),
           _d("Thane", 19.22, 72.98, 8.1, "tier1", [
               _t("Thane West", 19.22, 72.97, 760, "400601", "city"),
               _t("Ghodbunder Road", 19.24, 72.99, 180, "400615", "locality"),
               _t("Kalyan", 19.24, 73.13, 420, "421301", "town"),
           ]),
           _d("Nashik", 20.00, 73.79, 1.9, "tier2", [
               _t("Nashik", 20.00, 73.79, 490, "422001", "city"),
               _t("College Road", 20.01, 73.78, 150, "422005", "locality"),
               _t("Panchavati", 20.02, 73.83, 120, "422003", "locality"),
           ]),
           _d("Aurangabad", 19.88, 75.34, 1.6, "tier2", [
               _t("Aurangabad", 19.88, 75.34, 380, "431001", "city"),
               _t("Osmanpura", 19.89, 75.33, 90, "431001", "locality"),
           ]),
           _d("Solapur", 17.66, 75.91, 1.5, "tier3", [
               _t("Solapur", 17.66, 75.91, 320, "413001", "city"),
           ]),
           _d("Kolhapur", 16.70, 74.24, 1.0, "tier3", [
               _t("Kolhapur", 16.70, 74.24, 240, "416001", "city"),
           ]),
           _d("Amravati", 20.93, 77.75, 0.9, "tier3", [
               _t("Amravati", 20.93, 77.75, 220, "444601", "city"),
           ]),
           _d("Navi Mumbai (Raigad belt)", 19.03, 73.02, 1.2, "tier1", [
               _t("Vashi", 19.08, 72.85, 260, "400703", "locality"),
               _t("Kharghar", 19.11, 73.10, 190, "410210", "locality"),
           ]),
       ]),
    _s("Karnataka", "South", 15.32, 75.71, 68,
       IND(gsdpGrowth=8.6, marketGrowth=86, creditOpportunity=88, depositOpportunity=79, customerPotential=84,
           digitalReadiness=88, marketConcentration=74, dataConfidence="HIGH"),
       [
           _d("Bengaluru Urban", 12.97, 77.59, 9.6, "tier1", [
               _t("Bengaluru", 12.97, 77.59, 1300, "560001", "city"),
               _t("Koramangala", 12.94, 77.62, 180, "560034", "locality"),
               _t("Whitefield", 12.97, 77.73, 190, "560066", "locality"),
               _t("Indiranagar", 12.97, 77.64, 150, "560038", "locality"),
               _t("Jayanagar", 12.93, 77.59, 170, "560041", "locality"),
           ]),
           _d("Mysuru", 12.30, 76.64, 1.1, "tier2", [
               _t("Mysuru", 12.30, 76.64, 420, "570001", "city"),
               _t("Kuvempunagar", 12.29, 76.63, 90, "570023", "locality"),
           ]),
           _d("Belagavi", 15.85, 74.50, 0.9, "tier3", [
               _t("Belagavi", 15.85, 74.50, 320, "590001", "city"),
           ]),
           _d("Hubballi-Dharwad", 15.36, 75.12, 1.0, "tier2", [
               _t("Hubballi", 15.36, 75.12, 360, "580020", "city"),
               _t("Dharwad", 15.46, 75.07, 260, "580001", "town"),
           ]),
           _d("Mangaluru", 12.91, 74.86, 0.7, "tier2", [
               _t("Mangaluru", 12.91, 74.86, 300, "575001", "city"),
           ]),
           _d("Ballari", 15.14, 76.92, 0.5, "tier3", [
               _t("Ballari", 15.14, 76.92, 190, "583101", "city"),
           ]),
           _d("Kalaburagi", 17.33, 76.83, 0.5, "tier3", [
               _t("Kalaburagi", 17.33, 76.83, 180, "585101", "city"),
           ]),
           _d("Davanagere", 14.46, 75.92, 0.5, "tier3", [
               _t("Davanagere", 14.46, 75.92, 170, "577001", "city"),
           ]),
           _d("Udupi", 13.34, 74.75, 0.4, "tier3", [
               _t("Udupi", 13.34, 74.75, 120, "576101", "city"),
           ]),
           _d("Tumakuru", 13.34, 77.10, 0.5, "tier3", [
               _t("Tumakuru", 13.34, 77.10, 160, "572101", "city"),
           ]),
       ]),
    _s("Delhi NCR", "North", 28.61, 77.21, 34,
       IND(gsdpGrowth=8.4, marketGrowth=82, creditOpportunity=88, depositOpportunity=90, customerPotential=80,
           digitalReadiness=92, marketConcentration=88, dataConfidence="HIGH"),
       [
           _d("New Delhi", 28.61, 77.21, 0.35, "tier1", [
               _t("New Delhi", 28.61, 77.21, 260, "110001", "city"),
               _t("Connaught Place", 28.63, 77.22, 60, "110001", "locality"),
               _t("Saket", 28.52, 77.19, 90, "110017", "locality"),
           ]),
           _d("South West Delhi", 28.55, 77.15, 2.3, "tier1", [
               _t("Hauz Khas", 28.55, 77.20, 100, "110016", "locality"),
               _t("Dwarka", 28.59, 77.05, 130, "110075", "locality"),
           ]),
           _d("North West Delhi", 28.72, 77.13, 2.2, "tier1", [
               _t("Rohini", 28.70, 77.12, 180, "110085", "locality"),
               _t("Ashok Vihar", 28.69, 77.17, 90, "110052", "locality"),
           ]),
           _d("West Delhi", 28.65, 77.09, 2.5, "tier1", [
               _t("Rajouri Garden", 28.65, 77.12, 110, "110027", "locality"),
               _t("Janakpuri", 28.62, 77.09, 130, "110058", "locality"),
           ]),
           _d("East Delhi", 28.60, 77.32, 1.7, "tier1", [
               _t("Preet Vihar", 28.64, 77.31, 90, "110092", "locality"),
               _t("Mayur Vihar", 28.61, 77.29, 110, "110091", "locality"),
           ]),
       ]),
    _s("Telangana", "South", 17.98, 79.06, 39,
       IND(gsdpGrowth=8.9, marketGrowth=85, creditOpportunity=84, depositOpportunity=78, customerPotential=81,
           digitalReadiness=86, marketConcentration=70, dataConfidence="HIGH"),
       [
           _d("Hyderabad", 17.39, 78.49, 6.8, "tier1", [
               _t("Hyderabad", 17.39, 78.49, 1100, "500001", "city"),
               _t("HITEC City", 17.45, 78.38, 95, "500081", "locality"),
               _t("Gachibowli", 17.44, 78.35, 80, "500032", "locality"),
               _t("Banjara Hills", 17.41, 78.43, 110, "500034", "locality"),
           ]),
           _d("Rangareddy", 17.24, 78.32, 2.4, "tier1", [
               _t("Kukatpally", 17.48, 78.40, 150, "500072", "locality"),
               _t("Shamshabad", 17.24, 78.32, 60, "501218", "town"),
           ]),
           _d("Warangal", 18.00, 79.58, 1.0, "tier2", [
               _t("Warangal", 18.00, 79.58, 380, "506002", "city"),
           ]),
           _d("Nizamabad", 18.67, 78.10, 0.5, "tier3", [
               _t("Nizamabad", 18.67, 78.10, 160, "503001", "city"),
           ]),
           _d("Karimnagar", 18.44, 79.13, 0.5, "tier3", [
               _t("Karimnagar", 18.44, 79.13, 150, "505001", "city"),
           ]),
           _d("Khammam", 17.25, 80.15, 0.4, "tier3", [
               _t("Khammam", 17.25, 80.15, 140, "507001", "city"),
           ]),
           _d("Medchal-Malkajgiri", 17.63, 78.48, 0.6, "tier2", [
               _t("Medchal", 17.63, 78.48, 60, "501401", "town"),
               _t("Uppal", 17.40, 78.56, 110, "500039", "locality"),
           ]),
           _d("Mahbubnagar", 16.74, 77.99, 0.5, "tier3", [
               _t("Mahbubnagar", 16.74, 77.99, 130, "509001", "city"),
           ]),
       ]),
    _s("Tamil Nadu", "South", 11.13, 78.66, 77,
       IND(gsdpGrowth=8.0, marketGrowth=80, creditOpportunity=85, depositOpportunity=82, customerPotential=83,
           digitalReadiness=82, marketConcentration=76, dataConfidence="HIGH"),
       [
           _d("Chennai", 13.08, 80.27, 7.1, "tier1", [
               _t("Chennai", 13.08, 80.27, 1100, "600001", "city"),
               _t("T Nagar", 13.04, 80.23, 120, "600017", "locality"),
               _t("Velachery", 12.98, 80.22, 110, "600042", "locality"),
               _t("Anna Nagar", 13.09, 80.21, 130, "600040", "locality"),
           ]),
           _d("Coimbatore", 11.02, 76.96, 2.2, "tier1", [
               _t("Coimbatore", 11.02, 76.96, 700, "641001", "city"),
               _t("Gandhipuram", 11.02, 76.96, 90, "641012", "locality"),
               _t("Peelamedu", 11.03, 77.04, 80, "641004", "locality"),
           ]),
           _d("Madurai", 9.93, 78.12, 1.5, "tier2", [
               _t("Madurai", 9.93, 78.12, 520, "625001", "city"),
           ]),
           _d("Tiruchirappalli", 10.79, 78.70, 1.0, "tier2", [
               _t("Tiruchirappalli", 10.79, 78.70, 340, "620001", "city"),
           ]),
           _d("Salem", 11.66, 78.15, 0.9, "tier3", [
               _t("Salem", 11.66, 78.15, 280, "636001", "city"),
           ]),
           _d("Tirunelveli", 8.71, 77.76, 0.4, "tier3", [
               _t("Tirunelveli", 8.71, 77.76, 120, "627001", "city"),
           ]),
           _d("Erode", 11.34, 77.72, 0.5, "tier3", [
               _t("Erode", 11.34, 77.72, 130, "638001", "city"),
           ]),
           _d("Vellore", 12.92, 79.13, 0.5, "tier3", [
               _t("Vellore", 12.92, 79.13, 140, "632001", "city"),
           ]),
           _d("Thoothukudi", 8.76, 78.13, 0.3, "tier3", [
               _t("Thoothukudi", 8.76, 78.13, 90, "628001", "city"),
           ]),
           _d("Thanjavur", 10.79, 79.14, 0.3, "tier3", [
               _t("Thanjavur", 10.79, 79.14, 80, "613001", "city"),
           ]),
           _d("Kancheepuram", 12.83, 79.70, 0.6, "tier2", [
               _t("Kanchipuram", 12.83, 79.70, 100, "631502", "town"),
               _t("Chengalpattu", 12.69, 79.98, 90, "603001", "town"),
           ]),
       ]),
    _s("Gujarat", "West", 22.67, 71.57, 71,
       IND(gsdpGrowth=8.3, marketGrowth=83, creditOpportunity=86, depositOpportunity=80, customerPotential=82,
           digitalReadiness=80, marketConcentration=72, dataConfidence="HIGH"),
       [
           _d("Ahmedabad", 23.02, 72.57, 7.2, "tier1", [
               _t("Ahmedabad", 23.02, 72.57, 1200, "380001", "city"),
               _t("Navrangpura", 23.03, 72.55, 140, "380009", "locality"),
               _t("Maninagar", 22.99, 72.60, 120, "380008", "locality"),
           ]),
           _d("Surat", 21.17, 72.83, 6.0, "tier1", [
               _t("Surat", 21.17, 72.83, 900, "395001", "city"),
               _t("Adajan", 21.20, 72.79, 130, "395009", "locality"),
               _t("Vesu", 21.13, 72.76, 90, "395007", "locality"),
           ]),
           _d("Vadodara", 22.31, 73.19, 2.1, "tier1", [
               _t("Vadodara", 22.31, 73.19, 560, "390001", "city"),
               _t("Alkapuri", 22.31, 73.18, 90, "390007", "locality"),
           ]),
           _d("Rajkot", 22.30, 70.80, 1.6, "tier2", [
               _t("Rajkot", 22.30, 70.80, 430, "360001", "city"),
           ]),
           _d("Bhavnagar", 21.76, 72.15, 0.7, "tier3", [
               _t("Bhavnagar", 21.76, 72.15, 190, "364001", "city"),
           ]),
           _d("Gandhinagar", 23.22, 72.65, 0.3, "tier2", [
               _t("Gandhinagar", 23.22, 72.65, 110, "382010", "city"),
           ]),
           _d("Jamnagar", 22.47, 70.06, 0.6, "tier3", [
               _t("Jamnagar", 22.47, 70.06, 170, "361001", "city"),
           ]),
           _d("Junagadh", 21.52, 70.46, 0.4, "tier3", [
               _t("Junagadh", 21.52, 70.46, 120, "362001", "city"),
           ]),
           _d("Anand", 22.56, 72.95, 0.3, "tier3", [
               _t("Anand", 22.56, 72.95, 100, "388001", "city"),
           ]),
       ]),
    _s("West Bengal", "East", 22.99, 87.85, 99,
       IND(gsdpGrowth=6.4, marketGrowth=68, creditOpportunity=70, depositOpportunity=74, customerPotential=78,
           digitalReadiness=66, marketConcentration=64, dataConfidence="MEDIUM"),
       [
           _d("Kolkata", 22.57, 88.36, 4.5, "tier1", [
               _t("Kolkata", 22.57, 88.36, 1100, "700001", "city"),
               _t("Park Street", 22.55, 88.35, 70, "700016", "locality"),
               _t("Ballygunge", 22.53, 88.36, 60, "700019", "locality"),
           ]),
           _d("North 24 Parganas", 22.62, 88.75, 10.0, "tier1", [
               _t("Salt Lake Sector V", 22.57, 88.43, 120, "700091", "locality"),
               _t("Barasat", 22.72, 88.48, 90, "700124", "town"),
               _t("Barrackpore", 22.76, 88.37, 80, "700120", "town"),
           ]),
           _d("Howrah", 22.59, 88.31, 1.0, "tier2", [
               _t("Howrah", 22.59, 88.31, 300, "711101", "city"),
           ]),
           _d("Hooghly", 22.90, 88.39, 0.8, "tier3", [
               _t("Serampore", 22.75, 88.34, 70, "712201", "town"),
               _t("Chandannagar", 22.87, 88.37, 60, "712136", "town"),
           ]),
           _d("South 24 Parganas", 22.29, 88.32, 8.1, "tier2", [
               _t("Behala", 22.50, 88.31, 100, "700034", "locality"),
               _t("Diamond Harbour", 22.19, 88.19, 40, "743331", "town"),
           ]),
           _d("Paschim Bardhaman", 23.24, 87.86, 1.1, "tier3", [
               _t("Asansol", 23.68, 86.98, 260, "713301", "city"),
               _t("Durgapur", 23.55, 87.29, 230, "713201", "city"),
           ]),
           _d("Murshidabad", 24.18, 88.28, 0.8, "tier3", [
               _t("Berhampore", 24.10, 88.26, 90, "742101", "town"),
           ]),
           _d("Nadia", 23.26, 88.54, 0.7, "tier3", [
               _t("Krishnanagar", 23.40, 88.49, 70, "741101", "town"),
           ]),
           _d("Darjeeling", 27.04, 88.26, 0.3, "tier3", [
               _t("Darjeeling", 27.04, 88.26, 40, "734101", "town"),
               _t("Siliguri (belt)", 26.71, 88.43, 220, "734001", "city"),
           ]),
           _d("Malda", 25.01, 88.14, 0.4, "tier3", [
               _t("Malda", 25.01, 88.14, 60, "732101", "town"),
           ]),
       ]),
    _s("Rajasthan", "North", 26.57, 73.85, 81,
       IND(gsdpGrowth=7.2, marketGrowth=72, creditOpportunity=74, depositOpportunity=70, customerPotential=76,
           digitalReadiness=64, marketConcentration=56, dataConfidence="MEDIUM"),
       [
           _d("Jaipur", 26.91, 75.79, 3.5, "tier1", [
               _t("Jaipur", 26.91, 75.79, 900, "302001", "city"),
               _t("Vaishali Nagar", 26.90, 75.74, 120, "302021", "locality"),
               _t("Malviya Nagar", 26.85, 75.81, 100, "302017", "locality"),
           ]),
           _d("Jodhpur", 26.29, 73.03, 1.4, "tier2", [
               _t("Jodhpur", 26.29, 73.03, 420, "342001", "city"),
           ]),
           _d("Udaipur", 24.59, 73.71, 0.7, "tier3", [
               _t("Udaipur", 24.59, 73.71, 230, "313001", "city"),
           ]),
           _d("Kota", 25.21, 75.86, 1.1, "tier2", [
               _t("Kota", 25.21, 75.86, 330, "324001", "city"),
           ]),
           _d("Bikaner", 28.02, 73.31, 0.8, "tier3", [
               _t("Bikaner", 28.02, 73.31, 240, "334001", "city"),
           ]),
           _d("Ajmer", 26.45, 74.64, 0.6, "tier3", [
               _t("Ajmer", 26.45, 74.64, 180, "305001", "city"),
           ]),
           _d("Alwar", 27.55, 76.63, 0.7, "tier3", [
               _t("Alwar", 27.55, 76.63, 160, "301001", "city"),
           ]),
           _d("Bharatpur", 27.22, 77.49, 0.5, "tier3", [
               _t("Bharatpur", 27.22, 77.49, 130, "321001", "city"),
           ]),
       ]),
    _s("Kerala", "South", 10.35, 76.46, 36,
       IND(gsdpGrowth=6.8, marketGrowth=64, creditOpportunity=68, depositOpportunity=80, customerPotential=70,
           digitalReadiness=84, marketConcentration=68, dataConfidence="MEDIUM"),
       [
           _d("Ernakulam", 10.00, 76.30, 3.3, "tier1", [
               _t("Kochi", 9.93, 76.27, 640, "682001", "city"),
               _t("Kaloor", 10.00, 76.29, 80, "682017", "locality"),
               _t("Kakkanad", 10.01, 76.31, 90, "682030", "locality"),
           ]),
           _d("Thiruvananthapuram", 8.52, 76.94, 1.7, "tier2", [
               _t("Thiruvananthapuram", 8.52, 76.94, 420, "695001", "city"),
           ]),
           _d("Kozhikode", 11.26, 75.78, 1.7, "tier2", [
               _t("Kozhikode", 11.26, 75.78, 380, "673001", "city"),
           ]),
           _d("Thrissur", 10.53, 76.21, 1.2, "tier2", [
               _t("Thrissur", 10.53, 76.21, 260, "680001", "city"),
           ]),
           _d("Kollam", 8.89, 76.61, 0.8, "tier3", [
               _t("Kollam", 8.89, 76.61, 180, "691001", "city"),
           ]),
           _d("Kannur", 11.87, 75.37, 0.6, "tier3", [
               _t("Kannur", 11.87, 75.37, 140, "670001", "city"),
           ]),
           _d("Alappuzha", 9.50, 76.34, 0.6, "tier3", [
               _t("Alappuzha", 9.50, 76.34, 130, "688001", "city"),
           ]),
           _d("Kottayam", 9.59, 76.52, 0.6, "tier3", [
               _t("Kottayam", 9.59, 76.52, 120, "686001", "city"),
           ]),
       ]),
    _s("Madhya Pradesh", "Central", 23.25, 77.50, 87,
       IND(gsdpGrowth=7.4, marketGrowth=73, creditOpportunity=71, depositOpportunity=68, customerPotential=80,
           digitalReadiness=60, marketConcentration=52, dataConfidence="MEDIUM"),
       [
           _d("Indore", 22.72, 75.86, 3.3, "tier1", [
               _t("Indore", 22.72, 75.86, 850, "452001", "city"),
               _t("Vijay Nagar", 22.76, 75.89, 110, "452010", "locality"),
               _t("Bhawarkuan", 22.74, 75.87, 80, "452001", "locality"),
           ]),
           _d("Bhopal", 23.26, 77.41, 2.4, "tier1", [
               _t("Bhopal", 23.26, 77.41, 680, "462001", "city"),
               _t("MP Nagar", 23.24, 77.43, 90, "462011", "locality"),
               _t("Arera Colony", 23.24, 77.42, 80, "462016", "locality"),
           ]),
           _d("Jabalpur", 23.18, 79.99, 1.4, "tier2", [
               _t("Jabalpur", 23.18, 79.99, 400, "482001", "city"),
           ]),
           _d("Gwalior", 26.22, 78.18, 1.3, "tier2", [
               _t("Gwalior", 26.22, 78.18, 370, "474001", "city"),
           ]),
           _d("Ujjain", 23.18, 75.79, 0.6, "tier3", [
               _t("Ujjain", 23.18, 75.79, 170, "456001", "city"),
           ]),
           _d("Sagar", 23.84, 78.74, 0.5, "tier3", [
               _t("Sagar", 23.84, 78.74, 130, "470001", "city"),
           ]),
           _d("Dewas", 22.96, 76.05, 0.4, "tier3", [
               _t("Dewas", 22.96, 76.05, 110, "455001", "city"),
           ]),
           _d("Ratlam", 23.33, 75.04, 0.4, "tier3", [
               _t("Ratlam", 23.33, 75.04, 100, "457001", "city"),
           ]),
           _d("Rewa", 24.53, 81.30, 0.4, "tier3", [
               _t("Rewa", 24.53, 81.30, 100, "486001", "city"),
           ]),
           _d("Satna", 24.58, 80.83, 0.4, "tier3", [
               _t("Satna", 24.58, 80.83, 95, "485001", "city"),
           ]),
       ]),
    _s("Andhra Pradesh", "South", 15.91, 79.74, 53,
       IND(gsdpGrowth=7.8, marketGrowth=75, creditOpportunity=76, depositOpportunity=72, customerPotential=78,
           digitalReadiness=68, marketConcentration=58, dataConfidence="MEDIUM"),
       [
           _d("Visakhapatnam", 17.69, 83.22, 2.0, "tier1", [
               _t("Visakhapatnam", 17.69, 83.22, 560, "530001", "city"),
               _t("Dwaraka Nagar", 17.71, 83.22, 80, "530016", "locality"),
               _t("Madhurawada", 17.82, 83.36, 70, "530041", "locality"),
           ]),
           _d("Krishna (Vijayawada)", 16.51, 80.65, 1.2, "tier1", [
               _t("Vijayawada", 16.51, 80.65, 420, "520001", "city"),
               _t("Benz Circle", 16.50, 80.67, 60, "520010", "locality"),
           ]),
           _d("Guntur", 16.31, 80.44, 0.9, "tier2", [
               _t("Guntur", 16.31, 80.44, 280, "522001", "city"),
           ]),
           _d("Tirupati", 13.63, 79.42, 0.6, "tier2", [
               _t("Tirupati", 13.63, 79.42, 210, "517501", "city"),
           ]),
           _d("Nellore", 14.44, 79.99, 0.6, "tier3", [
               _t("Nellore", 14.44, 79.99, 180, "524001", "city"),
           ]),
           _d("Kurnool", 15.83, 78.04, 0.6, "tier3", [
               _t("Kurnool", 15.83, 78.04, 170, "518001", "city"),
           ]),
           _d("Anantapur", 14.68, 77.60, 0.4, "tier3", [
               _t("Anantapur", 14.68, 77.60, 130, "515001", "city"),
           ]),
       ]),
    _s("Bihar", "East", 25.68, 85.51, 125,
       IND(gsdpGrowth=7.0, marketGrowth=66, creditOpportunity=62, depositOpportunity=64, customerPotential=84,
           digitalReadiness=54, marketConcentration=46, dataConfidence="MEDIUM"),
       [
           _d("Patna", 25.59, 85.14, 2.5, "tier1", [
               _t("Patna", 25.59, 85.14, 640, "800001", "city"),
               _t("Boring Road", 25.61, 85.11, 90, "800013", "locality"),
               _t("Kankarbagh", 25.59, 85.16, 110, "800020", "locality"),
           ]),
           _d("Gaya", 24.79, 85.00, 0.6, "tier3", [
               _t("Gaya", 24.79, 85.00, 190, "823001", "city"),
           ]),
           _d("Bhagalpur", 25.25, 86.98, 0.5, "tier3", [
               _t("Bhagalpur", 25.25, 86.98, 160, "812001", "city"),
           ]),
           _d("Muzaffarpur", 26.12, 85.39, 0.5, "tier3", [
               _t("Muzaffarpur", 26.12, 85.39, 160, "842001", "city"),
           ]),
           _d("Darbhanga", 26.15, 85.90, 0.4, "tier3", [
               _t("Darbhanga", 26.15, 85.90, 130, "846004", "city"),
           ]),
           _d("Purnia", 25.78, 87.47, 0.4, "tier3", [
               _t("Purnia", 25.78, 87.47, 120, "854301", "city"),
           ]),
           _d("Arrah (Bhojpur)", 25.56, 84.66, 0.3, "tier3", [
               _t("Arrah", 25.56, 84.66, 90, "802301", "town"),
           ]),
           _d("Begusarai", 25.42, 86.13, 0.3, "tier3", [
               _t("Begusarai", 25.42, 86.13, 85, "851101", "town"),
           ]),
       ]),
    _s("Haryana", "North", 29.06, 76.36, 30,
       IND(gsdpGrowth=8.2, marketGrowth=79, creditOpportunity=82, depositOpportunity=78, customerPotential=76,
           digitalReadiness=78, marketConcentration=66, dataConfidence="HIGH"),
       [
           _d("Gurugram", 28.46, 77.03, 1.5, "tier1", [
               _t("Gurugram", 28.46, 77.03, 380, "122001", "city"),
               _t("Cyber City", 28.49, 77.09, 70, "122002", "locality"),
               _t("Sector 56", 28.42, 77.11, 60, "122011", "locality"),
           ]),
           _d("Faridabad", 28.41, 77.31, 1.6, "tier1", [
               _t("Faridabad", 28.41, 77.31, 420, "121001", "city"),
               _t("Neharpar", 28.40, 77.34, 60, "121002", "locality"),
           ]),
           _d("Karnal", 29.69, 76.99, 0.5, "tier3", [
               _t("Karnal", 29.69, 76.99, 140, "132001", "city"),
           ]),
           _d("Panipat", 29.39, 76.96, 0.5, "tier3", [
               _t("Panipat", 29.39, 76.96, 140, "132103", "city"),
           ]),
           _d("Hisar", 29.15, 75.72, 0.5, "tier3", [
               _t("Hisar", 29.15, 75.72, 130, "125001", "city"),
           ]),
           _d("Sonipat", 28.99, 77.02, 0.5, "tier3", [
               _t("Sonipat", 28.99, 77.02, 130, "131001", "city"),
           ]),
           _d("Ambala", 30.38, 76.78, 0.4, "tier3", [
               _t("Ambala", 30.38, 76.78, 110, "134003", "city"),
           ]),
       ]),
    _s("Punjab", "North", 31.15, 75.57, 31,
       IND(gsdpGrowth=6.9, marketGrowth=67, creditOpportunity=70, depositOpportunity=72, customerPotential=72,
           digitalReadiness=66, marketConcentration=54, dataConfidence="MEDIUM"),
       [
           _d("Ludhiana", 30.90, 75.85, 1.8, "tier1", [
               _t("Ludhiana", 30.90, 75.85, 480, "141001", "city"),
               _t("Ferozepur Road", 30.88, 75.83, 80, "141001", "locality"),
           ]),
           _d("Amritsar", 31.63, 74.87, 1.3, "tier2", [
               _t("Amritsar", 31.63, 74.87, 340, "143001", "city"),
           ]),
           _d("Jalandhar", 31.33, 75.58, 0.9, "tier2", [
               _t("Jalandhar", 31.33, 75.58, 240, "144001", "city"),
           ]),
           _d("Patiala", 30.34, 76.39, 0.6, "tier3", [
               _t("Patiala", 30.34, 76.39, 170, "147001", "city"),
           ]),
           _d("SAS Nagar (Mohali)", 30.70, 76.72, 0.7, "tier2", [
               _t("Mohali", 30.70, 76.72, 190, "160055", "city"),
               _t("Phase 5", 30.69, 76.72, 50, "160059", "locality"),
           ]),
           _d("Bathinda", 30.21, 74.95, 0.5, "tier3", [
               _t("Bathinda", 30.21, 74.95, 140, "151001", "city"),
           ]),
           _d("Hoshiarpur", 31.53, 75.91, 0.3, "tier3", [
               _t("Hoshiarpur", 31.53, 75.91, 90, "146001", "town"),
           ]),
       ]),
    _s("Odisha", "East", 20.28, 84.72, 47,
       IND(gsdpGrowth=7.5, marketGrowth=70, creditOpportunity=68, depositOpportunity=66, customerPotential=74,
           digitalReadiness=60, marketConcentration=50, dataConfidence="MEDIUM"),
       [
           _d("Khordha", 20.30, 85.82, 1.3, "tier2", [
               _t("Bhubaneswar", 20.30, 85.82, 400, "751001", "city"),
               _t("Jaydev Vihar", 20.30, 85.82, 60, "751013", "locality"),
               _t("Chandaka", 20.34, 85.79, 50, "751024", "locality"),
           ]),
           _d("Cuttack", 20.46, 85.88, 0.7, "tier2", [
               _t("Cuttack", 20.46, 85.88, 220, "753001", "city"),
           ]),
           _d("Sundargarh", 22.22, 84.86, 0.6, "tier3", [
               _t("Rourkela", 22.22, 84.86, 170, "769001", "city"),
           ]),
           _d("Sambalpur", 21.47, 83.97, 0.5, "tier3", [
               _t("Sambalpur", 21.47, 83.97, 130, "768001", "city"),
           ]),
           _d("Puri", 19.81, 85.83, 0.3, "tier3", [
               _t("Puri", 19.81, 85.83, 70, "752001", "town"),
           ]),
           _d("Balasore", 21.49, 86.94, 0.4, "tier3", [
               _t("Balasore", 21.49, 86.94, 100, "756001", "city"),
           ]),
       ]),
    _s("Assam", "East", 26.20, 92.94, 36,
       IND(gsdpGrowth=7.1, marketGrowth=65, creditOpportunity=62, depositOpportunity=66, customerPotential=70,
           digitalReadiness=56, marketConcentration=48, dataConfidence="LIMITED"),
       [
           _d("Kamrup Metropolitan", 26.14, 91.74, 1.1, "tier2", [
               _t("Guwahati", 26.14, 91.74, 320, "781001", "city"),
               _t("Paltan Bazar", 26.18, 91.75, 70, "781008", "locality"),
               _t("Maligaon", 26.18, 91.68, 60, "781012", "locality"),
           ]),
           _d("Cachar", 24.82, 92.80, 0.5, "tier3", [
               _t("Silchar", 24.82, 92.80, 130, "788001", "city"),
           ]),
           _d("Dibrugarh", 27.47, 94.91, 0.4, "tier3", [
               _t("Dibrugarh", 27.47, 94.91, 110, "786001", "city"),
           ]),
           _d("Jorhat", 26.75, 94.22, 0.3, "tier3", [
               _t("Jorhat", 26.75, 94.22, 90, "785001", "town"),
           ]),
           _d("Sonitpur", 26.64, 92.80, 0.3, "tier3", [
               _t("Tezpur", 26.64, 92.80, 70, "784001", "town"),
           ]),
       ]),
    _s("Jharkhand", "East", 23.61, 85.28, 40,
       IND(gsdpGrowth=7.3, marketGrowth=66, creditOpportunity=64, depositOpportunity=64, customerPotential=74,
           digitalReadiness=56, marketConcentration=48, dataConfidence="LIMITED"),
       [
           _d("Ranchi", 23.34, 85.31, 1.2, "tier2", [
               _t("Ranchi", 23.34, 85.31, 380, "834001", "city"),
               _t("Lalpur", 23.35, 85.32, 60, "834001", "locality"),
               _t("Harmu", 23.36, 85.34, 40, "834002", "locality"),
           ]),
           _d("Dhanbad", 23.80, 86.44, 1.1, "tier2", [
               _t("Dhanbad", 23.80, 86.44, 320, "826001", "city"),
           ]),
           _d("East Singhbhum", 22.80, 86.20, 1.0, "tier2", [
               _t("Jamshedpur", 22.80, 86.20, 300, "831001", "city"),
               _t("Bistupur", 22.79, 86.20, 50, "831001", "locality"),
           ]),
           _d("Bokaro", 23.67, 86.15, 0.6, "tier3", [
               _t("Bokaro Steel City", 23.67, 86.15, 160, "827004", "town"),
           ]),
           _d("Deoghar", 24.48, 86.70, 0.3, "tier3", [
               _t("Deoghar", 24.48, 86.70, 70, "814112", "town"),
           ]),
           _d("Hazaribagh", 23.99, 85.36, 0.3, "tier3", [
               _t("Hazaribagh", 23.99, 85.36, 80, "825301", "town"),
           ]),
       ]),
    _s("Chhattisgarh", "Central", 21.25, 81.63, 30,
       IND(gsdpGrowth=7.7, marketGrowth=68, creditOpportunity=66, depositOpportunity=64, customerPotential=72,
           digitalReadiness=56, marketConcentration=46, dataConfidence="LIMITED"),
       [
           _d("Raipur", 21.25, 81.63, 1.2, "tier2", [
               _t("Raipur", 21.25, 81.63, 340, "492001", "city"),
               _t("Shankar Nagar", 21.25, 81.61, 60, "492001", "locality"),
           ]),
           _d("Durg", 21.19, 81.35, 1.0, "tier2", [
               _t("Bhilai", 21.19, 81.35, 280, "490001", "city"),
           ]),
           _d("Bilaspur", 22.08, 82.15, 0.5, "tier3", [
               _t("Bilaspur", 22.08, 82.15, 140, "495001", "city"),
           ]),
           _d("Korba", 22.35, 82.68, 0.4, "tier3", [
               _t("Korba", 22.35, 82.68, 120, "495677", "town"),
           ]),
           _d("Raigarh", 21.90, 83.40, 0.3, "tier3", [
               _t("Raigarh", 21.90, 83.40, 90, "496001", "town"),
           ]),
       ]),
    _s("Uttarakhand", "North", 30.07, 78.44, 12,
       IND(gsdpGrowth=7.9, marketGrowth=70, creditOpportunity=70, depositOpportunity=70, customerPotential=68,
           digitalReadiness=66, marketConcentration=52, dataConfidence="LIMITED"),
       [
           _d("Dehradun", 30.32, 78.03, 0.8, "tier2", [
               _t("Dehradun", 30.32, 78.03, 260, "248001", "city"),
               _t("Rajpur Road", 30.34, 78.05, 40, "248001", "locality"),
           ]),
           _d("Haridwar", 29.95, 78.16, 0.7, "tier2", [
               _t("Haridwar", 29.95, 78.16, 160, "249401", "city"),
               _t("Jwalapur", 29.94, 78.15, 50, "249401", "town"),
           ]),
           _d("Udham Singh Nagar", 28.97, 79.40, 0.5, "tier3", [
               _t("Rudrapur", 28.98, 79.40, 80, "263153", "town"),
           ]),
           _d("Nainital", 29.38, 79.45, 0.4, "tier3", [
               _t("Haldwani", 29.22, 79.51, 80, "263139", "town"),
           ]),
           _d("Almora", 29.60, 79.65, 0.1, "tier3", [
               _t("Almora", 29.60, 79.65, 30, "263601", "town"),
           ]),
       ]),
    _s("Himachal Pradesh", "North", 31.77, 77.34, 7.5,
       IND(gsdpGrowth=7.4, marketGrowth=63, creditOpportunity=62, depositOpportunity=66, customerPotential=60,
           digitalReadiness=64, marketConcentration=48, dataConfidence="LIMITED"),
       [
           _d("Shimla", 31.10, 77.17, 0.2, "tier3", [
               _t("Shimla", 31.10, 77.17, 90, "171001", "town"),
           ]),
           _d("Kangra", 32.22, 76.32, 0.2, "tier3", [
               _t("Dharamshala", 32.22, 76.32, 40, "176215", "town"),
           ]),
           _d("Mandi", 31.71, 76.93, 0.1, "tier3", [
               _t("Mandi", 31.71, 76.93, 30, "175001", "town"),
           ]),
           _d("Solan", 30.91, 77.10, 0.1, "tier3", [
               _t("Solan", 30.91, 77.10, 30, "173212", "town"),
           ]),
       ]),
    _s("Jammu & Kashmir", "North", 33.45, 76.24, 14,
       IND(gsdpGrowth=6.6, marketGrowth=60, creditOpportunity=58, depositOpportunity=62, customerPotential=64,
           digitalReadiness=54, marketConcentration=44, dataConfidence="LIMITED"),
       [
           _d("Srinagar", 34.08, 74.80, 1.2, "tier2", [
               _t("Srinagar", 34.08, 74.80, 300, "190001", "city"),
           ]),
           _d("Jammu", 32.73, 74.86, 0.9, "tier2", [
               _t("Jammu", 32.73, 74.86, 260, "180001", "city"),
               _t("Gandhi Nagar", 32.70, 74.87, 50, "180004", "locality"),
           ]),
           _d("Anantnag", 33.73, 75.15, 0.3, "tier3", [
               _t("Anantnag", 33.73, 75.15, 70, "192101", "town"),
           ]),
           _d("Baramulla", 34.20, 74.34, 0.2, "tier3", [
               _t("Baramulla", 34.20, 74.34, 50, "193101", "town"),
           ]),
       ]),
    _s("Tripura", "East", 23.83, 91.28, 4.1,
       IND(gsdpGrowth=6.5, marketGrowth=58, creditOpportunity=56, depositOpportunity=60, customerPotential=60,
           digitalReadiness=52, marketConcentration=42, dataConfidence="LIMITED"),
       [
           _d("West Tripura", 23.83, 91.28, 0.5, "tier3", [
               _t("Agartala", 23.83, 91.28, 140, "799001", "city"),
           ]),
           _d("Gomati", 23.53, 91.48, 0.1, "tier3", [
               _t("Udaipur (Tripura)", 23.53, 91.48, 25, "799120", "town"),
           ]),
           _d("North Tripura", 24.37, 92.17, 0.1, "tier3", [
               _t("Dharmanagar", 24.37, 92.17, 25, "799250", "town"),
           ]),
       ]),
    _s("Puducherry", "South", 11.94, 79.83, 1.6,
       IND(gsdpGrowth=7.2, marketGrowth=68, creditOpportunity=70, depositOpportunity=68, customerPotential=66,
           digitalReadiness=72, marketConcentration=54, dataConfidence="LIMITED"),
       [
           _d("Puducherry", 11.94, 79.83, 0.7, "tier3", [
               _t("Puducherry", 11.94, 79.83, 240, "605001", "city"),
               _t("White Town", 11.93, 79.83, 30, "605001", "locality"),
           ]),
           _d("Karaikal", 10.92, 79.83, 0.1, "tier3", [
               _t("Karaikal", 10.92, 79.83, 30, "609602", "town"),
           ]),
       ]),
]


def iter_districts():
    """Yield (state, district_dict) pairs."""
    for s in STATES:
        for d in s["districts"]:
            yield s, d


def iter_towns():
    """Yield (state, district, town_dict) triples."""
    for s, d in iter_districts():
        for t in d["towns"]:
            yield s, d, t
