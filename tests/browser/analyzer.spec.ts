import { test, expect } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import AxeBuilder from "@axe-core/playwright";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".app-shell")).toHaveAttribute("data-ready", "true");
});

test("example analysis, comparison and saved trade persist", async ({ page }) => {
  const errors: string[] = []; page.on("pageerror", e => errors.push(e.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Know the impact");
  await expect(page.locator(".category-table tbody tr")).toHaveCount(8);
  await page.getByRole("button", { name: "Save trade", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Trade saved");
  await page.getByRole("button", { name: /Player comparison/ }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.locator(".comparison-table")).toContainText("Luka Doncic");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.reload();
  await page.getByRole("button", { name: /Saved trades/ }).click();
  await expect(page.locator(".saved-item")).toHaveCount(1);
  await page.getByRole("button", { name: "Load", exact: true }).click();
  await expect(page.locator(".category-table tbody tr")).toHaveCount(8);
  expect(errors).toEqual([]);
});

test("manual partial roster and trade-only mode work", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Use my roster", exact: true }).click();
  const search = page.getByRole("combobox", { name: "Search players" });
  for (const name of ["Nikola Jokic", "Giannis Antetokounmpo"]) {
    await search.fill(name); await page.getByRole("option", { name: new RegExp(name) }).click();
  }
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page.getByRole("button", { name: "Choose a player to give" }).click();
  await page.getByRole("combobox", { name: "Search players" }).fill("Nikola Jokic");
  await page.getByRole("option", { name: /Nikola Jokic/ }).click();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page.getByRole("button", { name: "Choose a player to receive" }).click();
  await page.getByRole("combobox", { name: "Search players" }).fill("Luka Doncic");
  await page.getByRole("option", { name: /Luka Doncic/ }).click();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page.getByRole("button", { name: "Analyze trade", exact: true }).click();
  await expect(page.getByText("Partial roster: comparing your 2 entered players.")).toBeVisible();
  await page.getByRole("checkbox", { name: "Compare the trade without my roster" }).check();
  await page.getByRole("button", { name: "Analyze trade", exact: true }).click();
  await expect(page.getByRole("tab", { name: "Roster impact" })).toBeDisabled();
  await expect(page.locator(".trade-value-summary")).toBeVisible();
});

test("an uneven trade requires a selected drop", async ({ page }) => {
  await page.goto("/");
  await page.locator(".receive-side").getByRole("button", { name: "Add another player" }).click();
  await page.getByRole("combobox", { name: "Search players" }).fill("Nikola Jokic");
  await page.getByRole("option", { name: /Nikola Jokic/ }).click();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page.getByRole("button", { name: "Analyze trade", exact: true }).click();
  await expect(page.locator(".builder").getByRole("alert")).toContainText("Choose who to drop");
  await page.getByRole("button", { name: "Choose drops", exact: false }).click();
  await page.getByRole("combobox", { name: "Search players" }).fill("Devin Booker");
  await page.getByRole("option", { name: /Devin Booker/ }).click();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page.getByRole("button", { name: "Analyze trade", exact: true }).click();
  await expect(page.locator(".builder").getByRole("alert")).toHaveCount(0);
  await expect(page.locator(".table-footer")).toContainText("13 → 13");
});

test("counteroffer loads and availability assumptions stay explicit", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Explore this trade" }).first().click();
  await expect(page.locator(".category-table tbody tr")).toHaveCount(8);
  await page.getByRole("button", { name: "Review availability assumptions" }).click();
  await page.locator(".assumption-list input").first().check();
  await page.getByRole("button", { name: "Apply assumptions" }).click();
  await expect(page.getByText("1 player assumption(s) excluded from team estimates.")).toBeVisible();
});

test("phone, tablet and desktop layouts avoid page overflow", async ({ page }) => {
  mkdirSync("reports/screenshots", { recursive: true });
  for (const width of [320, 375, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    await expect(page.locator(".app-shell")).toHaveAttribute("data-ready", "true");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    if (width === 375 || width === 1440) await page.screenshot({ path: `reports/screenshots/${width === 375 ? "mobile" : "desktop"}.png`, fullPage: true });
  }
});

test("schedule estimates disclose assumptions and update with the window", async ({ page }) => {
  await page.getByRole("button", { name: "Schedule window", exact: true }).click();
  await expect(page.locator(".basis-note")).toContainText("Assumes participation");
  await page.getByRole("combobox", { name: "Schedule window" }).selectOption("14");
  await expect(page.locator(".basis-note")).toContainText("14-day potential");
  await page.getByRole("combobox", { name: "Schedule timezone" }).selectOption("UTC");
  await expect(page.locator(".basis-note")).toContainText("(UTC)");
  await page.getByRole("button", { name: "Per game", exact: true }).click();
  await expect(page.locator(".basis-note")).toHaveCount(0);
});

test("the player picker supports keyboard selection", async ({ page }) => {
  await page.getByRole("button", { name: "Use my roster", exact: true }).click();
  const search = page.getByRole("combobox", { name: "Search players" });
  await search.fill("Nikola Jokic");
  await search.press("Enter");
  await expect(page.locator(".selected-chips")).toContainText("Nikola Jokic");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("core screens and dialogs pass automated accessibility checks", async ({ page }) => {
  test.setTimeout(90000);
  const results: { name: string; violations: unknown[] }[] = [];
  const audit = async (name: string) => {
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    results.push({ name, violations: result.violations });
    mkdirSync("reports", { recursive: true });
    writeFileSync("reports/accessibility.json", JSON.stringify({ checkedAt: new Date().toISOString(), results }, null, 2));
    expect(result.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) }))).toEqual([]);
  };
  for (const theme of ["light", "dark"]) {
    await page.setViewportSize({ width: 1440, height: 1000 });
    if (await page.locator("html").getAttribute("data-theme") !== theme) await page.getByRole("button", { name: `Switch to ${theme} mode` }).click();
    await audit(`${theme}: desktop`);
    for (const name of ["Player comparison", "How trade analysis works", "Season snapshot", "Review availability assumptions"]) {
      await page.getByRole("button", { name, exact: true }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await audit(`${theme}: ${name}`);
      await page.getByRole("button", { name: "Close dialog" }).click();
    }
    await page.getByRole("button", { name: /My roster/ }).click();
    await audit(`${theme}: roster picker`);
    await page.keyboard.press("Escape");
    await page.evaluate(() => { (document.activeElement as HTMLElement)?.blur(); window.scrollTo({ top: 0, behavior: "instant" }); });
    await page.screenshot({ path: `reports/screenshots/${theme}-desktop.png`, fullPage: true });
    await page.setViewportSize({ width: 375, height: 900 });
    await audit(`${theme}: mobile`);
    await page.screenshot({ path: `reports/screenshots/${theme}-mobile.png`, fullPage: true });
  }
});

test("theme follows the device until chosen and remembers the choice", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "Switch to light mode" }).click();
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByRole("button", { name: "Switch to dark mode" }).click();
  await page.emulateMedia({ colorScheme: "light" });
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  for (const width of [320, 375, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(page.getByRole("button", { name: "Switch to light mode" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
});

test("player headshots load from mapped NBA IDs across trade and comparison views", async ({ page }) => {
  const photo = page.locator(".give-side .avatar-photo").first();
  await expect(photo).toHaveClass(/is-loaded/, { timeout: 20000 });
  expect(new URL((await photo.getAttribute("src"))!, page.url()).searchParams.get("url")).toBe("https://cdn.nba.com/headshots/nba/latest/260x190/1629029.png");
  expect(await photo.evaluate(img => (img as HTMLImageElement).naturalWidth)).toBeGreaterThan(20);
  await expect(page.locator(".give-side .avatar-initials")).toBeHidden();
  await page.getByRole("button", { name: "Player comparison", exact: true }).click();
  await expect(page.locator(".comparison-table .avatar-photo").first()).toHaveClass(/is-loaded/, { timeout: 20000 });
});

test("unavailable player photos retain initials without breaking the analyzer", async ({ page }) => {
  await page.route("**/_next/image?**", route => route.abort("failed"));
  await page.reload();
  await expect(page.locator(".app-shell")).toHaveAttribute("data-ready", "true");
  await expect(page.locator(".give-side .avatar-photo")).toHaveCount(0);
  await expect(page.locator(".give-side .avatar-initials")).toBeVisible();
  await expect(page.locator(".give-side .avatar-initials")).toHaveText("LD");
  await expect(page.locator(".category-table tbody tr")).toHaveCount(8);
  await page.getByRole("button", { name: "Analyze trade", exact: true }).click();
  await expect(page.locator(".category-table tbody tr")).toHaveCount(8);
});
