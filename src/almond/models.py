from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Employee:
    id: str
    hourly_cost_mxn: int
    availability: Mapping[int, tuple[int, int]]  # day -> [start hour, end hour)


@dataclass(frozen=True)
class DemandPoint:
    day: int
    hour: int
    demand: int
    visitors: int


@dataclass(frozen=True)
class Scenario:
    employees: tuple[Employee, ...]
    demand: tuple[DemandPoint, ...]
    days: int = 7
    open_start: int = 8
    open_end: int = 18


@dataclass(frozen=True)
class Assignment:
    employee_id: str
    day: int
    start: int
    end: int

    @property
    def hours(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class Schedule:
    assignments: tuple[Assignment, ...]

    def hours_by_employee(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in self.assignments:
            result[item.employee_id] = result.get(item.employee_id, 0) + item.hours
        return result

    def assigned(self, employee_id: str, day: int, hour: int) -> bool:
        return any(a.employee_id == employee_id and a.day == day and a.start <= hour < a.end for a in self.assignments)


@dataclass(frozen=True)
class Verification:
    valid: bool
    violations: tuple[str, ...]
    coverage: Mapping[tuple[int, int], int]


@dataclass(frozen=True)
class BaselineAnalysis:
    schedule: Schedule
    cost_mxn: int
    total_hours: int
    availability_violations: tuple[str, ...]
    weekly_hour_violations: tuple[str, ...]
    coverage: Mapping[tuple[int, int], int]
    coverage_percentage: float
    understaffing: int
    overstaffing: int
    coverage_violations: tuple[str, ...] = field(default_factory=tuple)
    overlap_violations: tuple[str, ...] = field(default_factory=tuple)
    unknown_employee_violations: tuple[str, ...] = field(default_factory=tuple)

    @property
    def violations(self) -> tuple[str, ...]:
        return (
            self.availability_violations
            + self.overlap_violations
            + self.unknown_employee_violations
            + self.weekly_hour_violations
            + self.coverage_violations
        )


@dataclass(frozen=True)
class Economics:
    baseline_cost_mxn: int
    optimized_cost_mxn: int
    avoided_cost_mxn: int
    savings_percentage: float
    baseline_coverage_percentage: float = 0.0
    optimized_coverage_percentage: float = 0.0
    baseline_understaffing: int = 0
    optimized_understaffing: int = 0
    baseline_overstaffing: int = 0
    optimized_overstaffing: int = 0

    @property
    def current_cost_mxn(self) -> int:
        return self.baseline_cost_mxn


@dataclass(frozen=True)
class OptimizationResult:
    schedule: Schedule
    objective_cost_mxn: int
    solver_status: str
    explanations: tuple[str, ...] = field(default_factory=tuple)
