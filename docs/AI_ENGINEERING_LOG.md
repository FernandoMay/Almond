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

The human owner retained authority over product scope, modeling assumptions, acceptance of findings, commit boundaries, and repository delivery. Agents did not commit or push changes.

## Human validation boundaries

The human owner must validate legal interpretation, service-time assumptions, wage data, operational availability rules, and any production use of schedules. Passing automated tests is not legal or payroll approval.

## Decisive solver prompt

“Given hourly demand and employee availability, choose binary hourly assignments that minimize MXN labor cost plus uncovered-demand penalty. Enforce availability, at most one contiguous interval per employee per day, and no more than 40 weekly hours. Return a schedule that an independent verifier can inspect.”

## Current work-unit decisions

The demo marks the explicit midday interval `[12:00, 16:00)` as peak. Peak coverage is modeled as a hard constraint when the model is feasible; an infeasible hard peak model is retried with bounded shortage slack, which remains visible and receives the peak objective weight. Objective weights are scenario data: labor `1`, normal shortage `10000`, and peak shortage `20000`. Overtime pricing uses a configurable weekly threshold and multiplier, while the optimizer's 40-hour weekly cap remains hard.

The current-policy assumption is a fixed five-person floor for every opening hour `[08:00, 18:00)`, rotated by day across the generated employees. It is explicit configuration, preserves availability and contiguous shifts, and is not selected from the savings target. In the seed-40 demo it creates 350 scheduled hours, 109 overstaffed person-hours, and 70 overtime hours. With the configured overtime rule, its cost is 26,950 MXN versus 16,402 MXN optimized, producing 39.14% computed savings. The challenge target is only the scenario acceptance threshold (>=8%); it is deliberately absent from the solver objective and cost formula.

The API work unit adds `GET /health`, `GET /v1/demo`, and `POST /v1/optimize/demo`. Both demo routes call `cli.run_demo(seed)`, so seed-controlled reproducibility and the CLI result shape are shared rather than reimplemented. The API is a local product surface; no deployment, persistence, or UI claim is made.
