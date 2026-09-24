import { test, expect, type Page } from '@playwright/test';

async function loginAsManager(page: Page) {
  await page.goto('/login');
  await page.locator('#login-email').fill('manager@test.com');
  await page.locator('#login-password').fill('Manager@123');
  await page.locator('form').filter({ has: page.locator('#login-email') }).getByRole('button', { name: 'Sign In' }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}

test('manager analytics routes render the expected channel and campaign dashboards', async ({ page }) => {
  await loginAsManager(page);
  await page.goto('/channel-attribution');
  await expect(page.locator('h1', { hasText: 'Channel Attribution' })).toBeVisible();

  await page.goto('/campaign-analytics');
  await expect(page.locator('h1', { hasText: 'Campaign Analytics' })).toBeVisible();
});
