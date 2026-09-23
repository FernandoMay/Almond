"""HTTP product surface for deterministic Almond optimization."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from .cli import run_demo, run_scenario, run_scenario_with_schedule
from .io import InputFileError, parse_csv_bundle, parse_json_bytes, schedule_csv
from .models import (
    BaselinePolicy,
    DemandPoint,
    Employee,
    ObjectiveWeights,
    OptimizationConfig,
    OvertimeConfig,
    Scenario,
)


API_VERSION = "v1"


class HealthResponse(BaseModel):
    status: str = Field(description="Service health status.")
    api_version: str = Field(description="Stable API version identifier.")


class DemoRequest(BaseModel):
    seed: int = Field(default=40, ge=0, description="Non-negative seed for the deterministic demo.")


class DemoResponse(BaseModel):
    """The CLI-compatible deterministic demo result."""

    solver_status: str
    current: dict[str, Any]
    optimized: dict[str, Any]
    economics: dict[str, Any]
    configuration: dict[str, Any]
    explanations: list[str]
    constraints: dict[str, Any]


class AvailabilityWindow(BaseModel):
    start: int = Field(ge=0, le=24)
    end: int = Field(ge=0, le=24)

    @model_validator(mode="after")
    def validate_window(self) -> "AvailabilityWindow":
        if self.start >= self.end:
            raise ValueError("availability windows require start < end")
        return self


class StoreEmployee(BaseModel):
    id: str = Field(min_length=1)
    hourly_rate_mxn: int = Field(ge=0, le=1_000_000)
    availability: dict[int, AvailabilityWindow] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_days(self) -> "StoreEmployee":
        if any(day < 0 or day >= 7 for day in self.availability):
            raise ValueError("availability day must be between 0 and 6")
        return self


class StoreDemandBucket(BaseModel):
    day: int = Field(ge=0, le=6)
    hour: int = Field(ge=0, le=23)
    visitors: int = Field(ge=0, le=1_000_000)
    required_staff: int = Field(ge=0, le=1_000)
    peak: bool = False


class StoreHorizon(BaseModel):
    days: int = Field(ge=1, le=7)
    opening_hour: int = Field(ge=0, le=23)
    closing_hour: int = Field(ge=1, le=24)

    @model_validator(mode="after")
    def validate_hours(self) -> "StoreHorizon":
        if self.opening_hour >= self.closing_hour:
            raise ValueError("opening_hour must be before closing_hour")
        return self


class StoreObjectiveWeights(BaseModel):
    labor_cost: int = Field(default=1, ge=0, le=1_000_000)
    normal_uncovered_demand: int = Field(default=10_000, ge=0, le=1_000_000_000)
    peak_uncovered_demand: int = Field(default=20_000, ge=0, le=1_000_000_000)


class StoreOvertimeConfig(BaseModel):
    weekly_threshold: int = Field(default=40, ge=0, le=168)
    multiplier: float = Field(default=1.5, ge=0, le=10)


class StoreBaselinePolicy(BaseModel):
    staffing_floor: int = Field(default=5, ge=0, le=1_000)
    shift_start: int = Field(default=8, ge=0, le=23)
    shift_end: int = Field(default=18, ge=1, le=24)


class OptimizeRequest(BaseModel):
    employees: list[StoreEmployee] = Field(min_length=1)
    demand: list[StoreDemandBucket] = Field(min_length=1)
    horizon: StoreHorizon
    objective_weights: StoreObjectiveWeights = Field(default_factory=StoreObjectiveWeights)
    overtime: StoreOvertimeConfig = Field(default_factory=StoreOvertimeConfig)
    baseline_policy: StoreBaselinePolicy | None = None

    @model_validator(mode="after")
    def validate_scenario(self) -> "OptimizeRequest":
        employee_ids = [employee.id for employee in self.employees]
        if len(employee_ids) != len(set(employee_ids)):
            raise ValueError("employee IDs must be unique")
        slots = [(point.day, point.hour) for point in self.demand]
        if len(slots) != len(set(slots)):
            raise ValueError("demand day/hour slots must be unique")
        if any(point.day >= self.horizon.days for point in self.demand):
            raise ValueError("demand day must be inside the configured horizon")
        if any(not self.horizon.opening_hour <= point.hour < self.horizon.closing_hour for point in self.demand):
            raise ValueError("demand hour must be inside the configured opening hours")
        for employee in self.employees:
            for day, window in employee.availability.items():
                if day >= self.horizon.days:
                    raise ValueError("availability day must be inside the configured horizon")
                if window.start < self.horizon.opening_hour or window.end > self.horizon.closing_hour:
                    raise ValueError("availability must be inside the configured opening hours")
        if self.baseline_policy is not None:
            policy = self.baseline_policy
            if policy.shift_start >= policy.shift_end:
                raise ValueError("baseline shift_start must be before shift_end")
            if policy.shift_start < self.horizon.opening_hour or policy.shift_end > self.horizon.closing_hour:
                raise ValueError("baseline shift must be inside the configured opening hours")
        return self


class OptimizeResponse(DemoResponse):
    scenario: dict[str, Any]


def build_scenario(request: OptimizeRequest) -> Scenario:
    employees = tuple(
        Employee(
            employee.id,
            employee.hourly_rate_mxn,
            {day: (window.start, window.end) for day, window in employee.availability.items()},
        )
        for employee in request.employees
    )
    demand = tuple(
        DemandPoint(point.day, point.hour, point.required_staff, point.visitors, point.peak)
        for point in request.demand
    )
    return Scenario(
        employees,
        demand,
        days=request.horizon.days,
        open_start=request.horizon.opening_hour,
        open_end=request.horizon.closing_hour,
        optimization=OptimizationConfig(
            objective_weights=ObjectiveWeights(**request.objective_weights.model_dump()),
            overtime=OvertimeConfig(**request.overtime.model_dump()),
        ),
        baseline_policy=BaselinePolicy(
            **(request.baseline_policy.model_dump() if request.baseline_policy else {
                "shift_start": request.horizon.opening_hour,
                "shift_end": request.horizon.closing_hour,
            })
        ),
    )


def scenario_metadata(scenario: Scenario) -> dict[str, Any]:
    return {
        "days": scenario.days,
        "opening_hours": {"start": scenario.open_start, "end": scenario.open_end},
        "employee_count": len(scenario.employees),
        "demand_bucket_count": len(scenario.demand),
    }


app = FastAPI(
    title="Almond API",
    version=API_VERSION,
    description="Versioned access to Almond's deterministic workforce optimization demo.",
)

WEB_ROOT = Path(__file__).resolve().parents[2] / "web"
app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    """Serve the dependency-light local operations dashboard."""
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/health", response_model=HealthResponse, summary="Check API health")
def health() -> HealthResponse:
    """Return a stable liveness response without executing optimization."""
    return HealthResponse(status="ok", api_version=API_VERSION)


@app.get("/v1/demo", response_model=DemoResponse, summary="Run the default deterministic demo")
def get_demo() -> dict[str, Any]:
    """Return the seed-40 demo using the same composition as the CLI."""
    return run_demo()


@app.post(
    "/v1/optimize/demo",
    response_model=DemoResponse,
    summary="Optimize the deterministic demo",
    description="Run the existing Almond demo composition with an optional non-negative seed.",
)
def optimize_demo(request: DemoRequest) -> dict[str, Any]:
    """Return a deterministic demo result for the requested seed."""
    return run_demo(request.seed)


@app.post(
    "/v1/optimize",
    response_model=OptimizeResponse,
    summary="Optimize a validated store scenario",
    description="Optimize a new store from employee availability and explicit hourly demand buckets.",
)
def optimize_store(request: OptimizeRequest) -> dict[str, Any]:
    scenario = build_scenario(request)
    result = run_scenario(scenario)
    result["scenario"] = scenario_metadata(scenario)
    return result


def _validated_result(request: OptimizeRequest) -> dict[str, Any]:
    scenario = build_scenario(request)
    result = run_scenario(scenario)
    result["scenario"] = scenario_metadata(scenario)
    return result


@app.post("/v1/optimize/json-file", response_model=OptimizeResponse, summary="Optimize a JSON scenario file")
async def optimize_json_file(file: UploadFile = File(...)) -> dict[str, Any]:
    try:
        payload = parse_json_bytes(file.filename, await file.read())
        request = OptimizeRequest.model_validate(payload)
    except InputFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"invalid OptimizeRequest JSON: {exc}") from exc
    return _validated_result(request)


@app.post("/v1/optimize/csv", response_model=OptimizeResponse, summary="Optimize a CSV scenario bundle")
async def optimize_csv(
    employees: UploadFile = File(...),
    availability: UploadFile = File(...),
    demand: UploadFile = File(...),
    days: int = Form(...),
    opening_hour: int = Form(...),
    closing_hour: int = Form(...),
) -> dict[str, Any]:
    try:
        payload = parse_csv_bundle(
            await employees.read(), await availability.read(), await demand.read(),
            days=days, opening_hour=opening_hour, closing_hour=closing_hour,
        )
        request = OptimizeRequest.model_validate(payload)
    except InputFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"invalid CSV scenario: {exc}") from exc
    return _validated_result(request)


def _schedule_response(scenario: Scenario) -> PlainTextResponse:
    _, schedule = run_scenario_with_schedule(scenario)
    return PlainTextResponse(schedule_csv(schedule), media_type="text/csv")


@app.get("/v1/demo/schedule.csv", response_class=PlainTextResponse, summary="Export the optimized demo schedule")
def export_demo_schedule() -> PlainTextResponse:
    from .generator import generate_demo

    return _schedule_response(generate_demo())


@app.post("/v1/optimize/schedule.csv", response_class=PlainTextResponse, summary="Export an optimized scenario schedule")
def export_store_schedule(request: OptimizeRequest) -> PlainTextResponse:
    return _schedule_response(build_scenario(request))


def main() -> None:
    """Run the API with Uvicorn for local development."""
    import uvicorn

    uvicorn.run("almond.api:app", host="127.0.0.1", port=8000)
