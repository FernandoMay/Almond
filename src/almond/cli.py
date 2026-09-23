import json

from .baseline import analyze_baseline, build_baseline
from .economics import compare
from .explain import configuration, evaluate_constraints
from .generator import generate_demo
from .optimizer import optimize
from .verifier import verify


def run_scenario(scenario) -> dict:
    return run_scenario_with_schedule(scenario)[0]


def run_scenario_with_schedule(scenario):
    baseline = build_baseline(scenario)
    result = optimize(scenario)
    current_analysis = analyze_baseline(baseline, scenario)
    optimized_analysis = analyze_baseline(result.schedule, scenario)
    verification = verify(result.schedule, scenario)
    economics = compare(baseline, result.schedule, scenario)
    return {
        "solver_status": result.solver_status,
        "current": {
            "cost_mxn": current_analysis.cost_mxn,
            "coverage_percentage": round(current_analysis.coverage_percentage, 2),
            "understaffing": current_analysis.understaffing,
            "peak_understaffing": current_analysis.peak_understaffing,
            "peak_coverage_percentage": round(current_analysis.peak_coverage_percentage, 2),
            "overstaffing": current_analysis.overstaffing,
            "total_hours": current_analysis.total_hours,
            "regular_hours": current_analysis.regular_hours,
            "overtime_hours": current_analysis.overtime_hours,
            "violations": list(current_analysis.violations),
            "peak_coverage_violations": list(current_analysis.peak_coverage_violations),
        },
        "optimized": {
            "cost_mxn": economics.optimized_cost_mxn,
            "coverage_percentage": round(optimized_analysis.coverage_percentage, 2),
            "understaffing": optimized_analysis.understaffing,
            "peak_understaffing": optimized_analysis.peak_understaffing,
            "peak_coverage_percentage": round(optimized_analysis.peak_coverage_percentage, 2),
            "overstaffing": optimized_analysis.overstaffing,
            "total_hours": optimized_analysis.total_hours,
            "regular_hours": optimized_analysis.regular_hours,
            "overtime_hours": optimized_analysis.overtime_hours,
            "violations": list(verification.violations),
            "peak_coverage_violations": list(verification.peak_violations),
        },
        "economics": {
            "current_cost_mxn": economics.baseline_cost_mxn,
            "optimized_cost_mxn": economics.optimized_cost_mxn,
            "avoided_cost_mxn": economics.avoided_cost_mxn,
            "savings_percentage": round(economics.savings_percentage, 2),
            "baseline_overtime_hours": economics.baseline_overtime_hours,
            "optimized_overtime_hours": economics.optimized_overtime_hours,
        },
        "configuration": configuration(scenario),
        "explanations": list(result.explanations),
        "constraints": evaluate_constraints(result.schedule, scenario),
    }, result.schedule


def run_demo(seed: int = 40) -> dict:
    return run_scenario(generate_demo(seed))


def main() -> None:
    print(json.dumps(run_demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
