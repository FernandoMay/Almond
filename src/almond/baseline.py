from .models import Scenario, Schedule, Assignment


def build_baseline(scenario: Scenario) -> Schedule:
    """Fixed full-open shifts: a transparent comparison, not a presumed optimum."""
    return Schedule(tuple(Assignment(e.id, day, scenario.open_start, scenario.open_end) for e in scenario.employees for day in range(scenario.days)))


def schedule_cost(schedule: Schedule, scenario: Scenario) -> int:
    rates = {e.id: e.hourly_cost_mxn for e in scenario.employees}
    return sum(a.hours * rates[a.employee_id] for a in schedule.assignments)
