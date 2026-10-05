"""Data-quality validation (§31) — invalid PINs, bad coordinates, duplicates, stale data."""

import math
import re
from datetime import datetime, timezone

PIN_RE = re.compile(r"^\d{6}$")

# India bounding box (approximate, public geography)
LAT_RANGE = (6.0, 37.5)
LNG_RANGE = (68.0, 98.0)

STALE_DAYS = 730  # demo layer re-verifies on every seed run


def validate_pin(pin: str) -> str | None:
    """Return an error string, or None when the PIN is structurally valid."""
    if not PIN_RE.match(pin or ""):
        return "invalid format (must be 6 digits)"
    if pin[0] in ("0", "9"):
        return "invalid first digit (Indian PINs start 1-8)"
    if len(set(pin)) == 1:
        return "degenerate PIN (all digits identical)"
    return None


def validate_coords(lat: float | None, lng: float | None) -> str | None:
    if lat is None or lng is None:
        return "missing coordinates"
    if math.isnan(lat) or math.isnan(lng):
        return "NaN coordinates"
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LNG_RANGE[0] <= lng <= LNG_RANGE[1]):
        return "coordinates outside India bounding box"
    return None


def find_duplicate_branches(branches: list[dict], within_km: float = 0.3) -> list[dict]:
    """Same-bank branches closer than `within_km` (haversine) — likely duplicates."""
    from lib.geo import haversine_km

    duplicates = []
    by_bank: dict[str, list[dict]] = {}
    for b in branches:
        by_bank.setdefault(b.get("bankId", ""), []).append(b)
    for bank_id, group in by_bank.items():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if a.get("lat") is None or b.get("lat") is None:
                    continue
                if haversine_km(a["lat"], a["lng"], b["lat"], b["lng"]) < within_km:
                    duplicates.append({"bankId": bank_id, "a": a["id"], "b": b["id"],
                                       "note": f"{a.get('name')} / {b.get('name')} within {within_km} km"})
    return duplicates

def quality_report(branch_docs: list[dict], pin_docs: list[dict], source_doc: dict | None = None) -> dict:
    now = datetime.now(timezone.utc)
    branch_errors, pin_errors = [], []
    for b in branch_docs:
        if err := validate_coords(b.get("lat"), b.get("lng")):
            branch_errors.append({"id": b["id"], "issue": f"coordinates: {err}"})
        if err := validate_pin(str(b.get("pincode", ""))):
            branch_errors.append({"id": b["id"], "issue": f"pincode: {err}"})
        if not b.get("districtId"):
            branch_errors.append({"id": b["id"], "issue": "missing district mapping"})
    for p in pin_docs:
        if err := validate_pin(str(p.get("pin", ""))):
            pin_errors.append({"id": p["id"], "issue": err})

    stale = 0
    for b in branch_docs:
        lv = b.get("lastVerified")
        if isinstance(lv, datetime):
            age = (now.replace(tzinfo=None) - lv.replace(tzinfo=lv.tzinfo) if lv.tzinfo else now.replace(tzinfo=None) - lv).days
        elif isinstance(lv, str):
            try:
                age = (now - datetime.fromisoformat(lv).replace(tzinfo=timezone.utc)).days
            except ValueError:
                age = STALE_DAYS + 1
        else:
            age = STALE_DAYS + 1
        if age > STALE_DAYS:
            stale += 1

    dups = find_duplicate_branches(branch_docs)
    return {
        "branchCount": len(branch_docs),
        "pinAreaCount": len(pin_docs),
        "issues": {
            "invalidCoordinates": len([e for e in branch_errors if "coordinates" in e["issue"]]),
            "invalidPincodes": len([e for e in branch_errors if "pincode" in e["issue"]]) + len(pin_errors),
            "missingDistrict": len([e for e in branch_errors if "district" in e["issue"]]),
            "duplicateBranches": len(dups),
            "staleRecords": stale,
        },
        "details": (branch_errors + [{"id": d["id"], "issue": "pincode: invalid"} for d in pin_errors])[:50],
        "duplicateExamples": dups[:10],
        "dataSource": source_doc,
    }
