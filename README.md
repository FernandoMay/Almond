# Almond

Almond is the backend/core-engine MVP for Jornada40: it turns hourly demand into an explainable workforce schedule.

## Setup and run

```bash
python -m pip install -e "."
python -m pytest -q
python -m almond
```

The demo is generated from seed `40`; all costs are calculated from generated assignments and employee rates. The console output is JSON with MXN economics, coverage, violations, and constraint evaluations.

## Architecture

`models.py` contains typed domain objects. `generator.py` creates deterministic data; `demand.py` derives staffing need; `baseline.py` creates a transparent full-open comparison; `optimizer.py` solves the hourly CP-SAT model; `verifier.py` independently checks schedules; `economics.py` compares costs; `explain.py` exposes constraint results; `cli.py` composes the vertical slice.

## Limitations

This MVP models one role, integer hourly demand, fixed hourly rates, and a single contiguous interval per employee per day. It does not yet model breaks, skills, overtime premiums, absences, payroll, persistence, or a UI. Uncovered demand is reported rather than silently accepted.

## AI-first engineering notes

The implementation is deliberately small, deterministic, and independently verified. Generated artifacts are English. Solver output is never trusted without the verifier, and the demo savings figure is computed rather than asserted.
