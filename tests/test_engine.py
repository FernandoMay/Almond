from almond.baseline import analyze_baseline, build_baseline
from almond.economics import compare
from almond.generator import generate_current_schedule, generate_demo
from almond.demand import required_staff
from almond.models import Assignment, Employee, Scenario, Schedule
from almond.optimizer import optimize
from almond.verifier import verify


def test_generation_is_deterministic():
    assert generate_demo() == generate_demo()
    scenario = generate_demo()
    assert generate_current_schedule(scenario) == generate_current_schedule(scenario)


def test_baseline_reports_violations_and_coverage_metrics():
    scenario = Scenario(
        (Employee("E1", 60, {0: (8, 10)}),),
        (generate_demo().demand[0],),
        days=1,
        open_start=8,
        open_end=10,
    )
    schedule = Schedule((Assignment("E1", 0, 7, 11),))

    analysis = analyze_baseline(schedule, scenario)

    assert analysis.availability_violations == ("availability: E1 day 0",)
    assert analysis.coverage[(0, 8)] == 1
    assert analysis.understaffing == scenario.demand[0].demand - 1
    assert analysis.total_hours == 4


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


def test_baseline_reports_overlapping_assignments_for_employee_day():
    scenario = generate_demo()
    invalid = Schedule((Assignment("E1", 0, 8, 10), Assignment("E1", 0, 9, 11)))

    analysis = analyze_baseline(invalid, scenario)

    assert "overlap: E1 day 0" in analysis.violations


def test_baseline_reports_unknown_employee_without_cost_key_error():
    scenario = generate_demo()
    invalid = Schedule((Assignment("UNKNOWN", 0, 8, 10),))

    analysis = analyze_baseline(invalid, scenario)

    assert analysis.cost_mxn == 0
    assert "unknown employee: UNKNOWN" in analysis.violations


def test_economics_formula():
    scenario = generate_demo()
    base = build_baseline(scenario)
    optimized = optimize(scenario).schedule
    result = compare(base, optimized, scenario)
    assert result.avoided_cost_mxn == result.baseline_cost_mxn - result.optimized_cost_mxn
    assert result.savings_percentage == result.avoided_cost_mxn / result.baseline_cost_mxn * 100
    assert result.baseline_coverage_percentage < result.optimized_coverage_percentage


def test_economics_handles_zero_cost_baseline():
    scenario = Scenario((Employee("E1", 0, {0: (8, 9)}),), ())
    empty = Schedule(())

    result = compare(empty, empty, scenario)

    assert result.baseline_cost_mxn == 0
    assert result.optimized_cost_mxn == 0
    assert result.avoided_cost_mxn == 0
    assert result.savings_percentage == 0.0
