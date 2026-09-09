import { test, expect } from '@playwright/test';

test('public links, registration, and all dashboard pages are connected', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('/');
    await page.getByRole('link', {name:'Features', exact:true}).click();
    await expect(page.locator('#features')).toBeInViewport();
    for (const route of ['/privacy','/terms','/forgot-password','/login','/register']) {
        const response = await page.goto(route);
        expect(response?.status()).toBe(200);
        await expect(page.locator('h1, h2').first()).toBeVisible();
    }
    await page.goto('/register');
    await page.getByLabel('Full Name').fill('Navigation User');
    await page.getByLabel('Work Email').fill('navigation@example.com');
    await page.getByLabel('Password', {exact:true}).fill('NavigationPassword123!');
    await page.getByRole('button', {name:'Register', exact:true}).click();
    await expect(page).toHaveURL('/dashboard');
    const nav = page.getByRole('navigation', {name:'Marketing dashboard'});
    await nav.getByRole('link', {name:'Leads & Predictions'}).click();
    await expect(page.getByRole('cell', {name:'TEST-LEAD', exact:true})).toBeVisible();
    await page.getByLabel('Lead', {exact:false}).selectOption({label:'TEST-LEAD'});
    await page.getByRole('button', {name:'View prediction'}).click();
    await expect(page.getByRole('cell', {name:'Test segment', exact:true})).toBeVisible();
    await nav.getByRole('link', {name:'Attribution & Segments'}).click();
    await expect(page.getByRole('cell', {name:'SEO', exact:true})).toBeVisible();
    await nav.getByRole('link', {name:'Budget Simulator'}).click();
    await expect(page.getByRole('cell', {name:'Test budget', exact:true})).toBeVisible();
    await expect(nav.getByRole('link', {name:'Budget Simulator'})).toHaveAttribute('aria-current','page');
    await nav.getByRole('link', {name:'Overview', exact:true}).click();
    const downloaded = page.waitForEvent('download');
    await page.getByRole('button', {name:'Export Report'}).click();
    expect((await downloaded).suggestedFilename()).toBe('marketing-summary.json');
    await page.getByRole('button', {name:'Sign out', exact:true}).click();
    await expect(page).toHaveURL('/login');
    await page.goto('/dashboard/budget');
    await expect(page).toHaveURL(/\/login\?next=%2Fdashboard%2Fbudget$/);
    await page.getByLabel('Work Email').fill('navigation@example.com');
    await page.getByLabel('Password', {exact:true}).fill('NavigationPassword123!');
    await page.getByRole('button', {name:'Sign In',exact:true}).click();
    await expect(page).toHaveURL('/dashboard/budget');
    await expect(page.getByRole('cell', {name:'Test budget',exact:true})).toBeVisible();
    expect(errors).toEqual([]);
});
