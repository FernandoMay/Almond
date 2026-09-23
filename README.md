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
- `POST /v1/optimize` — accepts a validated new-store scenario and returns the same result shape plus a `scenario` metadata block. Employees have unique IDs, non-negative MXN hourly rates, and bounded per-day availability windows. Demand buckets use unique `day`/`hour` slots and explicit `required_staff` values.
- `POST /v1/optimize/json-file` — accepts one `.json` upload containing the documented `OptimizeRequest` object and applies the same validation and scenario path.
- `POST /v1/optimize/csv` — accepts `employees.csv`, `availability.csv`, and `demand.csv` multipart uploads plus `days`, `opening_hour`, and `closing_hour` form fields. Exact headers are `id,hourly_rate_mxn`, `employee_id,day,start,end`, and `day,hour,visitors,required_staff,peak`; peak values are `true` or `false`.
- `GET /v1/demo/schedule.csv` and `POST /v1/optimize/schedule.csv` — export only the optimized schedule as deterministic `text/csv` with header `employee_id,day,start,end,hours`.

Example request:

```json
{
  "employees": [{"id": "A1", "hourly_rate_mxn": 100, "availability": {"0": {"start": 8, "end": 10}}}],
  "demand": [{"day": 0, "hour": 8, "visitors": 8, "required_staff": 1}],
  "horizon": {"days": 1, "opening_hour": 8, "closing_hour": 10},
  "baseline_policy": {"staffing_floor": 1, "shift_start": 8, "shift_end": 10}
}
```

Objective weights, overtime settings, and baseline policy are optional. The endpoint rejects empty domain collections, duplicate employee IDs, duplicate demand slots, and values outside the modeled horizon with `422`. The endpoint translates the request into immutable domain objects and uses the same baseline, optimizer, verifier, economics, and explanation path as the CLI and demo API. Repeating the same request is deterministic.

Uploaded files are statelessly parsed; duplicate IDs/slots, unknown employees, missing headers, empty files, invalid ranges, malformed JSON, and wrong extensions are rejected with clear 4xx responses. Repeating the same input produces the same result and schedule bytes. The API is a local/runtime surface only. Persistence, authentication, UI, deployment, and asynchronous job storage remain planned; no deployment topology is implemented or implied.

## Architecture

`models.py` contains typed domain objects. `generator.py` creates deterministic data and the current schedule; `demand.py` derives staffing need; `baseline.py` analyzes the current schedule; `optimizer.py` solves the hourly CP-SAT model; `verifier.py` independently checks schedules; `economics.py` compares schedule-derived costs and coverage; `explain.py` exposes constraint results; `io.py` parses uploads and serializes schedule CSV; `cli.py` composes the vertical slice; `api.py` exposes the versioned HTTP boundary by calling that same composition.

## Limitations

This MVP models one role, integer hourly demand, fixed hourly rates, explicit peak buckets, and a single contiguous interval per employee per day. It prices arbitrary schedules with configurable regular-hour thresholds and overtime multipliers; the optimized schedule retains a hard 40-hour weekly cap. Breaks, skills, absences, payroll, persistence, authentication, UI, deployment, and asynchronous job storage remain planned. Uncovered demand is reported rather than silently accepted.

## AI-first engineering notes

The implementation is deliberately small, deterministic, and independently verified. Generated artifacts are English. Solver output is never trusted without the verifier, and the demo savings figure is computed rather than asserted.
