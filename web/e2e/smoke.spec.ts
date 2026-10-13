import { expect, test } from "@playwright/test";

const errors: string[] = [];

test.beforeEach(async ({ page }) => {
  errors.length = 0;
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
});

async function ready(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.waitForSelector("body[data-ready=true]");
  await page.waitForFunction(() => window.__gravity!.frames() > 5);
}

test("renders frames, runs live and has no console errors", async ({ page }) => {
  await ready(page);
  expect(await page.evaluate(() => window.__gravity!.live())).toBe(true);
  await expect(page.locator("#clock")).not.toHaveText("----");
  expect(errors).toEqual([]);
});

test("focus on a planet and on a moon from the body list", async ({ page }) => {
  await ready(page);
  await page.locator('#bodies [data-id="Jupiter"]').click();
  expect(await page.evaluate(() => window.__gravity!.focus())).toBe("Jupiter");
  await expect(page.locator("#info-name")).toHaveText("Jupiter");
  await page.locator('#bodies [data-id="Io"]').click();
  expect(await page.evaluate(() => window.__gravity!.focus())).toBe("Io");
});

test("speed controls leave live mode and advance time", async ({ page }) => {
  await ready(page);
  const before = await page.evaluate(() => window.__gravity!.ms());
  await page.locator("#speeds button").last().click();
  await page.waitForTimeout(600);
  expect(await page.evaluate(() => window.__gravity!.live())).toBe(false);
  expect(await page.evaluate(() => window.__gravity!.ms())).toBeGreaterThan(before + 3600_000);
  await page.locator("#live").click();
  expect(await page.evaluate(() => window.__gravity!.live())).toBe(true);
});

test("credits dialog names the texture source and licence", async ({ page }) => {
  await ready(page);
  await page.locator("#credits-open").click();
  await expect(page.locator("#credits")).toContainText("Solar System Scope");
  await expect(page.locator("#credits")).toContainText("CC BY 4.0");
});

test("shows a message when WebGL is unavailable", async ({ page }) => {
  await page.goto("/?nowebgl");
  await expect(page.locator("#nowebgl")).toBeVisible();
  await expect(page.locator("#nowebgl h1")).toHaveText("WebGL is not available");
});

test("no horizontal scroll at 400 px", async ({ page }) => {
  await page.setViewportSize({ width: 400, height: 800 });
  await ready(page);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});

test("command palette: open with /, filter, arrow keys and Enter focus a body", async ({ page }) => {
  await ready(page);
  await page.keyboard.press("/");
  const input = page.getByRole("combobox");
  await expect(input).toBeFocused();
  await input.fill("jup");
  await expect(page.getByRole("option").first()).toHaveText(/Jupiter/);
  await page.keyboard.press("Enter");
  await expect(page.locator("#palette")).not.toBeVisible();
  expect(await page.evaluate(() => window.__gravity!.focus())).toBe("Jupiter");
  await page.keyboard.press("Control+k");
  await page.getByRole("combobox").fill("voy");
  await page.keyboard.press("ArrowDown");
  await expect(page.getByRole("option", { selected: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator("#palette")).not.toBeVisible();
});

test("number keys focus planets and ? opens the shortcut list", async ({ page }) => {
  await ready(page);
  await page.keyboard.press("5");
  expect(await page.evaluate(() => window.__gravity!.focus())).toBe("Jupiter");
  await page.keyboard.press("?");
  await expect(page.locator("#help")).toBeVisible();
});
