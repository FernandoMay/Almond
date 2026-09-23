import { expect, test } from "@playwright/test";

const validScenario = {
  employees: [
    { id: "A1", hourly_rate_mxn: 100, availability: { "0": { start: 8, end: 10 } } },
  ],
  demand: [{ day: 0, hour: 8, visitors: 8, required_staff: 1 }],
  horizon: { days: 1, opening_hour: 8, closing_hour: 10 },
  baseline_policy: { staffing_floor: 1, shift_start: 8, shift_end: 10 },
};

async function openDashboard(page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Almond optimization desk" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Run demo" })).toBeEnabled();
}

test("loads the accessible dashboard shell", async ({ page }) => {
  await openDashboard(page);

  await expect(page.getByRole("heading", { name: /See the cost of today’s coverage/i })).toBeVisible();
  await expect(page.getByRole("button", { name: "Run demo" })).toBeVisible();
  await expect(page.getByLabel("Upload JSON scenario")).toBeAttached();
});

test("runs the demo, renders verified results, and downloads its CSV", async ({ page }) => {
  await openDashboard(page);

  await page.getByRole("button", { name: "Run demo" }).click();
  await expect(page.getByText("Demo complete. The optimized schedule passed independent validation.")).toBeVisible();
  await expect(page.getByText("39.14% savings")).toBeVisible();
  await expect(page.getByText("26,950 MXN")).toBeVisible();
  await expect(page.getByText("16,402 MXN")).toBeVisible();
  await expect(page.getByText("Passed", { exact: true })).toBeVisible();
  await expect(page.getByRole("table", { name: "Optimized schedule by day and employee" }).getByRole("row")).not.toHaveCount(1);
  await expect(page.getByRole("gridcell")).not.toHaveCount(0);

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download optimized schedule CSV" }).click();
  const download = await downloadPromise;
  const filePath = await download.path();
  expect(filePath).not.toBeNull();
  const csv = await (await import("node:fs/promises")).readFile(filePath, "utf8");
  expect(csv.split("\n", 1)[0]).toBe("employee_id,day,start,end,hours");
});

test("uploads a valid JSON scenario and disables the demo-only download", async ({ page }) => {
  await openDashboard(page);

  await page.getByLabel("Upload JSON scenario").setInputFiles({
    name: "scenario.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(validScenario)),
  });
  await expect(page.getByText("Scenario complete. Review the verified result below.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Download optimized schedule CSV" })).toBeDisabled();
  await expect(page.getByText("Uploaded scenario schedule export is available through the API or CLI; this dashboard does not retain uploaded files.")).toBeVisible();
});

test("shows a visible error for malformed JSON without losing the dashboard", async ({ page }) => {
  await openDashboard(page);

  await page.getByLabel("Upload JSON scenario").setInputFiles({
    name: "broken.json",
    mimeType: "application/json",
    buffer: Buffer.from("{bad"),
  });
  await expect(page.getByText("uploaded file contains malformed UTF-8 JSON", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Almond optimization desk" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Run demo" })).toBeEnabled();
});
