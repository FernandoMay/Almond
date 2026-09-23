# Almond five-minute demo script

## 0:00–0:40 — Name the problem

“A store has hourly demand, employee availability, and wage rates. A rigid staffing policy can cover demand while still paying for unnecessary coverage and overtime. Almond turns that operating question into a schedule that can be inspected, verified, and priced.”

## 0:40–1:20 — Show the input

Run the deterministic demo from the repository root:

```bash
.venv/bin/almond
```

Explain the modeled inputs: seed `40`, seven days, 08:00–18:00 opening hours, seven employees, fixed MXN hourly rates, eight service minutes per visitor, and peak buckets `[12:00, 16:00)`. The current policy is an explicit five-person floor rotated across the same employees.

## 1:20–2:20 — Establish the baseline

Show the current-policy metrics:

- `26,950 MXN` cost;
- `100.00%` overall coverage and `100.00%` peak coverage;
- `109` overstaffed person-hours;
- `350` scheduled hours, including `70` overtime hours;
- `7` weekly-hour policy violations from the intentionally rigid comparison policy.

The baseline is not an understaffed straw man: it covers the modeled demand. Its inefficiency is the documented fixed-floor assumption.

## 2:20–3:20 — Run the optimization

Open the local presentation surface:

```bash
.venv/bin/almond-api
# In another terminal or browser:
open http://127.0.0.1:8000/
```

Click **Run demo**. Almond uses CP-SAT, then independently verifies the returned schedule. The optimized result is `16,402 MXN`, `100.00%` overall coverage, `100.00%` peak coverage, `241` hours, zero overtime, zero verifier violations, and `10,548 MXN` avoided cost.

## 3:20–4:00 — Explain the economics

The computed savings are **39.14%**: `(26,950 - 16,402) / 26,950`. The challenge acceptance target is `8%`; it is not an optimizer input, objective term, or hardcoded output. Costs come from generated assignments, employee rates, and the configured overtime rule.

## 4:00–5:00 — Earn trust

Ask: **“Why should I trust that 39.14% isn't just an artifact of your assumptions?”**

Answer: “You should not treat it as a universal savings promise. It is a reproducible, scenario-specific result. The current and optimized schedules use the same generated demand, employees, availability, rates, horizon, and coverage rules. The baseline assumption is explicit and covers 100% of modeled demand; the optimizer's schedule is checked by a separate verifier for identity, availability, overlap, weekly hours, normal coverage, and peak coverage. Run the command twice and compare the bytes. If we change the fixed-floor policy, service time, wages, demand, or other assumptions, the result must be recomputed and may change.”

Close with the release gate:

```bash
make verify
```

It runs the Python, browser, JavaScript, deterministic CLI, two-pass report, and required-artifact checks. Docker is a separate command because its verification depends on a local Docker installation:

```bash
make docker-verify
```
