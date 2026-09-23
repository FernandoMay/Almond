import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8000",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
  },
  webServer: {
    command: ".venv/bin/uvicorn almond.api:app --host 127.0.0.1 --port 8000",
    url: "http://127.0.0.1:8000/",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
