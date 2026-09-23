# Architecture

The engine is a functional pipeline: deterministic scenario → demand calculation → explicit fixed-floor baseline and CP-SAT optimization → independent verification → economics and explanations → CLI/API JSON.

Domain dataclasses are immutable and do not depend on OR-Tools. Only `optimizer.py` imports CP-SAT. This keeps the verifier independent of solver decisions and makes model behavior testable. The optimization objective uses explicit labor, normal-shortage, and peak-shortage weights, subject to availability, contiguous daily intervals, explicit peak coverage, and a hard 40-hour weekly cap.

## Product surface

`api.py` is the FastAPI boundary. `GET /health` returns the stable `ok` status and API version `v1`. `GET /v1/demo` and `POST /v1/optimize/demo` call `cli.run_demo(seed)`; `POST /v1/optimize` validates a new-store request, builds immutable domain objects, and calls `cli.run_scenario(scenario)`. Thus CLI, demo API, and new-store API share solver, verification, economics, and explanation composition rather than duplicating route logic. The new endpoint returns demo-compatible result fields plus scenario metadata. UI, persistence, file upload, authentication, and deployment are planned, not implemented.
