import { expect, test } from "@playwright/test";

test("peak number, fan and record render in English", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("gridmd.lang", "en"));
  await page.goto("./");
  await expect(page.locator(".num")).toContainText(/\d{3}\s*MW/);
  await expect(page.locator("#chart svg path").first()).toHaveAttribute("d", /^M/);
  await expect(page.locator("#tldr")).toContainText("Every morning at 9:00");
  await expect(page.locator("#record")).toContainText("How it has done");
});

test("switching to Romanian and Russian translates the page and is remembered", async ({ page }) => {
  await page.addInitScript(() => { if (!localStorage.getItem("gridmd.lang")) localStorage.setItem("gridmd.lang", "en"); });
  await page.goto("./");
  await page.getByRole("button", { name: "RO" }).click();
  await expect(page.locator("#tldr")).toContainText("În fiecare dimineață");
  await expect(page.locator("html")).toHaveAttribute("lang", "ro");
  await page.getByRole("button", { name: "RU" }).click();
  await expect(page.locator("#tldr")).toContainText("Каждое утро");
  await expect(page.locator(".num")).toContainText("МВт");
  await page.reload();
  await expect(page.locator("#tldr")).toContainText("Каждое утро");
});
