import { defineConfig, devices } from "@playwright/test";

const channel = process.env.E2E_BROWSER_CHANNEL;
if (channel !== undefined && channel !== "chrome" && channel !== "msedge") {
  throw new Error(
    "E2E_BROWSER_CHANNEL must be chrome or msedge when provided.",
  );
}

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  workers: 3,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: process.env.FRONTEND_URL ?? "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"], channel } },
  ],
});
