import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  timeout: 30_000,
  use: { baseURL: process.env.BASE_URL || "http://localhost:4174/grid.md/", launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined } },
  webServer: process.env.BASE_URL ? undefined : { command: "pnpm build && pnpm preview", url: "http://localhost:4174/grid.md/", timeout: 120_000, reuseExistingServer: true },
});
