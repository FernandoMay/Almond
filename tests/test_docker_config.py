from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_docker_demo_contract_is_static_and_local_only():
    dockerfile = (ROOT / "Dockerfile").read_text()
    compose = (ROOT / "docker-compose.yml").read_text()
    dockerignore = (ROOT / ".dockerignore").read_text()
    makefile = (ROOT / "Makefile").read_text()

    assert "FROM python:3.12-slim" in dockerfile
    assert "pip install ." in dockerfile
    assert "USER almond" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    assert "/health" in dockerfile
    assert "services:" in compose
    assert "8000:8000" in compose
    assert 'restart: "no"' in compose
    assert "/health" in compose
    assert ".venv/" in dockerignore
    assert "node_modules/" in dockerignore
    assert ".env" in dockerignore
    assert "docker compose up --build" in makefile
    assert "docker compose down" in makefile

    for forbidden in ("postgres", "mysql", "sqlite", "volume:", "deploy:"):
        assert forbidden not in compose.lower()
