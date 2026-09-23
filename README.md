# Almond

Almond is the backend/core-engine MVP for Jornada40: it turns hourly demand into an explainable workforce schedule.

## Setup and run

```bash
python -m pip install -e "."
python -m pytest -q
python -m almond
# Optional local API
.venv/bin/almond-api
```

The demo is generated from seed `40`; peak buckets are the explicit midday window `[12:00, 16:00)`. All costs are calculated from generated assignments and employee rates. The current comparison is a configurable deterministic policy: a five-person fixed staffing floor works 08:00–18:00 every day, with round-robin rotation across the same employees and availability. This assumption provides full demand coverage but deliberately measures the overstaffing and overtime of a rigid operating policy. The console output is JSON with current-versus-optimized MXN economics, regular/overtime hours, separate peak coverage, violations, objective weights, overtime settings, and constraint evaluations.

For seed `40`, the current policy costs 26,950 MXN, covers 100% overall and at peak, records 109 overstaffed person-hours and 70 overtime hours, and exposes seven weekly-hour policy violations. The optimized schedule costs 16,402 MXN, also covers 100% overall and at peak, and has no verifier violations. The schedule-derived savings are 10,548 MXN or 39.14%. The 8% figure is the challenge acceptance target; it is not an optimizer input or a hardcoded output.

## API

The first FastAPI product surface is implemented and reuses the CLI composition path. Run `.venv/bin/almond-api` (or `uvicorn almond.api:app`) for local development. It exposes:

- `GET /health` — returns `{"status":"ok","api_version":"v1"}`.
- `GET /v1/demo` — returns the deterministic seed-40 result in the same JSON shape as `almond`.
- `POST /v1/optimize/demo` — accepts an optional non-negative integer `seed` (default `40`) and returns the same result shape. Invalid request bodies use normal FastAPI `422` responses.

The API is a local/runtime surface only. UI, persistence, authentication, and deployment remain planned; no deployment topology is implemented or implied.

## Architecture

`models.py` contains typed domain objects. `generator.py` creates deterministic data and the current schedule; `demand.py` derives staffing need; `baseline.py` analyzes the current schedule; `optimizer.py` solves the hourly CP-SAT model; `verifier.py` independently checks schedules; `economics.py` compares schedule-derived costs and coverage; `explain.py` exposes constraint results; `cli.py` composes the vertical slice; `api.py` exposes the versioned HTTP boundary by calling that same composition.

## Limitations

This MVP models one role, integer hourly demand, fixed hourly rates, explicit peak buckets, and a single contiguous interval per employee per day. It prices arbitrary schedules with configurable regular-hour thresholds and overtime multipliers; the optimized schedule retains a hard 40-hour weekly cap. Breaks, skills, absences, payroll, persistence, and a UI remain out of scope. Uncovered demand is reported rather than silently accepted.

## AI-first engineering notes

The implementation is deliberately small, deterministic, and independently verified. Generated artifacts are English. Solver output is never trusted without the verifier, and the demo savings figure is computed rather than asserted.
