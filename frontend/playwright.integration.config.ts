import { defineConfig, devices } from '@playwright/test';

const databaseUrl = process.env.SUPABASE_TEST_DATABASE_URL;
const authUrl = process.env.SUPABASE_TEST_URL;
const publishableKey = process.env.SUPABASE_TEST_PUBLISHABLE_KEY;
if (!databaseUrl || !authUrl || !publishableKey) {
  throw new Error('Configura SUPABASE_TEST_* con supabase status para la prueba local.');
}
for (const value of [databaseUrl, authUrl]) {
  if (!['127.0.0.1', 'localhost', '[::1]'].includes(new URL(value).hostname)) {
    throw new Error('La prueba crea datos y solo admite Supabase local desechable.');
  }
}

export default defineConfig({
  testDir: './integration',
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:4175', trace: 'off' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: '../backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port 8015',
      url: 'http://127.0.0.1:8015/health',
      reuseExistingServer: false,
      env: {
        MUEBLERIA_ENVIRONMENT: 'test', MUEBLERIA_DATABASE_URL: databaseUrl,
        MUEBLERIA_SUPABASE_URL: authUrl,
        MUEBLERIA_CORS_ORIGINS: '["http://127.0.0.1:4175"]',
      },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 4175 --strictPort',
      url: 'http://127.0.0.1:4175',
      reuseExistingServer: false,
      env: {
        VITE_API_BASE_URL: 'http://127.0.0.1:8015',
        VITE_SUPABASE_URL: authUrl, VITE_SUPABASE_ANON_KEY: publishableKey,
      },
    },
  ],
});
