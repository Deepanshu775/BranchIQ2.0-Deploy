"""BranchIQ geospatial engine — real distance math, grid-indexed.

Heavy calculations run in the backend only (performance rule §30): the browser
never computes thousands of distances. A flat 2D grid index buckets branch docs
into ~0.12° cells (~13 km at Indian latitudes), so radius queries only scan a
3x3 neighbourhood instead of every branch in a state.
"""

import math
from collections import defaultdict

EARTH_R_KM = 6371.0088
CELL_DEG = 0.12


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km."""
    if None in (lat1, lng1, lat2, lng2):
        return float("inf")
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_R_KM * math.asin(math.sqrt(a))


def _cell(lat: float, lng: float) -> tuple[int, int]:
    return (math.floor(lat / CELL_DEG), math.floor(lng / CELL_DEG))


class GeoIndex:
    """Grid index over documents with lat/lng fields (dict-like docs)."""

    def __init__(self, docs: list[dict], lat_key: str = "lat", lng_key: str = "lng"):
        self.lat_key, self.lng_key = lat_key, lng_key
        self._cells: dict[tuple[int, int], list[dict]] = defaultdict(list)
        for d in docs:
            lat, lng = d.get(lat_key), d.get(lng_key)
            if lat is None or lng is None:
                continue
            self._cells[_cell(lat, lng)].append(d)

    def query(self, lat: float, lng: float, radius_km: float) -> list[tuple[dict, float]]:
        """All docs within radius_km, as (doc, distance_km) sorted nearest-first."""
        cx, cy = _cell(lat, lng)
        span = math.ceil(radius_km / (CELL_DEG * 111.0)) + 1  # lat cells are ~111 km; lng cells are shorter, so this is conservative
        out: list[tuple[dict, float]] = []
        seen: set[int] = set()
        for dx in range(-span, span + 1):
            for dy in range(-span, span + 1):
                for d in self._cells.get((cx + dx, cy + dy), []):
                    key = id(d)
                    if key in seen:
                        continue
                    seen.add(key)
                    dist = haversine_km(lat, lng, d[self.lat_key], d[self.lng_key])
                    if dist <= radius_km:
                        out.append((d, dist))
        out.sort(key=lambda x: x[1])
        return out

    def counts_by_radius(self, lat: float, lng: float, radii_km: list[float]) -> dict[float, int]:
        near = self.query(lat, lng, max(radii_km))
        return {r: sum(1 for _, dist in near if dist <= r) for r in radii_km}

    def nearest(self, lat: float, lng: float) -> tuple[dict | None, float]:
        """Nearest doc and its distance — searches progressively wider rings."""
        cx, cy = _cell(lat, lng)
        best: tuple[dict, float] | None = None  # kept across rings: resetting it per ring discards
        for span in range(0, 40):               # the center-cell hit and returns a farther branch
            for dx in range(-span, span + 1):
                for dy in range(-span, span + 1):
                    ring_edge = span == 0 or abs(dx) == span or abs(dy) == span
                    if not ring_edge:
                        continue  # inner cells were scanned on earlier rings
                    for d in self._cells.get((cx + dx, cy + dy), []):
                        dist = haversine_km(lat, lng, d[self.lat_key], d[self.lng_key])
                        if best is None or dist < best[1]:
                            best = (d, dist)
            if best is not None and best[1] <= span * CELL_DEG * 111.0:
                return best
        return (None, float("inf"))


def catchment_summary(pop_center: dict, pop_index: GeoIndex | None, area_pop: float,
                      own_index: GeoIndex, comp_index: GeoIndex, radii_km: list[float],
                      businesses: float) -> dict:
    """Catchment analysis for one location.

    `area_pop` is the candidate's 5 km service-area catchment (the anchor), so rings scale
    relative to 5 km — not to the widest radius, which would inflate the headline figure.
    """
    own = own_index.query(pop_center["lat"], pop_center["lng"], max(radii_km))
    comp = comp_index.query(pop_center["lat"], pop_center["lng"], max(radii_km))
    anchor = 5.0
    rings = []
    for r in radii_km:
        scale = (r / anchor) ** 1.5 if r <= anchor else 1.0 + math.log(r / anchor) * 0.55
        rings.append({
            "radiusKm": r,
            "population": int(round(area_pop * scale)),
            "ownBranches": sum(1 for _, dist in own if dist <= r),
            "competitorBranches": sum(1 for _, dist in comp if dist <= r),
            "businessDensity": int(round(businesses * scale)),
        })
    return {"rings": rings,
            "population": int(round(area_pop)),
            "ownBranches": len(own),
            "competitorBranches": len(comp),
            "nearestOwnKm": round(own[0][1], 2) if own else None,
            "nearestCompetitorKm": round(comp[0][1], 2) if comp else None}
