from fastapi.testclient import TestClient

from almond.api import app
from almond.cli import run_demo


client = TestClient(app)


MINIMAL_PAYLOAD = {
    "employees": [
        {"id": "A1", "hourly_rate_mxn": 100, "availability": {"0": {"start": 8, "end": 10}}}
    ],
    "demand": [{"day": 0, "hour": 8, "visitors": 8, "required_staff": 1}],
    "horizon": {"days": 1, "opening_hour": 8, "closing_hour": 10},
    "baseline_policy": {"staffing_floor": 1, "shift_start": 8, "shift_end": 10},
}


def test_health_returns_stable_status_and_api_version():
    assert client.get("/health").json() == {"status": "ok", "api_version": "v1"}


def test_get_demo_returns_default_deterministic_result():
    first = client.get("/v1/demo")
    second = client.get("/v1/demo")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


def test_post_demo_uses_default_seed_and_is_deterministic():
    first = client.post("/v1/optimize/demo", json={})
    second = client.post("/v1/optimize/demo", json={})

    assert first.json() == second.json() == run_demo()


def test_post_demo_custom_seed_is_deterministic():
    first = client.post("/v1/optimize/demo", json={"seed": 7})
    second = client.post("/v1/optimize/demo", json={"seed": 7})

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json() == run_demo(7)


def test_post_demo_rejects_invalid_seed():
    response = client.post("/v1/optimize/demo", json={"seed": -1})

    assert response.status_code == 422


def test_get_demo_matches_cli_composition():
    assert client.get("/v1/demo").json() == run_demo()


def test_optimize_accepts_minimal_feasible_store_and_is_deterministic():
    first = client.post("/v1/optimize", json=MINIMAL_PAYLOAD)
    second = client.post("/v1/optimize", json=MINIMAL_PAYLOAD)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["optimized"]["violations"] == []
    assert first.json()["scenario"]["opening_hours"] == {"start": 8, "end": 10}


def test_optimize_rejects_duplicate_employee_ids():
    payload = {**MINIMAL_PAYLOAD, "employees": MINIMAL_PAYLOAD["employees"] * 2}
    assert client.post("/v1/optimize", json=payload).status_code == 422


def test_optimize_rejects_duplicate_demand_slots():
    payload = {**MINIMAL_PAYLOAD, "demand": MINIMAL_PAYLOAD["demand"] * 2}
    assert client.post("/v1/optimize", json=payload).status_code == 422


def test_optimize_rejects_missing_or_empty_domain_data():
    assert client.post("/v1/optimize", json={}).status_code == 422
    assert client.post("/v1/optimize", json={**MINIMAL_PAYLOAD, "employees": []}).status_code == 422
    assert client.post("/v1/optimize", json={**MINIMAL_PAYLOAD, "demand": []}).status_code == 422


def test_custom_scenario_returns_verified_deterministic_result():
    payload = {
        "employees": [
            {"id": "A1", "hourly_rate_mxn": 100, "availability": {"0": {"start": 8, "end": 10}}},
            {"id": "A2", "hourly_rate_mxn": 120, "availability": {"0": {"start": 8, "end": 10}}},
        ],
        "demand": [
            {"day": 0, "hour": 8, "visitors": 8, "required_staff": 1, "peak": True},
            {"day": 0, "hour": 9, "visitors": 8, "required_staff": 1, "peak": True},
        ],
        "horizon": {"days": 1, "opening_hour": 8, "closing_hour": 10},
        "baseline_policy": {"staffing_floor": 1, "shift_start": 8, "shift_end": 10},
    }
    response = client.post("/v1/optimize", json=payload)
    assert response.status_code == 200
    assert response.json()["optimized"]["violations"] == []
    assert response.json()["optimized"]["peak_coverage_violations"] == []
