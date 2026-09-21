# Assumptions

- The demonstration has one generic employee role and seven modeled days.
- Demand is calculated as ceiling(visitor count × service minutes / 60), with eight service minutes by default.
- Employees have fixed hourly rates and no premiums or breaks.
- Availability is an inclusive start and exclusive end window.
- A schedule can contain at most one contiguous interval per employee per day.
- A large finite penalty makes uncovered demand visible and strongly disfavored; the verifier still reports it.
