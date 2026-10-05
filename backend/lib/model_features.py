"""The single feature contract shared by the trainer and the live predictor.

Training rows and prediction-time candidate features must be vectorized identically — one
list, one converter. Changing the order invalidates saved artifacts, so bump MODEL_VERSION.
"""

MODEL_VERSION = "1.0.0"

# (key, human label, fallback when the feature is missing)
FEATURE_SPECS: list[tuple[str, str, float]] = [
    ("catchmentPop", "Population catchment", 60000.0),
    ("creditGrowthPct", "Credit growth", 10.0),
    ("depositGrowthPct", "Deposit growth", 10.0),
    ("businessCount", "Business density", 500.0),
    ("urbanization", "Urbanization", 55.0),
    ("bankWhitespace", "Bank whitespace", 60.0),
    ("digitalReadiness", "Digital readiness", 65.0),
    ("nearestOwnKm", "Distance to own branch", 8.0),
    ("competitiveBalance", "Competitive balance", 70.0),
    ("marketGrowth", "Market growth", 60.0),
    ("customerPotential", "Customer potential", 60.0),
    ("ownWithin5", "Own branches within 5 km", 0.0),
    ("compWithin5", "Competitor branches within 5 km", 5.0),
]

FEATURE_ORDER = [k for k, _, _ in FEATURE_SPECS]
FEATURE_LABELS = {k: label for k, label, _ in FEATURE_SPECS}


def to_vector(features: dict) -> list[float]:
    """Dict → ordered numeric vector, substituting the documented fallback for None/missing."""
    out: list[float] = []
    for key, _label, fallback in FEATURE_SPECS:
        v = features.get(key)
        out.append(float(fallback) if v is None else float(v))
    return out


def competitive_balance(comp_within_5: int) -> float:
    """Competition read as a bell curve: a live market without saturation peaks around 7."""
    return max(0.0, 100.0 - abs(comp_within_5 - 7) * 7.0)
