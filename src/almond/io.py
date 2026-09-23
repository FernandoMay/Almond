"""Stateless file adapters for the validated Almond API contract."""

import csv
import io
from collections.abc import Mapping

from .models import Schedule


SCHEDULE_HEADER = ("employee_id", "day", "start", "end", "hours")


class InputFileError(ValueError):
    """Raised when an uploaded JSON or CSV file is not a valid input."""


def parse_json_bytes(filename: str | None, content: bytes) -> Mapping:
    if not filename or not filename.lower().endswith(".json"):
        raise InputFileError("uploaded file must have a .json extension")
    if not content.strip():
        raise InputFileError("uploaded JSON file is empty")
    import json

    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputFileError("uploaded file contains malformed UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise InputFileError("uploaded JSON must be an object")
    allowed = {"employees", "demand", "horizon", "objective_weights", "overtime", "baseline_policy"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise InputFileError(f"uploaded JSON has unknown fields: {', '.join(unknown)}")
    return value


def _read_csv(name: str, content: bytes, expected: tuple[str, ...]) -> list[dict[str, str]]:
    if not content.strip():
        raise InputFileError(f"{name} is empty")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputFileError(f"{name} must be UTF-8 CSV") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or tuple(reader.fieldnames) != expected:
        raise InputFileError(f"{name} must have headers: {','.join(expected)}")
    rows = list(reader)
    if any(None in row for row in rows):
        raise InputFileError(f"{name} contains extra columns; each row must match the exact schema")
    if not rows or any(value is None for row in rows for value in row.values()):
        raise InputFileError(f"{name} contains an empty row or no data")
    return rows


def _integer(value: str, field: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise InputFileError(f"{field} must be an integer") from exc


def parse_csv_bundle(
    employees_content: bytes,
    availability_content: bytes,
    demand_content: bytes,
    *,
    days: int,
    opening_hour: int,
    closing_hour: int,
) -> dict:
    employees = _read_csv("employees.csv", employees_content, ("id", "hourly_rate_mxn"))
    availability = _read_csv("availability.csv", availability_content, ("employee_id", "day", "start", "end"))
    demand = _read_csv("demand.csv", demand_content, ("day", "hour", "visitors", "required_staff", "peak"))

    employee_rows: dict[str, dict] = {}
    for row in employees:
        employee_id = row["id"]
        if not employee_id or employee_id in employee_rows:
            raise InputFileError("employees.csv contains a duplicate or empty id")
        employee_rows[employee_id] = {
            "id": employee_id,
            "hourly_rate_mxn": _integer(row["hourly_rate_mxn"], "hourly_rate_mxn"),
            "availability": {},
        }

    seen_availability: set[tuple[str, int]] = set()
    for row in availability:
        employee_id = row["employee_id"]
        day = _integer(row["day"], "availability day")
        start = _integer(row["start"], "availability start")
        end = _integer(row["end"], "availability end")
        if employee_id not in employee_rows:
            raise InputFileError(f"availability references unknown employee: {employee_id}")
        if (employee_id, day) in seen_availability:
            raise InputFileError("availability.csv contains duplicate employee/day rows")
        seen_availability.add((employee_id, day))
        employee_rows[employee_id]["availability"][str(day)] = {"start": start, "end": end}

    demand_rows = []
    seen_slots: set[tuple[int, int]] = set()
    for row in demand:
        day = _integer(row["day"], "demand day")
        hour = _integer(row["hour"], "demand hour")
        if (day, hour) in seen_slots:
            raise InputFileError("demand.csv contains duplicate day/hour slots")
        seen_slots.add((day, hour))
        peak = row["peak"].strip().lower()
        if peak not in {"true", "false"}:
            raise InputFileError("demand peak must be true or false")
        demand_rows.append({
            "day": day,
            "hour": hour,
            "visitors": _integer(row["visitors"], "visitors"),
            "required_staff": _integer(row["required_staff"], "required_staff"),
            "peak": peak == "true",
        })

    return {
        "employees": list(employee_rows.values()),
        "demand": demand_rows,
        "horizon": {"days": days, "opening_hour": opening_hour, "closing_hour": closing_hour},
    }


def schedule_csv(schedule: Schedule) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(SCHEDULE_HEADER)
    for assignment in sorted(schedule.assignments, key=lambda item: (item.day, item.start, item.end, item.employee_id)):
        writer.writerow((assignment.employee_id, assignment.day, assignment.start, assignment.end, assignment.hours))
    return output.getvalue()
