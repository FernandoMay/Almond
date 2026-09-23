# Data model

- `Employee`: id, MXN hourly cost, and per-day `[start, end)` availability.
- `DemandPoint`: day, hour, visitor count, required integer staff, and explicit peak marker.
- `Scenario`: employees, demand buckets, modeled days, opening hours, objective weights, and overtime configuration.
- `BaselinePolicy`: fixed staffing floor and contiguous shift interval used to construct the current-policy comparison.
- `Assignment`: employee, day, and contiguous `[start, end)` interval.
- `Schedule`: assignments with per-employee hour aggregation.
- `Verification`: validity, violations, observed coverage, and separate peak coverage evidence.
- `BaselineAnalysis`: current schedule cost, overall/peak coverage, under/overstaffing, regular/overtime hours, and all observed violations.
- `Economics`: baseline/optimized costs, avoided cost, percentage savings, and regular/overtime hours.

Hours are integer buckets. End times are exclusive. Costs are MXN integer amounts.

## API boundaries

The HTTP boundary uses typed Pydantic models for health, demo, and new-store requests/responses. `OptimizeRequest` requires non-empty employees, non-empty demand, and a bounded horizon. Employees contain unique IDs, integer MXN rates, and day-keyed availability windows. Demand contains unique `(day, hour)` slots, visitors, explicit required staff, and an optional peak marker. Objective weights, overtime configuration, and baseline policy are optional. Duplicate IDs/slots, empty collections, invalid windows, and out-of-horizon values are rejected with FastAPI's standard 422 response. `DemoResponse` preserves the CLI result shape; `OptimizeResponse` adds `scenario` metadata without changing existing demo routes.
