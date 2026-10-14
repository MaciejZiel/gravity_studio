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
});

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

test("stops drawing when paused and nothing moves, and resumes on input", async ({ page }) => {
  await ready(page);
  await page.locator("#play").click(); // leaves live mode and pauses
  await page.waitForTimeout(1500);
  const f0 = await page.evaluate(() => window.__gravity!.frames());
  await page.waitForTimeout(700);
  expect(await page.evaluate(() => window.__gravity!.frames())).toBe(f0);
  await page.locator('#bodies [data-id="Mars"]').click();
  await page.waitForTimeout(400);
  expect(await page.evaluate(() => window.__gravity!.frames())).toBeGreaterThan(f0);
});

test("shows a reload prompt when the WebGL context is lost and recovers when it returns", async ({ page }) => {
  await ready(page);
  await page.evaluate(() => {
    const gl = (document.getElementById("view") as HTMLCanvasElement).getContext("webgl2") ?? (document.getElementById("view") as HTMLCanvasElement).getContext("webgl");
    (window as unknown as { __ext: WEBGL_lose_context }).__ext = gl!.getExtension("WEBGL_lose_context")!;
    (window as unknown as { __ext: WEBGL_lose_context }).__ext.loseContext();
  });
  await expect(page.locator("#contextlost")).toBeVisible();
  await expect(page.locator("#reload")).toBeVisible();
  await page.evaluate(() => (window as unknown as { __ext: WEBGL_lose_context }).__ext.restoreContext());
  await expect(page.locator("#contextlost")).toBeHidden();
  const f0 = await page.evaluate(() => window.__gravity!.frames());
  await page.waitForFunction((n) => window.__gravity!.frames() > n + 3, f0);
});

test("global shortcuts do not fire while the credits dialog is open", async ({ page }) => {
  await ready(page);
  await page.locator("#credits-open").click();
  await page.keyboard.press("5");
  expect(await page.evaluate(() => window.__gravity!.focus())).toBe("Sun");
  await page.keyboard.press("Escape");
  await expect(page.locator("#credits")).not.toHaveAttribute("open", "");
  await page.locator("#view").focus();
  await page.keyboard.press("5");
  expect(await page.evaluate(() => window.__gravity!.focus())).toBe("Jupiter");
});

test("tabs move with arrow keys and point at their panels", async ({ page }) => {
  await page.setViewportSize({ width: 400, height: 800 });
  await ready(page);
  const time = page.locator("#tab-time");
  await expect(time).toHaveAttribute("aria-controls", "panel-time");
  await time.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator("#tab-view")).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("#tab-view")).toBeFocused();
  await expect(page.locator("#panel-view")).toBeVisible();
  await page.keyboard.press("End");
  await expect(page.locator("#tab-tours")).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("ArrowRight");
  await expect(page.locator("#tab-time")).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("#tab-view")).toHaveAttribute("tabindex", "-1");
});
