"""BranchIQ prediction layer — transparent heuristic model with per-feature contributions.

Per PRD §19: real ML (XGBoost/LightGBM) requires historical training data that does not
exist yet. This layer is an explicitly-labelled "MODEL PREDICTION" heuristic: a fixed,
disclosed weight vector over normalized features pushed through a logistic function.
When historical branch-performance data is ingested, swap `predict()` for a trained
model — the response contract (probability + contributions) stays identical.
"""

import math

FEATURE_SPECS = [
    ("catchmentPop", "Population catchment", 1.10, 60000),
    ("creditGrowthPct", "Credit growth", 1.25, 14.0),
    ("depositGrowthPct", "Deposit growth", 1.05, 12.0),
    ("businessCount", "Business density", 0.95, 45),
    ("urbanization", "Urbanization", 0.80, 78.0),
    ("bankWhitespace", "Bank whitespace", 1.30, 70.0),
    ("digitalReadiness", "Digital readiness", 0.55, 75.0),
    ("nearestOwnKm", "Distance to own branch", 0.90, 6.0),
    ("competitiveBalance", "Competitive balance", 0.60, 70.0),
]

BIAS = 0.15  # z at a perfectly typical market (every feature at its anchor) → p ≈ 0.54


def predict(features: dict) -> dict:
    """Trained XGBoost prediction when an artifact exists, else the transparent heuristic.

    The response contract (probability + contributions + modelType/note) is identical either
    way, so every caller and the frontend stay unchanged across the swap.
    """
    try:
        from lib import model_store

        trained = model_store.predict(features)
        if trained:
            return trained
    except Exception:
        pass
    return heuristic_predict(features)


def heuristic_predict(features: dict) -> dict:
    """Features are CENTERED on their anchor: x=1 is a typical market, so a contribution is
    the signed push away from typical. Without centering every weight stacks additively and
    the sigmoid saturates at ~1.0 for all locations."""
    z = BIAS
    contributions = []
    for key, label, weight, anchor in FEATURE_SPECS:
        v = features.get(key) or 0.0
        x = max(0.0, min(2.0, v / anchor))
        contribution = weight * (x - 1.0)
        z += contribution
        contributions.append({"feature": key, "label": label,
                              "contribution": round(contribution, 3),
                              "contributionPct": 0})

    p = 1.0 / (1.0 + math.exp(-z))
    probability = round(p * 100, 1)
    total_abs = sum(abs(c["contribution"]) for c in contributions) or 1.0
    for c in contributions:
        c["contributionPct"] = round(abs(c["contribution"]) / total_abs * 100, 1)
    contributions.sort(key=lambda c: c["contribution"], reverse=True)
    return {
        "probability": probability,
        "modelType": "BranchIQ heuristic logistic model (transparent centered weights) — MODEL PREDICTION",
        "note": "Will be replaced by a trained XGBoost/LightGBM model once historical "
                "branch-performance data is ingested. Does not replace the business score.",
        "contributions": contributions,
    }
