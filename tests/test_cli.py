import json
from pathlib import Path

import pytest

from almond.cli import main, run_demo


SCENARIO = {
    "employees": [{"id": "A1", "hourly_rate_mxn": 100, "availability": {"0": {"start": 8, "end": 10}}}],
    "demand": [{"day": 0, "hour": 8, "visitors": 8, "required_staff": 1}],
    "horizon": {"days": 1, "opening_hour": 8, "closing_hour": 10},
    "baseline_policy": {"staffing_floor": 1, "shift_start": 8, "shift_end": 10},
}

EMPLOYEES = "id,hourly_rate_mxn\nA1,100\n"
AVAILABILITY = "employee_id,day,start,end\nA1,0,8,10\n"
DEMAND = "day,hour,visitors,required_staff,peak\n0,8,8,1,false\n"


def _write_json(path: Path) -> None:
    path.write_text(json.dumps(SCENARIO), encoding="utf-8")


def _write_csv_bundle(directory: Path) -> None:
    (directory / "employees.csv").write_text(EMPLOYEES, encoding="utf-8")
    (directory / "availability.csv").write_text(AVAILABILITY, encoding="utf-8")
    (directory / "demand.csv").write_text(DEMAND, encoding="utf-8")


def test_no_argument_mode_preserves_demo_json(capsys):
    assert main([]) == 0
    assert json.loads(capsys.readouterr().out) == run_demo()


def test_demo_result_has_presentation_ready_schedule_and_coverage_rows():
    result = run_demo()
    schedule = result["optimized_schedule"]
    coverage = result["hourly_coverage"]
    assert all(list(row) == ["employee_id", "day", "start", "end", "hours"] for row in schedule)
    assert schedule == sorted(schedule, key=lambda row: (row["day"], row["employee_id"], row["start"], row["end"]))
    assert coverage == sorted(coverage, key=lambda row: (row["day"], row["hour"]))
    assert all(list(row) == ["day", "hour", "required", "scheduled", "gap", "coverage_percentage", "peak"] for row in coverage)


def test_json_file_workflow_writes_result_and_schedule(tmp_path):
    scenario = tmp_path / "scenario.json"
    result = tmp_path / "nested" / "result.json"
    schedule = tmp_path / "nested" / "optimized.csv"
    _write_json(scenario)

    assert main(["optimize", "--json-file", str(scenario), "--result-json", str(result), "--schedule-csv", str(schedule)]) == 0
    assert json.loads(result.read_text(encoding="utf-8"))["solver_status"] == "OPTIMAL"
    assert schedule.read_text(encoding="utf-8").splitlines()[0] == "employee_id,day,start,end,hours"


def test_csv_bundle_workflow_matches_json_bytes(tmp_path):
    scenario = tmp_path / "scenario.json"
    _write_json(scenario)
    _write_csv_bundle(tmp_path)
    json_result = tmp_path / "json-result.json"
    json_schedule = tmp_path / "json-schedule.csv"
    csv_result = tmp_path / "csv-result.json"
    csv_schedule = tmp_path / "csv-schedule.csv"

    json_args = ["optimize", "--json-file", str(scenario), "--result-json", str(json_result), "--schedule-csv", str(json_schedule)]
    csv_args = [
        "optimize", "--employees", str(tmp_path / "employees.csv"), "--availability", str(tmp_path / "availability.csv"),
        "--demand", str(tmp_path / "demand.csv"), "--days", "1", "--opening-hour", "8", "--closing-hour", "10",
        "--result-json", str(csv_result), "--schedule-csv", str(csv_schedule),
    ]
    assert main(json_args) == main(csv_args) == 0
    assert json_result.read_bytes() == csv_result.read_bytes()
    assert json_schedule.read_bytes() == csv_schedule.read_bytes()


def test_result_and_schedule_outputs_are_deterministic(tmp_path):
    scenario = tmp_path / "scenario.json"
    _write_json(scenario)
    result_one = tmp_path / "result-one.json"
    schedule_one = tmp_path / "schedule-one.csv"
    result_two = tmp_path / "result-two.json"
    schedule_two = tmp_path / "schedule-two.csv"
    args = ["optimize", "--json-file", str(scenario), "--result-json", str(result_one), "--schedule-csv", str(schedule_one)]
    repeat_args = ["optimize", "--json-file", str(scenario), "--result-json", str(result_two), "--schedule-csv", str(schedule_two)]
    assert main(args) == main(repeat_args) == 0
    assert result_one.read_bytes() == result_two.read_bytes()
    assert schedule_one.read_bytes() == schedule_two.read_bytes()
    assert schedule_one.read_text(encoding="utf-8").splitlines()[0] == "employee_id,day,start,end,hours"


def test_missing_output_paths_prints_only_result_json(capsys, tmp_path):
    scenario = tmp_path / "scenario.json"
    _write_json(scenario)
    assert main(["optimize", "--json-file", str(scenario)]) == 0
    assert json.loads(capsys.readouterr().out)["solver_status"] == "OPTIMAL"


@pytest.mark.parametrize(
    "args",
    [
        ["optimize"],
        ["optimize", "--json-file", "scenario.json", "--employees", "employees.csv"],
        ["optimize", "--employees", "employees.csv", "--availability", "availability.csv", "--demand", "demand.csv", "--days", "1"],
    ],
)
def test_invalid_argument_combinations_exit_without_traceback(args, capsys):
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_malformed_input_is_concise_and_nonzero(tmp_path, capsys):
    scenario = tmp_path / "scenario.json"
    scenario.write_text("{bad", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["optimize", "--json-file", str(scenario)])
    stderr = capsys.readouterr().err
    assert error.value.code == 2
    assert "malformed UTF-8 JSON" in stderr
    assert "Traceback" not in stderr
