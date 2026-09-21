from .models import Assignment, BaselineAnalysis, Scenario, Schedule


def build_baseline(scenario: Scenario) -> Schedule:
    """Return the generated current schedule used as the baseline comparison."""
    from .generator import generate_current_schedule

    return generate_current_schedule(scenario)


def schedule_cost(schedule: Schedule, scenario: Scenario) -> int:
    rates = {e.id: e.hourly_cost_mxn for e in scenario.employees}
    return sum(a.hours * rates[a.employee_id] for a in schedule.assignments if a.employee_id in rates)


def analyze_baseline(schedule: Schedule, scenario: Scenario) -> BaselineAnalysis:
    """Measure a current schedule without assuming universal availability."""
    employees = {e.id: e for e in scenario.employees}
    availability_violations = []
    overlap_violations = []
    unknown_employee_violations = []
    assignments_by_employee_day: dict[tuple[str, int], list[tuple[int, int]]] = {}
    for assignment in schedule.assignments:
        employee = employees.get(assignment.employee_id)
        if employee is None:
            unknown_employee_violations.append(f"unknown employee: {assignment.employee_id}")
            continue
        window = employee.availability.get(assignment.day, (0, 0))
        if assignment.start >= assignment.end or not (window[0] <= assignment.start and assignment.end <= window[1]):
            availability_violations.append(f"availability: {assignment.employee_id} day {assignment.day}")
        key = (assignment.employee_id, assignment.day)
        if any(
            assignment.start < end and start < assignment.end
            for start, end in assignments_by_employee_day.get(key, ())
        ):
            overlap_violations.append(f"overlap: {assignment.employee_id} day {assignment.day}")
        assignments_by_employee_day.setdefault(key, []).append((assignment.start, assignment.end))

    weekly_hour_violations = [
        f"weekly hours: {employee_id}={hours}"
        for employee_id, hours in schedule.hours_by_employee().items()
        if hours > 40
    ]
    coverage = {
        (point.day, point.hour): sum(
            1 for assignment in schedule.assignments
            if assignment.day == point.day and assignment.start <= point.hour < assignment.end
        )
        for point in scenario.demand
    }
    required = sum(point.demand for point in scenario.demand)
    covered = sum(min(coverage[point.day, point.hour], point.demand) for point in scenario.demand)
    understaffing = sum(max(point.demand - coverage[point.day, point.hour], 0) for point in scenario.demand)
    overstaffing = sum(max(coverage[point.day, point.hour] - point.demand, 0) for point in scenario.demand)
    coverage_violations = tuple(
        f"coverage: day {point.day} hour {point.hour}"
        for point in scenario.demand
        if coverage[point.day, point.hour] < point.demand
    )
    return BaselineAnalysis(
        schedule=schedule,
        cost_mxn=schedule_cost(schedule, scenario),
        total_hours=sum(assignment.hours for assignment in schedule.assignments),
        availability_violations=tuple(availability_violations),
        weekly_hour_violations=tuple(weekly_hour_violations),
        coverage=coverage,
        coverage_percentage=(covered / required * 100) if required else 0.0,
        understaffing=understaffing,
        overstaffing=overstaffing,
        coverage_violations=coverage_violations,
        overlap_violations=tuple(overlap_violations),
        unknown_employee_violations=tuple(unknown_employee_violations),
    )
