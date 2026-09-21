from .baseline import analyze_baseline, schedule_cost
from .models import Economics, Scenario, Schedule


def compare(baseline: Schedule, optimized: Schedule, scenario: Scenario) -> Economics:
    baseline_analysis = analyze_baseline(baseline, scenario)
    base = baseline_analysis.cost_mxn
    opt = schedule_cost(optimized, scenario)
    avoided = base - opt
    optimized_analysis = analyze_baseline(optimized, scenario)
    return Economics(
        base,
        opt,
        avoided,
        (avoided / base * 100) if base else 0.0,
        baseline_analysis.coverage_percentage,
        optimized_analysis.coverage_percentage,
        baseline_analysis.understaffing,
        optimized_analysis.understaffing,
        baseline_analysis.overstaffing,
        optimized_analysis.overstaffing,
    )
