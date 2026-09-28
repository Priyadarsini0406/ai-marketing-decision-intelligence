import { test, expect, type Page } from '@playwright/test';

const DARK_BG = 'rgb(9, 8, 13)';       // #09080d, design of record
const LIGHT_BG = 'rgb(247, 245, 242)'; // #F7F5F2

/**
 * Navigates and waits for hydration. The theme class is applied pre-paint by
 * app.html, so the button is visible from SSR HTML — clicking before Svelte
 * attaches its listeners would silently do nothing.
 */
async function gotoHydrated(page: Page, path: string) {
    await page.goto(path);
    await page.waitForFunction(() => '__SVELTEKIT_CLIENT_ROUTING__' in window);
}

const isLight = (page: Page) =>
    page.evaluate(() => document.documentElement.classList.contains('di-light'));

const bodyBg = (page: Page) =>
    page.evaluate(() => getComputedStyle(document.body).backgroundColor);

const storedTheme = (page: Page) =>
    page.evaluate(() => localStorage.getItem('di-theme'));

const toLight = (page: Page) => page.getByRole('button', { name: 'Switch to light theme' });
const toDark = (page: Page) => page.getByRole('button', { name: 'Switch to dark theme' });

/**
 * Clicks the toggle and waits for the theme to settle. Retried because SSR
 * renders the button before Svelte attaches its listener, so a click issued
 * in the first moments after load is dropped. The retry still fails the test
 * if the toggle is genuinely broken.
 */
async function expectSwitch(page: Page, target: 'light' | 'dark') {
    const button = target === 'light' ? toLight(page) : toDark(page);
    await expect(async () => {
        await button.click();
        expect(await isLight(page)).toBe(target === 'light');
    }).toPass({ timeout: 15000 });
    expect(await storedTheme(page)).toBe(target);
    expect(await bodyBg(page)).toBe(target === 'light' ? LIGHT_BG : DARK_BG);
    expect(await page.evaluate(() => document.documentElement.style.colorScheme)).toBe(target);
}

test('dark is the default theme and the toggle switches to light', async ({ page }) => {
    await gotoHydrated(page, '/');

    expect(await isLight(page)).toBe(false);
    expect(await storedTheme(page)).toBeNull();      // nothing stored yet
    expect(await bodyBg(page)).toBe(DARK_BG);
    expect(await page.evaluate(() => document.documentElement.style.colorScheme)).toBe('dark');
    await expect(toLight(page)).toBeVisible();

    await expectSwitch(page, 'light');
    await expect(toDark(page)).toBeVisible();
});

test('the selected theme survives a reload', async ({ page }) => {
    await gotoHydrated(page, '/');
    await expectSwitch(page, 'light');

    await page.reload();
    // Applied before paint, so it is already correct without hydration.
    expect(await isLight(page)).toBe(true);
    expect(await bodyBg(page)).toBe(LIGHT_BG);

    await expectSwitch(page, 'dark');
    await page.reload();
    expect(await isLight(page)).toBe(false);
    expect(await bodyBg(page)).toBe(DARK_BG);
});

test('the toggle is present and functional on landing, login and register', async ({ page }) => {
    for (const route of ['/', '/login', '/register']) {
        await gotoHydrated(page, route);
        await expect(toLight(page)).toBeVisible();
        await expectSwitch(page, 'light');
        await expectSwitch(page, 'dark');
    }
});

test('both themes are available inside a signed-in dashboard and do not shift layout', async ({ page }) => {
    await gotoHydrated(page, '/login');
    const signIn = page.locator('section[aria-label="Sign in"]');
    await signIn.getByLabel('Email address').fill('admin@example.com');
    await signIn.getByLabel('Password', { exact: true }).fill('BrowserTestPassword123!');
    await signIn.getByRole('button', { name: 'Sign in', exact: true }).click();
    await expect(page).not.toHaveURL('/login');
    await page.waitForFunction(() => '__SVELTEKIT_CLIENT_ROUTING__' in window);

    await expect(toLight(page)).toBeVisible();
    expect(await bodyBg(page)).toBe(DARK_BG);
    const darkBox = await page.locator('main').boundingBox();

    await expectSwitch(page, 'light');
    const lightBox = await page.locator('main').boundingBox();

    // Same components in both themes: the shell must not reflow.
    expect(Math.abs((darkBox?.width ?? 0) - (lightBox?.width ?? 0))).toBeLessThan(2);
    expect(Math.abs((darkBox?.height ?? 0) - (lightBox?.height ?? 0))).toBeLessThan(2);
});

test('the login/register flip card still works in both themes', async ({ page }) => {
    await gotoHydrated(page, '/login');
    const flip = page.locator('.flip');

    await expect(flip).not.toHaveClass(/flipped/);
    await page.getByRole('button', { name: 'Create a student account' }).click();
    await expect(flip).toHaveClass(/flipped/);

    // Flip back while the light palette is active.
    await expectSwitch(page, 'light');
    await page.getByRole('button', { name: 'Sign in instead' }).click();
    await expect(flip).not.toHaveClass(/flipped/);
    expect(await isLight(page)).toBe(true);
});
