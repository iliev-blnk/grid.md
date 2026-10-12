import { expect, test } from "@playwright/test";

test("the story has seven chapters and follows the language switch", async ({ page }) => {
  await page.addInitScript(() => { if (!localStorage.getItem("gridmd.lang")) localStorage.setItem("gridmd.lang", "en"); });
  await page.goto("./");
  await page.locator("a.storylink").click();
  await expect(page.locator(".chapter")).toHaveCount(7);
  await expect(page.locator("h1")).toHaveText("Moldova's grid, 2021–2026");
  await expect(page.locator("#solar .num")).toContainText("MW");
  await page.getByRole("button", { name: "RU" }).click();
  await expect(page.locator("h1")).toHaveText("Энергосистема Молдовы, 2021–2026");
  await expect(page.locator(".chapter svg")).toHaveCount(6);
});
