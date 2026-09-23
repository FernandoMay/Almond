import random

from .models import Assignment, DemandPoint, Employee, Scenario, Schedule


DEMO_PEAK_START = 12
DEMO_PEAK_END = 16


def is_demo_peak_hour(hour: int) -> bool:
    """Mark the explicit midday window [12:00, 16:00) as demo peak demand."""
    return DEMO_PEAK_START <= hour < DEMO_PEAK_END


def generate_demo(seed: int = 40) -> Scenario:
    """Build a stable, feasible, intentionally small week."""
    rng = random.Random(seed)
    employees = tuple(
        Employee(f"E{i+1}", 58 + i * 4, {day: (8, 18) for day in range(7)})
        for i in range(7)
    )
    demand = []
    for day in range(7):
        for hour in range(8, 18):
            visitors = 10 + (hour - 8) * 2 + (day % 3) * 3 + rng.randint(0, 5)
            demand.append(
                DemandPoint(
                    day,
                    hour,
                    max(1, (visitors + 7) // 8),
                    visitors,
                    peak=is_demo_peak_hour(hour),
                )
            )
    return Scenario(employees, tuple(demand))


def generate_current_schedule(scenario: Scenario) -> Schedule:
    """Generate the configured fixed-floor operating policy.

    The demo policy represents an observed practice assumption: a fixed
    five-person floor covers every opening hour, with employees rotated
    deterministically by day. It is intentionally simple and overstaffs quiet
    buckets; it is not selected from the target savings percentage.
    """
    assignments = []
    employee_count = len(scenario.employees)
    if not employee_count:
        return Schedule(())
    policy = scenario.baseline_policy
    if policy.staffing_floor <= 0 or policy.shift_start >= policy.shift_end:
        return Schedule(())
    for day in range(scenario.days):
        for offset in range(min(policy.staffing_floor, employee_count)):
            employee = scenario.employees[(day + offset) % employee_count]
            start = policy.shift_start
            end = policy.shift_end
            if employee.availability.get(day, (0, 0))[0] <= start and end <= employee.availability.get(day, (0, 0))[1]:
                assignments.append(Assignment(employee.id, day, start, end))
    return Schedule(tuple(assignments))
