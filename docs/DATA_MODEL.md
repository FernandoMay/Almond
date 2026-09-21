# Data model

- `Employee`: id, MXN hourly cost, and per-day `[start, end)` availability.
- `DemandPoint`: day, hour, visitor count, and required integer staff.
- `Scenario`: employees, demand buckets, modeled days, and opening hours.
- `Assignment`: employee, day, and contiguous `[start, end)` interval.
- `Schedule`: assignments with per-employee hour aggregation.
- `Verification`: validity, violations, and observed coverage by bucket.
- `Economics`: baseline cost, optimized cost, avoided cost, and percentage savings.

Hours are integer buckets. End times are exclusive. Costs are MXN integer amounts.
