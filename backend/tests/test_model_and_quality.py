"""Prediction layer + data-quality validation tests (PRD §19, §31, §29)."""

from datetime import datetime, timedelta, timezone

from data_pipeline.validate import (
    find_duplicate_branches,
    quality_report,
    validate_coords,
    validate_pin,
)
from lib import ml_model


def ml_features(**overrides) -> dict:
    f = {"catchmentPop": 60000, "creditGrowthPct": 14.0, "depositGrowthPct": 12.0,
         "businessCount": 45, "urbanization": 78.0, "bankWhitespace": 70.0,
         "digitalReadiness": 75.0, "nearestOwnKm": 6.0, "competitiveBalance": 70.0}
    f.update(overrides)
    return f


class TestHeuristicModel:
    def test_typical_market_is_near_fifty_percent(self):
        out = ml_model.heuristic_predict(ml_features())
        assert 45 <= out["probability"] <= 65

    def test_probability_in_range_and_labelled_as_model_prediction(self):
        out = ml_model.heuristic_predict(ml_features())
        assert 0 <= out["probability"] <= 100
        assert "MODEL PREDICTION" in out["modelType"]

    def test_strong_market_scores_above_weak_market(self):
        strong = ml_model.heuristic_predict(ml_features(catchmentPop=140000, creditGrowthPct=22,
                                              depositGrowthPct=20, bankWhitespace=95))
        weak = ml_model.heuristic_predict(ml_features(catchmentPop=8000, creditGrowthPct=6,
                                            depositGrowthPct=5, bankWhitespace=20))
        assert strong["probability"] > weak["probability"]

    def test_does_not_saturate_at_one_hundred(self):
        out = ml_model.heuristic_predict(ml_features(catchmentPop=10_000_000, creditGrowthPct=90,
                                           depositGrowthPct=90, businessCount=9999,
                                           urbanization=100, bankWhitespace=100,
                                           digitalReadiness=100, nearestOwnKm=100,
                                           competitiveBalance=100))
        assert out["probability"] < 100

    def test_contributions_cover_every_feature_and_are_sorted(self):
        out = ml_model.heuristic_predict(ml_features())
        assert len(out["contributions"]) == len(ml_model.FEATURE_SPECS)
        vals = [c["contribution"] for c in out["contributions"]]
        assert vals == sorted(vals, reverse=True)

    def test_contribution_percentages_sum_to_about_hundred(self):
        out = ml_model.heuristic_predict(ml_features(catchmentPop=90000, creditGrowthPct=18))
        total = sum(c["contributionPct"] for c in out["contributions"])
        assert abs(total - 100.0) < 1.0

    def test_missing_features_default_to_zero_without_error(self):
        out = ml_model.heuristic_predict({})
        assert 0 <= out["probability"] <= 100

    def test_is_deterministic(self):
        assert ml_model.heuristic_predict(ml_features()) == ml_model.heuristic_predict(ml_features())


class TestValidatePin:
    def test_valid_pin(self):
        assert validate_pin("250001") is None

    def test_wrong_length_or_non_numeric(self):
        for bad in ("25001", "2500011", "abcdef", "", "25 001"):
            assert validate_pin(bad) is not None

    def test_none_is_invalid(self):
        assert validate_pin(None) is not None  # type: ignore[arg-type]

    def test_invalid_first_digit(self):
        assert validate_pin("050001") is not None
        assert validate_pin("950001") is not None

    def test_degenerate_pin(self):
        assert validate_pin("111111") is not None


class TestValidateCoords:
    def test_valid_indian_coordinates(self):
        assert validate_coords(28.6139, 77.2090) is None

    def test_missing_coordinates(self):
        assert validate_coords(None, 77.0) == "missing coordinates"
        assert validate_coords(28.0, None) == "missing coordinates"

    def test_nan_coordinates(self):
        assert validate_coords(float("nan"), 77.0) == "NaN coordinates"

    def test_outside_india_bounding_box(self):
        assert validate_coords(51.5, -0.12) is not None   # London
        assert validate_coords(0.0, 0.0) is not None


class TestDuplicateBranches:
    def _b(self, bid, lat, lng, bank="hdfc"):
        return {"id": bid, "name": bid, "lat": lat, "lng": lng, "bankId": bank,
                "pincode": "250001", "districtId": "d1"}

    def test_detects_same_bank_colocated_branches(self):
        dups = find_duplicate_branches([self._b("a", 28.6139, 77.2090),
                                        self._b("b", 28.6140, 77.2091)])
        assert len(dups) == 1
        assert {dups[0]["a"], dups[0]["b"]} == {"a", "b"}

    def test_different_banks_at_same_spot_are_not_duplicates(self):
        dups = find_duplicate_branches([self._b("a", 28.6139, 77.2090, "hdfc"),
                                        self._b("b", 28.6139, 77.2090, "sbi")])
        assert dups == []

    def test_distant_same_bank_branches_are_not_duplicates(self):
        dups = find_duplicate_branches([self._b("a", 28.6139, 77.2090),
                                        self._b("b", 28.9845, 77.7064)])
        assert dups == []

    def test_branches_missing_coordinates_are_skipped(self):
        dups = find_duplicate_branches([{"id": "a", "lat": None, "lng": None, "bankId": "hdfc"},
                                        self._b("b", 28.6139, 77.2090)])
        assert dups == []

    def test_empty_input(self):
        assert find_duplicate_branches([]) == []


class TestQualityReport:
    def _good(self):
        return {"id": "b1", "name": "Meerut Main", "lat": 28.98, "lng": 77.70,
                "pincode": "250001", "districtId": "d1", "bankId": "hdfc",
                "lastVerified": datetime.now(timezone.utc).isoformat()}

    def test_clean_dataset_reports_no_issues(self):
        rep = quality_report([self._good()], [{"id": "p1", "pin": "250001"}])
        assert rep["branchCount"] == 1 and rep["pinAreaCount"] == 1
        assert all(v == 0 for v in rep["issues"].values())

    def test_flags_each_issue_class(self):
        bad_coords = {**self._good(), "id": "b2", "lat": 51.5, "lng": -0.12}
        bad_pin = {**self._good(), "id": "b3", "pincode": "99"}
        no_district = {**self._good(), "id": "b4", "districtId": None}
        stale = {**self._good(), "id": "b5", "lastVerified":
                 (datetime.now(timezone.utc) - timedelta(days=3000)).isoformat()}
        dup = {**self._good(), "id": "b6"}
        rep = quality_report([self._good(), bad_coords, bad_pin, no_district, stale, dup],
                             [{"id": "p1", "pin": "000000"}])
        iss = rep["issues"]
        assert iss["invalidCoordinates"] >= 1
        assert iss["invalidPincodes"] >= 2        # branch pin + locality pin
        assert iss["missingDistrict"] >= 1
        assert iss["staleRecords"] >= 1
        assert iss["duplicateBranches"] >= 1
        assert rep["details"]

    def test_missing_last_verified_counts_as_stale(self):
        doc = {k: v for k, v in self._good().items() if k != "lastVerified"}
        assert quality_report([doc], [])["issues"]["staleRecords"] == 1

    def test_empty_dataset(self):
        rep = quality_report([], [])
        assert rep["branchCount"] == 0 and all(v == 0 for v in rep["issues"].values())
