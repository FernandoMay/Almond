from .models import Scenario, Schedule


def evaluate_constraints(schedule: Schedule, scenario: Scenario) -> dict[str, bool]:
    employee_map = {e.id: e for e in scenario.employees}
    availability = all(a.employee_id in employee_map and employee_map[a.employee_id].availability.get(a.day, (0, 0))[0] <= a.start <= a.end <= employee_map[a.employee_id].availability.get(a.day, (0, 0))[1] for a in schedule.assignments)
    weekly = all(value <= 40 for value in schedule.hours_by_employee().values())
    peak_coverage = all(
        sum(1 for a in schedule.assignments if a.day == point.day and a.start <= point.hour < a.end) >= point.demand
        for point in scenario.demand
        if point.peak
    )
    return {
        "availability": availability,
        "max_40_weekly_hours": weekly,
        "non_empty_intervals": all(a.start < a.end for a in schedule.assignments),
        "peak_coverage": peak_coverage,
    }


def configuration(scenario: Scenario) -> dict[str, object]:
    weights = scenario.optimization.objective_weights
    overtime = scenario.optimization.overtime
    return {
        "objective_weights": {
            "labor_cost": weights.labor_cost,
            "normal_uncovered_demand": weights.normal_uncovered_demand,
            "peak_uncovered_demand": weights.peak_uncovered_demand,
        },
        "overtime": {
            "weekly_threshold": overtime.weekly_threshold,
            "multiplier": overtime.multiplier,
        },
    }
