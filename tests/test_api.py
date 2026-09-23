from fastapi.testclient import TestClient
import json

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


def test_dashboard_and_static_assets_are_served_without_changing_api_routes():
    page = client.get("/")
    assert page.status_code == 200
    assert "Almond optimization desk" in page.text
    assert "Run demo" in page.text
    assert "Upload JSON scenario" in page.text
    assert "/static/app.js" in page.text
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/health").json() == {"status": "ok", "api_version": "v1"}
    assert client.get("/v1/demo").status_code == 200


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


def test_json_file_success_and_malformed_input():
    success = client.post("/v1/optimize/json-file", files={"file": ("scenario.json", json.dumps(MINIMAL_PAYLOAD), "application/json")})
    direct = client.post("/v1/optimize", json=MINIMAL_PAYLOAD)
    assert success.status_code == 200
    assert success.json() == direct.json()

    malformed = client.post("/v1/optimize/json-file", files={"file": ("scenario.json", "{bad", "application/json")})
    wrong_extension = client.post("/v1/optimize/json-file", files={"file": ("scenario.txt", "{}", "text/plain")})
    assert malformed.status_code == wrong_extension.status_code == 400


def _csv_files():
    return {
        "employees": ("employees.csv", "id,hourly_rate_mxn\nA1,100\n", "text/csv"),
        "availability": ("availability.csv", "employee_id,day,start,end\nA1,0,8,10\n", "text/csv"),
        "demand": ("demand.csv", "day,hour,visitors,required_staff,peak\n0,8,8,1,false\n", "text/csv"),
    }


def test_csv_bundle_success_validation_and_deterministic_output():
    fields = {"days": "1", "opening_hour": "8", "closing_hour": "10"}
    first = client.post("/v1/optimize/csv", files=_csv_files(), data=fields)
    second = client.post("/v1/optimize/csv", files=_csv_files(), data=fields)
    assert first.status_code == second.status_code == 200
    assert first.json() == client.post("/v1/optimize", json=MINIMAL_PAYLOAD).json()
    assert first.content == second.content

    invalid = _csv_files()
    invalid["availability"] = ("availability.csv", "employee_id,day,start,end\nUNKNOWN,0,8,10\n", "text/csv")
    assert client.post("/v1/optimize/csv", files=invalid, data=fields).status_code == 400


def test_csv_bundle_rejects_extra_row_field_with_client_error():
    files = _csv_files()
    files["employees"] = ("employees.csv", "id,hourly_rate_mxn\nA1,100,unexpected\n", "text/csv")

    response = client.post(
        "/v1/optimize/csv",
        files=files,
        data={"days": "1", "opening_hour": "8", "closing_hour": "10"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "employees.csv contains extra columns; each row must match the exact schema"


def test_schedule_exports_have_stable_csv_contract():
    demo = client.get("/v1/demo/schedule.csv")
    assert demo.status_code == 200
    assert demo.headers["content-type"].startswith("text/csv")
    assert demo.text.splitlines()[0] == "employee_id,day,start,end,hours"
    assert len(demo.text.splitlines()) > 1

    exported = client.post("/v1/optimize/schedule.csv", json=MINIMAL_PAYLOAD)
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    assert exported.text.splitlines()[0] == "employee_id,day,start,end,hours"
