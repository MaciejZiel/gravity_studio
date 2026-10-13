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

test("announces the selection once and keeps the changing numbers out of a live region", async ({ page }) => {
  await ready(page);
  await expect(page.locator("#info")).not.toHaveAttribute("aria-live", /.+/);
  await expect(page.locator("#announce")).toHaveText("");
  await page.locator('#bodies [data-id="Jupiter"]').click();
  await expect(page.locator("#announce")).toHaveText("Jupiter, Planet");
  const mutations = await page.evaluate(
    () =>
      new Promise<number>((resolve) => {
        let n = 0;
        const obs = new MutationObserver((list) => (n += list.length));
        obs.observe(document.getElementById("announce")!, { childList: true, characterData: true, subtree: true });
        setTimeout(() => resolve(n), 1200);
      }),
  );
  expect(mutations).toBe(0);
test.describe("reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("camera jumps instantly and tours wait for Next", async ({ page }) => {
    await ready(page);
    await page.locator('#bodies [data-id="Jupiter"]').click();
    await page.waitForFunction(() => window.__gravity!.frames() > 0);
    const d0 = await page.evaluate(() => window.__gravity!.distance());
    await page.waitForTimeout(600);
    const d1 = await page.evaluate(() => window.__gravity!.distance());
    expect(Math.abs(d1 - d0)).toBeLessThan(1e-6);
    expect(d0).toBeLessThan(3);

    await page.locator("#tours button").first().click();
    const title = await page.locator("#tour-title").textContent();
    await page.waitForTimeout(8000);
    await expect(page.locator("#tour-title")).toHaveText(title!);
    await page.locator("#tour-next").click();
    await expect(page.locator("#tour-title")).not.toHaveText(title!);
  });
});

test("without the preference the camera eases toward a new focus", async ({ page }) => {
  await ready(page);
  await page.locator('#bodies [data-id="Jupiter"]').click();
  const d0 = await page.evaluate(() => window.__gravity!.distance());
  await page.waitForTimeout(600);
  const d1 = await page.evaluate(() => window.__gravity!.distance());
  expect(Math.abs(d1 - d0)).toBeGreaterThan(0.05);
});
