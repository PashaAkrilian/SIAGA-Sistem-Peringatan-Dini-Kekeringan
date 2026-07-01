"""
test_api.py — Tes dasar untuk memastikan endpoint backend berperilaku benar.
Jalankan dengan:  pytest
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_metrics_shape():
    r = client.get("/api/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "test" in body and "train" in body
    assert 0 <= body["test"]["r2"] <= 1


def test_forecast_peak_is_2026():
    r = client.get("/api/forecast")
    assert r.status_code == 200
    body = r.json()
    assert body["peak_month"].startswith("2026")
    assert len(body["data"]) == 12


def test_islands_all_eight():
    r = client.get("/api/islands")
    assert r.status_code == 200
    islands = r.json()
    assert len(islands) == 8
    for isl in islands:
        assert isl["status"] in {"normal", "warning", "extreme"}


def test_historical_valid_island():
    r = client.get("/api/historical?island=Jawa")
    assert r.status_code == 200
    assert r.json()["island"] == "Jawa"
    assert len(r.json()["data"]) > 100


def test_historical_invalid_island():
    r = client.get("/api/historical?island=Atlantis")
    assert r.status_code == 400


def test_simulation_monotonic():
    """Skenario pemanasan lebih agresif harus menghasilkan proyeksi lebih kering."""
    mild = client.get("/api/simulate?oni_increment=0.05").json()
    harsh = client.get("/api/simulate?oni_increment=0.35").json()
    assert harsh["peak_score_median"] < mild["peak_score_median"]


def test_feature_importance():
    r = client.get("/api/feature-importance")
    assert r.status_code == 200
    body = r.json()
    assert len(body["shap"]) > 0
    assert len(body["gain"]) > 0
