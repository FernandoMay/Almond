from .models import Assignment, OptimizationResult, Scenario, Schedule


def _build_model(scenario: Scenario, hard_peak: bool):
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    points = tuple(scenario.demand)
    hours = tuple((p.day, p.hour) for p in points)
    demand = {(p.day, p.hour): p.demand for p in points}
    peak = {(p.day, p.hour): p.peak for p in points}
    worked = {
        (e.id, d, h): model.NewBoolVar(f"w_{e.id}_{d}_{h}")
        for e in scenario.employees
        for d, h in hours
    }
    uncovered = {
        (d, h): model.NewIntVar(0, demand[d, h], f"u_{d}_{h}")
        for d, h in hours
    }
    for employee in scenario.employees:
        for d, h in hours:
            start, end = employee.availability.get(d, (0, 0))
            if not start <= h < end:
                model.Add(worked[employee.id, d, h] == 0)
        model.Add(sum(worked[employee.id, d, h] for d, h in hours) <= 40)
        for d in range(scenario.days):
            present = [
                worked[employee.id, d, h]
                for h in range(scenario.open_start, scenario.open_end)
                if (employee.id, d, h) in worked
            ]
            if not present:
                continue
            starts = [model.NewBoolVar(f"start_{employee.id}_{d}_{i}") for i in range(len(present))]
            model.Add(sum(starts) <= 1)
            model.Add(present[0] <= starts[0])
            for i in range(1, len(present)):
                model.Add(present[i] - present[i - 1] <= starts[i])
    for d, h in hours:
        staffed = sum(worked[e.id, d, h] for e in scenario.employees)
        model.Add(staffed + uncovered[d, h] >= demand[d, h])
        if hard_peak and peak[d, h]:
            model.Add(staffed >= demand[d, h])
    weights = scenario.optimization.objective_weights
    labor = sum(
        worked[e.id, d, h] * e.hourly_cost_mxn * weights.labor_cost
        for e in scenario.employees
        for d, h in hours
    )
    shortage = sum(
        uncovered[d, h] * (weights.peak_uncovered_demand if peak[d, h] else weights.normal_uncovered_demand)
        for d, h in hours
    )
    model.Minimize(labor + shortage)
    return model, worked


def optimize(scenario: Scenario) -> OptimizationResult:
    try:
        from ortools.sat.python import cp_model
    except ImportError as exc:
        raise RuntimeError("OR-Tools is required; install the project dependencies") from exc

    hard_peak = True
    model, worked = _build_model(scenario, hard_peak)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 40
    status = solver.Solve(model)
    if status == cp_model.INFEASIBLE:
        hard_peak = False
        model, worked = _build_model(scenario, hard_peak)
        status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"solver failed with status {solver.StatusName(status)}")
    assignments = []
    for employee in scenario.employees:
        for day in range(scenario.days):
            selected = [
                hour
                for hour in range(scenario.open_start, scenario.open_end)
                if (employee.id, day, hour) in worked and solver.Value(worked[employee.id, day, hour])
            ]
            if selected:
                assignments.append(Assignment(employee.id, day, min(selected), max(selected) + 1))
    schedule = Schedule(tuple(assignments))
    from .baseline import schedule_cost

    cost = schedule_cost(schedule, scenario)
    weights = scenario.optimization.objective_weights
    peak_mode = "hard" if hard_peak else "bounded slack fallback"
    explanations = (
        f"Objective weights: labor={weights.labor_cost}, normal shortage={weights.normal_uncovered_demand}, peak shortage={weights.peak_uncovered_demand}.",
        f"Peak coverage uses a {peak_mode} constraint; shortage remains explicit and weighted.",
        f"Each employee has at most one contiguous interval per day and a hard 40-hour weekly cap; overtime is priced above {scenario.optimization.overtime.weekly_threshold} hours.",
    )
    return OptimizationResult(schedule, cost, solver.StatusName(status), explanations)
