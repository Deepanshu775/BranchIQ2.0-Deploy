"""BranchIQ scoring engines — every weight/threshold lives in data/scoring_config.json.

Layered model (never presented as official data):
- state-level scores: ported 1.0 engine (30/20/15/15/10/10) for the existing pages
- district & town/city scores: same family, computed from measured demo branch networks
- location scores: BranchIQ 2.0 framework (§14) with cannibalization/saturation/cost penalties,
  whitespace engine (§11), cannibalization engine (§12), decision bands (§15)
"""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "data" / "scoring_config.json"
with open(CONFIG_PATH) as fh:
    CONFIG: dict = json.load(fh)


def clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def rnd(v: float) -> int:
    return int(round(v))


# ---------------------------------------------------------------- state engine (ported 1.0)
def norm(v: float, lo: float, hi: float) -> float:
    return 50.0 if hi == lo else (v - lo) / (hi - lo) * 100.0


def bank_presence(bank: dict, region: dict) -> int:
    """BranchIQ model estimate of a bank's presence in a state (ported from engine.js)."""
    banks = bank["_all_banks"]
    br_vals = [b["branches"] for b in banks]
    size_score = 30 + 0.6 * norm(bank["branches"], min(br_vals), max(br_vals))
    ind = region["indicators"]
    bias = 0.0
    name = region["name"]
    if bank["sector"] == "Private":
        if name in {"Maharashtra", "Delhi NCR", "Karnataka", "Telangana", "Goa", "Kerala"}:
            bias += 10
        if name in {"Uttar Pradesh", "West Bengal", "Madhya Pradesh", "Rajasthan"}:
            bias -= 8
    else:
        if name in {"Uttar Pradesh", "West Bengal", "Madhya Pradesh", "Rajasthan"}:
            bias += 10
        if name == "Goa":
            bias -= 4
    digital_tilt = (ind["digitalReadiness"] - 70) * 0.15 if bank["sector"] == "Private" else 0.0
    return rnd(clamp(size_score * 0.72 + bias + digital_tilt, 10, 96))


def state_scores(bank: dict, region: dict) -> dict:
    """Ported state-level opportunity engine (existing pages keep their numbers)."""
    ind = region["indicators"]
    presence = bank_presence(bank, region)
    comp = rnd(clamp(0.55 * (100 - presence) + 0.4 * ind["marketGrowth"]
                     - 0.15 * ind["marketConcentration"] + 18))
    w = CONFIG["state_score_weights"]
    sub = {
        "marketGrowth": ind["marketGrowth"],
        "creditOpportunity": ind["creditOpportunity"],
        "depositOpportunity": ind["depositOpportunity"],
        "customerPotential": ind["customerPotential"],
        "competitiveOpportunity": comp,
        "digitalReadiness": ind["digitalReadiness"],
    }
    overall = rnd(sum(sub[k] * w[k] for k in w))
    return {**sub, "overall": overall, "presence": presence}


def decision_for_state_score(score: float) -> dict:
    for band in CONFIG["state_decision_bands"]:
        if score >= band["min"]:
            return band
    return CONFIG["state_decision_bands"][-1]


# ---------------------------------------------------------------- decision bands (2.0)
def decision_for_location_score(score: float) -> dict:
    for band in CONFIG["decision_bands"]:
        if score >= band["min"]:
            return band
    return CONFIG["decision_bands"][-1]


# ---------------------------------------------------------------- cannibalization engine (§12)
def cannibalization_risk(nearest_own_km: float | None, own_within_3km: int) -> dict:
    if nearest_own_km is None:
        return {"risk": "NONE", "penalty": 0, "nearestOwnKm": None,
                "note": "No branches of this bank recorded in the area (demo branch layer)."}
    bands = CONFIG["cannibalization_bands_km"]
    for band in bands:
        if nearest_own_km < band["max_km"]:
            overlap_penalty = min(own_within_3km, 3)  # each extra own branch inside 3 km tightens overlap
            return {
                "risk": band["risk"],
                "penalty": band["penalty"] + (overlap_penalty if band["risk"] == "HIGH" else 0),
                "nearestOwnKm": round(nearest_own_km, 2),
                "note": f"Nearest own branch is {nearest_own_km:.1f} km away "
                        f"({band['risk']} cannibalization risk at configurable <{band['max_km']:g} km band)",
            }
    return {"risk": "NONE", "penalty": 0, "nearestOwnKm": round(nearest_own_km, 2),
            "note": "Nearest own branch beyond the highest configured band."}


# ---------------------------------------------------------------- whitespace engine (§11)
def whitespace_score(demand: float, nearest_own_km: float | None, own_within_5km: int,
                     competitor_count_5km: int) -> int:
    w = CONFIG["whitespace"]
    demand_component = clamp(demand)
    own_absence = 100.0 if nearest_own_km is None else clamp(nearest_own_km / 8.0 * 100)
    if competitor_count_5km >= w["competitor_too_many_threshold"]:
        comp_balance = 25.0
    elif competitor_count_5km <= 4:
        comp_balance = 60.0 + 10.0 * competitor_count_5km  # some competition signals a live market
    else:
        comp_balance = 100.0 - (competitor_count_5km - 4) * 3.0
    return rnd(clamp(w["demand_weight"] * demand_component
                     + w["own_absence_weight"] * own_absence
                     + w["competitor_balance_weight"] * comp_balance))


# ---------------------------------------------------------------- location score (§14)
def location_score(features: dict) -> dict:
    """Transparent location opportunity score with full breakdown.

    features keys: marketGrowth(0-100), creditGrowthPct, depositGrowthPct, digitalReadiness,
    urbanization, customerPotential, catchmentPop, businessCount, nearestOwnKm, ownWithin3,
    ownWithin5, nearestCompKm, compWithin1/3/5/10, tier, operatingCostIndex
    """
    w = CONFIG["location_score_weights"]

    # NOTE: each sub-component scales its raw input to its own 0-100 band. Dividing first and
    # clamping second (e.g. clamp(pop/60000, 0, 70)) silently yields ~1.4, flattening every score.
    credit_pot = clamp((features["creditGrowthPct"] - 6) / 10 * 58
                       + min(features["businessCount"] / 1500, 1.0) * 42)
    deposit_pot = clamp((features["depositGrowthPct"] - 6) / 10 * 58
                        + min(features["catchmentPop"] / 220000, 1.0) * 42)
    customer_pot = clamp(min(features["catchmentPop"] / 220000, 1.0) * 68
                         + features["urbanization"] * 0.32)
    whitespace = whitespace_score(
        (features["marketGrowth"] + features["customerPotential"]) / 2,
        features["nearestOwnKm"], features["ownWithin5"], features["compWithin5"])
    comp_in_5 = features["compWithin5"]
    if comp_in_5 <= 2:
        competitive = 62 + 8 * comp_in_5  # thin competition, some signal
    else:
        # high demand + high competition is opportunity; low demand + high competition is saturation
        demand_quality = (features["marketGrowth"] + features["customerPotential"]) / 2
        competitive = clamp(70 + (demand_quality - 60) * 0.5 - (comp_in_5 - 2) * 2.2)
    business_pot = clamp(min(features["businessCount"] / 2200, 1.0) * 100)
    accessibility = clamp(features["accessibility"] * 100)
    digital = features["digitalReadiness"]

    comps = {
        "marketGrowth": rnd(clamp(features["marketGrowth"])),
        "creditPotential": rnd(credit_pot),
        "depositPotential": rnd(deposit_pot),
        "customerPotential": rnd(customer_pot),
        "bankWhitespace": whitespace,
        "competitiveOpportunity": rnd(competitive),
        "businessPotential": rnd(business_pot),
        "accessibility": rnd(accessibility),
        "digitalReadiness": rnd(digital),
    }
    base = sum(comps[k] * w[k] for k in w)

    cann = cannibalization_risk(features["nearestOwnKm"], features["ownWithin3"])
    penalties: dict[str, float] = {"Cannibalization Risk": cann["penalty"]}

    branches_per_10k = (features["compWithin5"] + features["ownWithin5"]) / max(features["catchmentPop"] / 10000, 0.01)
    if branches_per_10k > CONFIG["penalties"]["saturation_high_threshold_per_10k_pop"]:
        penalties["Market Saturation"] = CONFIG["penalties"]["saturation_penalty"]
    cost = features["operatingCostIndex"] * 5 + (CONFIG["penalties"]["operating_cost_high_competition"]
                                                 if comp_in_5 >= CONFIG["competitor_high_intensity"] else 0)
    if cost > 0:
        penalties["Operating Cost"] = rnd(cost)

    total_penalty = sum(penalties.values())
    final = rnd(clamp(base - total_penalty))
    decision = decision_for_location_score(final)

    breakdown = [{"key": k, "label": LABELS[k], "weight": w[k], "score": comps[k],
                  "weighted": round(comps[k] * w[k], 2)} for k in w]
    return {
        "score": final,
        "baseScore": rnd(base),
        "breakdown": breakdown,
        "penalties": [{"label": k, "penalty": v} for k, v in penalties.items() if v > 0],
        "totalPenalty": round(total_penalty, 1),
        "decision": {"label": decision["label"], "color": decision["color"]},
        "cannibalization": cann,
        "whitespaceScore": whitespace,
        "branchesPer10kPop": round(branches_per_10k, 2),
    }


# ---------------------------------------------------------------- blended BranchIQ score (§19)
def blend_scores(business_score: float, ml_probability: float, confidence_level: str) -> dict:
    """ML prediction + business rule engine + data confidence → final BranchIQ score.

    The ML weight is scaled down as data confidence drops (and to zero when confidence is
    INSUFFICIENT), so a thin-evidence location always falls back to the transparent business
    score rather than to a model guess. Weights live in data/scoring_config.json.
    """
    cfg = CONFIG["blend"]
    multiplier = cfg["confidence_ml_weight_multiplier"].get(confidence_level.upper(), 0.5)
    ml_weight = cfg["ml_weight"] * multiplier
    business_weight = 1.0 - ml_weight
    blended = rnd(clamp(business_score * business_weight + ml_probability * ml_weight))
    decision = decision_for_location_score(blended)
    delta = blended - rnd(business_score)
    return {
        "businessScore": rnd(business_score),
        "mlProbability": round(ml_probability, 1),
        "branchIQScore": blended,
        "businessWeight": round(business_weight, 3),
        "mlWeight": round(ml_weight, 3),
        "confidenceLevel": confidence_level.upper(),
        "delta": delta,
        "decision": {"label": decision["label"], "color": decision["color"]},
        "priority": priority_for_score(blended),
        "note": (f"BranchIQ score = {business_weight:.0%} transparent business score + "
                 f"{ml_weight:.0%} model probability (model weight scaled by "
                 f"{confidence_level.upper()} data confidence). "
                 f"The model {'raises' if delta > 0 else 'lowers' if delta < 0 else 'leaves'} "
                 f"the business score{f' by {abs(delta)} points' if delta else ' unchanged'}."),
    }


LABELS = {
    "marketGrowth": "Market Growth",
    "creditPotential": "Credit Potential",
    "depositPotential": "Deposit Potential",
    "customerPotential": "Customer Potential",
    "bankWhitespace": "Bank Whitespace",
    "competitiveOpportunity": "Competitive Opportunity",
    "businessPotential": "Business/MSME Potential",
    "accessibility": "Accessibility",
    "digitalReadiness": "Digital Readiness",
}


def priority_for_score(score: float) -> str:
    if score >= 90:
        return "P1 — IMMEDIATE FEASIBILITY"
    if score >= 80:
        return "P2 — SHORTLIST"
    if score >= 65:
        return "P3 — PIPELINE"
    if score >= 50:
        return "P4 — MONITOR"
    return "P5 — DEPRIORITIZE"


# ---------------------------------------------------------------- evidence (§18)
def evidence_points(loc: dict, features: dict, scored: dict, bank_short: str) -> list[dict]:
    """5-7 evidence bullets — each states the metric AND its data type."""
    ev: list[dict] = []
    comp = {c["key"]: c["score"] for c in scored["breakdown"]}
    if loc.get("catchmentPop"):
        ev.append({"text": f"Catchment of ~{int(loc['catchmentPop']):,} residents within the "
                           f"{loc.get('catchmentRadiusKm', 5)} km service radius (MODEL ESTIMATE from public geography).",
                   "type": "MODEL ESTIMATE"})
    if features["nearestOwnKm"] is not None:
        ev.append({"text": f"Whitespace score {scored['whitespaceScore']}/100 — nearest {bank_short} branch is "
                           f"{features['nearestOwnKm']:.1f} km away "
                           f"({'large' if scored['whitespaceScore'] >= 70 else 'moderate'} expansion gap).",
                   "type": "BRANCHIQ ANALYTICAL SCORE"})
    else:
        ev.append({"text": f"No {bank_short} branch recorded within the search area — full whitespace "
                           f"(score {scored['whitespaceScore']}/100, demo branch layer).",
                   "type": "BRANCHIQ ANALYTICAL SCORE"})
    comp5 = features["compWithin5"]
    comp_quality = ("healthy competitive signal with room to differentiate"
                    if 2 < comp5 < CONFIG["whitespace"]["competitor_too_many_threshold"]
                    else ("thin competitive set" if comp5 <= 2 else "saturated competitive set"))
    ev.append({"text": f"{comp5} competitor branches within 5 km (nearest "
                       f"{(features['nearestCompKm'] or 0):.1f} km) — {comp_quality}.",
               "type": "DEMO DATA (branch placement)"})
    ev.append({"text": f"District credit growth ~{features['creditGrowthPct']}% and deposit growth "
                       f"~{features['depositGrowthPct']}% (MODEL ESTIMATE derived from public state indicators).",
               "type": "MODEL ESTIMATE"})
    ev.append({"text": f"~{int(features['businessCount'])} businesses/MSMEs estimated in the catchment — "
                       f"MSME potential {comp['businessPotential']}/100 (MODEL ESTIMATE).",
               "type": "MODEL ESTIMATE"})
    if features["ownWithin3"] > 0:
        ev.append({"text": f"Cannibalization watch: {features['ownWithin3']} own branch(es) within 3 km — "
                           f"{scored['cannibalization']['risk']} risk (configurable bands).",
                   "type": "BRANCHIQ ANALYTICAL SCORE"})
    ev.append({"text": f"Accessibility {comp['accessibility']}/100 for site type '{loc.get('siteType', 'n/a')}' "
                       f"(DEMO site classification).", "type": "DEMO DATA"})
    return ev[:7]
