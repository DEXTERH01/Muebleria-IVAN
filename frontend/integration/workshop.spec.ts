import { execFileSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { expect, test, type Page } from '@playwright/test';

test('cotización a instalación con Auth, API y PostgreSQL reales', async ({ browser, request }) => {
  const nonce = randomUUID().replaceAll('-', '');
  const password = `Local-${nonce}!aA1`;
  const customerEmail = `customer-${nonce}@example.test`;
  const adminEmail = `admin-${nonce}@example.test`;
  const name = `Cliente local ${nonce.slice(0, 8)}`;
  const authUrl = process.env.SUPABASE_TEST_URL!;
  const publishableKey = process.env.SUPABASE_TEST_PUBLISHABLE_KEY!;

  for (const email of [customerEmail, adminEmail]) {
    const response = await request.post(`${authUrl}/auth/v1/signup`, {
      headers: { apikey: publishableKey }, data: { email, password },
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.access_token).toBeTruthy();
    if (email === adminEmail) {
      execFileSync('../backend/.venv/Scripts/python.exe', ['-c', [
        'import os',
        'from sqlalchemy import create_engine, text',
        'engine = create_engine(os.environ["SUPABASE_TEST_DATABASE_URL"])',
        'with engine.begin() as connection:',
        '    connection.execute(text("update app.profiles set role = :role where user_id = :id"), {"role": "admin", "id": os.environ["LOCAL_ADMIN_ID"]})',
        'engine.dispose()',
      ].join('\n')], { env: { ...process.env, LOCAL_ADMIN_ID: data.user.id } });
    }
  }

  const customerContext = await browser.newContext();
  const adminContext = await browser.newContext();
  const customer = await customerContext.newPage();
  const admin = await adminContext.newPage();
  const login = async (page: Page, email: string) => {
    await page.goto('http://127.0.0.1:4175/iniciar-sesion');
    await page.getByLabel('Correo electrónico').fill(email);
    await page.getByLabel('Contraseña', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Entrar', exact: true }).click();
    await expect(page).not.toHaveURL(/iniciar-sesion/);
  };

  try {
    await login(customer, customerEmail);
    await customer.goto('http://127.0.0.1:4175/cotizador');
    await expect(customer.locator('.estimate-total strong')).toBeVisible();
    await customer.getByLabel('Nombre', { exact: true }).fill(name);
    await customer.getByLabel('Correo', { exact: true }).fill(customerEmail);
    const created = customer.waitForResponse((r) => r.url().endsWith('/quotes') && r.request().method() === 'POST');
    await customer.getByRole('button', { name: 'Enviar cotización' }).last().click();
    const quoteResponse = await created;
    expect(quoteResponse.status()).toBe(201);
    const quote = (await quoteResponse.json()).data;
    await expect(customer.getByText(quote.code, { exact: true })).toBeVisible();

    await login(admin, adminEmail);
    await admin.goto('http://127.0.0.1:4175/admin/cotizaciones');
    const card = admin.locator('.admin-quote-card').filter({ hasText: quote.code });
    await card.getByRole('button', { name: 'Aprobar', exact: true }).click();
    await card.getByRole('button', { name: 'Convertir en pedido' }).click();
    const conversion = admin.getByRole('dialog');
    await conversion.getByLabel('Dirección de entrega').fill('Av. Prueba Local 123');
    await conversion.getByLabel('Distrito', { exact: true }).fill('Miraflores');
    const converted = admin.waitForResponse((r) => r.url().endsWith('/convert') && r.request().method() === 'POST');
    await conversion.getByRole('button', { name: 'Crear pedido' }).click();
    const orderResponse = await converted;
    expect(orderResponse.status()).toBe(201);
    const order = (await orderResponse.json()).data;
    await expect(conversion).toHaveCount(0);
    await admin.goto(`http://127.0.0.1:4175/admin/pedido/${order.code}`);

    const pay = async (type: string) => {
      await admin.getByRole('button', { name: 'Registrar pago', exact: true }).first().click();
      const dialog = admin.getByRole('dialog');
      await dialog.getByLabel('Tipo de pago').selectOption({ label: type });
      const payment = admin.waitForResponse((r) => r.url().endsWith('/payments') && r.request().method() === 'POST');
      await dialog.getByRole('button', { name: 'Registrar pago', exact: true }).click();
      expect((await payment).status()).toBe(201);
      await expect(dialog).toHaveCount(0);
      await expect(admin.getByRole('status')).toContainText('Pago registrado correctamente.');
    };
    const advance = async (canonicalStatus: string, displayStatus: string) => {
      const moved = admin.waitForResponse((r) => r.url().endsWith('/status')
        && r.request().method() === 'PATCH'
        && r.request().postDataJSON().newStatus === canonicalStatus);
      await admin.getByRole('button', { name: 'Siguiente etapa →' }).click();
      expect((await moved).status()).toBe(200);
      await expect(admin.locator(`.order-header .status-${displayStatus}`)).toBeVisible();
    };
    await pay('Anticipo');
    for (const [canonical, display] of [['cutting', 'corte'], ['assembly', 'armado'], ['ready', 'listo']]) {
      await advance(canonical, display);
    }
    await pay('Saldo final');
    await advance('installed', 'instalado');
    await expect(admin.getByRole('button', { name: 'Siguiente etapa →' })).toBeDisabled();

    await customer.goto('http://127.0.0.1:4175/mi-cuenta');
    const orderCard = customer.locator('.customer-order-card').filter({ hasText: order.code });
    await expect(orderCard.locator('.customer-order-status')).toHaveText('Instalado');
    await expect(orderCard.locator('.customer-order-details div').filter({ hasText: 'Saldo pendiente' }).locator('dd'))
      .toContainText(/S\/\s*0/);
    await orderCard.getByRole('button', { name: 'Ver historial de etapas' }).click();
    await expect(orderCard.locator('.order-history-list li')).toHaveCount(8);
  } finally {
    await customerContext.close();
    await adminContext.close();
  }
});
