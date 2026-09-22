from .models import DemandPoint


def required_staff(visitors: int, service_minutes: int = 8, productive_minutes: int = 60) -> int:
    if visitors < 0 or service_minutes <= 0 or productive_minutes <= 0:
        raise ValueError("visitors must be non-negative and time inputs must be positive")
    return max(0, (visitors * service_minutes + productive_minutes - 1) // productive_minutes)


def calculate_demand(
    visitors_by_hour: list[tuple[int, int, int]],
    service_minutes: int = 8,
    peak_hours: set[int] | frozenset[int] | None = None,
) -> tuple[DemandPoint, ...]:
    """Calculate demand, optionally marking a configured set of peak hours."""
    peak_hours = peak_hours or frozenset()
    return tuple(
        DemandPoint(day, hour, required_staff(visitors, service_minutes), visitors, hour in peak_hours)
        for day, hour, visitors in visitors_by_hour
    )
