import { expect, test } from '@playwright/test';

const deployedBaseUrl = process.env.DEPLOYED_BASE_URL?.replace(/\/$/, '');

test.describe('Demo publicada', () => {
  test.skip(!deployedBaseUrl, 'Define DEPLOYED_BASE_URL para probar la demo publicada.');

  test('carga el catálogo y el detalle desde la API real', async ({ page }) => {
    test.setTimeout(120_000);
    const pageErrors: string[] = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));

    const catalogResponse = page.waitForResponse(
      (response) => response.url().includes('/api/v1/products?') && response.request().method() === 'GET',
    );
    await page.goto(`${deployedBaseUrl}/catalogo`);
    expect((await catalogResponse).status()).toBe(200);

    const cards = page.locator('.product-card');
    await expect(cards.first()).toBeVisible();
    await expect.poll(() => cards.first().locator('img').evaluate((image) => (
      image instanceof HTMLImageElement ? image.naturalWidth : 0
    ))).toBeGreaterThan(0);
    const productName = await cards.first().locator('h3').innerText();
    await cards.first().getByRole('button', { name: 'Ver detalle' }).click();
    await expect(page).toHaveURL(/\/producto\/[^/]+$/);
    await expect(page.getByRole('heading', { name: productName })).toBeVisible();
    await expect(page.locator('.detail-info .price')).toBeVisible();
    expect(pageErrors).toEqual([]);
  });

  test('calcula una estimación sin guardar una cotización', async ({ page }) => {
    test.setTimeout(120_000);
    const pageErrors: string[] = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));

    const estimateResponse = page.waitForResponse(
      (response) => response.url().endsWith('/api/v1/quotes/estimate')
        && response.request().method() === 'POST',
    );
    await page.goto(`${deployedBaseUrl}/cotizador`);
    expect((await estimateResponse).status()).toBe(200);
    await expect(page.getByRole('heading', { name: 'Cuéntanos sobre tu proyecto.' })).toBeVisible();
    await expect(page.locator('.estimate-total strong')).toContainText(/S\/\s*[\d,.]+/);
    await expect(page.locator('.estimate button').last()).toBeEnabled();
    await expect(page.getByRole('alert')).toHaveCount(0);
    expect(pageErrors).toEqual([]);
  });

  test('envía al inicio de sesión al abrir el portal sin autenticación', async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto(`${deployedBaseUrl}/mi-cuenta`);
    await expect(page).toHaveURL(/\/iniciar-sesion\?redirect=%2Fmi-cuenta$/);
    await expect(page.getByRole('heading', { name: 'Inicia sesión' })).toBeVisible();
  });
});
