import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    workers: 1,
    timeout: 60000,
    use: {
        actionTimeout: 10000,
        navigationTimeout: 15000,
        baseURL: 'http://127.0.0.1:5175',
        channel: 'chrome',
        trace: 'retain-on-failure'
    },
    webServer: [
        {
            command: '..\\.venv\\Scripts\\python.exe ..\\backend\\browser_test_server.py',
            url: 'http://127.0.0.1:8011',
            reuseExistingServer: false
        },
        {
            command: 'npm.cmd run dev -- --host 127.0.0.1 --port 5175 --strictPort',
            url: 'http://127.0.0.1:5175',
            env: { BACKEND_URL: 'http://127.0.0.1:8011' },
            reuseExistingServer: false
        }
    ]
});
