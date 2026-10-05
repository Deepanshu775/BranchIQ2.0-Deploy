"""XGBoost training pipeline — builds the labelled dataset from branch_performance and fits
a gradient-boosted classifier of "high-performing branch market" (PRD §19, §20).

Label: a branch is positive when its 4-year business (deposits + advances) CAGR lands in the
top third of the training population. Features are the same geospatial/market signals
BranchIQ computes for a candidate location (lib/model_features.FEATURE_ORDER), so the trained
model can score an unbuilt location.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from lib import scoring
from lib.db import db
from lib.geo import GeoIndex
from lib.model_features import FEATURE_ORDER, MODEL_VERSION, competitive_balance, to_vector

ARTIFACT_DIR = Path(__file__).parent.parent / "model_artifacts"
MODEL_PATH = ARTIFACT_DIR / "branch_model.json"
META_PATH = ARTIFACT_DIR / "branch_model_meta.json"


def _cagr(first: float, last: float, years: int) -> float:
    if first <= 0 or years <= 0:
        return 0.0
    return (last / first) ** (1.0 / years) - 1.0


async def build_dataset() -> dict:
    """Join performance history + branch master + market metrics + geospatial context."""
    perf = await db.branch_performance.find({}, {"_id": 0}).to_list(500000)
    if not perf:
        return {"rows": [], "labels": [], "meta": {"error": "no branch_performance rows"}}

    by_branch: dict[str, list[dict]] = {}
    for p in perf:
        by_branch.setdefault(p["branchId"], []).append(p)

    branches = await db.branches.find({}, {"_id": 0}).to_list(100000)
    branch_by_id = {b["id"]: b for b in branches}
    metrics = await db.market_metrics.find({}, {"_id": 0}).to_list(200000)
    metric_by_ref = {m["refId"]: m for m in metrics}
    cities = await db.cities.find({}, {"_id": 0}).to_list(100000)
    city_by_id = {c["id"]: c for c in cities}

    by_district: dict[str, list[dict]] = {}
    for b in branches:
        by_district.setdefault(b["districtId"], []).append(b)
    index_cache: dict[tuple[str, str], tuple[GeoIndex, GeoIndex]] = {}

    def indexes(district_id: str, bank_id: str) -> tuple[GeoIndex, GeoIndex]:
        key = (district_id, bank_id)
        if key not in index_cache:
            group = by_district.get(district_id, [])
            index_cache[key] = (GeoIndex([b for b in group if b["bankId"] == bank_id]),
                                GeoIndex([b for b in group if b["bankId"] != bank_id]))
        return index_cache[key]

    rows: list[dict] = []
    source_types: dict[str, int] = {}
    for branch_id, history in by_branch.items():
        branch = branch_by_id.get(branch_id)
        if not branch or len(history) < 2:
            continue
        history.sort(key=lambda h: h["fiscalYear"])
        first, last = history[0], history[-1]
        growth = _cagr(first.get("businessCr") or 0.0, last.get("businessCr") or 0.0, len(history) - 1)

        own_index, comp_index = indexes(branch["districtId"], branch["bankId"])
        own_near = [d for _, d in own_index.query(branch["lat"], branch["lng"], 10) if d > 0.01]
        comp_near = [d for _, d in comp_index.query(branch["lat"], branch["lng"], 10)]
        own5 = sum(1 for d in own_near if d <= 5)
        comp5 = sum(1 for d in comp_near if d <= 5)
        nearest_own = round(own_near[0], 3) if own_near else None

        m = metric_by_ref.get(branch.get("cityId")) or metric_by_ref.get(branch["districtId"], {})
        city = city_by_id.get(branch.get("cityId", ""), {})
        demand = (m.get("marketGrowth", 60) + m.get("customerPotential", 60)) / 2
        features = {
            "catchmentPop": max(city.get("populationK", 60) * 1000 * 0.45, 4000),
            "creditGrowthPct": m.get("creditGrowthPct", 10),
            "depositGrowthPct": m.get("depositGrowthPct", 10),
            "businessCount": m.get("businessCount", 500),
            "urbanization": m.get("urbanization", 55),
            "bankWhitespace": scoring.whitespace_score(demand, nearest_own, own5, comp5),
            "digitalReadiness": m.get("digitalReadiness", 65),
            "nearestOwnKm": nearest_own,
            "competitiveBalance": competitive_balance(comp5),
            "marketGrowth": m.get("marketGrowth", 60),
            "customerPotential": m.get("customerPotential", 60),
            "ownWithin5": own5,
            "compWithin5": comp5,
        }
        src = last.get("sourceType", "unknown")
        source_types[src] = source_types.get(src, 0) + 1
        rows.append({"branchId": branch_id, "growth": growth, "vector": to_vector(features)})

    if not rows:
        return {"rows": [], "labels": [], "meta": {"error": "no branch with >= 2 fiscal years"}}

    growths = sorted(r["growth"] for r in rows)
    threshold = growths[int(len(growths) * 0.667)]
    labels = [1 if r["growth"] >= threshold else 0 for r in rows]
    return {
        "rows": [r["vector"] for r in rows],
        "labels": labels,
        "meta": {
            "trainingRows": len(rows),
            "positiveRate": round(sum(labels) / len(labels), 3),
            "labelDefinition": "business (deposits + advances) CAGR in the top third of the "
                               "training population",
            "labelThresholdCagr": round(threshold, 4),
            "rowsBySourceType": source_types,
            "featureOrder": FEATURE_ORDER,
        },
    }


async def train() -> dict:
    """Fit XGBoost on the current panel and persist the artifact. Returns metrics + importances."""
    import numpy as np
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier

    data = await build_dataset()
    if not data["rows"]:
        return {"status": "failed", **data["meta"]}
    X = np.array(data["rows"], dtype=float)
    y = np.array(data["labels"], dtype=int)
    if len(set(data["labels"])) < 2 or len(y) < 40:
        return {"status": "failed", "error": "need >= 40 rows and both classes present",
                **data["meta"]}

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    model = XGBClassifier(n_estimators=240, max_depth=4, learning_rate=0.08, subsample=0.9,
                          colsample_bytree=0.9, reg_lambda=1.2, eval_metric="logloss",
                          random_state=42)
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    metrics = {
        "rocAuc": round(float(roc_auc_score(y_te, proba)), 3),
        "accuracy": round(float(accuracy_score(y_te, (proba >= 0.5).astype(int))), 3),
        "trainRows": int(len(y_tr)),
        "testRows": int(len(y_te)),
    }

    booster = model.get_booster()
    booster.feature_names = FEATURE_ORDER
    gain = booster.get_score(importance_type="gain")
    total = sum(gain.values()) or 1.0
    importances = sorted(
        ({"feature": f, "gain": round(gain.get(f, 0.0), 2),
          "importancePct": round(gain.get(f, 0.0) / total * 100, 1)} for f in FEATURE_ORDER),
        key=lambda r: -r["importancePct"])

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(MODEL_PATH))
    meta = {
        "status": "trained",
        "modelType": "XGBoost gradient-boosted classifier (XGBClassifier)",
        "modelVersion": MODEL_VERSION,
        "trainedAt": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "featureImportances": importances,
        "target": "Probability that a branch market performs in the top third on business CAGR",
        "disclaimer": ("MODEL PREDICTION — trained on the branch-performance panel currently "
                       "ingested. Where that panel is the DEMO/TRAINING layer, accuracy figures "
                       "describe the demo data only and are not real-world validation."),
        **data["meta"],
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    return meta
