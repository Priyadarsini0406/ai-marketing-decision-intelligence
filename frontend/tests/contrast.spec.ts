import { test, expect } from '@playwright/test';

for (const mode of ['dark', 'light']) {
    test(`${mode}: public and portal text stays readable at rest and on hover`, async ({ context }) => {
        await context.addInitScript(value => localStorage.setItem('di-theme', value), mode);
        for (const [path, audience] of [
            ['/', 'student'], ['/login', 'student'], ['/register', 'student'], ['/forgot-password', 'student'],
            ['/student/settings', 'student'], ['/settings', 'admission_manager'], ['/admin/account', 'admin']
        ]) {
            const page = await context.newPage();
        await page.route('**/api/**', async route => {
            const path = new URL(route.request().url()).pathname;
            const data = path === '/api/auth/me'
                ? { id: 'contrast-user', name: 'Contrast Tester', email: 'tester@example.com', role: audience, active: true }
                : path.includes('notifications') ? [] : {};
            await route.fulfill({ json: data });
        });

            await page.goto(path);
            if (path === '/student/settings' || path === '/settings' || path === '/admin/account') await expect(page.locator('aside').first()).toBeVisible();
            await expect(page.locator('html')).toHaveClass(mode === 'light' ? /di-light/ : /^(?!.*di-light).*$/);
            for (const state of ['rest', 'hover']) {
                if (state === 'hover') {
                    const primary = page.locator('button:not(:disabled), a.di-btn').filter({ visible: true }).first();
                    if (await primary.count()) await primary.hover();
                }
            const failures = await page.evaluate(() => {
                const luminance = (rgb: number[]) => rgb.map(v => {
                    const c = v / 255;
                    return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4;
                }).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
                const parse = (value: string) => {
                    const values = (value.match(/[\d.]+/g) ?? []).map(Number);
                    return value.startsWith('color(srgb ') ? values.map((v, i) => i < 3 ? v * 255 : v) : values;
                };
                const ratio = (a: number[], b: number[]) => {
                    const x = luminance(a), y = luminance(b);
                    return (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
                };
                const result: string[] = [];
                for (const element of document.querySelectorAll<HTMLElement>('button, a, input, textarea, h1, h2, h3, p, label, td, th, li, dt, dd, small, strong, span')) {
                    if (!element.checkVisibility() || !element.getBoundingClientRect().width) continue;
                    if (element instanceof HTMLInputElement && ['checkbox', 'radio', 'range', 'color', 'hidden'].includes(element.type)) continue;
                    if (!['INPUT', 'TEXTAREA'].includes(element.tagName) && !Array.from(element.childNodes).some(node => node.nodeType === Node.TEXT_NODE && node.textContent?.trim())) continue;
                    const css = getComputedStyle(element);
                    const foreground = parse(css.color).slice(0, 3);
                    let background: number[] | undefined;
                    const gradient = css.backgroundImage.match(/rgba?\([^)]+\)/g);
                    if (gradient) {
                        for (const stop of gradient) {
                            const color = parse(stop);
                            if ((color[3] ?? 1) === 1 && ratio(foreground, color.slice(0, 3)) < 4.5) result.push(`${element.textContent?.trim()}: gradient contrast`);
                        }
                        continue;
                    }
                    let node: HTMLElement | null = element;
                    while (node) {
                        const nodeStyle = getComputedStyle(node);
                        const stops = nodeStyle.backgroundImage.match(/rgba?\([^)]+\)/g);
                        if (stops) {
                            for (const stop of stops) {
                                const color = parse(stop);
                                if ((color[3] ?? 1) === 1 && ratio(foreground, color.slice(0, 3)) < 4.5) result.push(`${element.textContent?.trim()}: parent gradient contrast`);
                            }
                            break;
                        }
                        const color = parse(nodeStyle.backgroundColor);
                        if ((color[3] ?? 1) === 1) { background = color.slice(0, 3); break; }
                        node = node.parentElement;
                    }
                    if (background && ratio(foreground, background) < 4.5) result.push(`${element.textContent?.trim() || element.tagName}: ${css.color}`);
                }
                return result;
            });
            expect(failures, `${mode} ${path} ${state}`).toEqual([]);
            }
            await page.close();
        }
    });
}
