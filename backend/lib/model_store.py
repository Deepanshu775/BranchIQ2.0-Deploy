"""Loads the trained XGBoost artifact and serves predictions with real SHAP contributions.

Falls back silently when no artifact exists — the heuristic model in lib/ml_model.py remains
the predictor until training has run, so the API contract never changes.
"""

import json
import threading

from lib.model_features import FEATURE_LABELS, FEATURE_ORDER, to_vector
from lib.trainer import META_PATH, MODEL_PATH

_lock = threading.Lock()
_cache: dict = {"mtime": None, "booster": None, "meta": None}

HEURISTIC_NOTE = ("No trained artifact yet — BranchIQ is serving the transparent heuristic "
                  "model. Ingest branch-performance history and run training to activate "
                  "the XGBoost predictor.")


def _load():
    """Return (booster, meta) or (None, None). Reloads when the artifact changes on disk."""
    if not MODEL_PATH.exists():
        return None, None
    mtime = MODEL_PATH.stat().st_mtime
    with _lock:
        if _cache["mtime"] != mtime:
            import xgboost as xgb

            booster = xgb.Booster()
            booster.load_model(str(MODEL_PATH))
            booster.feature_names = FEATURE_ORDER
            meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}
            _cache.update({"mtime": mtime, "booster": booster, "meta": meta})
        return _cache["booster"], _cache["meta"]


def is_ready() -> bool:
    try:
        booster, _ = _load()
        return booster is not None
    except Exception:
        return False


def info() -> dict:
    """Model-lab payload: status, metrics and feature importances (or heuristic status)."""
    try:
        booster, meta = _load()
    except Exception as exc:  # pragma: no cover - artifact corruption
        return {"status": "error", "error": str(exc), "modelType": "BranchIQ heuristic model"}
    if booster is None:
        return {"status": "heuristic",
                "modelType": "BranchIQ heuristic logistic model (transparent centered weights)",
                "note": HEURISTIC_NOTE,
                "featureImportances": [], "metrics": {}}
    return {**(meta or {}), "status": "trained",
            "featureOrder": FEATURE_ORDER}


def predict(features: dict) -> dict | None:
    """Trained-model prediction with per-feature SHAP contributions, or None if unavailable."""
    try:
        import numpy as np
        import xgboost as xgb

        booster, meta = _load()
        if booster is None:
            return None
        vec = np.array([to_vector(features)], dtype=float)
        dm = xgb.DMatrix(vec, feature_names=FEATURE_ORDER)
        probability = float(booster.predict(dm)[0]) * 100
        shap = booster.predict(dm, pred_contribs=True)[0]  # last entry is the bias term
        contribs = [{"feature": f, "label": FEATURE_LABELS[f],
                     "contribution": round(float(shap[i]), 3), "contributionPct": 0.0}
                    for i, f in enumerate(FEATURE_ORDER)]
        total = sum(abs(c["contribution"]) for c in contribs) or 1.0
        for c in contribs:
            c["contributionPct"] = round(abs(c["contribution"]) / total * 100, 1)
        contribs.sort(key=lambda c: c["contribution"], reverse=True)
        metrics = (meta or {}).get("metrics", {})
        return {
            "probability": round(probability, 1),
            "modelType": f"XGBoost gradient-boosted classifier (trained "
                         f"{(meta or {}).get('trainedAt', 'n/a')[:10]}) — MODEL PREDICTION",
            "note": (f"Trained on {(meta or {}).get('trainingRows', 0)} branch-performance rows; "
                     f"holdout ROC-AUC {metrics.get('rocAuc', 'n/a')}. SHAP values show each "
                     f"feature's signed push on the prediction. Does not replace the business score."),
            "contributions": contribs,
        }
    except Exception:
        return None
