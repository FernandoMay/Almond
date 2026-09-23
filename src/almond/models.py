from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ObjectiveWeights:
    """Deterministic coefficients for the solver objective."""

    labor_cost: int = 1
    normal_uncovered_demand: int = 10_000
    peak_uncovered_demand: int = 20_000


@dataclass(frozen=True)
class OvertimeConfig:
    weekly_threshold: int = 40
    multiplier: float = 1.5


@dataclass(frozen=True)
class OptimizationConfig:
    objective_weights: ObjectiveWeights = field(default_factory=ObjectiveWeights)
    overtime: OvertimeConfig = field(default_factory=OvertimeConfig)


@dataclass(frozen=True)
class BaselinePolicy:
    """Explicit operating policy used for the current-schedule comparison."""

    staffing_floor: int = 5
    shift_start: int = 8
    shift_end: int = 18


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
    peak: bool = False


@dataclass(frozen=True)
class Scenario:
    employees: tuple[Employee, ...]
    demand: tuple[DemandPoint, ...]
    days: int = 7
    open_start: int = 8
    open_end: int = 18
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    baseline_policy: BaselinePolicy = field(default_factory=BaselinePolicy)


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
    peak_coverage: Mapping[tuple[int, int], int] = field(default_factory=dict)
    peak_violations: tuple[str, ...] = field(default_factory=tuple)


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
    peak_coverage: Mapping[tuple[int, int], int] = field(default_factory=dict)
    peak_understaffing: int = 0
    peak_coverage_violations: tuple[str, ...] = field(default_factory=tuple)
    peak_required: int = 0
    peak_covered: int = 0
    regular_hours: Mapping[str, int] = field(default_factory=dict)
    overtime_hours: Mapping[str, int] = field(default_factory=dict)

    @property
    def peak_coverage_percentage(self) -> float:
        return self.peak_covered / self.peak_required * 100 if self.peak_required else 0.0

    @property
    def violations(self) -> tuple[str, ...]:
        return (
            self.availability_violations
            + self.overlap_violations
            + self.unknown_employee_violations
            + self.weekly_hour_violations
            + self.coverage_violations
            + self.peak_coverage_violations
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
    baseline_regular_hours: Mapping[str, int] = field(default_factory=dict)
    baseline_overtime_hours: Mapping[str, int] = field(default_factory=dict)
    optimized_regular_hours: Mapping[str, int] = field(default_factory=dict)
    optimized_overtime_hours: Mapping[str, int] = field(default_factory=dict)

    @property
    def current_cost_mxn(self) -> int:
        return self.baseline_cost_mxn


@dataclass(frozen=True)
class OptimizationResult:
    schedule: Schedule
    objective_cost_mxn: int
    solver_status: str
    explanations: tuple[str, ...] = field(default_factory=tuple)
