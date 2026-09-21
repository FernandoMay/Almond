# AI engineering log

## Delegated work

The project used bounded AI-agent work units with human review between them:

| Work unit | Delegated responsibility | Human supervision and validation |
| --- | --- | --- |
| Core vertical slice | Create the deterministic generator, demand engine, CP-SAT optimizer, verifier, economics, CLI, tests, and initial documentation. | Reviewed the returned artifacts, ran the test/demo commands, and required an independent verification pass. |
| Verification | Independently inspect the generated schedule and verifier behavior. | Accepted the finding that overlapping assignments were not rejected and required a focused correction. |
| Baseline/economics | Add a deterministic current schedule and schedule-derived Current vs Optimized economics. | Reviewed the negative savings result as an honest coverage tradeoff rather than accepting a fabricated 8\% claim. |
| Baseline hardening | Add overlap and unknown-employee diagnostics and remove an unsupported documentation claim. | Re-ran the full test suite and CLI before commit. |

The human owner retained authority over product scope, modeling assumptions, acceptance of findings, commit boundaries, and repository delivery. Agents did not commit or push changes.

## Human validation boundaries

The human owner must validate legal interpretation, service-time assumptions, wage data, operational availability rules, and any production use of schedules. Passing automated tests is not legal or payroll approval.

## Decisive solver prompt

“Given hourly demand and employee availability, choose binary hourly assignments that minimize MXN labor cost plus uncovered-demand penalty. Enforce availability, at most one contiguous interval per employee per day, and no more than 40 weekly hours. Return a schedule that an independent verifier can inspect.”
