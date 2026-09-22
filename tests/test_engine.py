from almond.baseline import analyze_baseline, build_baseline
from almond.economics import compare
from almond.generator import generate_current_schedule, generate_demo
from almond.demand import calculate_demand, required_staff
from almond.models import Assignment, Employee, ObjectiveWeights, OptimizationConfig, OvertimeConfig, Scenario, Schedule
from almond.baseline import overtime_hours_by_employee, schedule_cost
from almond.optimizer import optimize
from almond.verifier import verify


def test_generation_is_deterministic():
    assert generate_demo() == generate_demo()
    scenario = generate_demo()
    assert generate_current_schedule(scenario) == generate_current_schedule(scenario)


def test_demo_marks_only_the_documented_midday_peak_window():
    scenario = generate_demo()
    assert {point.hour for point in scenario.demand if point.peak} == {12, 13, 14, 15}
    assert not any(point.peak for point in scenario.demand if point.hour in {8, 11, 16, 17})


def test_demand_calculation_can_mark_configured_peak_hours():
    result = calculate_demand([(0, 8, 10), (0, 12, 10)], peak_hours={12})
    assert [point.peak for point in result] == [False, True]


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


def test_peak_coverage_is_reported_separately():
    scenario = Scenario(
        (Employee("E1", 60, {0: (8, 10)}),),
        (generate_demo().demand[0].__class__(0, 8, 2, 10, True),),
        days=1,
        open_start=8,
        open_end=10,
    )
    analysis = analyze_baseline(Schedule((Assignment("E1", 0, 8, 9),)), scenario)
    checked = verify(analysis.schedule, scenario)
    assert analysis.peak_understaffing == 1
    assert analysis.peak_coverage_violations == ("peak coverage: day 0 hour 8",)
    assert analysis.peak_coverage_violations[0] in analysis.violations
    assert checked.peak_violations == analysis.peak_coverage_violations


def test_demand_calculation():
    assert required_staff(15) == 2


def test_optimized_schedule_respects_hours_availability_and_coverage():
    scenario = generate_demo()
    result = optimize(scenario)
    checked = verify(result.schedule, scenario)
    assert checked.valid
    assert max(result.schedule.hours_by_employee().values()) <= 40


def test_optimizer_exposes_peak_shortage_when_hard_peak_coverage_is_infeasible():
    scenario = Scenario(
        (Employee("E1", 60, {0: (8, 9)}),),
        (generate_demo().demand[0].__class__(0, 8, 2, 10, True),),
        days=1,
        open_end=9,
    )
    result = optimize(scenario)
    checked = verify(result.schedule, scenario)
    assert not checked.valid
    assert checked.peak_violations == ("peak coverage: day 0 hour 8",)
    assert "bounded slack fallback" in result.explanations[1]


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


def test_overtime_uses_configured_threshold_and_multiplier():
    scenario = Scenario(
        (Employee("E1", 100, {0: (8, 60)}),),
        (),
        days=1,
        open_start=8,
        open_end=60,
        optimization=OptimizationConfig(overtime=OvertimeConfig(weekly_threshold=40, multiplier=1.5)),
    )
    schedule = Schedule((Assignment("E1", 0, 8, 58),))
    assert overtime_hours_by_employee(schedule, scenario) == {"E1": 10}
    assert schedule_cost(schedule, scenario) == 5_500


def test_objective_configuration_is_carried_and_explained():
    weights = ObjectiveWeights(labor_cost=2, normal_uncovered_demand=3, peak_uncovered_demand=7)
    scenario = Scenario((Employee("E1", 60, {0: (8, 9)}),), (), days=1, open_end=9,
                        optimization=OptimizationConfig(objective_weights=weights))
    result = optimize(scenario)
    assert "labor=2, normal shortage=3, peak shortage=7" in result.explanations[0]
