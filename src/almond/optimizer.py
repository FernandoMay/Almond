from .models import Assignment, OptimizationResult, Scenario, Schedule


def optimize(scenario: Scenario) -> OptimizationResult:
    try:
        from ortools.sat.python import cp_model
    except ImportError as exc:
        raise RuntimeError("OR-Tools is required; install the project dependencies") from exc

    model = cp_model.CpModel()
    hours = [(p.day, p.hour) for p in scenario.demand]
    demand = {(p.day, p.hour): p.demand for p in scenario.demand}
    worked = {(e.id, d, h): model.NewBoolVar(f"w_{e.id}_{d}_{h}") for e in scenario.employees for d, h in hours}
    uncovered = {(d, h): model.NewIntVar(0, demand[d, h], f"u_{d}_{h}") for d, h in hours}
    for e in scenario.employees:
        for d, h in hours:
            start, end = e.availability.get(d, (0, 0))
            if not start <= h < end:
                model.Add(worked[e.id, d, h] == 0)
        model.Add(sum(worked[e.id, d, h] for d, h in hours) <= 40)
        # A gap is forbidden: each employee's modeled daily work is one interval.
        for d in range(scenario.days):
            present = [worked[e.id, d, h] for h in range(scenario.open_start, scenario.open_end)]
            starts = [model.NewBoolVar(f"start_{e.id}_{d}_{i}") for i in range(len(present))]
            model.Add(sum(starts) <= 1)
            model.Add(present[0] <= starts[0])
            for i in range(1, len(present)):
                model.Add(present[i] - present[i - 1] <= starts[i])
    for d, h in hours:
        model.Add(sum(worked[e.id, d, h] for e in scenario.employees) + uncovered[d, h] >= demand[d, h])
    labor = sum(worked[e.id, d, h] * e.hourly_cost_mxn for e in scenario.employees for d, h in hours)
    model.Minimize(labor + sum(uncovered.values()) * 10000)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 40
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"solver failed with status {solver.StatusName(status)}")
    assignments = []
    for e in scenario.employees:
        for d in range(scenario.days):
            selected = [h for h in range(scenario.open_start, scenario.open_end) if solver.Value(worked[e.id, d, h])]
            if selected:
                assignments.append(Assignment(e.id, d, min(selected), max(selected) + 1))
    cost = sum(a.hours * e.hourly_cost_mxn for a in assignments for e in scenario.employees if e.id == a.employee_id)
    explanations = ("Coverage is prioritized with a large uncovered-demand penalty.", "Each employee has at most one contiguous interval per day and 40 weekly hours.")
    return OptimizationResult(Schedule(tuple(assignments)), cost, solver.StatusName(status), explanations)
