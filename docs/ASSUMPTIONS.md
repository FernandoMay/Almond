# Assumptions

- The demonstration has one generic employee role and seven modeled days.
- Demand is calculated as ceiling(visitor count × service minutes / 60), with eight service minutes by default.
- Employees have fixed hourly rates; arbitrary schedules use a configurable overtime threshold and multiplier, while optimized schedules retain a hard 40-hour cap. Breaks are not modeled.
- Availability is an inclusive start and exclusive end window.
- A schedule can contain at most one contiguous interval per employee per day.
- Objective weights are explicit scenario data: labor cost, normal shortage, and peak shortage. A feasible model hard-covers peak buckets; infeasible peak coverage falls back to bounded, visible shortage, and the verifier still reports it separately.
- The current-policy baseline is an explicit configurable assumption: five employees are kept on the floor from 08:00 through 18:00 every day, selected by deterministic round-robin rotation. It is intended to model an observed fixed-floor operating policy, not to back-solve the acceptance target. Removing the fixed floor would change the comparison and its measured inefficiency.
- The baseline may exceed the optimizer's 40-hour cap. Its hours are still analyzed with the configured 40-hour regular threshold and 1.5 overtime multiplier, and weekly-hour violations remain visible rather than being hidden.
- The challenge acceptance target is at least 8% computed savings with valid optimized coverage. It is a scenario-level test criterion, not an implementation assumption or a solver objective term.
- The new-store API accepts explicit required staff rather than recalculating it from visitors; visitors remain explanatory input. Request keys are validated at the HTTP boundary, then translated into immutable domain records.
- The reproducibility boundary is the complete JSON request or the three exact-schema CSV files plus horizon fields and fixed CP-SAT settings (`num_search_workers=1`, `random_seed=40`); identical inputs must produce identical JSON and schedule CSV. Persistence, authentication, UI, deployment, and asynchronous job storage remain planned.
