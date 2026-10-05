"""BranchIQ seed — builds the full demo dataset from the curated base layers.

Run: cd /app/backend && python seed.py

PROVENANCE (labels stored on every doc where relevant):
- States/districts/towns + populations + coordinates: public geography (Census/OpenStreetMap), approximate.
- PIN codes: correct state prefixes; individual codes marked approximate/demo — never claimed official.
- Branch placement, PIN-locality economics, candidate sites: DETERMINISTIC SYNTHETIC DEMO data
  (seeded by stable hashes so rankings are reproducible). Clearly labelled sourceType="demo".

Idempotent: drops and rebuilds the demo collections, then re-applies indexes.
"""

import hashlib
import math
import random
from datetime import datetime, timezone

from data.banks_base import BANKS_BASE
from data.geo_data import STATES
from data.sources_registry import SOURCES_REGISTRY
from lib.db import db, ensure_indexes

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

COLLECTIONS = ["banks", "states", "districts", "cities", "pincodes", "branches",
               "market_metrics", "location_candidates", "data_sources",
               "opportunity_scores", "model_predictions"]

BRANCH_SUFFIXES = ["Main Road", "Market", "Station Road", "Bazaar", "Chowk",
                   "Industrial Area", "Extension", "Ring Road", "Court Road", "Bus Stand"]

# (site type, accessibility 0-1, business rate, catchment factor)
SITE_TYPES = [
    ("High Street / Market Centre", 0.88, 0.012, 1.00),
    ("Transport Transit Hub", 0.93, 0.009, 0.90),
    ("Residential Cluster", 0.70, 0.004, 1.15),
    ("Commercial Business Zone", 0.85, 0.014, 1.20),
    ("Tech / Industrial Park", 0.78, 0.006, 1.30),
    ("Semi-Urban Growth Block", 0.58, 0.003, 0.80),
]


def slug(s: str) -> str:
    return (s.strip().lower().replace("&", " and ").replace("/", " ")
            .replace("(", "").replace(")", "").replace(".", "").strip()
            .replace(" ", "-"))


def rng_for(*parts: str) -> random.Random:
    digest = hashlib.md5("|".join(parts).encode()).hexdigest()
    return random.Random(int(digest, 16))


def offset(lat: float, lng: float, dist_km: float, angle: float) -> tuple[float, float]:
    dlat = dist_km * math.cos(angle) / 111.0
    dlng = dist_km * math.sin(angle) / (111.0 * max(math.cos(math.radians(lat)), 0.3))
    return round(lat + dlat, 6), round(lng + dlng, 6)


def _km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Local haversine so seeding has no import cycle with the request path."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(a))


def expected_branches(bank: dict, district: dict, state_name: str) -> int:
    tier_factor = {"tier1": 2.4, "tier2": 1.3, "tier3": 0.55}[district["tier"]]
    base = 1.2 + district["population_mn"] * 0.9
    private, urban_ok = bank["sector"] == "Private", state_name in {
        "Maharashtra", "Delhi NCR", "Karnataka", "Telangana", "Goa", "Kerala", "Puducherry", "Haryana"}
    rural = state_name in {"Uttar Pradesh", "West Bengal", "Madhya Pradesh", "Rajasthan", "Bihar",
                           "Jharkhand", "Chhattisgarh", "Odisha", "Assam", "Uttarakhand",
                           "Himachal Pradesh", "Jammu & Kashmir", "Tripura"}
    bias = 1.2 if (private and urban_ok) or (not private and rural) else (0.8 if private else 1.0)
    return max(0, round(base * tier_factor * bank["footprint_weight"] * bias))


async def main() -> None:
    for c in COLLECTIONS:
        try:
            await db.drop_collection(c)
        except Exception:
            pass
    await ensure_indexes()

    banks_docs = []
    for b in BANKS_BASE:
        banks_docs.append({
            "id": slug(b["short"]), "short": b["short"], "name": b["name"], "sector": b["sector"],
            "reportingPeriod": b["reportingPeriod"], "branches": b["branches"], "deposits": b["deposits"],
            "advances": b["advances"], "depositGrowth": b["depositGrowth"], "creditGrowth": b["creditGrowth"],
            "digitalReadiness": b["digitalReadiness"], "geographicCoverage": b["geographicCoverage"],
            "footprintWeight": b["footprint_weight"], "source": b["source"], "sourceUrl": b["sourceUrl"],
            "sourceType": "official",
        })
    await db.banks.insert_many(banks_docs)

    states_docs, districts_docs, cities_docs, pincodes_docs = [], [], [], []
    branches_docs, metrics_docs, candidates_docs = [], [], []

    for s in STATES:
        sid = slug(s["name"])
        states_docs.append({"id": sid, "name": s["name"], "region": s["region"], "lat": s["lat"],
                            "lng": s["lng"], "populationMn": s["population_mn"],
                            "indicators": s["indicators"]})

        for d in s["districts"]:
            did = f"{sid}::{slug(d['name'])}"
            districts_docs.append({"id": did, "stateId": sid, "state": s["name"], "name": d["name"],
                                   "lat": d["lat"], "lng": d["lng"], "populationMn": d["population_mn"],
                                   "tier": d["tier"]})

            towns = d["towns"]
            weights = [max(t["population_k"], 1) for t in towns]
            ind = s["indicators"]
            rb = rng_for("mm", did)
            urbanization = round({"tier1": rb.uniform(88, 96), "tier2": rb.uniform(45, 72),
                                  "tier3": rb.uniform(22, 42)}[d["tier"]], 1)
            credit_growth = round(6 + ind["creditOpportunity"] / 10 + rb.uniform(-1, 1.5), 1)
            deposit_growth = round(6 + ind["depositOpportunity"] / 10 + rb.uniform(-1, 1.5), 1)
            deposit_vol = round(d["population_mn"] * 1e6 * (55000 * ind["depositOpportunity"] / 75) / 1e7)
            credit_vol = round(d["population_mn"] * 1e6 * (48000 * ind["creditOpportunity"] / 75) / 1e7)
            business_count = round(d["population_mn"] * 1800 * (0.4 + urbanization / 100))
            metrics_docs.append({
                "scope": "district", "refId": did, "stateId": sid, "districtId": did,
                "population": round(d["population_mn"] * 1e6),
                "populationGrowth": round(0.9 + (ind["marketGrowth"] - 60) / 18 + rb.uniform(-0.3, 0.4), 2),
                "urbanization": urbanization,
                "creditGrowthPct": credit_growth, "depositGrowthPct": deposit_growth,
                "depositVolumeCr": deposit_vol, "creditVolumeCr": credit_vol,
                "cdRatio": round(credit_vol / max(deposit_vol, 1) * 100, 1),
                "businessCount": business_count,
                "competitorDensity": round(rb.uniform(30, 80), 1),
                "digitalReadiness": round(min(99, ind["digitalReadiness"] + rb.uniform(-4, 4))),
                "customerPotential": round(min(99, ind["customerPotential"] + rb.uniform(-3, 3))),
                "marketGrowth": round(min(99, ind["marketGrowth"] + rb.uniform(-4, 3))),
                "dataLabels": {"population": "PUBLIC MARKET DATA", "urbanization": "PUBLIC MARKET DATA",
                               "creditGrowthPct": "MODEL ESTIMATE", "depositGrowthPct": "MODEL ESTIMATE",
                               "depositVolumeCr": "MODEL ESTIMATE", "creditVolumeCr": "MODEL ESTIMATE",
                               "businessCount": "MODEL ESTIMATE"},
            })

            for t in towns:
                cid = f"{did}::{slug(t['name'])}::{t['pin']}"
                cities_docs.append({"id": cid, "stateId": sid, "districtId": did, "name": t["name"],
                                    "lat": t["lat"], "lng": t["lng"], "populationK": t["population_k"],
                                    "pin": t["pin"], "kind": t["kind"], "tier": d["tier"]})
                pincodes_docs.append({
                    "id": f"pin-{t['pin']}-{slug(t['name'])}", "pin": t["pin"], "cityId": cid,
                    "districtId": did, "stateId": sid, "localityName": f"{t['name']} (core)",
                    "lat": t["lat"], "lng": t["lng"], "catchmentPopK": t["population_k"],
                    "pinSource": "approximate"})
                if t["population_k"] >= 150:
                    rp = rng_for("pin", cid)
                    for i in range(1, rp.randrange(2, 4)):
                        plat, plng = offset(t["lat"], t["lng"], rp.uniform(0.6, 2.2), rp.uniform(0, 2 * math.pi))
                        pincodes_docs.append({
                            "id": f"pin-{t['pin']}-{slug(t['name'])}-{i}", "pin": str(int(t["pin"]) + i),
                            "cityId": cid, "districtId": did, "stateId": sid,
                            "localityName": f"{t['name']} Area {i}", "lat": plat, "lng": plng,
                            "catchmentPopK": round(t["population_k"] * rp.uniform(0.15, 0.35), 1),
                            "pinSource": "demo"})

                rc = rng_for("cmm", cid)
                vol_dep = round(t["population_k"] * 1000 * (55000 * ind["depositOpportunity"] / 75) / 1e7
                                * rc.uniform(0.9, 1.3))
                vol_cre = round(t["population_k"] * 1000 * (48000 * ind["creditOpportunity"] / 75) / 1e7
                                * rc.uniform(0.9, 1.3))
                town_share = t["population_k"] * 1000 / max(d["population_mn"] * 1e6, 1)
                metrics_docs.append({
                    "scope": "city", "refId": cid, "stateId": sid, "districtId": did, "cityId": cid,
                    "population": round(t["population_k"] * 1000),
                    "urbanization": round(min(98, urbanization + 12), 1),
                    "creditGrowthPct": round(credit_growth + rc.uniform(-1.5, 1.5), 1),
                    "depositGrowthPct": round(deposit_growth + rc.uniform(-1.5, 1.5), 1),
                    "depositVolumeCr": vol_dep, "creditVolumeCr": vol_cre,
                    "cdRatio": round(vol_cre / max(vol_dep, 1) * 100, 1),
                    "businessCount": round(max(business_count * town_share * 1.2, 8)),
                    "competitorDensity": round(rc.uniform(25, 80), 1),
                    "digitalReadiness": round(min(99, ind["digitalReadiness"] + rc.uniform(-3, 4))),
                    "customerPotential": round(min(99, ind["customerPotential"] + rc.uniform(-2, 3))),
                    "marketGrowth": round(min(99, ind["marketGrowth"] + rc.uniform(-3, 3))),
                })

                # Candidate branch locations (demo, deterministic)
                r3 = rng_for("cand", cid)
                n = 2 + (1 if t["population_k"] >= 300 else 0) + (1 if t["population_k"] >= 800 else 0)
                start = r3.randrange(len(SITE_TYPES))
                # A 5 km service area captures only part of a large city, so damp the share as the
                # settlement grows — otherwise the headline catchment reads as the whole city.
                pop_abs = t["population_k"] * 1000
                catch_share = 1.0 if pop_abs <= 120_000 else max(0.18, (120_000 / pop_abs) ** 0.45)
                for i in range(n):
                    st_name, access, biz_rate, factor = SITE_TYPES[(start + i) % len(SITE_TYPES)]
                    angle = r3.uniform(0, 2 * math.pi)
                    dist = r3.uniform(0.4, 2.4)
                    lat, lng = offset(t["lat"], t["lng"], dist, angle)
                    catch = int(max(4000, pop_abs * catch_share * factor * r3.uniform(0.85, 1.15)))
                    candidates_docs.append({
                        "id": f"{cid}::cand-{i + 1}", "cityId": cid, "districtId": did, "stateId": sid,
                        "name": f"{t['name']} — {st_name}", "siteType": st_name, "lat": lat, "lng": lng,
                        "pincode": t["pin"], "catchmentPop": catch,
                        "businessCount": round(catch * biz_rate * r3.uniform(0.85, 1.15)),
                        "accessibility": access,
                        "operatingCostIndex": round((0.3 + access * 0.45) * (1.15 if d["tier"] == "tier1" else 1.0), 2),
                        "catchmentRadiusKm": 5, "sourceType": "demo",
                    })

            # Demo branches per bank, placed across the district's towns
            tier_factor = {"tier1": 2.4, "tier2": 1.3, "tier3": 0.55}[d["tier"]]
            for bank in BANKS_BASE:
                bank_id = slug(bank["short"])
                count = expected_branches(bank, d, s["name"])
                r = rng_for("branches", did, bank["short"])
                picks = r.choices(range(len(towns)), weights=weights, k=count)
                placed: list[tuple[float, float]] = []  # same-bank sites, to avoid demo duplicates
                for i, ti in enumerate(picks):
                    t = towns[ti]
                    lat = lng = None
                    for _attempt in range(12):
                        angle = r.uniform(0, 2 * math.pi)
                        dist = r.uniform(0.3, 2.6)
                        cand_lat, cand_lng = offset(t["lat"], t["lng"], dist, angle)
                        if all(_km(cand_lat, cand_lng, pl, pg) >= 0.45 for pl, pg in placed):
                            lat, lng = cand_lat, cand_lng
                            break
                    if lat is None:
                        continue  # town is saturated for this bank — skip rather than stack duplicates
                    placed.append((lat, lng))
                    branch_type = ("urban" if dist < 1.0 and t["kind"] == "city"
                                   else "semi-urban" if t["kind"] in ("town", "locality") else "rural")
                    branches_docs.append({
                        "id": f"br-{hashlib.md5(f'{did}:{bank_id}:{i}'.encode()).hexdigest()[:12]}",
                        "bankId": bank_id, "bankShort": bank["short"], "bankName": bank["name"],
                        "name": f"{bank['short']} {t['name']} {r.choice(BRANCH_SUFFIXES)} Branch",
                        "code": f"{bank['short'][:2].upper()}-{r.randrange(10000, 99999)}",
                        "stateId": sid, "districtId": did,
                        "cityId": f"{did}::{slug(t['name'])}::{t['pin']}", "city": t["name"],
                        "pincode": t["pin"], "lat": lat, "lng": lng, "branchType": branch_type,
                        "openingDate": f"{r.randrange(1985, 2024)}-{r.randrange(1, 13):02d}-{r.randrange(1, 29):02d}",
                        "sourceType": "demo", "status": "operational", "lastVerified": TODAY,
                    })

    await db.data_sources.insert_many([
        {"sourceId": src["source_id"], "sourceName": src["source_name"], "organization": src["organization"],
         "dataset": src["dataset"], "period": src["period"], "url": src["url"], "dataType": src["data_type"],
         "confidence": src["confidence"], "usedFor": src["used_for"]}
        for src in SOURCES_REGISTRY])

    for name, docs in [("states", states_docs), ("districts", districts_docs), ("cities", cities_docs),
                       ("pincodes", pincodes_docs), ("branches", branches_docs),
                       ("market_metrics", metrics_docs), ("location_candidates", candidates_docs)]:
        if docs:
            await db[name].insert_many(docs)

    print(f"DEMO seed complete (deterministic, labelled sourceType='demo'): "
          f"{len(states_docs)} states, {len(districts_docs)} districts, {len(cities_docs)} cities, "
          f"{len(pincodes_docs)} PIN areas, {len(branches_docs)} demo branches, "
          f"{len(candidates_docs)} candidate locations, {len(metrics_docs)} market metrics.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
