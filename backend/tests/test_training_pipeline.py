"""Training-pipeline tests — panel generation, CSV ingestion, dataset build, model endpoints."""

import os

import pytest
from data_pipeline.performance.ingest_csv import parse_rows
from lib.model_features import FEATURE_ORDER, competitive_balance, to_vector

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "branchiq-admin-2026")


class TestFeatureContract:
    def test_vector_length_matches_feature_order(self):
        assert len(to_vector({})) == len(FEATURE_ORDER)

    def test_missing_and_none_values_use_fallbacks(self):
        vec = to_vector({"nearestOwnKm": None})
        assert all(isinstance(v, float) for v in vec)
        assert vec[FEATURE_ORDER.index("nearestOwnKm")] == 8.0

    def test_supplied_values_are_passed_through(self):
        vec = to_vector({"catchmentPop": 123456, "compWithin5": 9})
        assert vec[FEATURE_ORDER.index("catchmentPop")] == 123456.0
        assert vec[FEATURE_ORDER.index("compWithin5")] == 9.0

    def test_competitive_balance_peaks_mid_competition(self):
        assert competitive_balance(7) == 100.0
        assert competitive_balance(0) < competitive_balance(4) < competitive_balance(7)
        assert competitive_balance(25) == 0.0


class TestCsvIngestion:
    def _rows(self, **over):
        row = {"branch_id": "br-1", "bank": "HDFC Bank", "fiscal_year": "FY2024-25",
               "deposits_cr": "210.5", "advances_cr": "150", "accounts": "18000",
               "source": "Annual report", "source_url": "https://example.org"}
        row.update(over)
        return [row]

    def test_valid_row_is_normalized(self):
        docs, errors = parse_rows(self._rows())
        assert errors == []
        d = docs[0]
        assert d["branchId"] == "br-1" and d["depositsCr"] == 210.5 and d["advancesCr"] == 150.0
        assert d["businessCr"] == 360.5
        assert d["sourceType"] == "official"

    def test_missing_required_column_is_rejected(self):
        docs, errors = parse_rows(self._rows(deposits_cr=""))
        assert docs == [] and "missing deposits_cr" in errors[0]

    def test_non_numeric_value_is_rejected(self):
        docs, errors = parse_rows(self._rows(advances_cr="n/a"))
        assert docs == [] and "not numeric" in errors[0]

    def test_negative_values_are_rejected(self):
        docs, errors = parse_rows(self._rows(deposits_cr="-5"))
        assert docs == [] and "negative" in errors[0]

    def test_duplicate_branch_year_is_flagged(self):
        rows = self._rows() + self._rows(deposits_cr="300")
        docs, errors = parse_rows(rows)
        assert len(docs) == 2 and any("duplicate" in e for e in errors)

    def test_comma_separated_numbers_and_case_insensitive_headers(self):
        docs, errors = parse_rows([{"BRANCH_ID": "br-2", "Bank": "SBI", "Fiscal_Year": "FY2023-24",
                                    "Deposits_Cr": "1,200.25", "Advances_Cr": "900"}])
        assert errors == [] and docs[0]["depositsCr"] == 1200.25

    def test_empty_file(self):
        assert parse_rows([]) == ([], [])


class TestModelApi:
    @pytest.fixture(scope="class")
    def client_m(self):
        import httpx

        from tests.conftest import API_URL
        with httpx.Client(base_url=API_URL, timeout=180.0) as c:
            yield c

    def test_training_data_summary(self, client_m):
        r = client_m.get("/model/training-data")
        assert r.status_code == 200
        body = r.json()
        assert body["rows"] > 0 and body["branches"] > 0
        assert body["fiscalYears"]
        assert body["rowsBySourceType"]

    def test_model_info_reports_trained_artifact(self, client_m):
        r = client_m.get("/model/info")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in {"trained", "heuristic"}
        if body["status"] == "trained":
            assert body["metrics"]["rocAuc"] >= 0.5
            assert len(body["featureImportances"]) == len(FEATURE_ORDER)
            assert abs(sum(f["importancePct"] for f in body["featureImportances"]) - 100) < 1.5
            assert body["disclaimer"]

    def test_training_requires_valid_admin_token(self, client_m):
        assert client_m.post("/model/train", json={"adminToken": "wrong"}).status_code == 401
        assert client_m.post("/model/train", json={}).status_code == 422

    def test_prediction_uses_trained_model_when_available(self, client_m):
        info = client_m.get("/model/info").json()
        state = client_m.get("/states").json()[0]
        ranked = client_m.get("/locations/ranked",
                              params={"state_id": state["id"], "bank": "hdfc-bank", "limit": 3}).json()
        assert ranked
        detail = client_m.get(f"/location/{ranked[0]['id']}", params={"bank": "hdfc-bank"}).json()
        pred = detail["mlPrediction"]
        assert 0 <= pred["probability"] <= 100
        assert pred["contributions"]
        if info["status"] == "trained":
            assert "XGBoost" in pred["modelType"]
            assert len(pred["contributions"]) == len(FEATURE_ORDER)

    def test_admin_endpoint_trains_and_returns_metrics(self, client_m):
        r = client_m.post("/model/train", json={"adminToken": ADMIN_TOKEN})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "trained"
        assert 0.0 <= body["metrics"]["rocAuc"] <= 1.0
        assert body["trainingRows"] >= 40
        assert body["featureImportances"]
