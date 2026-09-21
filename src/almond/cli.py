import json

from .baseline import build_baseline
from .economics import compare
from .explain import evaluate_constraints
from .generator import generate_demo
from .optimizer import optimize
from .verifier import verify


def run_demo() -> dict:
    scenario = generate_demo()
    baseline = build_baseline(scenario)
    result = optimize(scenario)
    verification = verify(result.schedule, scenario)
    economics = compare(baseline, result.schedule, scenario)
    required = sum(p.demand for p in scenario.demand)
    covered = sum(verification.coverage.values())
    return {"solver_status": result.solver_status, "baseline_cost_mxn": economics.baseline_cost_mxn, "optimized_cost_mxn": economics.optimized_cost_mxn, "avoided_cost_mxn": economics.avoided_cost_mxn, "savings_percentage": round(economics.savings_percentage, 2), "coverage_percentage": round(covered / required * 100, 2), "violations": list(verification.violations), "constraints": evaluate_constraints(result.schedule, scenario)}


def main() -> None:
    print(json.dumps(run_demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
