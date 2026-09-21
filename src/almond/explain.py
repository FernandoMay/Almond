from .models import Scenario, Schedule


def evaluate_constraints(schedule: Schedule, scenario: Scenario) -> dict[str, bool]:
    employee_map = {e.id: e for e in scenario.employees}
    availability = all(a.employee_id in employee_map and employee_map[a.employee_id].availability.get(a.day, (0, 0))[0] <= a.start <= a.end <= employee_map[a.employee_id].availability.get(a.day, (0, 0))[1] for a in schedule.assignments)
    weekly = all(value <= 40 for value in schedule.hours_by_employee().values())
    return {"availability": availability, "max_40_weekly_hours": weekly, "non_empty_intervals": all(a.start < a.end for a in schedule.assignments)}
