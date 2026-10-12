import { expect, test } from "@playwright/test";

test("tomorrow's fan and the record render", async ({ page }) => {
  await page.goto("./");
  await expect(page.locator("svg.fan")).toHaveCount(1);
  await expect(page.locator("svg.fan path").first()).toHaveAttribute("d", /^M/);
  await expect(page.locator("#summary")).toContainText("Peak around");
  await expect(page.locator("#record")).toContainText("Record");
});
