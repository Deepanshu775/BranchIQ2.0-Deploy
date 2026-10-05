"""Scoring engine tests — whitespace, cannibalization, location score, decision bands (PRD §29)."""

import copy

import pytest
from lib import scoring


def base_features(**overrides) -> dict:
    f = {
        "marketGrowth": 70.0,
        "creditGrowthPct": 12.0,
        "depositGrowthPct": 11.0,
        "digitalReadiness": 72.0,
        "urbanization": 65.0,
        "customerPotential": 70.0,
        "catchmentPop": 120000.0,
        "businessCount": 1200.0,
        "nearestOwnKm": 8.0,
        "ownWithin3": 0,
        "ownWithin5": 0,
        "nearestCompKm": 1.5,
        "compWithin1": 1,
        "compWithin3": 3,
        "compWithin5": 5,
        "compWithin10": 8,
        "tier": "Tier 2",
        "operatingCostIndex": 0.5,
        "accessibility": 0.8,
    }
    f.update(overrides)
    return f


class TestConfig:
    def test_location_weights_sum_to_one(self):
        assert abs(sum(scoring.CONFIG["location_score_weights"].values()) - 1.0) < 1e-6

    def test_state_weights_sum_to_one(self):
        assert abs(sum(scoring.CONFIG["state_score_weights"].values()) - 1.0) < 1e-6

    def test_thresholds_are_configurable_not_hardcoded(self):
        for key in ("decision_bands", "cannibalization_bands_km", "whitespace", "penalties"):
            assert key in scoring.CONFIG

    def test_clamp_bounds(self):
        assert scoring.clamp(-20) == 0.0
        assert scoring.clamp(180) == 100.0
        assert scoring.clamp(55) == 55.0


class TestWhitespace:
    def test_absent_own_network_scores_higher_than_adjacent_branch(self):
        far = scoring.whitespace_score(70, None, 0, 5)
        near = scoring.whitespace_score(70, 0.5, 2, 5)
        assert far > near

    def test_increases_with_distance_from_own_branch(self):
        scores = [scoring.whitespace_score(70, km, 0, 5) for km in (0.5, 2, 5, 8)]
        assert scores == sorted(scores)

    def test_increases_with_demand(self):
        assert scoring.whitespace_score(30, 6, 0, 5) < scoring.whitespace_score(90, 6, 0, 5)

    def test_excessive_competition_depresses_score(self):
        threshold = scoring.CONFIG["whitespace"]["competitor_too_many_threshold"]
        assert scoring.whitespace_score(70, 6, 0, threshold + 5) < scoring.whitespace_score(70, 6, 0, 4)

    def test_some_competition_beats_none(self):
        assert scoring.whitespace_score(70, 6, 0, 3) > scoring.whitespace_score(70, 6, 0, 0)

    def test_stays_in_0_100(self):
        for demand in (0, 50, 100):
            for km in (None, 0.0, 50.0):
                for comp in (0, 5, 40):
                    assert 0 <= scoring.whitespace_score(demand, km, 0, comp) <= 100


class TestCannibalization:
    def test_no_own_branch_is_zero_penalty(self):
        out = scoring.cannibalization_risk(None, 0)
        assert out["risk"] == "NONE" and out["penalty"] == 0 and out["nearestOwnKm"] is None

    def test_under_two_km_is_high(self):
        out = scoring.cannibalization_risk(1.2, 1)
        assert out["risk"] == "HIGH" and out["penalty"] > 0

    def test_two_to_five_km_is_medium(self):
        assert scoring.cannibalization_risk(3.5, 0)["risk"] == "MEDIUM"

    def test_beyond_five_km_is_low_or_none(self):
        assert scoring.cannibalization_risk(9.0, 0)["risk"] in {"LOW", "NONE"}

    def test_penalty_is_monotonically_non_increasing_with_distance(self):
        penalties = [scoring.cannibalization_risk(km, 0)["penalty"] for km in (0.5, 3.0, 7.0, 30.0)]
        assert penalties == sorted(penalties, reverse=True)

    def test_overlapping_own_branches_increase_high_risk_penalty(self):
        one = scoring.cannibalization_risk(1.0, 1)["penalty"]
        three = scoring.cannibalization_risk(1.0, 3)["penalty"]
        assert three > one

    def test_overlap_bonus_is_capped(self):
        assert scoring.cannibalization_risk(1.0, 3)["penalty"] == scoring.cannibalization_risk(1.0, 99)["penalty"]


class TestLocationScore:
    def test_shape_and_bounds(self):
        out = scoring.location_score(base_features())
        assert 0 <= out["score"] <= 100
        assert len(out["breakdown"]) == len(scoring.CONFIG["location_score_weights"])
        assert out["decision"]["label"]
        assert "cannibalization" in out and "whitespaceScore" in out

    def test_breakdown_weights_match_config(self):
        out = scoring.location_score(base_features())
        w = scoring.CONFIG["location_score_weights"]
        for row in out["breakdown"]:
            assert row["weight"] == w[row["key"]]
            assert 0 <= row["score"] <= 100
            assert row["label"]

    def test_base_score_equals_weighted_sum_of_components(self):
        out = scoring.location_score(base_features())
        assert abs(out["baseScore"] - round(sum(r["weighted"] for r in out["breakdown"]))) <= 1

    def test_final_score_is_base_minus_penalties(self):
        out = scoring.location_score(base_features(nearestOwnKm=1.0, ownWithin3=2))
        assert out["totalPenalty"] > 0
        assert out["score"] == max(0, min(100, round(out["baseScore"] - out["totalPenalty"])))

    def test_strong_market_outranks_weak_market(self):
        strong = scoring.location_score(base_features())["score"]
        weak = scoring.location_score(base_features(
            marketGrowth=25, creditGrowthPct=6, depositGrowthPct=6, customerPotential=25,
            catchmentPop=9000, businessCount=40, digitalReadiness=30,
            urbanization=20, accessibility=0.3))["score"]
        assert strong > weak

    def test_nearby_own_branch_lowers_score(self):
        far = scoring.location_score(base_features(nearestOwnKm=9.0))["score"]
        near = scoring.location_score(base_features(nearestOwnKm=0.8, ownWithin3=2, ownWithin5=2))["score"]
        assert near < far

    def test_high_demand_high_competition_beats_low_demand_high_competition(self):
        hi = scoring.location_score(base_features(compWithin5=9, marketGrowth=88, customerPotential=88))
        lo = scoring.location_score(base_features(compWithin5=9, marketGrowth=30, customerPotential=30))
        comp_hi = next(r["score"] for r in hi["breakdown"] if r["key"] == "competitiveOpportunity")
        comp_lo = next(r["score"] for r in lo["breakdown"] if r["key"] == "competitiveOpportunity")
        assert comp_hi > comp_lo

    def test_saturation_penalty_applies_on_dense_small_catchment(self):
        out = scoring.location_score(base_features(catchmentPop=4000, compWithin5=25, ownWithin5=3))
        assert any(p["label"] == "Market Saturation" for p in out["penalties"])

    def test_operating_cost_penalty_grows_with_cost_index(self):
        cheap = scoring.location_score(base_features(operatingCostIndex=0.1))
        pricey = scoring.location_score(base_features(operatingCostIndex=1.0))
        assert pricey["totalPenalty"] > cheap["totalPenalty"]

    def test_zero_and_extreme_inputs_stay_in_range(self):
        zeros = base_features(marketGrowth=0, creditGrowthPct=0, depositGrowthPct=0,
                              digitalReadiness=0, urbanization=0, customerPotential=0,
                              catchmentPop=0, businessCount=0, accessibility=0.0,
                              nearestOwnKm=0.0, ownWithin3=5, ownWithin5=5,
                              compWithin5=50, operatingCostIndex=1.0)
        extremes = base_features(marketGrowth=100, creditGrowthPct=40, depositGrowthPct=40,
                                 digitalReadiness=100, urbanization=100, customerPotential=100,
                                 catchmentPop=5_000_000, businessCount=100000, accessibility=1.0,
                                 nearestOwnKm=None, ownWithin3=0, ownWithin5=0,
                                 compWithin5=0, operatingCostIndex=0.0)
        for f in (zeros, extremes):
            out = scoring.location_score(f)
            assert 0 <= out["score"] <= 100
            assert all(0 <= r["score"] <= 100 for r in out["breakdown"])

    def test_is_deterministic(self):
        f = base_features()
        assert scoring.location_score(copy.deepcopy(f)) == scoring.location_score(copy.deepcopy(f))

    def test_branches_per_10k_pop_is_computed(self):
        out = scoring.location_score(base_features(catchmentPop=100000, compWithin5=5, ownWithin5=5))
        assert out["branchesPer10kPop"] == pytest.approx(1.0, abs=0.01)


class TestDecisionBands:
    @pytest.mark.parametrize("score", [0, 20, 49, 50, 64, 65, 79, 80, 89, 90, 100])
    def test_every_score_maps_to_a_band(self, score):
        band = scoring.decision_for_location_score(score)
        assert band["label"] and band["color"]

    def test_bands_are_ordered_by_score(self):
        labels = [scoring.decision_for_location_score(s)["label"] for s in (95, 85, 70, 55, 20)]
        assert len(set(labels)) == 5

    def test_never_uses_imperative_language(self):
        for band in scoring.CONFIG["decision_bands"]:
            assert "must" not in band["label"].lower()

    def test_priority_labels(self):
        assert scoring.priority_for_score(95).startswith("P1")
        assert scoring.priority_for_score(85).startswith("P2")
        assert scoring.priority_for_score(70).startswith("P3")
        assert scoring.priority_for_score(55).startswith("P4")
        assert scoring.priority_for_score(10).startswith("P5")

    def test_state_bands_cover_full_range(self):
        for s in (100, 75, 50, 0):
            assert scoring.decision_for_state_score(s)["label"]


class TestEvidence:
    def test_returns_between_five_and_seven_labelled_points(self):
        f = base_features()
        scored = scoring.location_score(f)
        loc = {"catchmentPop": 120000, "catchmentRadiusKm": 5, "siteType": "High Street"}
        ev = scoring.evidence_points(loc, f, scored, "HDFC")
        assert 5 <= len(ev) <= 7
        assert all(e["text"] and e["type"] for e in ev)

    def test_handles_absent_own_branch_and_missing_catchment(self):
        f = base_features(nearestOwnKm=None, nearestCompKm=None, ownWithin3=0)
        scored = scoring.location_score(f)
        ev = scoring.evidence_points({}, f, scored, "SBI")
        assert len(ev) >= 5
        assert any("No SBI branch recorded" in e["text"] for e in ev)


class TestBlendedScore:
    def test_weights_sum_to_one_and_score_is_the_weighted_mix(self):
        out = scoring.blend_scores(80, 60, "HIGH")
        assert abs(out["businessWeight"] + out["mlWeight"] - 1.0) < 1e-6
        assert out["branchIQScore"] == round(80 * out["businessWeight"] + 60 * out["mlWeight"])
        assert out["businessScore"] == 80 and out["mlProbability"] == 60

    def test_lower_confidence_shrinks_the_ml_weight(self):
        weights = [scoring.blend_scores(80, 20, lvl)["mlWeight"]
                   for lvl in ("HIGH", "MEDIUM", "LOW", "INSUFFICIENT")]
        assert weights == sorted(weights, reverse=True)
        assert weights[-1] == 0.0

    def test_insufficient_confidence_falls_back_to_business_score(self):
        out = scoring.blend_scores(73, 99, "INSUFFICIENT")
        assert out["branchIQScore"] == 73 and out["delta"] == 0

    def test_delta_sign_follows_the_model(self):
        assert scoring.blend_scores(60, 95, "HIGH")["delta"] > 0
        assert scoring.blend_scores(90, 20, "HIGH")["delta"] < 0

    def test_decision_band_matches_the_blended_score(self):
        out = scoring.blend_scores(95, 95, "HIGH")
        assert out["decision"] == {k: v for k, v in
                                   scoring.decision_for_location_score(out["branchIQScore"]).items()
                                   if k in ("label", "color")}
        assert out["priority"].startswith("P")

    def test_score_stays_in_range_and_note_is_explanatory(self):
        for business, ml in ((0, 0), (100, 100), (0, 100), (100, 0)):
            out = scoring.blend_scores(business, ml, "MEDIUM")
            assert 0 <= out["branchIQScore"] <= 100
            assert "business score" in out["note"]

    def test_unknown_confidence_level_is_handled(self):
        out = scoring.blend_scores(70, 70, "unknown-level")
        assert 0 <= out["branchIQScore"] <= 100
