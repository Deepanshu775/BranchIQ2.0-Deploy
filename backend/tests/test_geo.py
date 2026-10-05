"""Geospatial engine tests — distance, proximity, radius counts, catchment (PRD §29)."""

import math

from lib.geo import CELL_DEG, GeoIndex, catchment_summary, haversine_km

# Reference pairs (public geography), tolerance 1.5%
DELHI = (28.6139, 77.2090)
MUMBAI = (19.0760, 72.8777)
MEERUT = (28.9845, 77.7064)


def _branch(bid: str, lat: float, lng: float, bank: str = "hdfc") -> dict:
    return {"id": bid, "name": bid, "lat": lat, "lng": lng, "bankId": bank}


class TestHaversine:
    def test_zero_distance(self):
        assert haversine_km(*DELHI, *DELHI) == 0.0

    def test_known_pair_delhi_mumbai(self):
        d = haversine_km(*DELHI, *MUMBAI)
        assert abs(d - 1153.0) / 1153.0 < 0.015

    def test_known_pair_delhi_meerut(self):
        d = haversine_km(*DELHI, *MEERUT)
        assert 60.0 < d < 75.0

    def test_symmetry(self):
        assert haversine_km(*DELHI, *MUMBAI) == haversine_km(*MUMBAI, *DELHI)

    def test_one_degree_latitude_is_about_111km(self):
        d = haversine_km(28.0, 77.0, 29.0, 77.0)
        assert abs(d - 111.2) < 1.0

    def test_triangle_inequality(self):
        ab = haversine_km(*DELHI, *MEERUT)
        bc = haversine_km(*MEERUT, *MUMBAI)
        ac = haversine_km(*DELHI, *MUMBAI)
        assert ac <= ab + bc + 1e-6

    def test_missing_coordinates_returns_infinity(self):
        assert haversine_km(None, 77.0, 28.0, 77.0) == float("inf")  # type: ignore[arg-type]
        assert haversine_km(28.0, 77.0, 28.0, None) == float("inf")  # type: ignore[arg-type]


class TestGeoIndex:
    def setup_method(self):
        # Clustered around Delhi at increasing offsets (~0.009 deg lat ≈ 1 km)
        self.docs = [
            _branch("b0", 28.6139, 77.2090),            # 0 km
            _branch("b1", 28.6219, 77.2090),            # ~0.9 km
            _branch("b2", 28.6389, 77.2090),            # ~2.8 km
            _branch("b3", 28.6569, 77.2090),            # ~4.8 km
            _branch("b4", 28.7019, 77.2090),            # ~9.8 km
            _branch("b5", 19.0760, 72.8777),            # Mumbai, far away
        ]
        self.idx = GeoIndex(self.docs)

    def test_query_returns_sorted_nearest_first(self):
        res = self.idx.query(28.6139, 77.2090, 12)
        dists = [d for _, d in res]
        assert dists == sorted(dists)
        assert res[0][0]["id"] == "b0"

    def test_query_excludes_outside_radius(self):
        ids = {doc["id"] for doc, _ in self.idx.query(28.6139, 77.2090, 4)}
        assert ids == {"b0", "b1", "b2"}

    def test_counts_by_radius_are_monotonic(self):
        counts = self.idx.counts_by_radius(28.6139, 77.2090, [1, 3, 5, 10])
        assert counts[1] >= 1
        assert counts[1] <= counts[3] <= counts[5] <= counts[10]
        assert counts[10] == 5  # all Delhi-cluster docs, Mumbai excluded

    def test_counts_match_brute_force(self):
        lat, lng = 28.62, 77.21
        for r in (1, 3, 5, 10):
            brute = sum(1 for d in self.docs if haversine_km(lat, lng, d["lat"], d["lng"]) <= r)
            assert self.idx.counts_by_radius(lat, lng, [r])[r] == brute

    def test_nearest_matches_brute_force(self):
        lat, lng = 28.65, 77.22
        doc, dist = self.idx.nearest(lat, lng)
        brute = min(self.docs, key=lambda d: haversine_km(lat, lng, d["lat"], d["lng"]))
        assert doc is not None and doc["id"] == brute["id"]
        assert abs(dist - haversine_km(lat, lng, brute["lat"], brute["lng"])) < 1e-6

    def test_nearest_on_empty_index(self):
        doc, dist = GeoIndex([]).nearest(28.0, 77.0)
        assert doc is None and dist == float("inf")

    def test_query_on_empty_index(self):
        assert GeoIndex([]).query(28.0, 77.0, 50) == []

    def test_docs_missing_coordinates_are_skipped(self):
        idx = GeoIndex([{"id": "x", "lat": None, "lng": None}, _branch("y", 28.6139, 77.2090)])
        res = idx.query(28.6139, 77.2090, 5)
        assert [doc["id"] for doc, _ in res] == ["y"]

    def test_cross_cell_boundary_is_found(self):
        # place a doc just across a grid-cell edge; the 3x3 neighbourhood must still catch it
        base_lat = math.floor(28.6139 / CELL_DEG) * CELL_DEG
        idx = GeoIndex([_branch("edge", base_lat - 0.001, 77.2090)])
        res = idx.query(base_lat + 0.001, 77.2090, 2)
        assert len(res) == 1

    def test_alternate_key_names(self):
        idx = GeoIndex([{"id": "a", "latitude": 28.6139, "longitude": 77.2090}],
                       lat_key="latitude", lng_key="longitude")
        assert len(idx.query(28.6139, 77.2090, 1)) == 1


class TestCatchment:
    def setup_method(self):
        self.own = GeoIndex([_branch("own1", 28.6569, 77.2090)])          # ~4.8 km
        self.comp = GeoIndex([_branch("c1", 28.6219, 77.2090, "sbi"),     # ~0.9 km
                              _branch("c2", 28.6389, 77.2090, "icici")])  # ~2.8 km
        self.center = {"lat": 28.6139, "lng": 77.2090}

    def test_rings_are_monotonic_and_anchored_at_5km(self):
        out = catchment_summary(self.center, None, 100000, self.own, self.comp,
                                [1, 3, 5, 10], businesses=1000)
        rings = {r["radiusKm"]: r for r in out["rings"]}
        assert rings[5]["population"] == 100000           # 5 km is the anchor
        assert rings[1]["population"] < rings[3]["population"] < rings[5]["population"]
        assert rings[10]["population"] > rings[5]["population"]
        pops = [r["population"] for r in out["rings"]]
        assert pops == sorted(pops)

    def test_branch_counts_per_ring(self):
        out = catchment_summary(self.center, None, 100000, self.own, self.comp,
                                [1, 3, 5, 10], businesses=1000)
        rings = {r["radiusKm"]: r for r in out["rings"]}
        assert rings[1]["competitorBranches"] == 1
        assert rings[3]["competitorBranches"] == 2
        assert rings[1]["ownBranches"] == 0
        assert rings[10]["ownBranches"] == 1

    def test_headline_nearest_distances(self):
        out = catchment_summary(self.center, None, 100000, self.own, self.comp,
                                [1, 3, 5, 10], businesses=1000)
        assert 4.0 < out["nearestOwnKm"] < 5.5
        assert 0.5 < out["nearestCompetitorKm"] < 1.5
        assert out["ownBranches"] == 1 and out["competitorBranches"] == 2

    def test_empty_networks_report_none(self):
        out = catchment_summary(self.center, None, 50000, GeoIndex([]), GeoIndex([]),
                                [1, 5], businesses=0)
        assert out["nearestOwnKm"] is None
        assert out["nearestCompetitorKm"] is None
        assert out["ownBranches"] == 0 and out["competitorBranches"] == 0

    def test_zero_population_catchment(self):
        out = catchment_summary(self.center, None, 0, self.own, self.comp, [1, 5], businesses=0)
        assert all(r["population"] == 0 and r["businessDensity"] == 0 for r in out["rings"])
