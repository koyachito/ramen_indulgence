// @ts-check
const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

const MOBILE_VIEWPORTS = [{ width: 390, height: 844 }];

test.describe("top page", () => {
  test("shows concept copy and link to diagnosis", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/ラーメン免罪符/);
    await expect(page.getByText("ラーメン欲を赦されよう")).toBeVisible();
    await expect(page.getByRole("link", { name: /診断/ })).toBeVisible();
  });

  test("navigates to diagnosis page", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /診断/ }).click();
    await expect(page).toHaveURL(/\/diagnosis/);
  });

  test("accessibility: no critical violations", async ({ page }) => {
    await page.goto("/");
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();
    const critical = results.violations.filter((v) => v.impact === "critical");
    expect(critical).toEqual([]);
  });
});

test.describe("diagnosis page", () => {
  test("shows all 7 questions", async ({ page }) => {
    await page.goto("/diagnosis");
    await expect(page.getByText("QUESTION 1 / 7")).toBeVisible();
    await expect(page.getByText("QUESTION 7 / 7")).toBeVisible();
  });

  test("completes full diagnosis and reaches result", async ({ page }) => {
    await page.goto("/diagnosis");

    const radioGroups = page.locator('fieldset[data-question]');
    const count = await radioGroups.count();
    for (let i = 0; i < count; i++) {
      const group = radioGroups.nth(i);
      const firstRadio = group.locator('input[type="radio"]').first();
      await firstRadio.click();
    }

    await page.locator('form').evaluate((form) => form.submit());
    await expect(page).toHaveURL(/\/result/);
    await expect(page.getByText("近くのラーメンを探す")).toBeVisible();
  });

  test("accessibility: no critical violations", async ({ page }) => {
    await page.goto("/diagnosis");
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();
    const critical = results.violations.filter((v) => v.impact === "critical");
    expect(critical).toEqual([]);
  });
});

test.describe("result page", () => {
  const VALID_FORM = {
    current_hour: "20",
    current_month: "6",
    current_day: "22",
    meals: "1",
    ramen_count_today: "0",
    achievement: "worked",
    mood: "tired",
    after_plan: "work_more",
    reason_not_to_eat: "none",
    ramen_type: "miso",
    forgiveness_style: "praise",
  };

  async function postResult(page) {
    await page.goto("/diagnosis");
    await page.evaluate((data) => {
      const form = document.querySelector("form");
      for (const [name, value] of Object.entries(data)) {
        let el = form.elements.namedItem(name);
        if (!el) {
          el = document.createElement("input");
          el.type = "hidden";
          el.name = name;
          form.appendChild(el);
        }
        if (el.type === "radio") {
          const radio = form.querySelector(`[name="${name}"][value="${value}"]`);
          if (radio) radio.checked = true;
        } else {
          el.value = value;
        }
      }
      form.submit();
    }, VALID_FORM);
    await page.waitForURL(/\/result/);
  }

  test("shows result actions", async ({ page }) => {
    await postResult(page);
    await expect(page.getByText("近くのラーメンを探す")).toBeVisible();
    await expect(page.getByText("赦しの画像を保存")).toBeVisible();
    await expect(page.getByText("赦しの結果をツイート")).toBeVisible();
  });
});

test.describe("about page", () => {
  test("shows creator info", async ({ page }) => {
    await page.goto("/about");
    await expect(page.getByText("koyachito")).toBeVisible();
  });

  test("accessibility: no critical violations", async ({ page }) => {
    await page.goto("/about");
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();
    const critical = results.violations.filter((v) => v.impact === "critical");
    expect(critical).toEqual([]);
  });
});

test.describe("mobile layout", () => {
  for (const viewport of MOBILE_VIEWPORTS) {
    test(`top page is visible at ${viewport.width}x${viewport.height}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto("/");
      await expect(page.getByRole("link", { name: /診断/ })).toBeVisible();
    });

    test(`diagnosis page is visible at ${viewport.width}x${viewport.height}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto("/diagnosis");
      await expect(page.getByText("QUESTION 1 / 7")).toBeVisible();
    });
  }
});
