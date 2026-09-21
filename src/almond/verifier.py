from .models import Scenario, Schedule, Verification


def verify(schedule: Schedule, scenario: Scenario) -> Verification:
    violations: list[str] = []
    employees = {e.id: e for e in scenario.employees}
    assignments_by_employee_day: dict[tuple[str, int], list[tuple[int, int]]] = {}
    for a in schedule.assignments:
        e = employees.get(a.employee_id)
        if e is None:
            violations.append(f"unknown employee: {a.employee_id}")
            continue
        window = e.availability.get(a.day, (0, 0))
        if a.start >= a.end or not (window[0] <= a.start and a.end <= window[1]):
            violations.append(f"availability: {a.employee_id} day {a.day}")
        key = (a.employee_id, a.day)
        if any(a.start < end and start < a.end for start, end in assignments_by_employee_day.get(key, ())):
            violations.append(f"overlap: {a.employee_id} day {a.day}")
        assignments_by_employee_day.setdefault(key, []).append((a.start, a.end))
    hours = schedule.hours_by_employee()
    for employee_id, total in hours.items():
        if total > 40:
            violations.append(f"weekly hours: {employee_id}={total}")
    coverage = {}
    for point in scenario.demand:
        coverage[point.day, point.hour] = sum(1 for a in schedule.assignments if a.day == point.day and a.start <= point.hour < a.end)
        if coverage[point.day, point.hour] < point.demand:
            violations.append(f"coverage: day {point.day} hour {point.hour}")
    return Verification(not violations, tuple(violations), coverage)
