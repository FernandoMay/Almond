# Architecture

The engine is a functional pipeline: deterministic scenario → demand calculation → explicit fixed-floor baseline and CP-SAT optimization → independent verification → economics and explanations → CLI/API JSON.

Domain dataclasses are immutable and do not depend on OR-Tools. Only `optimizer.py` imports CP-SAT. This keeps the verifier independent of solver decisions and makes model behavior testable. The optimization objective uses explicit labor, normal-shortage, and peak-shortage weights, subject to availability, contiguous daily intervals, explicit peak coverage, and a hard 40-hour weekly cap.

## Product surface

`api.py` is the FastAPI boundary. JSON and CSV routes delegate parsing to `io.py`, validate through `OptimizeRequest`, build immutable domain objects, and call the same `cli.run_scenario` composition. `io.py` has no optimization or economics logic. Schedule export uses the shared scenario execution path and serializes only the optimized `Schedule` in deterministic order. Thus CLI, demo API, file ingestion, and new-store API share solver, verification, economics, and explanation composition rather than duplicating route logic. UI, persistence, authentication, deployment, and asynchronous job storage are planned, not implemented.
