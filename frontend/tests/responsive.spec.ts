import { test, expect } from '@playwright/test';

const devices = [
    { name: 'small phone', width: 320, height: 568 },
    { name: 'phone', width: 390, height: 844 },
    { name: 'phone landscape', width: 844, height: 390 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'small laptop', width: 1024, height: 768 },
    { name: 'desktop', width: 1440, height: 900 }
];

for (const device of devices) {
  for (const mode of ['light', 'dark']) {
    test(`${mode} ${device.name}: pages fit and navigation remains usable`, async ({ context }) => {
        await context.addInitScript(value => localStorage.setItem('di-theme', value), mode);
        for (const [path, role] of [
            ['/', 'student'], ['/register', 'student'], ['/login', 'student'],
            ['/student/settings', 'student'], ['/student/enquiries/new', 'student'],
            ['/settings', 'admission_manager'], ['/reports', 'admission_manager'], ['/admin/account', 'admin']
        ]) {
            const page = await context.newPage();
            await page.setViewportSize(device);
            await page.route('**/api/**', async route => {
                const url = new URL(route.request().url()).pathname;
                await route.fulfill({ json: url === '/api/auth/me'
                    ? { id: 'responsive-user', name: 'Responsive Tester', email: 'test@example.com', role, active: true }
                    : url.includes('notifications') || url.includes('courses') || url.includes('institutions') ? [] : {} });
            });
            await page.goto(path);
            await page.waitForFunction(() => '__SVELTEKIT_CLIENT_ROUTING__' in window);
            const portal = !['/', '/register', '/login'].includes(path);
            if (portal) await expect(page.locator('aside').first()).toBeAttached();
            const overflow = await page.evaluate(() => {
                const failures: string[] = [];
                for (const element of document.querySelectorAll<HTMLElement>('body, main, .sh-content, .st-content, .stage, .form-pane, .di-header')) {
                    if (element.checkVisibility() && element.scrollWidth > element.clientWidth + 2) failures.push(`${element.className || element.tagName}: ${element.scrollWidth} > ${element.clientWidth}`);
                }
                return failures;
            });
            expect(overflow, `${device.name} ${path}`).toEqual([]);
            if (portal && device.width < 1024) {
                await page.getByRole('button', { name: 'Open navigation', exact: true }).click();
                const navigation = page.getByRole('navigation', { name: 'Role navigation' });
                await expect(navigation).toBeInViewport();
                await page.getByRole('button', { name: 'Close navigation', exact: true }).last().click();
                await expect(navigation).not.toBeInViewport();
            }
            if (portal) {
                await page.getByRole('button', { name: /notifications/i }).first().click();
                const panel = page.locator('.hbell-panel');
                await expect(panel).toBeVisible();
                const bounds = await panel.boundingBox();
                expect(bounds!.x).toBeGreaterThanOrEqual(0);
                expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(device.width + 1);
            }
            await page.close();
        }
    });
  }
}
