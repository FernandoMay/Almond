from fastapi.testclient import TestClient

from almond.api import app
from almond.cli import run_demo


client = TestClient(app)


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
