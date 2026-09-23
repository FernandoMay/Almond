const $ = (selector) => document.querySelector(selector);

const elements = {
  apiStatus: $("#api-status"),
  feedback: $("#feedback"),
  results: $("#results"),
  solverStatus: $("#solver-status"),
  runDemo: $("#run-demo"),
  scenarioFile: $("#scenario-file"),
  download: $("#download-schedule"),
  downloadNote: $("#download-note"),
};

let activeSource = null;

const formatMxn = (value) => `${new Intl.NumberFormat("en-US").format(value)} MXN`;
const formatPercent = (value) => `${Number(value).toFixed(2)}%`;
const formatPair = (current, optimized, formatter) => `${formatter(current)} → ${formatter(optimized)}`;
const totalHours = (hours) => Object.values(hours || {}).reduce((total, value) => total + Number(value), 0);
const dayName = (day) => ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day] || `Day ${day}`;
const hourLabel = (hour) => `${String(hour).padStart(2, "0")}:00`;

function setState(state, message) {
  elements.apiStatus.dataset.state = state;
  elements.apiStatus.textContent = state === "loading" ? "Running" : state === "error" ? "Attention" : state === "success" ? "Complete" : "Ready";
  elements.feedback.dataset.state = state;
  elements.feedback.textContent = message;
}

function renderConstraints(constraints, explanations) {
  const list = elements.results.querySelector("#constraints");
  list.replaceChildren();
  Object.entries(constraints || {}).forEach(([name, valid]) => {
    const item = document.createElement("li");
    item.dataset.valid = String(valid);
    item.textContent = `${name.replaceAll("_", " ")} ${valid ? "passed" : "needs attention"}`;
    list.append(item);
  });
  const explanationList = $("#explanations");
  explanationList.replaceChildren();
  (explanations || []).forEach((explanation) => {
    const item = document.createElement("p");
    item.textContent = explanation;
    explanationList.append(item);
  });
}

function renderResult(result) {
  const current = result.current;
  const optimized = result.optimized;
  const economics = result.economics;
  $("#avoided-cost").textContent = formatMxn(economics.avoided_cost_mxn);
  $("#savings").textContent = `${formatPercent(economics.savings_percentage)} savings`;
  $("#current-cost").textContent = formatMxn(economics.current_cost_mxn);
  $("#optimized-cost").textContent = formatMxn(economics.optimized_cost_mxn);
  $("#coverage").textContent = formatPair(current.coverage_percentage, optimized.coverage_percentage, formatPercent);
  $("#peak-coverage").textContent = formatPair(current.peak_coverage_percentage, optimized.peak_coverage_percentage, formatPercent);
  $("#overstaffing").textContent = `${current.overstaffing} hours`;
  $("#overtime").textContent = formatPair(totalHours(economics.baseline_overtime_hours), totalHours(economics.optimized_overtime_hours), (value) => `${value}h`);
  const valid = optimized.violations.length === 0 && optimized.peak_coverage_violations.length === 0;
  $("#validation").textContent = valid ? "Passed" : "Review";
  elements.solverStatus.textContent = result.solver_status;
  elements.solverStatus.dataset.state = valid ? "idle" : "error";
  renderConstraints(result.constraints, result.explanations);
  renderSchedule(result.optimized_schedule);
  renderCoverage(result.hourly_coverage);
  elements.results.hidden = false;
}

function renderSchedule(rows) {
  const body = $("#schedule-table tbody");
  body.replaceChildren();
  const safeRows = Array.isArray(rows) ? rows : [];
  $("#schedule-empty").hidden = safeRows.length !== 0;
  safeRows.forEach((row) => {
    const tr = document.createElement("tr");
    [dayName(Number(row.day)), row.employee_id, hourLabel(Number(row.start)), hourLabel(Number(row.end)), `${row.hours}h`].forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      tr.append(cell);
    });
    body.append(tr);
  });
}

function renderCoverage(rows) {
  const safeRows = Array.isArray(rows) ? rows : [];
  const grid = $("#coverage-heatmap");
  const body = $("#coverage-table tbody");
  grid.replaceChildren();
  body.replaceChildren();
  $("#coverage-empty").hidden = safeRows.length !== 0;
  safeRows.forEach((row) => {
    const difference = Number(row.gap);
    const state = difference < 0 ? "under" : difference === 0 ? "exact" : "over";
    const cell = document.createElement("div");
    cell.className = `heat-cell heat-${state}${row.peak ? " heat-peak" : ""}`;
    cell.setAttribute("role", "gridcell");
    cell.setAttribute("aria-label", `${dayName(row.day)} ${hourLabel(row.hour)}: ${row.scheduled} scheduled, ${row.required} required${row.peak ? ", peak" : ""}`);
    cell.textContent = `${dayName(row.day).slice(0, 3)} ${hourLabel(row.hour)} ${row.scheduled}/${row.required}`;
    grid.append(cell);

    const tr = document.createElement("tr");
    [dayName(Number(row.day)), hourLabel(Number(row.hour)), row.required, row.scheduled, difference > 0 ? `+${difference}` : difference, `${Number(row.coverage_percentage).toFixed(2)}%`, row.peak ? "Yes" : "No"].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    });
    body.append(tr);
  });
}

async function runRequest(request, source) {
  activeSource = source;
  setState("loading", "Optimizing the scenario and checking constraints…");
  elements.results.hidden = true;
  try {
    const response = await fetch(request.url, request.options);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The API rejected the scenario.");
    renderResult(payload);
    elements.download.disabled = source !== "demo";
    elements.downloadNote.textContent = source === "demo"
      ? "Available for this deterministic demo result."
      : "Uploaded scenario schedule export is available through the API or CLI; this dashboard does not retain uploaded files.";
    setState("success", source === "demo" ? "Demo complete. The optimized schedule passed independent validation." : "Scenario complete. Review the verified result below.");
  } catch (error) {
    setState("error", error.message);
  }
}

elements.runDemo.addEventListener("click", () => runRequest({ url: "/v1/demo" }, "demo"));
elements.scenarioFile.addEventListener("change", () => {
  const file = elements.scenarioFile.files[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  runRequest({ url: "/v1/optimize/json-file", options: { method: "POST", body: form } }, "upload");
  elements.scenarioFile.value = "";
});
elements.download.addEventListener("click", () => {
  if (activeSource === "demo") window.location.assign("/v1/demo/schedule.csv");
});
