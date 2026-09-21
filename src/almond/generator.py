import random

from .models import DemandPoint, Employee, Scenario


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
