# Assumptions

- The demonstration has one generic employee role and seven modeled days.
- Demand is calculated as ceiling(visitor count × service minutes / 60), with eight service minutes by default.
- Employees have fixed hourly rates; arbitrary schedules use a configurable overtime threshold and multiplier, while optimized schedules retain a hard 40-hour cap. Breaks are not modeled.
- Availability is an inclusive start and exclusive end window.
- A schedule can contain at most one contiguous interval per employee per day.
- Objective weights are explicit scenario data: labor cost, normal shortage, and peak shortage. A feasible model hard-covers peak buckets; infeasible peak coverage falls back to bounded, visible shortage, and the verifier still reports it separately.
