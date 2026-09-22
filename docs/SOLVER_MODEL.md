# Almond — Solver Model

## 1. Purpose

This document defines the mathematical model implemented by the Almond scheduling engine. It is intentionally aligned with the current CP-SAT implementation and distinguishes hard feasibility constraints from optimization objectives.

## 2. Decision Variables

For employee `e`, day `d`, and modeled hour `h`:

`x[e,d,h] ∈ {0,1}`

`x[e,d,h] = 1` means employee `e` is scheduled during hour `h` on day `d`.

For each modeled demand bucket:

`u[d,h] ≥ 0`

`u[d,h]` represents uncovered demand. It is bounded by the demand value for that bucket.

Each demand point also carries an explicit boolean `peak` marker. The demo marks the documented interval `[12:00, 16:00)` as peak.

## 3. Weekly Hours

For every employee:

`H[e] = Σ(d,h) x[e,d,h]`

The current MVP enforces:

`H[e] ≤ 40`

This is a hard constraint.

## 4. Availability

If hour `h` is outside employee `e`'s availability window on day `d`:

`x[e,d,h] = 0`

Availability is therefore a hard feasibility constraint.

## 5. Hourly Coverage

For every modeled demand bucket:

`Σe x[e,d,h] + u[d,h] ≥ R[d,h]`

where:

- `R[d,h]` = required demand/staffing for the bucket;
- `u[d,h]` = uncovered demand.

The current implementation permits an infeasible coverage requirement to be represented explicitly through `u`, rather than silently producing an invalid schedule.

For every peak bucket, the optimizer first adds `Σe x[e,d,h] ≥ R[d,h]` as a hard constraint. If that model is infeasible, it deterministically rebuilds the model with bounded `u[d,h]` slack. The verifier and baseline expose peak coverage and peak violations separately.

## 6. Daily Contiguity

The current implementation models each employee's scheduled hours for a day as one contiguous interval.

At most one daily start variable is permitted. A later worked hour requires either continuity from the preceding hour or a start at that hour.

This prevents a schedule such as:

`09:00–10:00 + 15:00–16:00`

from being represented as one employee's modeled daily interval.

## 7. Objective Function

The current MVP minimizes:

`w_labor × labor_cost + w_normal × normal_uncovered + w_peak × peak_uncovered`

where:

`labor_cost = Σ(e,d,h) x[e,d,h] × hourly_cost[e]`

where the scenario carries explicit deterministic weights. Defaults are `w_labor = 1`, `w_normal = 10000`, and `w_peak = 20000`; peak shortage is penalized more strongly than normal shortage.

This means coverage is prioritized before labor cost in the current demo model while preserving a visible distinction for peak shortage.

## 8. Solver Configuration

The current implementation uses OR-Tools CP-SAT.

For deterministic demo execution it currently configures:

- `num_search_workers = 1`
- `random_seed = 40`

The exact solver status is recorded as `OPTIMAL` or `FEASIBLE` when a valid result is returned.

## 9. Schedule Reconstruction

After solving, each employee's selected hourly variables are converted into an `Assignment` containing:

- employee ID;
- day;
- start hour;
- end hour.

The resulting schedule is subsequently passed to the verifier.

## 10. Independent Verification

The solver result must not be treated as sufficient evidence by itself.

The verifier independently checks the resulting schedule for:

- weekly hours;
- availability;
- coverage;
- peak coverage and peak violations;
- schedule validity.

## 11. Overtime economics

The optimizer retains the hard 40-hour weekly cap, while economics can analyze arbitrary schedules. For configured threshold `T` and multiplier `m`:

`regular[e] = min(H[e], T)`

`overtime[e] = max(H[e] - T, 0)`

`cost[e] = regular[e] × rate[e] + overtime[e] × rate[e] × m`

The defaults are `T = 40` and `m = 1.5`. Overtime is reported per employee for baseline and optimized schedules.

## 12. Remaining Objective Extensions

The following remain planned extensions:

1. schedule-change penalties;
2. configurable shift lengths and breaks.

The baseline layer now provides a deterministic current schedule and measures
its schedule-derived cost, coverage, peak coverage, understaffing, overstaffing,
availability, and weekly-hour violations. The economics layer compares those
values with the optimized schedule using the same hourly cost rules and reports
regular versus overtime hours.

These extensions must preserve the hard constraints above.

## 12. Design Principle

The optimizer is responsible for finding a candidate schedule.

The verifier is responsible for determining whether the candidate is valid.

The economics layer is responsible for determining whether the candidate creates measurable financial impact.

The UI must never infer validity or savings independently from these domain components.
