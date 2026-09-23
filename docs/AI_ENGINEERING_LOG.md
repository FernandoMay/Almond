# AI engineering log

## Delegated work

The project used bounded AI-agent work units with human review between them:

| Work unit | Delegated responsibility | Human supervision and validation |
| --- | --- | --- |
| Core vertical slice | Create the deterministic generator, demand engine, CP-SAT optimizer, verifier, economics, CLI, tests, and initial documentation. | Reviewed the returned artifacts, ran the test/demo commands, and required an independent verification pass. |
| Verification | Independently inspect the generated schedule and verifier behavior. | Accepted the finding that overlapping assignments were not rejected and required a focused correction. |
| Baseline/economics | Add a deterministic current schedule and schedule-derived Current vs Optimized economics. | Reviewed the negative savings result as an honest coverage tradeoff rather than accepting a fabricated 8\% claim. |
| Baseline hardening | Add overlap and unknown-employee diagnostics and remove an unsupported documentation claim. | Re-ran the full test suite and CLI before commit. |
| Peak/overtime/objective work unit | Add explicit deterministic peak marking and coverage, configurable objective weights, and regular/overtime economics. | Required separate peak metrics, overtime regression coverage, byte-identical CLI runs, and honest savings reporting. |
| Coverage-preserving baseline work unit | Replace the intentionally understaffed comparison with a configurable five-person, full-open fixed-floor policy; expose baseline regular/overtime metrics; and add the computed-savings acceptance test. | Required baseline coverage at or above demand, deterministic policy construction, schedule-derived economics, 100% optimized overall/peak coverage, and a fresh reproducible demo. |
| API product-surface work unit | Add the first FastAPI routes, shared seed-aware CLI composition, API tests, and runtime dependency metadata. | Required route-level determinism, CLI/API parity, normal 422 validation, and explicit documentation that UI, persistence, and deployment remain planned. |
| New-store optimization API work unit | Add typed validated `POST /v1/optimize` input, immutable scenario translation, shared application composition, behavior tests, and contract documentation. | Required duplicate/empty input rejection, deterministic custom scenarios, successful independent verification, exact current metrics, and explicit planned boundaries. |
| File ingestion/export work unit | Add stateless JSON/CSV adapters and deterministic optimized-schedule CSV exports over the existing validated API. | Required malformed-file and CSV contract rejection, JSON/CSV parity, repeated-output equality, exact schemas, and explicit planned persistence/auth/UI/deployment/async boundaries. |
| Operational CLI work unit | Add the local `almond optimize` command for JSON files and complete CSV bundles, with optional deterministic result JSON and optimized schedule CSV outputs while preserving no-argument demo behavior. | Required `main(argv)` and user-visible tests for both input forms, byte-identical repeated outputs, concise malformed-input failures, exact help/examples, current metrics, and two-pass report verification. |

The human owner retained authority over product scope, modeling assumptions, acceptance of findings, commit boundaries, and repository delivery. Agents did not commit or push changes.

## Human validation boundaries

The human owner must validate legal interpretation, service-time assumptions, wage data, operational availability rules, and any production use of schedules. Passing automated tests is not legal or payroll approval.

## Decisive solver prompt

“Given hourly demand and employee availability, choose binary hourly assignments that minimize MXN labor cost plus uncovered-demand penalty. Enforce availability, at most one contiguous interval per employee per day, and no more than 40 weekly hours. Return a schedule that an independent verifier can inspect.”

## Current work-unit decisions

The demo marks the explicit midday interval `[12:00, 16:00)` as peak. Peak coverage is modeled as a hard constraint when the model is feasible; an infeasible hard peak model is retried with bounded shortage slack, which remains visible and receives the peak objective weight. Objective weights are scenario data: labor `1`, normal shortage `10000`, and peak shortage `20000`. Overtime pricing uses a configurable weekly threshold and multiplier, while the optimizer's 40-hour weekly cap remains hard.

The current-policy assumption is a fixed five-person floor for every opening hour `[08:00, 18:00)`, rotated by day across the generated employees. It is explicit configuration, preserves availability and contiguous shifts, and is not selected from the savings target. In the seed-40 demo it creates 350 scheduled hours, 109 overstaffed person-hours, and 70 overtime hours. With the configured overtime rule, its cost is 26,950 MXN versus 16,402 MXN optimized, producing 39.14% computed savings. The challenge target is only the scenario acceptance threshold (>=8%); it is deliberately absent from the solver objective and cost formula.

The API work unit adds `GET /health`, `GET /v1/demo`, and `POST /v1/optimize/demo`. Both demo routes call `cli.run_demo(seed)`, so seed-controlled reproducibility and the CLI result shape are shared rather than reimplemented. The API is a local product surface; no deployment, persistence, or UI claim is made.

The current new-store work unit adds `POST /v1/optimize`. Its Pydantic contract requires non-empty employees and demand, unique employee IDs, unique demand `(day, hour)` slots, explicit required staff, bounded availability, and a bounded opening horizon. The request is translated once into immutable `Scenario` data and passed to `run_scenario`, which is also used by the CLI and demo routes. The endpoint adds only stable scenario metadata to the existing result shape. Persistence, file upload, authentication, UI, and deployment remain planned.

The current file workflow adds reusable `io.py` adapters for UTF-8 JSON and exact-header CSV files. CSV rows are translated into the same `OptimizeRequest` and `Scenario` path; the adapters do not duplicate solver or economics logic. Schedule exports sort rows by day, start, end, and employee ID and emit only `employee_id,day,start,end,hours`. Persistence, authentication, UI, deployment, and asynchronous job storage remain planned.

The operational CLI work unit preserves `almond` with no arguments as the seed-40 JSON demo and adds `almond optimize`. JSON input uses `parse_json_bytes`; the complete CSV bundle uses `parse_csv_bundle`; both then use `OptimizeRequest`, `build_scenario`, and `run_scenario_with_schedule`. Optional `--result-json` and `--schedule-csv` outputs are deterministic; absent result output is printed to stdout. The CLI is synchronous and local, not an API client, persistence boundary, authorization boundary, or asynchronous job runner.
