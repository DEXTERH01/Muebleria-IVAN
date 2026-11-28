import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const user = {
  id: '10000000-0000-4000-8000-000000000001',
  aud: 'authenticated',
  role: 'authenticated',
  email: 'admin@example.test',
  app_metadata: { provider: 'email', providers: ['email'] },
  user_metadata: { full_name: 'Admin Demo' },
  created_at: '2026-01-01T00:00:00Z',
};

const quote = {
  id: '60000000-0000-4000-8000-000000000002',
  code: 'COT-2026-0100',
  status: 'submitted',
  currency: 'PEN',
  contactName: 'María Demo',
  contactEmail: 'maria@example.test',
  contactPhone: null,
  subtotalMinor: 98000,
  adjustmentsMinor: 0,
  totalMinor: 98000,
  depositMinor: 49000,
  expiresAt: '2026-11-28T12:00:00Z',
  version: 1,
  createdAt: '2026-11-21T12:00:00Z',
  updatedAt: '2026-11-21T12:00:00Z',
  items: [{ productName: 'Escritorio Lima' }],
};

test('el administrador aprueba una cotización desde la lista protegida', async ({ page }) => {
  await page.addInitScript((admin) => {
    localStorage.setItem('sb-phase7-demo-auth-token', JSON.stringify({
      access_token: 'phase7-admin-token',
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      refresh_token: 'phase7-admin-refresh',
      user: admin,
    }));
  }, user);

  await page.route('https://phase7-demo.supabase.co/auth/v1/user**', (route) => route.fulfill({ json: user }));
  await page.route('http://127.0.0.1:8000/api/v1/auth/me', (route) => route.fulfill({
    json: { data: { userId: user.id, role: 'admin', fullName: 'Admin Demo', phone: null } },
  }));
  await page.route('http://127.0.0.1:8000/api/v1/orders?*', (route) => route.fulfill({
    json: { data: [], total: 0, page: 1, pageSize: 100 },
  }));

  let status: 'submitted' | 'approved' = 'submitted';
  await page.route('http://127.0.0.1:8000/api/v1/quotes?*', (route) => route.fulfill({
    json: { data: { items: [{ ...quote, status }], total: 1, page: 1, pageSize: 100 } },
  }));
  await page.route(`http://127.0.0.1:8000/api/v1/quotes/${quote.id}/status`, async (route) => {
    const request = route.request();
    expect(request.method()).toBe('PATCH');
    expect(request.postDataJSON()).toEqual({ status: 'approved', expectedVersion: 1 });
    status = 'approved';
    await route.fulfill({ json: { data: { ...quote, status, version: 2 } } });
  });

  await page.goto('/admin/cotizaciones');
  await expect(page.getByRole('heading', { name: 'Cotizaciones' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'María Demo' })).toBeVisible();

  const accessibility = await new AxeBuilder({ page }).analyze();
  expect(accessibility.violations).toEqual([]);

  for (const width of [360, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const dimensions = await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      content: document.documentElement.scrollWidth,
    }));
    expect(dimensions.content, `La administración desborda a ${width} px`)
      .toBeLessThanOrEqual(dimensions.viewport);
  }

  await page.getByRole('button', { name: 'Aprobar' }).click();
  await expect(page.getByRole('button', { name: 'Convertir en pedido' })).toBeVisible();
  await expect(page.getByRole('status')).toContainText('Cotización aprobada.');
});
