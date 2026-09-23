import argparse
import json
from pathlib import Path
from typing import Sequence

from .baseline import analyze_baseline, build_baseline
from .economics import compare
from .explain import configuration, evaluate_constraints
from .generator import generate_demo
from .io import InputFileError, parse_csv_bundle, parse_json_bytes, schedule_csv
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
    optimized_schedule = [
        {
            "employee_id": assignment.employee_id,
            "day": assignment.day,
            "start": assignment.start,
            "end": assignment.end,
            "hours": assignment.hours,
        }
        for assignment in sorted(
            result.schedule.assignments,
            key=lambda item: (item.day, item.employee_id, item.start, item.end),
        )
    ]
    hourly_coverage = [
        {
            "day": point.day,
            "hour": point.hour,
            "required": point.demand,
            "scheduled": optimized_analysis.coverage[point.day, point.hour],
            "gap": optimized_analysis.coverage[point.day, point.hour] - point.demand,
            "coverage_percentage": round(
                optimized_analysis.coverage[point.day, point.hour] / point.demand * 100, 2
            ) if point.demand else 100.0,
            "peak": point.peak,
        }
        for point in sorted(scenario.demand, key=lambda item: (item.day, item.hour))
    ]
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
        "optimized_schedule": optimized_schedule,
        "hourly_coverage": hourly_coverage,
    }, result.schedule


def run_demo(seed: int = 40) -> dict:
    return run_scenario(generate_demo(seed))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="almond",
        description="Run deterministic Almond workforce optimization without API calls.",
        epilog=(
            "Examples:\n"
            "  almond\n"
            "  almond optimize --json-file scenario.json --result-json result.json --schedule-csv optimized.csv\n"
            "  almond optimize --employees employees.csv --availability availability.csv "
            "--demand demand.csv --days 1 --opening-hour 8 --closing-hour 10"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    optimize_parser = subparsers.add_parser(
        "optimize",
        help="optimize a JSON scenario or an exact-schema CSV bundle",
        description=(
            "Use exactly one input form. JSON must contain the documented scenario object. "
            "The CSV form requires all three files and horizon flags. Outputs are optional: "
            "without --result-json, result JSON is printed to stdout; --schedule-csv writes "
            "the optimized schedule with header employee_id,day,start,end,hours."
        ),
        epilog=(
            "JSON example:\n"
            "  almond optimize --json-file scenario.json --result-json result.json --schedule-csv optimized.csv\n"
            "CSV example:\n"
            "  almond optimize --employees employees.csv --availability availability.csv --demand demand.csv "
            "--days 1 --opening-hour 8 --closing-hour 10"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    input_group = optimize_parser.add_mutually_exclusive_group()
    input_group.add_argument("--json-file", type=Path, help="UTF-8 JSON scenario file")
    input_group.add_argument("--employees", type=Path, help="CSV employees file (CSV bundle form)")
    optimize_parser.add_argument("--availability", type=Path, help="CSV availability file (CSV bundle form)")
    optimize_parser.add_argument("--demand", type=Path, help="CSV demand file (CSV bundle form)")
    optimize_parser.add_argument("--days", type=int, help="CSV bundle horizon length")
    optimize_parser.add_argument("--opening-hour", type=int, help="CSV bundle opening hour")
    optimize_parser.add_argument("--closing-hour", type=int, help="CSV bundle closing hour")
    optimize_parser.add_argument("--result-json", type=Path, help="write deterministic result JSON to this path")
    optimize_parser.add_argument("--schedule-csv", type=Path, help="write deterministic optimized schedule CSV to this path")
    return parser


def _read_scenario(args: argparse.Namespace):
    csv_options = (args.employees, args.availability, args.demand, args.days, args.opening_hour, args.closing_hour)
    if args.json_file is not None:
        if any(value is not None for value in csv_options):
            raise InputFileError("JSON input cannot be combined with CSV files or horizon flags")
        payload = parse_json_bytes(args.json_file.name, args.json_file.read_bytes())
    elif any(value is not None for value in csv_options):
        if not all(value is not None for value in csv_options):
            raise InputFileError("CSV input requires employees, availability, demand, days, opening-hour, and closing-hour")
        payload = parse_csv_bundle(
            args.employees.read_bytes(), args.availability.read_bytes(), args.demand.read_bytes(),
            days=args.days, opening_hour=args.opening_hour, closing_hour=args.closing_hour,
        )
    else:
        raise InputFileError("provide --json-file or the complete CSV bundle and horizon flags")

    # Import lazily: api.py reuses this module for the shared application path.
    from .api import OptimizeRequest, build_scenario

    return build_scenario(OptimizeRequest.model_validate(payload))


def _write_deterministic(path: Path, content: str) -> None:
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _run_optimize(args: argparse.Namespace) -> int:
    scenario = _read_scenario(args)
    result, schedule = run_scenario_with_schedule(scenario)
    result_json = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.result_json is not None:
        _write_deterministic(args.result_json, result_json)
    else:
        print(result_json, end="")
    if args.schedule_csv is not None:
        _write_deterministic(args.schedule_csv, schedule_csv(schedule))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        print(json.dumps(run_demo(), indent=2, sort_keys=True))
        return 0
    try:
        return _run_optimize(args)
    except (InputFileError, OSError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    main()
