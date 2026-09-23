from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_release_gate_declares_required_stages_and_artifacts():
    script = (ROOT / "scripts" / "verify.sh").read_text()

    for command in (
        ".venv/bin/pytest -q",
        "npm run test:e2e",
        "node --check web/app.js",
        ".venv/bin/almond",
        "pdflatex -interaction=nonstopmode -halt-on-error",
        "ALMOND VERIFY: PASS",
    ):
        assert command in script

    for artifact in (
        "Makefile",
        "README.md",
        "scripts/verify.sh",
        "scripts/docker-verify.sh",
        "package.json",
        "package-lock.json",
        "playwright.config.mjs",
        "e2e/dashboard.spec.mjs",
        "src/almond/api.py",
        "web/app.js",
        "Dockerfile",
        "tests/test_api.py",
        "docs/ALMOND_TECHNICAL_REPORT.tex",
        "docs/DEMO_SCRIPT.md",
        "docs/RELEASE_CHECKLIST.md",
    ):
        assert artifact in script


def test_docker_gate_has_explicit_unavailable_boundary():
    script = (ROOT / "scripts" / "docker-verify.sh").read_text()

    assert "docker: command not found" in script
    assert '"${COMPOSE[@]}" config' in script
    assert '"${COMPOSE[@]}" build' in script
    assert '"${COMPOSE[@]}" up -d' in script
    assert '"${COMPOSE[@]}" down' in script
    assert "ALMOND DOCKER VERIFY: PASS" in script


def test_docker_gate_registers_cleanup_and_bounded_readiness_before_probe():
    script = (ROOT / "scripts" / "docker-verify.sh").read_text()

    cleanup_registration = script.index("trap cleanup EXIT")
    compose_start = script.index('"${COMPOSE[@]}" up -d')
    readiness_poll = script.index("for ((attempt = 1; attempt <= 30; attempt++))")
    health_probe = script.index('"${COMPOSE[@]}" exec -T almond')

    assert cleanup_registration < compose_start
    assert readiness_poll < health_probe
    assert "ps --format '{{.State}} {{.Health}}' almond" in script
    assert "sleep 1" in script
    assert "Docker service did not become ready within 30 seconds" in script
