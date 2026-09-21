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

## 6. Daily Contiguity

The current implementation models each employee's scheduled hours for a day as one contiguous interval.

At most one daily start variable is permitted. A later worked hour requires either continuity from the preceding hour or a start at that hour.

This prevents a schedule such as:

`09:00–10:00 + 15:00–16:00`

from being represented as one employee's modeled daily interval.

## 7. Objective Function

The current MVP minimizes:

`labor_cost + uncovered_demand_penalty`

where:

`labor_cost = Σ(e,d,h) x[e,d,h] × hourly_cost[e]`

and uncovered demand receives a large penalty.

The current implementation uses a penalty coefficient of `10000`.

This means coverage is prioritized before labor cost in the current demo model.

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
- schedule validity;
- cost consistency.

Future verifier checks will additionally cover:

- peak coverage;
- economic savings;
- baseline comparison;
- configurable shift rules.

## 11. Planned Objective Extensions

The following are deliberately not claimed as implemented by the current solver model. They are planned extensions required for the full challenge solution:

1. explicit peak-hour coverage constraints;
2. baseline/current-schedule comparison;
3. overtime economics;
4. overstaffing measurement;
5. schedule-change penalties;
6. configurable shift lengths and breaks;
7. configurable objective weights;
8. economic savings calculation in MXN.

These extensions must preserve the hard constraints above.

## 12. Design Principle

The optimizer is responsible for finding a candidate schedule.

The verifier is responsible for determining whether the candidate is valid.

The economics layer is responsible for determining whether the candidate creates measurable financial impact.

The UI must never infer validity or savings independently from these domain components.
