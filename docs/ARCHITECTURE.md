# Architecture

The engine is a functional pipeline: deterministic scenario → demand calculation → explicit fixed-floor baseline and CP-SAT optimization → independent verification → economics and explanations → CLI/API JSON.

Domain dataclasses are immutable and do not depend on OR-Tools. Only `optimizer.py` imports CP-SAT. This keeps the verifier independent of solver decisions and makes model behavior testable. The optimization objective uses explicit labor, normal-shortage, and peak-shortage weights, subject to availability, contiguous daily intervals, explicit peak coverage, and a hard 40-hour weekly cap.

## Product surface

`api.py` is the FastAPI boundary. JSON and CSV routes delegate parsing to `io.py`, validate through `OptimizeRequest`, build immutable domain objects, and call the same `cli.run_scenario` composition. The `almond optimize` CLI reads those same files, validates and translates them through the same request path, then writes deterministic result JSON and optimized schedule CSV without an API call. `io.py` has no optimization or economics logic. `run_scenario_with_schedule` adds presentation-ready `optimized_schedule` rows and `hourly_coverage` rows to the shared result, derived from verified analysis and sorted deterministically. The API serves `web/index.html` at `GET /` and `/static` assets; `web/app.js` fetches result JSON and renders it without domain or solver logic. Thus CLI, demo API, file ingestion, new-store API, and dashboard share solver, verification, economics, and explanation composition rather than duplicating route logic. Persistence, authentication, deployment, asynchronous job storage, and production hardening are planned, not implemented.
