import json

from .baseline import analyze_baseline, build_baseline
from .economics import compare
from .explain import evaluate_constraints
from .generator import generate_demo
from .optimizer import optimize
from .verifier import verify


def run_demo() -> dict:
    scenario = generate_demo()
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
            "overstaffing": current_analysis.overstaffing,
            "violations": list(current_analysis.violations),
        },
        "optimized": {
            "cost_mxn": economics.optimized_cost_mxn,
            "coverage_percentage": round(optimized_analysis.coverage_percentage, 2),
            "understaffing": optimized_analysis.understaffing,
            "overstaffing": optimized_analysis.overstaffing,
            "violations": list(verification.violations),
        },
        "economics": {
            "current_cost_mxn": economics.baseline_cost_mxn,
            "optimized_cost_mxn": economics.optimized_cost_mxn,
            "avoided_cost_mxn": economics.avoided_cost_mxn,
            "savings_percentage": round(economics.savings_percentage, 2),
        },
        "constraints": evaluate_constraints(result.schedule, scenario),
    }


def main() -> None:
    print(json.dumps(run_demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
