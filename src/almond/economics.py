from .baseline import schedule_cost
from .models import Economics, Scenario, Schedule


def compare(baseline: Schedule, optimized: Schedule, scenario: Scenario) -> Economics:
    base = schedule_cost(baseline, scenario)
    opt = schedule_cost(optimized, scenario)
    avoided = base - opt
    return Economics(base, opt, avoided, (avoided / base * 100) if base else 0.0)
