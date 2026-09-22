# Almond

Almond is the backend/core-engine MVP for Jornada40: it turns hourly demand into an explainable workforce schedule.

## Setup and run

```bash
python -m pip install -e "."
python -m pytest -q
python -m almond
```

The demo is generated from seed `40`; peak buckets are the explicit midday window `[12:00, 16:00)`. All costs are calculated from generated assignments and employee rates. The current comparison is a deterministic rotating 08:00–16:00 schedule from the same employees and availability, not a fully open schedule. The console output is JSON with current-versus-optimized MXN economics, separate peak coverage, violations, objective weights, overtime settings, and constraint evaluations.

## Architecture

`models.py` contains typed domain objects. `generator.py` creates deterministic data and the current schedule; `demand.py` derives staffing need; `baseline.py` analyzes the current schedule; `optimizer.py` solves the hourly CP-SAT model; `verifier.py` independently checks schedules; `economics.py` compares schedule-derived costs and coverage; `explain.py` exposes constraint results; `cli.py` composes the vertical slice.

## Limitations

This MVP models one role, integer hourly demand, fixed hourly rates, explicit peak buckets, and a single contiguous interval per employee per day. It prices arbitrary schedules with configurable regular-hour thresholds and overtime multipliers; the optimized schedule retains a hard 40-hour weekly cap. Breaks, skills, absences, payroll, persistence, and a UI remain out of scope. Uncovered demand is reported rather than silently accepted.

## AI-first engineering notes

The implementation is deliberately small, deterministic, and independently verified. Generated artifacts are English. Solver output is never trusted without the verifier, and the demo savings figure is computed rather than asserted.
