const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results.json' }]
  ],
  projects: [
    {
      name: 'local',
      use: {
        baseURL: 'http://localhost:8000',
        browserName: 'chromium',
        headless: true,
        viewport: { width: 1280, height: 720 },
        trace: 'on-first-retry',
      },
    },
    
    {
      name: 'staging',
      use: {
        // TODO(Engagement): replace with your actual staging URL
        baseURL: 'https://staging.example.com',
        browserName: 'chromium',
        headless: true,
        viewport: { width: 1280, height: 720 },
        trace: 'on-first-retry',
      },
    },
    {
      name: 'production',
      use: {
        // TODO(Engagement): replace with your actual production URL
        baseURL: 'https://www.example.com',
        browserName: 'chromium',
        headless: true,
        viewport: { width: 1280, height: 720 },
        trace: 'on-first-retry',
      },
    },
    {
      name: 'staging-mobile',
      use: {
        // TODO(Engagement): replace with your actual staging URL
        baseURL: 'https://staging.example.com',
        browserName: 'chromium',
        headless: true,
        viewport: { width: 800, height: 600 },
        trace: 'on-first-retry',
      },
    },
    {
      name: 'production-mobile',
      use: {
        // TODO(Engagement): replace with your actual production URL
        baseURL: 'https://www.example.com',
        browserName: 'chromium',
        headless: true,
        viewport: { width: 800, height: 600 },
        trace: 'on-first-retry',
      },
    },
    // Special project for link checking - no traces/screenshots to avoid thousands of files
    {
      name: 'link-checker',
      testMatch: /check-links\.spec\.js$/,
      use: {
        browserName: 'chromium',
        headless: true,
        viewport: { width: 1280, height: 720 },
        screenshot: 'off',
        video: 'off',
        trace: 'off',
      },
      timeout: 1800000, // 30 minutes for link checking
      retries: 0, // Don't retry link checks
    },
  ],
  use: {
    screenshot: 'on',
    video: 'off',
  },
  testDir: './tests',
  testMatch: ['**/*.spec.js'],
  timeout: 90000,
  retries: 1,
});