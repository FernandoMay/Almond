from almond.baseline import build_baseline
from almond.economics import compare
from almond.generator import generate_demo
from almond.demand import required_staff
from almond.models import Assignment, Schedule
from almond.optimizer import optimize
from almond.verifier import verify


def test_generation_is_deterministic():
    assert generate_demo() == generate_demo()


def test_demand_calculation():
    assert required_staff(15) == 2


def test_optimized_schedule_respects_hours_availability_and_coverage():
    scenario = generate_demo()
    result = optimize(scenario)
    checked = verify(result.schedule, scenario)
    assert checked.valid
    assert max(result.schedule.hours_by_employee().values()) <= 40


def test_verifier_rejects_invalid_schedule():
    scenario = generate_demo()
    invalid = Schedule((Assignment("E1", 0, 7, 19),))
    checked = verify(invalid, scenario)
    assert not checked.valid
    assert any("availability" in v or "coverage" in v for v in checked.violations)


def test_verifier_rejects_overlapping_assignments_for_employee_day():
    scenario = generate_demo()
    invalid = Schedule((Assignment("E1", 0, 8, 10), Assignment("E1", 0, 9, 11)))

    checked = verify(invalid, scenario)

    assert not checked.valid
    assert "overlap: E1 day 0" in checked.violations


def test_economics_formula():
    scenario = generate_demo()
    base = build_baseline(scenario)
    optimized = optimize(scenario).schedule
    result = compare(base, optimized, scenario)
    assert result.avoided_cost_mxn == result.baseline_cost_mxn - result.optimized_cost_mxn
    assert result.savings_percentage == result.avoided_cost_mxn / result.baseline_cost_mxn * 100
