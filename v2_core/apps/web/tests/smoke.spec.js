const { test, expect } = require("@playwright/test");

test("login page smoke", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
  await expect(page.getByPlaceholder("email")).toBeVisible();
  await expect(page.getByPlaceholder("password")).toBeVisible();
});

test("nav links smoke", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("link", { name: "NovaRium V2" })).toBeVisible();
  await expect(page.getByRole("link", { name: "SQL Lab" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Analytics" })).toBeVisible();
});
