import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('registra un pago con voucher privado y reintenta sin volver a subirlo', async ({ page }, testInfo) => {
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
  let paid = false;
  const orderId = '80000000-0000-4000-8000-000000000001';
  await page.route('http://127.0.0.1:8000/api/v1/orders?*', (route) => route.fulfill({
    json: { data: [{
      id: orderId, code: 'PED-2026-0042', quoteId: 'quote-id', customerId: 'customer-id',
      status: 'ready', currency: 'PEN', totalMinor: 79900, depositRequiredMinor: 39950,
      paidMinor: paid ? 79900 : 39950, balanceMinor: paid ? 0 : 39950,
      version: 1, createdAt: '2026-11-28T12:00:00Z', updatedAt: '2026-11-28T12:00:00Z', promisedDate: null,
    }], total: 1, page: 1, pageSize: 100 },
  }));
  await page.route('http://127.0.0.1:8000/api/v1/customers?*', (route) => route.fulfill({
    json: { data: [], total: 0, page: 1, pageSize: 100 },
  }));
  const publicId = `muebleria-ivan/vouchers/${user.id}/receipt.pdf`;
  let uploads = 0;
  await page.route('http://127.0.0.1:8000/api/v1/media/signature', (route) => {
    expect(route.request().postDataJSON()).toEqual({ purpose: 'payment_voucher', format: 'pdf' });
    return route.fulfill({ json: { data: {
      cloudName: 'test-cloud', apiKey: 'test-api-key', timestamp: 123, signature: 'signed-upload',
      publicId, resourceType: 'raw', deliveryType: 'private', format: 'pdf',
      uploadUrl: 'https://api.cloudinary.com/v1_1/test-cloud/raw/upload',
    } } });
  });
  await page.route('https://api.cloudinary.com/v1_1/test-cloud/raw/upload', (route) => {
    uploads++;
    expect(route.request().headers().authorization).toBeUndefined();
    expect(route.request().postData()).toContain('private');
    return route.fulfill({ json: {
      public_id: publicId, version: 456, signature: 'a'.repeat(40), resource_type: 'raw', bytes: 12,
    } });
  });
  await page.route('http://127.0.0.1:8000/api/v1/media/assets', (route) => {
    expect(route.request().postDataJSON()).toMatchObject({ purpose: 'payment_voucher', format: 'pdf', resourceType: 'raw' });
    return route.fulfill({ status: 201, json: { data: { id: 'private-voucher-id', access: 'private', url: null } } });
  });
  const keys: string[] = [];
  await page.route(`http://127.0.0.1:8000/api/v1/orders/${orderId}/payments`, (route) => {
    keys.push(route.request().headers()['idempotency-key']);
    expect(route.request().postDataJSON()).toMatchObject({
      amountMinor: 39950, voucherAssetId: 'private-voucher-id', reference: 'YAPE-123',
    });
    if (keys.length === 1) return route.fulfill({ status: 503, json: { detail: 'Error temporal' } });
    paid = true;
    return route.fulfill({ status: 201, json: { data: { id: 'payment-id' } } });
  });

  await page.goto('/admin/pagos');
  await page.getByRole('button', { name: 'Registrar', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Registrar pago' });
  await expect(dialog.getByLabel(/^Monto/)).toHaveValue('399.50');
  await dialog.getByLabel('Referencia de la operación (opcional)').fill('YAPE-123');
  await dialog.getByLabel('Voucher (opcional)').setInputFiles({ name: 'voucher.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 test') });
  expect((await new AxeBuilder({ page }).include('[role="dialog"]').analyze()).violations).toEqual([]);
  for (const width of [360, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const size = await dialog.evaluate((element) => ({ content: element.scrollWidth, viewport: element.clientWidth }));
    expect(size.content).toBeLessThanOrEqual(size.viewport);
    if (width === 360 || width === 1440) {
      await page.screenshot({ path: testInfo.outputPath(`voucher-${width}.png`) });
    }
  }
  await dialog.getByRole('button', { name: 'Registrar pago', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('Reintenta esta misma operación');
  await dialog.getByRole('button', { name: 'Reintentar registro' }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.locator('tr').filter({ hasText: 'PED-2026-0042' })).toContainText('Pagado');
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBe(keys[1]);
  expect(uploads).toBe(1);
});
