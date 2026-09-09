import { test, expect } from '@playwright/test';
import { workspacePages } from '../src/lib/workspace-pages';

test('marketing workspace pages, inference, budgets, preferences, and reports', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/register');
    await page.getByLabel('Full Name').fill('Workspace User');
    await page.getByLabel('Work Email').fill('workspace@example.com');
    await page.getByLabel('Password', {exact:true}).fill('WorkspacePassword123!');
    await page.getByRole('button', {name:'Register',exact:true}).click();
    await expect(page).toHaveURL('/dashboard');
    const nav = page.getByRole('navigation', {name:'Marketing dashboard'});
    for (const item of workspacePages) {
        await nav.getByRole('link', {name:item.label,exact:true}).click();
        await expect(page.getByRole('heading', {name:item.label,exact:true})).toBeVisible();
        await expect(page.getByText('Loading...', {exact:true})).toHaveCount(0);
        await expect(page.getByRole('alert')).toHaveCount(0);
    }
    await page.getByLabel('Preferred display currency').selectOption('INR');
    await page.getByLabel('Compact workspace spacing').check();
    await page.getByRole('button', {name:'Save preferences'}).click();
    await expect(page.getByRole('status')).toHaveText('Preferences saved.');
    await page.reload();
    await expect(page.getByLabel('Preferred display currency')).toHaveValue('INR');
    await expect(page.getByLabel('Compact workspace spacing')).toBeChecked();
    await nav.getByRole('link', {name:'Budget Optimization',exact:true}).click();
    await page.getByLabel('Total budget (source currency)').fill('1000');
    await page.getByRole('button', {name:'Calculate allocation'}).click();
    await expect(page.getByRole('heading', {name:'Scenario result'})).toBeVisible();
    await nav.getByRole('link', {name:'What-If Simulator',exact:true}).click();
    await page.getByLabel('Total budget (source currency)').fill('1000');
    await page.getByLabel('SEO allocation', {exact:true}).fill('1000');
    await page.getByRole('button', {name:'Run simulation'}).click();
    await expect(page.getByText('Estimated conversions: 10', {exact:false})).toBeVisible();
    await nav.getByRole('link', {name:'Conversion Prediction',exact:true}).click();
    await page.getByRole('combobox', {name:'Lead',exact:true}).selectOption({label:'TEST-LEAD'});
    await page.getByRole('button', {name:'Predict conversion',exact:true}).click();
    await expect(page.getByRole('heading', {name:/Conversion probability:/})).toBeVisible();
    await nav.getByRole('link', {name:'Explainable AI',exact:true}).click();
    await page.getByRole('combobox', {name:'Lead',exact:true}).selectOption({label:'TEST-LEAD'});
    await page.getByRole('button', {name:'Explain prediction'}).click();
    await expect(page.getByRole('columnheader', {name:'log odds contribution'})).toBeVisible();
    await nav.getByRole('link', {name:'Reports',exact:true}).click();
    const download = page.waitForEvent('download');
    await page.getByRole('button', {name:'Export report (JSON)'}).click();
    expect((await download).suggestedFilename()).toBe('marketing-workspace-report.json');
    expect(errors).toEqual([]);
});
