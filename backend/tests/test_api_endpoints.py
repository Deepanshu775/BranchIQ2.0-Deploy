"""API endpoint tests against the live backend — catalog, geo queries, ranking, scoring, errors."""

import pytest


@pytest.fixture(scope="module")
def ids(client_mod):
    bank = client_mod.get("/banks").json()[0]
    state = client_mod.get("/states").json()[0]
    districts = client_mod.get("/districts", params={"state_id": state["id"]}).json()
    cities = client_mod.get("/cities", params={"district_id": districts[0]["id"]}).json()
    return {"bank": bank, "state": state, "district": districts[0],
            "city": cities[0] if cities else None}


@pytest.fixture(scope="module")
def client_mod():
    import httpx

    from tests.conftest import API_URL
    with httpx.Client(base_url=API_URL, timeout=60.0) as c:
        yield c


class TestCatalog:
    def test_banks(self, client_mod):
        r = client_mod.get("/banks")
        assert r.status_code == 200
        banks = r.json()
        assert len(banks) >= 9
        assert {"id", "name"} <= set(banks[0])

    def test_states(self, client_mod):
        r = client_mod.get("/states")
        assert r.status_code == 200
        assert len(r.json()) >= 20

    def test_districts_filtered_by_state(self, client_mod, ids):
        r = client_mod.get("/districts", params={"state_id": ids["state"]["id"]})
        assert r.status_code == 200
        rows = r.json()
        assert rows and all(d["stateId"] == ids["state"]["id"] for d in rows)

    def test_cities_filtered_by_district(self, client_mod, ids):
        r = client_mod.get("/cities", params={"district_id": ids["district"]["id"]})
        assert r.status_code == 200
        assert all(c["districtId"] == ids["district"]["id"] for c in r.json())

    def test_unknown_state_returns_empty_list(self, client_mod):
        r = client_mod.get("/districts", params={"state_id": "no-such-state"})
        assert r.status_code == 200 and r.json() == []


class TestBranchesAndCompetitors:
    def test_branches_paginated(self, client_mod, ids):
        r = client_mod.get("/branches", params={"bank": ids["bank"]["id"], "limit": 5})
        assert r.status_code == 200
        page = r.json()
        assert len(page["items"]) <= 5
        assert page["total"] >= len(page["items"])

    def test_branch_filter_applies(self, client_mod, ids):
        r = client_mod.get("/branches", params={"bank": ids["bank"]["id"],
                                                "district_id": ids["district"]["id"], "limit": 20})
        assert r.status_code == 200
        for b in r.json()["items"]:
            assert b["bankId"] == ids["bank"]["id"]
            assert b["districtId"] == ids["district"]["id"]

    def test_competitors_near_point(self, client_mod, ids):
        d = ids["district"]
        r = client_mod.get("/competitors", params={"lat": d["lat"], "lng": d["lng"],
                                                   "radius_km": 10,
                                                   "exclude_bank": ids["bank"]["id"]})
        assert r.status_code == 200
        body = r.json()
        assert body["radiusKm"] == 10.0
        assert body["center"]["lat"] == pytest.approx(d["lat"])
        for g in body["groups"]:
            assert g["count"] >= 1 and g["nearestKm"] <= 10.001
            assert ids["bank"]["short"] not in g["bankShort"]

    def test_competitors_radius_is_monotonic(self, client_mod, ids):
        d = ids["district"]
        small = client_mod.get("/competitors", params={"lat": d["lat"], "lng": d["lng"], "radius_km": 2}).json()
        big = client_mod.get("/competitors", params={"lat": d["lat"], "lng": d["lng"], "radius_km": 25}).json()
        assert big["total"] >= small["total"]

    def test_missing_required_params_is_422(self, client_mod):
        assert client_mod.get("/competitors").status_code == 422


class TestOpportunities:
    def test_states_ranked_descending(self, client_mod, ids):
        r = client_mod.get("/opportunities/states", params={"bank": ids["bank"]["id"]})
        assert r.status_code == 200
        scores = [row["score"] for row in r.json()]
        assert scores == sorted(scores, reverse=True)
        assert all(0 <= s <= 100 for s in scores)

    def test_districts_ranked_descending(self, client_mod, ids):
        r = client_mod.get("/opportunities/districts",
                           params={"state_id": ids["state"]["id"], "bank": ids["bank"]["id"]})
        assert r.status_code == 200
        rows = r.json()
        assert rows
        assert [x["overall"] for x in rows] == sorted((x["overall"] for x in rows), reverse=True)
        row = rows[0]
        assert row["ownBranches"] + row["competitorBranches"] == row["totalBranches"]

    def test_cities_ranked(self, client_mod, ids):
        r = client_mod.get("/opportunities/cities",
                           params={"district_id": ids["district"]["id"], "bank": ids["bank"]["id"]})
        assert r.status_code == 200
        rows = r.json()
        assert [x["overall"] for x in rows] == sorted((x["overall"] for x in rows), reverse=True)

    def test_market_overview(self, client_mod, ids):
        r = client_mod.get(f"/market/{ids['district']['id']}")
        assert r.status_code == 200
        assert r.json()

    def test_unknown_market_is_404(self, client_mod):
        assert client_mod.get("/market/does-not-exist").status_code == 404


class TestLocations:
    @pytest.fixture(scope="class")
    def ranked(self, client_mod, ids):
        r = client_mod.get("/locations/ranked",
                           params={"state_id": ids["state"]["id"], "bank": ids["bank"]["id"], "limit": 10})
        assert r.status_code == 200
        rows = r.json()
        assert rows, "seeded dataset should yield candidate locations"
        return rows

    def test_ranked_sorted_and_bounded(self, ranked):
        scores = [x["score"] for x in ranked]
        assert scores == sorted(scores, reverse=True)
        assert all(0 <= s <= 100 for s in scores)

    def test_ranked_rows_carry_geospatial_evidence(self, ranked):
        row = ranked[0]
        for key in ("pincode", "lat", "lng", "decision", "district", "city"):
            assert key in row

    def test_location_detail(self, client_mod, ranked, ids):
        r = client_mod.get(f"/location/{ranked[0]['id']}", params={"bank": ids["bank"]["id"]})
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == ranked[0]["id"]
        assert body["evidence"]
        assert body["dataConfidence"]

    def test_location_score_breakdown_is_transparent(self, client_mod, ranked, ids):
        r = client_mod.get(f"/location/{ranked[0]['id']}/score", params={"bank": ids["bank"]["id"]})
        assert r.status_code == 200
        body = r.json()
        assert len(body["breakdown"]) == 9
        assert abs(sum(w["weight"] for w in body["breakdown"]) - 1.0) < 1e-6
        assert 0 <= body["score"] <= 100

    def test_catchment_rings_are_monotonic(self, client_mod, ranked, ids):
        r = client_mod.get(f"/location/{ranked[0]['id']}/catchment", params={"bank": ids["bank"]["id"]})
        assert r.status_code == 200
        rings = r.json()["rings"]
        assert [x["population"] for x in rings] == sorted(x["population"] for x in rings)
        assert [x["competitorBranches"] for x in rings] == sorted(x["competitorBranches"] for x in rings)

    def test_unknown_location_is_404(self, client_mod):
        assert client_mod.get("/location/nope-123").status_code == 404
        assert client_mod.get("/location/nope-123/score").status_code == 404
        assert client_mod.get("/location/nope-123/catchment").status_code == 404


class TestSourcesAndQuality:
    def test_source_registry(self, client_mod):
        r = client_mod.get("/sources")
        assert r.status_code == 200
        rows = r.json()
        assert rows
        first = rows[0] if isinstance(rows, list) else rows["sources"][0]
        assert "organization" in first and "confidence" in first

    def test_scoring_config_is_exposed(self, client_mod):
        r = client_mod.get("/scoring-config")
        assert r.status_code == 200
        cfg = r.json()
        assert abs(sum(cfg["location_score_weights"].values()) - 1.0) < 1e-6

    def test_data_quality_dashboard(self, client_mod):
        r = client_mod.get("/quality")
        assert r.status_code == 200
        body = r.json()
        assert body["branchCount"] > 0
        assert "issues" in body


class TestBlendedScoreApi:
    def test_ranked_rows_expose_the_blend(self, client_mod, ids):
        rows = client_mod.get("/locations/ranked",
                              params={"state_id": ids["state"]["id"], "bank": ids["bank"]["id"],
                                      "limit": 5}).json()
        assert rows
        b = rows[0]["blended"]
        assert b["businessScore"] == rows[0]["score"]
        assert b["mlProbability"] == rows[0]["mlProbability"]
        assert 0 <= b["branchIQScore"] <= 100
        assert abs(b["businessWeight"] + b["mlWeight"] - 1.0) < 1e-6

    def test_detail_and_score_endpoints_agree_on_the_blend(self, client_mod, ids):
        rows = client_mod.get("/locations/ranked",
                              params={"state_id": ids["state"]["id"], "bank": ids["bank"]["id"],
                                      "limit": 1}).json()
        lid = rows[0]["id"]
        detail = client_mod.get(f"/location/{lid}", params={"bank": ids["bank"]["id"]}).json()
        score = client_mod.get(f"/location/{lid}/score", params={"bank": ids["bank"]["id"]}).json()
        assert detail["blended"] == score["blended"]
        assert detail["blended"]["confidenceLevel"] == detail["confidence"]["level"]
        assert detail["blended"]["decision"]["label"]
        assert detail["blended"]["note"]
