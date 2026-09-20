import { defineConfig } from '@playwright/test';

// Export tests supply their own auth response and do not need an API/database.
export default defineConfig({
    testDir: './tests',
    testMatch: 'reports.spec.ts',
    workers: 1,
    timeout: 60000,
    use: { baseURL: 'http://127.0.0.1:5177', channel: 'chrome', trace: 'retain-on-failure' },
    webServer: {
        command: 'npm.cmd run dev -- --host 127.0.0.1 --port 5177 --strictPort',
        url: 'http://127.0.0.1:5177',
        reuseExistingServer: false
    }
});
