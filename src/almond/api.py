"""HTTP product surface for the deterministic Almond demo."""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .cli import run_demo


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


app = FastAPI(
    title="Almond API",
    version=API_VERSION,
    description="Versioned access to Almond's deterministic workforce optimization demo.",
)


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


def main() -> None:
    """Run the API with Uvicorn for local development."""
    import uvicorn

    uvicorn.run("almond.api:app", host="127.0.0.1", port=8000)
