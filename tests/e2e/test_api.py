"""End-to-End API integration tests using FastAPI TestClient.

See PROJECT_ROADMAP.md Task 11 & §5.
"""

import pytest
from fastapi.testclient import TestClient
from aegisflow.api.main import app
from aegisflow.api.deps import get_app_state


@pytest.fixture(scope="module")
def client():
    # Trigger lifespan startup
    state = get_app_state()
    state.load_all()
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["dataset_hours"] == 8760
    assert data["artifacts_ready"] is True


def test_meta_config_and_theorems(client):
    res = client.get("/api/meta/config")
    assert res.status_code == 200
    cfg = res.json()
    assert cfg["aum0"] == 3_000_000_000.0
    assert len(cfg["strategies"]) == 4

    th_res = client.get("/api/theorems")
    assert th_res.status_code == 200
    th = th_res.json()
    assert "theorem_1_overdraft_bridge" in th
    assert "theorem_2_equity_horizon" in th
    assert "theorem_3_bond_need_time" in th
    assert th["theorem_1_overdraft_bridge"]["ratio_cheaper"] > 20.0


def test_stream_tick(client):
    res = client.get("/api/stream/tick?index=100")
    assert res.status_code == 200
    tick = res.json()
    assert tick["index"] == 100
    assert "market" in tick
    assert "flows" in tick
    assert "strategies" in tick
    assert "aegisflow" in tick["strategies"]

    # At 17:00 (e.g. index 17), gatekeeper should be populated
    res_17 = client.get("/api/stream/tick?index=17")
    assert res_17.status_code == 200
    tick_17 = res_17.json()
    gk = tick_17["strategies"]["aegisflow"]["gatekeeper"]
    assert gk is not None
    assert "buffer_usd" in gk
    assert "night_drain_quantiles" in gk


def test_stream_range_and_validation(client):
    # Valid range
    res = client.get("/api/stream/range?from=0&to=10&stride=2")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 5
    assert len(data["ticks"]) == 5

    # Invalid range: from >= to
    bad_res = client.get("/api/stream/range?from=50&to=10")
    assert bad_res.status_code == 400
    err = bad_res.json()
    assert err["detail"]["error"]["code"] == "INVALID_RANGE"


def test_backtest_endpoints(client):
    # Compare
    res_comp = client.get("/api/backtest/compare")
    assert res_comp.status_code == 200
    comp = res_comp.json()
    assert "strategies" in comp
    assert "aegisflow" in comp["strategies"]
    assert "alpha_vs" in comp

    # Ablations
    res_abl = client.get("/api/backtest/ablations")
    assert res_abl.status_code == 200
    abl = res_abl.json()
    assert len(abl) == 4

    # Frontier
    res_fr = client.get("/api/backtest/frontier")
    assert res_fr.status_code == 200
    fr = res_fr.json()
    assert len(fr) > 0

    # Sensitivity
    res_sens = client.get("/api/backtest/sensitivity")
    assert res_sens.status_code == 200


def test_stress_testing_endpoints(client):
    # Presets
    res_pre = client.get("/api/simulate/presets")
    assert res_pre.status_code == 200
    presets = res_pre.json()
    assert "payday_squeeze" in presets["presets"]

    # Stress test run
    payload = {
        "aum0": 3_000_000_000.0,
        "shocks": {
            "withdrawal_multiplier": 1.4,
            "rate_shock_bps": 50.0,
        },
    }
    res_stress = client.post("/api/simulate/stress-test", json=payload)
    assert res_stress.status_code == 200
    stress_data = res_stress.json()
    assert "results" in stress_data
    assert "aegisflow" in stress_data["results"]
    assert "worst_nights" in stress_data


def test_audit_logs(client):
    res = client.get("/api/logs/decisions?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
