import { test, expect, type Page } from '@playwright/test';

async function login(page: Page) {
    await page.getByLabel('Work Email', { exact: true }).fill('admin@example.com');
    await page.getByLabel('Password', { exact: true }).fill('BrowserTestPassword123!');
    await page.getByRole('button', { name: 'Sign In', exact: true }).click();
}

test('admin login connects every page and persistent management workflow', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/admin/users');
    await expect(page).toHaveURL(/\/login\?next=%2Fadmin%2Fusers$/);
    await login(page);
    await expect(page.getByRole('heading', { name: 'Manage users', exact: true })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Administration' }).getByRole('link', {name:'Manage users'})).toHaveAttribute('aria-current', 'page');

    await page.getByLabel('Full name').fill('Browser Marketer');
    await page.getByLabel('Email', { exact: true }).fill('browser.marketer@example.com');
    await page.getByLabel('Password', { exact: true }).fill('MarketerPassword123!');
    await page.getByRole('button', { name: 'Create user' }).click();
    const userRow = page.getByRole('row').filter({ hasText: 'browser.marketer@example.com' });
    await expect(userRow).toContainText('Active');
    await userRow.getByRole('button', { name: 'Edit' }).click();
    await page.getByLabel('Role').selectOption('executive');
    await page.getByRole('button', { name: 'Save changes' }).click();
    await expect(userRow).toContainText('executive');

    const nav = page.getByRole('navigation', { name: 'Administration' });
    await nav.getByRole('link', { name: 'Marketing datasets' }).click();
    await page.getByLabel('Upload CSV').setInputFiles('tests/fixtures/browser-campaign.csv');
    await page.getByRole('button', {name:'Upload dataset'}).click();
    await expect(page.getByRole('status')).toHaveText('Dataset uploaded successfully.');
    await page.getByRole('button', {name:'Preview / rename'}).click();
    await expect(page.getByRole('cell', {name:'SEO',exact:true})).toBeVisible();
    await page.getByLabel('Dataset name').fill('Renamed campaign');
    await page.getByRole('button', {name:'Save name'}).click();
    await expect(page.getByRole('cell', {name:'Renamed campaign',exact:true})).toBeVisible();

    await nav.getByRole('link', {name:'System / model configuration'}).click();
    await page.getByLabel('Organization name').fill('Browser Test Organization');
    await page.getByLabel('Report currency').selectOption('INR');
    await page.getByLabel('High probability threshold').fill('0.75');
    await page.getByRole('button', {name:'Save configuration'}).click();
    await expect(page.getByRole('status')).toHaveText('Configuration saved.');
    await page.reload();
    await expect(page.getByLabel('High probability threshold')).toHaveValue('0.75');

    await nav.getByRole('link', {name:'Analytics & reports'}).click();
    await expect(page.getByText('Browser Test Organization', {exact:false})).toBeVisible();
    await expect(page.getByRole('cell', {name:'Renamed campaign',exact:true})).toBeVisible();
    const downloadEvent = page.waitForEvent('download');
    await page.getByRole('button', {name:'Download full report (JSON)'}).click();
    const download = await downloadEvent;
    expect(download.suggestedFilename()).toBe('marketing-report.json');
    expect(await download.failure()).toBeNull();

    await nav.getByRole('link', {name:'Marketing datasets'}).click();
    await page.getByRole('button', {name:'Delete',exact:true}).click();
    await page.getByRole('button', {name:'Confirm delete'}).click();
    await expect(page.getByRole('cell', {name:'Renamed campaign',exact:true})).toHaveCount(0);
    await nav.getByRole('link', {name:'Overview',exact:true}).click();
    await expect(page.getByRole('heading', {name:'Administration',exact:true})).toBeVisible();
    await page.getByRole('link', {name:'My account',exact:true}).click();
    await page.getByRole('button', {name:'Sign out',exact:true}).click();
    await expect(page).toHaveURL('/login');
    await page.goto('/admin/reports');
    await expect(page).toHaveURL(/\/login\?next=%2Fadmin%2Freports$/);
    expect(errors).toEqual([]);
});

test('login rejects wrong credentials and ignores external redirect targets', async ({ page }) => {
    await page.goto('/login?next=https://example.com');
    await page.getByLabel('Work Email', {exact:true}).fill('admin@example.com');
    await page.getByLabel('Password', {exact:true}).fill('incorrect-password');
    await page.getByRole('button', {name:'Sign In', exact:true}).click();
    await expect(page.getByRole('alert')).toContainText('Invalid email or password');
    await login(page);
    await expect(page).toHaveURL('/admin');
    await expect(page.getByRole('heading', {name:'Administration',exact:true})).toBeVisible();
});
