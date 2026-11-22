import { test, expect, type Page } from '@playwright/test';

// The login page holds both the sign-in form and student registration, so
// fields are scoped to the sign-in section (as theme.spec.ts does).
async function login(page: Page, password = 'BrowserTestPassword123!') {
    // Wait for hydration: submitting before Svelte attaches its handlers does a
    // native form submit and silently loses the result (see theme.spec.ts).
    await page.waitForFunction(() => '__SVELTEKIT_CLIENT_ROUTING__' in window);
    const signIn = page.locator('section[aria-label="Sign in"]');
    await signIn.getByLabel('Email address').fill('admin@example.com');
    await signIn.getByLabel('Password', { exact: true }).fill(password);
    await signIn.getByRole('button', { name: 'Sign in', exact: true }).click();
}

test('admin login connects every page and persistent management workflow', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/admin/users');
    await expect(page).toHaveURL(/\/login\?next=%2Fadmin%2Fusers$/);
    await login(page);
    await expect(page.getByRole('heading', { name: 'Manage users', exact: true })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Administration' }).getByRole('link', { name:'Manage users' })).toHaveAttribute('aria-current', 'page');

    await page.getByLabel('Full name').fill('Browser Manager');
    await page.getByLabel('Email', { exact: true }).fill('browser.manager@example.com');
    await page.getByLabel('Password', { exact: true }).fill('ManagerPassword123!');
    await page.getByRole('button', { name: 'Create user' }).click();
    const userRow = page.getByRole('row').filter({ hasText: 'browser.manager@example.com' });
    await expect(userRow).toContainText('Active');
    await userRow.getByRole('button', { name: 'Edit' }).click();
    await page.getByLabel('Role').selectOption('marketing_manager');
    await page.getByRole('button', { name: 'Save changes' }).click();
    await expect(userRow).toContainText('marketing_manager');

    const nav = page.getByRole('navigation', { name: 'Administration' });
    await nav.getByRole('link', { name: 'Student Admission Datasets' }).click();
    await page.getByLabel('Upload CSV').setInputFiles('tests/fixtures/browser-campaign.csv');
    await page.getByRole('button', { name: 'Upload dataset' }).click();
    await expect(page.getByRole('status')).toHaveText('Dataset uploaded successfully.');
    await page.getByRole('button', { name: 'Preview / rename' }).click();
    await expect(page.getByRole('cell', { name: 'SEO', exact: true })).toBeVisible();
    await page.getByLabel('Dataset name').fill('Renamed campaign');
    await page.getByRole('button', { name: 'Save name' }).click();
    await expect(page.getByRole('cell', { name: 'Renamed campaign', exact: true })).toBeVisible();

    await nav.getByRole('link', { name: 'System / model configuration' }).click();
    await page.getByLabel('Organization name').fill('Browser Test Organization');
    await page.getByLabel('Report currency').selectOption('INR');
    await page.getByLabel('High probability threshold').fill('0.75');
    await page.getByRole('button', { name: 'Save configuration' }).click();
    await expect(page.getByRole('status')).toHaveText('Configuration saved.');
    await page.reload();
    await expect(page.getByLabel('High probability threshold')).toHaveValue('0.75');

    await nav.getByRole('link', { name: 'Analytics & reports' }).click();
    await expect(page.getByText('Browser Test Organization', { exact: false })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Renamed campaign', exact: true })).toBeVisible();
    const downloadEvent = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download full report (JSON)' }).click();
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
    await login(page, 'incorrect-password');
    await expect(page.getByRole('alert')).toContainText('Invalid email or password');
    await login(page);
    // The external ?next= target is ignored; admins land on their dashboard.
    await expect(page).toHaveURL('/admin/dashboard');
    await expect(page.getByRole('navigation', { name: 'Role navigation' })).toBeVisible();
});