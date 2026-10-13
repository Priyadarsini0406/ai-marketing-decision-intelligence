import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    workers: 1,
    timeout: 60000,
    use: {
        actionTimeout: 10000,
        navigationTimeout: 15000,
        baseURL: 'http://127.0.0.1:5175',
        channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome',
        trace: 'retain-on-failure'
    },
    webServer: [
        {
            command: 'node ../scripts/run-python.mjs ../backend/browser_test_server.py',
            url: 'http://127.0.0.1:8011',
            reuseExistingServer: false
        },
        {
            command: 'node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5175 --strictPort',
            url: 'http://127.0.0.1:5175',
            env: { BACKEND_URL: 'http://127.0.0.1:8011' },
            reuseExistingServer: false
        }
    ]
});
