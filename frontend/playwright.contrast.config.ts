import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    testMatch: ['contrast.spec.ts', 'responsive.spec.ts'],
    timeout: 120000,
    workers: 1,
    use: { baseURL: 'http://127.0.0.1:5176', channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome' },
    webServer: {
        command: 'node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5176 --strictPort',
        url: 'http://127.0.0.1:5176',
        reuseExistingServer: true
    }
});
