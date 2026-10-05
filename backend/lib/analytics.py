"""BranchIQ analytics service layer — all heavy computation lives here, never in the browser.

Document fields are camelCase (as written by seed.py) so they mirror the TS interfaces 1:1.
Caching: ranked results are memoised in-process for CACHE_TTL seconds (performance §30).
"""

import time
from collections import Counter
from datetime import datetime, timezone

from data.sources_registry import DEMO_DISCLAIMER, PIN_LEVEL_NOTE
from lib import ml_model, scoring
from lib.db import db
from lib.geo import GeoIndex, catchment_summary

_CACHE: dict[str, tuple[float, object]] = {}
CACHE_TTL = 120.0

DRIVER_TEXT = {
    "marketGrowth": "Attractive market growth",
    "creditOpportunity": "Strong credit environment",
    "depositOpportunity": "Healthy deposit environment",
    "customerPotential": "Large addressable customer base",
    "competitiveOpportunity": "Relative network positioning below leaders",
    "digitalReadiness": "High digital readiness",
}


def _cache_get(key: str):
    hit = _CACHE.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_TTL:
        return hit[1]
    return None


def _cache_set(key: str, val) -> None:
    _CACHE[key] = (time.monotonic(), val)
    if len(_CACHE) > 200:
        for k in list(_CACHE)[:100]:
            _CACHE.pop(k, None)


def top_drivers(sub: dict, n: int = 3) -> list[dict]:
    keys = [k for k in scoring.CONFIG["state_score_weights"] if k in sub]
    return sorted(({"key": k, "label": DRIVER_TEXT[k], "value": sub[k]} for k in keys),
                  key=lambda d: d["value"], reverse=True)[:n]


def priority_for_score(score: float) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 65:
        return "MEDIUM-HIGH"
    if score >= 50:
        return "MEDIUM"
    return "WATCH"


def recommendation_text(sub: dict, state: str) -> str:
    drivers = [d["key"] for d in top_drivers(sub, 3)]
    if sub["marketGrowth"] >= 78 and sub["creditOpportunity"] >= 78 and sub["competitiveOpportunity"] >= 70:
        return f"Evaluate selective physical and digital distribution expansion across high-growth micro-markets in {state}."
    if sub["digitalReadiness"] >= 80 and sub["competitiveOpportunity"] < 55:
        return f"Prioritise digital-first distribution and productivity in {state} rather than broad physical network expansion."
    if "customerPotential" in drivers and "marketGrowth" in drivers:
        return f"Assess phased expansion in {state} to capture a large addressable customer base as the market scales."
    return f"Focus on customer penetration and network productivity in {state}; further management validation required."


# ------------------------------------------------------------------ lookups
def _bank_match(bank: dict, param: str) -> bool:
    return param in (bank.get("short"), bank.get("name"), bank.get("id"))


async def resolve_bank(bank_param: str | None) -> dict | None:
    if not bank_param or bank_param in ("All Banks", "all", "default"):
        return await db.banks.find_one({"short": "HDFC Bank"})
    return await db.banks.find_one({"$or": [{"short": bank_param}, {"name": bank_param}, {"id": bank_param}]})


# ------------------------------------------------------------------ states (ported 1.0 engine)
async def states_ranked(bank_param: str | None) -> list[dict]:
    cache_key = f"states:{bank_param or 'All Banks'}"
    if (hit := _cache_get(cache_key)) is not None:
        return hit
    banks = await db.banks.find({}, {"_id": 0}).to_list(100)
    states = await db.states.find({}, {"_id": 0}).to_list(100)
    if not banks or not states:
        return []
    use_all = not bank_param or bank_param == "All Banks"
    selected = banks if use_all else [b for b in banks if _bank_match(b, bank_param)] or banks[:1]
    keys = list(scoring.CONFIG["state_score_weights"])

    rows = []
    for s in states:
        region = {"name": s["name"], "indicators": s["indicators"]}
        subs = [scoring.state_scores({**b, "_all_banks": banks}, region) for b in selected]
        sub = {k: round(sum(x[k] for x in subs) / len(subs)) for k in keys}
        overall = round(sum(x["overall"] for x in subs) / len(subs))
        presence = round(sum(x["presence"] for x in subs) / len(subs))
        decision = scoring.decision_for_state_score(overall)
        rows.append({
            "id": s["id"], "state": s["name"], "region": s["region"], "populationMn": s["populationMn"],
            "score": overall, "sub": sub, "presence": presence,
            "decision": {"label": decision["label"], "color": decision["color"]},
            "priority": priority_for_score(overall),
            "drivers": top_drivers(sub, 3),
            "recommendation": recommendation_text(sub, s["name"]),
            "dataConfidence": s["indicators"]["dataConfidence"],
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    _cache_set(cache_key, rows)
    return rows


# ------------------------------------------------------------------ shared frame
async def _districts_of(state_id: str | None, district_id: str | None, city: dict | None) -> list[str]:
    if city:
        return [city["districtId"]]
    if district_id:
        return [district_id]
    docs = await db.districts.find({"stateId": state_id}, {"id": 1}).to_list(1000)
    return [d["id"] for d in docs]


async def _frame(district_ids: list[str]) -> dict:
    branches = await db.branches.find({"districtId": {"$in": district_ids}}, {"_id": 0}).to_list(50000)
    candidates = await db.location_candidates.find({"districtId": {"$in": district_ids}}, {"_id": 0}).to_list(50000)
    city_ids = list({c["cityId"] for c in candidates})
    metrics = await db.market_metrics.find(
        {"refId": {"$in": district_ids + city_ids}}, {"_id": 0}).to_list(50000)
    return {"branches": branches, "candidates": candidates,
            "metric_by_ref": {m["refId"]: m for m in metrics}}


def _sub_scores(m: dict, presence: float) -> dict:
    return {
        "marketGrowth": round(m.get("marketGrowth", 60)),
        "creditOpportunity": round(scoring.clamp((m.get("creditGrowthPct", 10) - 6) / 10 * 100)),
        "depositOpportunity": round(scoring.clamp((m.get("depositGrowthPct", 10) - 6) / 10 * 100)),
        "customerPotential": round(m.get("customerPotential", 60)),
        "competitiveOpportunity": round(scoring.clamp(
            0.55 * (100 - scoring.clamp(presence, 0, 96)) + 0.4 * m.get("marketGrowth", 60)
            - 0.15 * m.get("competitorDensity", 50) + 18)),
        "digitalReadiness": round(m.get("digitalReadiness", 60)),
    }


def _weighted(sub: dict) -> int:
    w = scoring.CONFIG["state_score_weights"]
    return round(sum(sub[k] * w[k] for k in w))


# ------------------------------------------------------------------ districts
async def districts_ranked(state_id: str, bank_param: str | None) -> list[dict]:
    cache_key = f"districts:{state_id}:{bank_param}"
    if (hit := _cache_get(cache_key)) is not None:
        return hit
    bank = await resolve_bank(bank_param)
    state = await db.states.find_one({"id": state_id}, {"_id": 0})
    districts = await db.districts.find({"stateId": state_id}, {"_id": 0}).to_list(1000)
    if not (bank and districts):
        return []
    dids = [d["id"] for d in districts]
    frame = await _frame(dids)
    total_by = Counter(b["districtId"] for b in frame["branches"])
    own_by = Counter(b["districtId"] for b in frame["branches"] if b["bankId"] == bank["id"])

    rows = []
    for d in districts:
        m = frame["metric_by_ref"].get(d["id"], {})
        total, own = total_by.get(d["id"], 0), own_by.get(d["id"], 0)
        share = (own / total * 100) if total else 0.0
        sub = _sub_scores(m, scoring.clamp(share * 3, 0, 96))
        overall = _weighted(sub)
        decision = scoring.decision_for_state_score(overall)
        rows.append({
            "id": d["id"], "stateId": state_id, "state": d.get("state", state["name"] if state else ""),
            "name": d["name"], "tier": d["tier"], "populationMn": d["populationMn"],
            "ownBranches": own, "totalBranches": total, "competitorBranches": total - own,
            "penetrationPct": round(share, 1),
            "sub": sub, "overall": overall,
            "decision": {"label": decision["label"], "color": decision["color"]},
            "priority": priority_for_score(overall), "drivers": top_drivers(sub, 3),
            "dataConfidence": state["indicators"]["dataConfidence"] if state else "MEDIUM",
        })
    rows.sort(key=lambda r: r["overall"], reverse=True)
    _cache_set(cache_key, rows)
    return rows


# ------------------------------------------------------------------ cities
async def cities_ranked(district_id: str, bank_param: str | None) -> list[dict]:
    cache_key = f"cities:{district_id}:{bank_param}"
    if (hit := _cache_get(cache_key)) is not None:
        return hit
    bank = await resolve_bank(bank_param)
    district = await db.districts.find_one({"id": district_id}, {"_id": 0})
    cities = await db.cities.find({"districtId": district_id}, {"_id": 0}).sort("populationK", -1).to_list(1000)
    if not (bank and cities):
        return []
    frame = await _frame([district_id])
    own_index = GeoIndex([b for b in frame["branches"] if b["bankId"] == bank["id"]])
    comp_index = GeoIndex([b for b in frame["branches"] if b["bankId"] != bank["id"]])
    d_metric = frame["metric_by_ref"].get(district_id, {})

    rows = []
    for c in cities:
        m = frame["metric_by_ref"].get(c["id"], d_metric)
        near_own = own_index.query(c["lat"], c["lng"], 10)
        near_comp = comp_index.query(c["lat"], c["lng"], 10)
        nearest_own = round(near_own[0][1], 2) if near_own else None
        own5 = sum(1 for _, dist in near_own if dist <= 5)
        comp5 = sum(1 for _, dist in near_comp if dist <= 5)
        city_total = sum(1 for b in frame["branches"] if b["cityId"] == c["id"])
        own_city = sum(1 for b in frame["branches"] if b["cityId"] == c["id"] and b["bankId"] == bank["id"])
        share = (own_city / city_total * 100) if city_total else 0.0
        sub = _sub_scores(m, scoring.clamp(share * 3, 0, 96))
        whitespace = scoring.whitespace_score(
            (sub["marketGrowth"] + sub["customerPotential"]) / 2, nearest_own, own5, comp5)
        overall = _weighted(sub)
        decision = scoring.decision_for_state_score(overall)
        rows.append({
            "id": c["id"], "districtId": district_id, "district": district["name"] if district else "",
            "stateId": c["stateId"], "name": c["name"], "tier": c["tier"],
            "populationK": c["populationK"], "kind": c["kind"], "pin": c["pin"],
            "ownBranches": own_city, "competitorBranches": city_total - own_city,
            "nearestOwnKm": nearest_own,
            "nearestCompetitorKm": round(near_comp[0][1], 2) if near_comp else None,
            "whitespace": whitespace, "sub": sub, "overall": overall,
            "decision": {"label": decision["label"], "color": decision["color"]},
            "dataConfidence": "MEDIUM",
            "note": PIN_LEVEL_NOTE if c["kind"] == "locality" else None,
        })
    rows.sort(key=lambda r: r["overall"], reverse=True)
    _cache_set(cache_key, rows)
    return rows


# ------------------------------------------------------------------ locations (2.0 core)
def _candidate_features(cand: dict, m: dict, tier: str, own_index: GeoIndex, comp_index: GeoIndex) -> dict:
    lat, lng = cand["lat"], cand["lng"]
    near_own = own_index.query(lat, lng, 10)
    near_comp = comp_index.query(lat, lng, 10)
    return {
        "marketGrowth": m.get("marketGrowth", 60),
        "creditGrowthPct": m.get("creditGrowthPct", 10),
        "depositGrowthPct": m.get("depositGrowthPct", 10),
        "digitalReadiness": m.get("digitalReadiness", 60),
        "urbanization": m.get("urbanization", 50),
        "customerPotential": m.get("customerPotential", 60),
        "catchmentPop": cand.get("catchmentPop", 0),
        "businessCount": cand.get("businessCount", 0),
        "nearestOwnKm": near_own[0][1] if near_own else None,
        "ownWithin3": sum(1 for _, d in near_own if d <= 3),
        "ownWithin5": sum(1 for _, d in near_own if d <= 5),
        "nearestCompKm": near_comp[0][1] if near_comp else None,
        "compWithin1": sum(1 for _, d in near_comp if d <= 1),
        "compWithin3": sum(1 for _, d in near_comp if d <= 3),
        "compWithin5": sum(1 for _, d in near_comp if d <= 5),
        "compWithin10": len(near_comp),
        "tier": tier,
        "operatingCostIndex": cand.get("operatingCostIndex", 0.5),
        "accessibility": cand.get("accessibility", 0.7),
    }


def _score_candidate(cand: dict, features: dict, place: dict) -> dict:
    scored = scoring.location_score(features)
    pred = ml_model.predict({**features,
                             "bankWhitespace": scored["whitespaceScore"],
                             "competitiveBalance": max(0.0, 100 - abs(features["compWithin5"] - 7) * 7),
                             "nearestOwnKm": features["nearestOwnKm"] if features["nearestOwnKm"] is not None else 10.0})
    return {
        "id": cand["id"], "name": cand["name"], "siteType": cand["siteType"],
        "city": place["city"], "cityId": cand["cityId"],
        "district": place["district"], "districtId": cand["districtId"],
        "state": place["state"], "stateId": cand["stateId"],
        "pincode": cand["pincode"], "lat": cand["lat"], "lng": cand["lng"],
        "score": scored["score"], "baseScore": scored["baseScore"],
        "decision": scored["decision"], "priority": scoring.priority_for_score(scored["score"]),
        "cannibalization": scored["cannibalization"], "whitespaceScore": scored["whitespaceScore"],
        "nearestOwnKm": round(features["nearestOwnKm"], 2) if features["nearestOwnKm"] is not None else None,
        "nearestCompetitorKm": round(features["nearestCompKm"], 2) if features["nearestCompKm"] is not None else None,
        "catchmentPop": int(features["catchmentPop"]), "mlProbability": pred["probability"],
        "blended": scoring.blend_scores(scored["score"], pred["probability"], "MEDIUM"),
        "dataConfidence": "MEDIUM", "sourceType": "demo",
        "_scored": scored, "_pred": pred, "_features": features,
    }


async def locations_ranked(state_id: str | None, district_id: str | None, city_id: str | None,
                           bank_param: str | None, min_score: int | None = None,
                           min_population: int | None = None, limit: int = 20) -> list[dict]:
    bank = await resolve_bank(bank_param)
    if not bank:
        return []
    city = await db.cities.find_one({"id": city_id}, {"_id": 0}) if city_id else None
    if city and not district_id:
        district_id = city["districtId"]
    if district_id and not state_id:
        d = await db.districts.find_one({"id": district_id}, {"_id": 0})
        state_id = d["stateId"] if d else None

    cache_key = f"locs:{state_id}:{district_id}:{city_id}:{bank['id']}:{min_score}:{min_population}:{limit}"
    if (hit := _cache_get(cache_key)) is not None:
        return hit

    dids = await _districts_of(state_id, district_id, city)
    frame = await _frame(dids)
    own_index = GeoIndex([b for b in frame["branches"] if b["bankId"] == bank["id"]])
    comp_index = GeoIndex([b for b in frame["branches"] if b["bankId"] != bank["id"]])

    district_docs = await db.districts.find({"id": {"$in": dids}}, {"_id": 0}).to_list(1000)
    d_name = {d["id"]: d["name"] for d in district_docs}
    state_doc = await db.states.find_one({"id": state_id}, {"_id": 0}) if state_id else None
    state_name = state_doc["name"] if state_doc else ""
    city_docs = await db.cities.find(
        {"id": {"$in": list({c["cityId"] for c in frame["candidates"]})}}, {"_id": 0}).to_list(5000)
    city_by = {c["id"]: c for c in city_docs}

    rows = []
    for cand in frame["candidates"]:
        if city and cand["cityId"] != city["id"]:
            continue
        cdoc = city_by.get(cand["cityId"])
        if not cdoc:
            continue
        m = frame["metric_by_ref"].get(cand["cityId"]) or frame["metric_by_ref"].get(cand["districtId"], {})
        features = _candidate_features(cand, m, cdoc["tier"], own_index, comp_index)
        row = _score_candidate(cand, features, {
            "city": cdoc["name"], "district": d_name.get(cand["districtId"], ""), "state": state_name})
        if min_score is not None and row["score"] < min_score:
            continue
        if min_population is not None and row["catchmentPop"] < min_population:
            continue
        rows.append(row)

    rows.sort(key=lambda r: (-r["score"], -(r["catchmentPop"] or 0)))
    rows = rows[:limit]

    now = datetime.now(timezone.utc).isoformat()
    for row in rows[:50]:
        await db.opportunity_scores.replace_one(
            {"candidate_id": row["id"], "bank_id": bank["id"]},
            {"candidate_id": row["id"], "bank_id": bank["id"], "score": row["score"],
             "breakdown": row["_scored"]["breakdown"], "decision": row["decision"],
             "cannibalization": row["cannibalization"], "computedAt": now}, upsert=True)
        await db.model_predictions.replace_one(
            {"candidate_id": row["id"], "bank_id": bank["id"]},
            {"candidate_id": row["id"], "bank_id": bank["id"], "probability": row["mlProbability"],
             "modelType": row["_pred"]["modelType"], "contributions": row["_pred"]["contributions"],
             "computedAt": now}, upsert=True)

    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    _cache_set(cache_key, clean)
    return clean


async def location_detail(candidate_id: str, bank_param: str | None) -> dict | None:
    cand = await db.location_candidates.find_one({"id": candidate_id}, {"_id": 0})
    if not cand:
        return None
    bank = await resolve_bank(bank_param)
    cdoc = await db.cities.find_one({"id": cand["cityId"]}, {"_id": 0})
    ddoc = await db.districts.find_one({"id": cand["districtId"]}, {"_id": 0})
    sdoc = await db.states.find_one({"id": cand["stateId"]}, {"_id": 0})
    if not (bank and cdoc and ddoc and sdoc):
        return None

    frame = await _frame([cand["districtId"]])
    own_index = GeoIndex([b for b in frame["branches"] if b["bankId"] == bank["id"]])
    comp_index = GeoIndex([b for b in frame["branches"] if b["bankId"] != bank["id"]])
    has_city_metric = cand["cityId"] in frame["metric_by_ref"]
    m = frame["metric_by_ref"].get(cand["cityId"]) or frame["metric_by_ref"].get(cand["districtId"], {})

    features = _candidate_features(cand, m, cdoc["tier"], own_index, comp_index)
    row = _score_candidate(cand, features, {
        "city": cdoc["name"], "district": ddoc["name"], "state": sdoc["name"]})
    scored, pred = row["_scored"], row["_pred"]

    radii = [float(r) for r in scoring.CONFIG["catchment_radii_km"]]
    catchment = catchment_summary(cand, None, cand["catchmentPop"], own_index, comp_index,
                                  radii, cand["businessCount"])

    def dto(doc: dict, dist: float) -> dict:
        return {"id": doc["id"], "bankShort": doc["bankShort"], "bankName": doc["bankName"],
                "name": doc["name"], "lat": doc["lat"], "lng": doc["lng"],
                "distanceKm": round(dist, 2), "pincode": doc.get("pincode", ""),
                "branchType": doc.get("branchType", "")}

    confidence = data_confidence("location", has_city_metric, True, len(frame["branches"]))
    detail = {k: v for k, v in row.items() if not k.startswith("_")}
    # Re-blend with the location's real confidence level (the ranked list assumes MEDIUM).
    detail["blended"] = scoring.blend_scores(scored["score"], pred["probability"], confidence["level"])
    detail.update({
        "breakdown": scored["breakdown"], "penalties": scored["penalties"],
        "totalPenalty": scored["totalPenalty"], "branchesPer10kPop": scored["branchesPer10kPop"],
        "evidence": scoring.evidence_points(cand, features, scored, bank["short"]),
        "catchment": catchment,
        "nearbyOwn": [dto(d, dist) for d, dist in own_index.query(cand["lat"], cand["lng"], 10)[:8]],
        "nearbyCompetitors": [dto(d, dist) for d, dist in comp_index.query(cand["lat"], cand["lng"], 10)[:8]],
        "market": {k: v for k, v in m.items() if k not in ("_id", "dataLabels")},
        "marketSource": ("city" if has_city_metric else "district") + "-level indicators",
        "confidence": confidence,
        "mlPrediction": pred, "disclaimer": DEMO_DISCLAIMER,
        "productName": f"BranchIQ 2.0 — {bank['short']} · {cdoc['name']} · {cand['name']}",
    })
    return detail


def data_confidence(scope: str, has_city_metric: bool, has_district_metric: bool, branch_count: int) -> dict:
    """§22 — confidence from source count, granularity and missing variables."""
    notes: list[str] = []
    level = "MEDIUM"
    if scope in ("pin", "location"):
        notes.append(PIN_LEVEL_NOTE)
        if not (has_city_metric or has_district_metric):
            level = "LOW"
    if branch_count == 0:
        level = "INSUFFICIENT"
        notes.append("No branch data available for this area.")
    notes.append(DEMO_DISCLAIMER)
    return {"level": level, "notes": notes, "sourceCount": 3 if branch_count else 1}


async def market_overview(district_id: str) -> dict | None:
    district = await db.districts.find_one({"id": district_id}, {"_id": 0})
    if not district:
        return None
    metric = await db.market_metrics.find_one({"refId": district_id, "scope": "district"}, {"_id": 0})
    branches = await db.branches.find({"districtId": district_id}, {"_id": 0}).to_list(5000)
    cities = await db.cities.find({"districtId": district_id}, {"_id": 0}).sort("populationK", -1).to_list(100)
    return {
        "district": {"id": district["id"], "name": district["name"], "state": district.get("state", ""),
                     "stateId": district["stateId"], "tier": district["tier"],
                     "populationMn": district["populationMn"], "lat": district["lat"], "lng": district["lng"]},
        "metrics": metric or {},
        "branchesByBank": dict(Counter(b["bankShort"] for b in branches)),
        "branchCount": len(branches),
        "cities": cities,
        "disclaimer": DEMO_DISCLAIMER,
    }
