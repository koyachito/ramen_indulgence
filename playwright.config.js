// @ts-check
const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  retries: 1,
  use: {
    baseURL: "http://localhost:8000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile",
      use: { ...devices["iPhone 14"] },
    },
  ],
  webServer: {
    command: "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000",
    url: "http://localhost:8000/health",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
