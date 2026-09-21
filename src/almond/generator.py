import random

from .models import Assignment, DemandPoint, Employee, Scenario, Schedule


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
            demand.append(DemandPoint(day, hour, max(1, (visitors + 7) // 8), visitors))
    return Scenario(employees, tuple(demand))


def generate_current_schedule(scenario: Scenario) -> Schedule:
    """Generate a stable, plausible current schedule for the same scenario.

    This represents a simple fixed-shift operation rather than an arbitrary
    fully staffed comparison. Four employees rotate through 08:00–16:00
    shifts, leaving the final two opening hours uncovered by design.
    """
    assignments = []
    employee_count = len(scenario.employees)
    if not employee_count:
        return Schedule(())
    for day in range(scenario.days):
        for offset in range(min(4, employee_count)):
            employee = scenario.employees[(day + offset) % employee_count]
            start = scenario.open_start
            end = min(scenario.open_end, start + 8)
            if employee.availability.get(day, (0, 0))[0] <= start and end <= employee.availability.get(day, (0, 0))[1]:
                assignments.append(Assignment(employee.id, day, start, end))
    return Schedule(tuple(assignments))
