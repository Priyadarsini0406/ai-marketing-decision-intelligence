import { test, expect, type Page } from '@playwright/test';

async function download(page: Page, format: string) {
    const waiting = page.waitForEvent('download');
    await page.getByRole('button', { name: `Download entire analytics (${format})`, exact: true }).click();
    const file = await waiting;
    expect(await file.failure()).toBeNull();
    expect(file.suggestedFilename()).toBe(`admission-marketing-analytics.${format.toLowerCase()}`);
    const stream = await file.createReadStream();
    const chunks: Uint8Array[] = [];
    for await (const chunk of stream!) chunks.push(new Uint8Array(chunk));
    const bytes = new Uint8Array(chunks.reduce((total, chunk) => total + chunk.length, 0));
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    return bytes;
}

test('complete analytics exports include all sections despite an empty preview', async ({ page }) => {
    await page.addInitScript(() => sessionStorage.setItem('session', 'report-test'));
    await page.route('**/api/auth/me', route => route.fulfill({ json: { id: 'report-test', name: 'Report Manager', role: 'admission_manager', email: 'reports@example.com', active: true } }));
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/reports');
    await expect(page.getByRole('heading', { name: 'Reports & Analytics', level: 1 })).toBeVisible();
    await page.getByLabel('Search report').fill('no matching report record');
    await expect(page.locator('tbody tr')).toHaveCount(0);
    const json = JSON.parse(new TextDecoder().decode(await download(page, 'JSON')));
    expect(Object.keys(json.reports)).toHaveLength(6);
    expect(json.reports.lead).toHaveLength(6);
    expect(json.reports.channel).toHaveLength(7);
    expect(json.reports.campaign).toHaveLength(5);
    expect(json.reports.budget.reduce((total: number, row: { allocation_inr: number }) => total + row.allocation_inr, 0)).toBe(json.budget_summary.total_budget_inr);
    expect(json.segments).toHaveLength(3);
    expect(json.recommendations).toHaveLength(3);
    expect(json.scenario_comparison.simulated.admissions).toBe(224);
    expect(json.explanation.positive).toHaveLength(4);

    const csv = new TextDecoder().decode(await download(page, 'CSV')).replace(/^\uFEFF/, '');
    expect(csv.split('\r\n')[0]).toBe('"section","record","field","value"');
    for (const section of ['metadata', ...Object.keys(json.reports), 'budget_summary', 'segments', 'recommendations', 'scenario_comparison', 'explanation_summary', 'explanation_factors']) {
        expect(csv).toContain(`"${section}",`);
    }
    expect(csv).toContain('"lead","6","student_name","Vikram Singh"');
    expect(csv).toContain('"budget_summary","1","total_budget_inr","1000000"');
    expect(csv).toContain('"scenario_comparison","2","admissions","224"');

    const pdf = new TextDecoder('iso-8859-1').decode(await download(page, 'PDF'));
    expect(pdf).toMatch(/^%PDF-/);
    expect(pdf).toContain('%%EOF');
    for (const title of ['Lead Report', 'Prediction Report', 'Funnel Report', 'Channel Report', 'Campaign Report', 'Budget Report', 'Budget summary', 'Student segmentation', 'AI recommendations', 'What-if scenario comparison', 'Explainable AI summary', 'Explainable AI factors']) {
        expect(pdf).toContain(title);
    }
    expect(pdf).toContain('Vikram Singh');
    expect((pdf.match(/\/Type \/Page\b/g) || []).length).toBeGreaterThan(10);
    await page.setViewportSize({ width: 390, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.getByRole('button', { name: 'Download entire analytics (PDF)', exact: true })).toBeVisible();
    expect(errors).toEqual([]);
});
