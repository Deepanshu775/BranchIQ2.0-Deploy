"""Deterministic DEMO branch-performance panel — the training substrate for the XGBoost layer.

Not official data. Each row carries sourceType="demo-training" and a disclaimer, per PRD §34.
The panel is generated from the already-seeded network so the signal the model learns is the
same signal BranchIQ measures (market growth, credit/deposit growth, whitespace, competition).
"""

import hashlib
import random
from datetime import datetime, timezone

from lib.db import db
from lib.geo import GeoIndex

FISCAL_YEARS = ["FY2021-22", "FY2022-23", "FY2023-24", "FY2024-25"]
SOURCE_LABEL = "BranchIQ synthetic training panel"
DISCLAIMER = ("DEMO / TRAINING DATA — deterministic synthetic branch performance generated from "
              "the demo network. Not official bank or RBI data. Replace via the CSV ingestion path.")


def _rng(*parts: str) -> random.Random:
    return random.Random(int(hashlib.md5("|".join(parts).encode()).hexdigest()[:12], 16))


async def generate_panel(replace: bool = True) -> dict:
    """Write a multi-year performance panel for every demo branch. Returns a summary."""
    branches = await db.branches.find({}, {"_id": 0}).to_list(100000)
    metrics = await db.market_metrics.find({}, {"_id": 0}).to_list(100000)
    cities = await db.cities.find({}, {"_id": 0}).to_list(100000)
    metric_by_ref = {m["refId"]: m for m in metrics}
    city_by_id = {c["id"]: c for c in cities}

    # Geospatial context per district: own-bank and competitor networks
    by_district: dict[str, list[dict]] = {}
    for b in branches:
        by_district.setdefault(b["districtId"], []).append(b)

    docs: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()
    for did, group in by_district.items():
        d_metric = metric_by_ref.get(did, {})
        indexes: dict[str, tuple[GeoIndex, GeoIndex]] = {}
        for bank_id in {b["bankId"] for b in group}:
            indexes[bank_id] = (GeoIndex([b for b in group if b["bankId"] == bank_id]),
                                GeoIndex([b for b in group if b["bankId"] != bank_id]))
        for b in group:
            own_index, comp_index = indexes[b["bankId"]]
            m = metric_by_ref.get(b.get("cityId"), d_metric)
            city = city_by_id.get(b.get("cityId", ""), {})
            own_near = [d for _, d in own_index.query(b["lat"], b["lng"], 5) if d > 0.01]
            comp_near = [d for _, d in comp_index.query(b["lat"], b["lng"], 5)]
            r = _rng("perf", b["id"])

            pop = max(city.get("populationK", 50) * 1000, 5000)
            # Scale: deposits grow with catchment and urbanization, split across nearby branches
            competition = 1 + len(own_near) * 0.55 + len(comp_near) * 0.12
            base_deposits = pop / 1000 * (0.9 + m.get("urbanization", 50) / 110) / competition
            base_deposits = max(18.0, round(base_deposits * r.uniform(0.75, 1.3), 1))
            base_advances = round(base_deposits * (m.get("cdRatio", 70) / 100) * r.uniform(0.8, 1.2), 1)

            dep_growth = (m.get("depositGrowthPct", 10) + (0.9 if not own_near else -0.8)
                          + (m.get("marketGrowth", 60) - 60) / 14 + r.uniform(-2.2, 2.2)) / 100
            cre_growth = (m.get("creditGrowthPct", 10) + (m.get("digitalReadiness", 60) - 60) / 18
                          - len(own_near) * 0.5 + r.uniform(-2.4, 2.4)) / 100

            for i, fy in enumerate(FISCAL_YEARS):
                dep = round(base_deposits * (1 + dep_growth) ** i, 1)
                adv = round(base_advances * (1 + cre_growth) ** i, 1)
                docs.append({
                    "id": f"perf-{b['id']}-{fy}",
                    "branchId": b["id"], "bankId": b["bankId"], "bankShort": b["bankShort"],
                    "stateId": b["stateId"], "districtId": b["districtId"], "cityId": b.get("cityId"),
                    "fiscalYear": fy,
                    "depositsCr": dep, "advancesCr": adv,
                    "businessCr": round(dep + adv, 1),
                    "accounts": int(dep * 1000 * r.uniform(0.8, 1.2)),
                    "sourceType": "demo-training", "sourceName": SOURCE_LABEL,
                    "sourceUrl": None, "disclaimer": DISCLAIMER, "ingestedAt": now,
                })

    if replace:
        await db.branch_performance.delete_many({"sourceType": "demo-training"})
    if docs:
        await db.branch_performance.insert_many(docs)
    return {"rows": len(docs), "branches": len(branches), "fiscalYears": FISCAL_YEARS,
            "sourceType": "demo-training", "disclaimer": DISCLAIMER}


async def panel_summary() -> dict:
    """Training-data inventory: row counts per source type and fiscal year coverage."""
    rows = await db.branch_performance.find({}, {"_id": 0, "fiscalYear": 1, "sourceType": 1,
                                                 "branchId": 1}).to_list(500000)
    by_source: dict[str, int] = {}
    years: set[str] = set()
    branch_ids: set[str] = set()
    for r in rows:
        by_source[r.get("sourceType", "unknown")] = by_source.get(r.get("sourceType", "unknown"), 0) + 1
        years.add(r.get("fiscalYear", ""))
        branch_ids.add(r.get("branchId", ""))
    return {
        "rows": len(rows),
        "branches": len(branch_ids),
        "fiscalYears": sorted(y for y in years if y),
        "rowsBySourceType": by_source,
        "hasOfficialData": by_source.get("official", 0) > 0,
        "disclaimer": DISCLAIMER if by_source.get("demo-training") else None,
    }
