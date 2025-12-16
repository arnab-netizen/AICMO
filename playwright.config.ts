import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for AICMO Revenue Marketing Engine E2E tests.
 * 
 * CRITICAL: These tests run against Streamlit in E2E mode with proof-run enforcement.
 * NO real emails, DMs, or posts are sent during tests.
 */
export default defineConfig({
  testDir: './tests/playwright',
  
  // Run tests serially for deterministic DB state
  fullyParallel: false,
  workers: 1,
  
  // No retries - if test fails, fix the bug
  retries: 0,
  
  // Timeout per test (Streamlit can be slow on first load)
  timeout: 60000,
  
  // Reporter
  reporter: [
    ['html'],
    ['list']
  ],
  
  use: {
    // Base URL for all tests
    baseURL: 'http://127.0.0.1:8501',
    
    // Trace on first retry only (we have retries=0, so this won't happen)
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Viewport
    viewport: { width: 1280, height: 720 },
  },

  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        launchArgs: ['--headless=new'],
      },
    },
  ],

  // Do NOT start web server automatically - must be started manually with correct env vars
  // This ensures AICMO_E2E_MODE=1 and AICMO_PROOF_RUN=1 are set
  webServer: undefined,
});
