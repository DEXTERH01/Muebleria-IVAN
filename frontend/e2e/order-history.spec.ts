import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const orderId = '80000000-0000-4000-8000-000000000001';
const code = 'PED-2026-0042';

test('el operador consulta etapas y pagos paginados desde el pedido y el control de pagos', async ({ page }, testInfo) => {
  test.setTimeout(60_000);
  const user = {
    id: '10000000-0000-4000-8000-000000000001', aud: 'authenticated', role: 'authenticated',
    email: 'operator@example.test', app_metadata: { provider: 'email', providers: ['email'] },
    user_metadata: {}, created_at: '2026-01-01T00:00:00Z',
  };
  await page.addInitScript((identity) => localStorage.setItem('sb-phase7-demo-auth-token', JSON.stringify({
    access_token: 'local-operator-token', token_type: 'bearer', expires_in: 3600,
    expires_at: Math.floor(Date.now() / 1000) + 3600, refresh_token: 'local-refresh', user: identity,
  })), user);
  await page.route('https://phase7-demo.supabase.co/auth/v1/user**', (route) => route.fulfill({ json: user }));
  await page.route('http://127.0.0.1:8000/api/v1/auth/me', (route) => route.fulfill({
    json: { data: { userId: user.id, role: 'operator', fullName: 'Operador de prueba', phone: null } },
  }));
  const order = {
    id: orderId, code, quoteId: 'quote-id', customerId: 'customer-id', status: 'finishing', currency: 'PEN',
    totalMinor: 79900, depositRequiredMinor: 39950, paidMinor: 39950, balanceMinor: 39950,
    version: 6, createdAt: '2026-11-28T12:00:00Z', updatedAt: '2026-11-28T17:00:00Z', promisedDate: null,
  };
  await page.route('http://127.0.0.1:8000/api/v1/orders?*', (route) => route.fulfill({
    json: { data: [order], total: 1, page: 1, pageSize: 100 },
  }));
  await page.route('http://127.0.0.1:8000/api/v1/customers?*', (route) => route.fulfill({
    json: { data: [], total: 0, page: 1, pageSize: 100 },
  }));
  let historyUnavailable = true;
  await page.route(`http://127.0.0.1:8000/api/v1/orders/${orderId}`, (route) => {
    if (historyUnavailable) return route.fulfill({ status: 503, json: { detail: 'Historial temporalmente no disponible' } });
    const states = ['confirmed', 'materials_pending', 'cutting', 'assembly', 'finishing'];
    return route.fulfill({ json: { data: { ...order, statusHistory: states.map((state, index) => ({
      previousStatus: states[index - 1] ?? null, newStatus: state,
      occurredAt: `2026-11-28T${String(12 + index).padStart(2, '0')}:00:00Z`,
      note: state === 'finishing' ? `Barniz aplicado. ${'SEGUIMIENTO'.repeat(20)}` : null,
    })) } } });
  });
  const payment = {
    id: 'payment-id', orderId, amountMinor: 39950, currency: 'PEN', method: 'bank_transfer',
    paymentDate: '2026-11-28', status: 'recorded', reference: 'REF-PRIMERA',
  };
  await page.route(`http://127.0.0.1:8000/api/v1/orders/${orderId}/payments?*`, (route) => {
    const query = new URL(route.request().url()).searchParams;
    expect(query.get('pageSize')).toBe('10');
    const number = Number(query.get('page'));
    return route.fulfill({ json: {
      data: number === 1 ? Array.from({ length: 10 }, (_, index) => ({
        ...payment, id: `payment-${index}`, amountMinor: 1000,
        reference: index === 0 ? 'REF-PRIMERA' : `REFERENCIA-${index}`,
      })) : [{ ...payment, id: 'last-payment', status: 'voided', reference: 'REF-REVERTIDA' }],
      total: 11, page: number, pageSize: 10,
    } });
  });

  await page.goto(`/admin/pedido/${code}`);
  await expect(page.locator('.order-header')).toContainText('En acabado');
  const activity = page.locator('.order-activity-grid');
  await expect(activity.getByRole('alert')).toContainText('Historial temporalmente no disponible');
  await expect(activity.getByText('REF-PRIMERA', { exact: true })).toBeVisible();
  historyUnavailable = false;
  await activity.getByRole('button', { name: 'Reintentar historial' }).click();
  await expect(activity.getByText('Barniz aplicado')).toBeVisible();
  await expect(activity.locator('.order-history-list li')).toHaveCount(5);
  await activity.getByRole('button', { name: 'Página siguiente' }).click();
  await expect(activity.getByText('REF-REVERTIDA')).toBeVisible();
  await expect(activity.getByText('Revertido', { exact: true })).toBeVisible();
  expect((await new AxeBuilder({ page }).include('.order-activity-grid').analyze()).violations).toEqual([]);
  for (const width of [360, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const size = await activity.evaluate((element) => ({ content: element.scrollWidth, viewport: element.clientWidth }));
    expect(size.content).toBeLessThanOrEqual(size.viewport);
    if (width !== 768) await activity.screenshot({ path: testInfo.outputPath(`history-${width}.png`) });
  }

  await page.goto('/admin/pagos');
  await page.getByRole('button', { name: `Ver movimientos de ${code}` }).click();
  const dialog = page.getByRole('dialog', { name: `Movimientos de ${code}` });
  await expect(dialog.getByText('REF-PRIMERA', { exact: true })).toBeVisible();
  await dialog.getByRole('button', { name: 'Página siguiente' }).click();
  await expect(dialog.getByText('REF-REVERTIDA')).toBeVisible();
  await dialog.getByRole('button', { name: 'Cerrar', exact: true }).press('Escape');
  await expect(dialog).toHaveCount(0);
});

test('protege también el enlace directo a un pedido sin sesión', async ({ page }) => {
  await page.goto(`/admin/pedido/${code}`);
  await expect(page).toHaveURL(/\/iniciar-sesion\?redirect=/);
  await expect(page.getByRole('heading', { name: 'Inicia sesión' })).toBeVisible();
  await expect(page.getByText('Pedido no disponible')).toHaveCount(0);
});
