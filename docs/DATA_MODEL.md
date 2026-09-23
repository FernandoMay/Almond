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

The HTTP boundary uses typed Pydantic models for health and demo requests/responses. `DemoRequest.seed` is an optional non-negative integer defaulting to 40. `DemoResponse` preserves the CLI result shape: solver status, current and optimized analyses, economics, configuration, explanations, and constraint evaluations. Invalid request data is rejected with FastAPI's standard 422 response; domain failures are not converted into success responses.
