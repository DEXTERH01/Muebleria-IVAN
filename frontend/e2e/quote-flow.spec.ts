import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

const productId = '40000000-0000-4000-8000-000000000001';
const materialId = '50000000-0000-4000-8000-000000000001';
const finishId = '50000000-0000-4000-8000-000000000002';

const productSummary = {
  id: productId,
  slug: 'closet-siena',
  name: 'Clóset Siena',
  description: 'Clóset de referencia para dormitorio.',
  category: 'Dormitorio',
  basePriceMinor: 145000,
  minProductionDays: 10,
  maxProductionDays: 15,
  primaryImage: null,
};

const selectedMaterial = {
  id: materialId,
  code: 'MELAMINE',
  name: 'Melamina',
  adjustmentMinor: 0,
};

const selectedFinish = {
  id: finishId,
  code: 'NOGAL',
  name: 'Nogal',
  adjustmentMinor: 0,
};

const breakdown = {
  referenceBaseMinor: 145000,
  sizeAdjustedBaseMinor: 145000,
  materialMinor: 0,
  finishMinor: 0,
  accessoriesMinor: 0,
  rulesMinor: 0,
  unitTotalMinor: 145000,
};

const estimateItem = {
  productId,
  productName: productSummary.name,
  quantity: 1,
  widthMm: 1800,
  heightMm: 2200,
  depthMm: 550,
  material: selectedMaterial,
  finish: selectedFinish,
  accessories: [],
  appliedRules: [],
  breakdown,
  lineTotalMinor: 145000,
  minProductionDays: 10,
  maxProductionDays: 15,
};

const quote = {
  id: '60000000-0000-4000-8000-000000000001',
  code: 'COT-2026-0099',
  status: 'submitted',
  currency: 'PEN',
  contactName: 'Ana Demo',
  contactEmail: 'ana@example.test',
  contactPhone: null,
  subtotalMinor: 145000,
  adjustmentsMinor: 0,
  totalMinor: 145000,
  depositMinor: 72500,
  expiresAt: '2026-11-28T12:00:00Z',
  version: 1,
  createdAt: '2026-11-21T12:00:00Z',
  updatedAt: '2026-11-21T12:00:00Z',
  items: [{
    id: '70000000-0000-4000-8000-000000000001',
    productId,
    productName: productSummary.name,
    quantity: 1,
    widthMm: 1800,
    heightMm: 2200,
    depthMm: 550,
    material: selectedMaterial,
    finish: selectedFinish,
    accessories: [],
    configuration: {},
    basePriceMinor: 145000,
    breakdown,
    lineTotalMinor: 145000,
  }],
};

async function mockQuoteApi(page: Page) {
  await page.route('http://127.0.0.1:8000/api/v1/products?*', (route) => route.fulfill({
    json: { data: { items: [productSummary], page: 1, pageSize: 100, total: 1 } },
  }));
  await page.route('http://127.0.0.1:8000/api/v1/products/closet-siena', (route) => route.fulfill({
    json: {
      data: {
        ...productSummary,
        active: true,
        measurementLimits: {
          minWidthMm: 1800,
          maxWidthMm: 3000,
          minHeightMm: 2200,
          maxHeightMm: 2800,
          minDepthMm: 550,
          maxDepthMm: 900,
        },
        images: [],
        materials: [{
          id: materialId,
          code: 'MELAMINE',
          name: 'Melamina',
          description: 'Melamina estándar',
          priceAdjustmentMinor: 0,
          priceAdjustmentPercent: '0',
          isDefault: true,
        }],
        finishes: [{
          id: finishId,
          code: 'NOGAL',
          name: 'Nogal',
          description: 'Acabado nogal',
          priceAdjustmentMinor: 0,
          priceAdjustmentPercent: '0',
          isDefault: true,
        }],
        accessories: [],
      },
    },
  }));
  await page.route('http://127.0.0.1:8000/api/v1/quotes/estimate', (route) => route.fulfill({
    json: {
      data: {
        currency: 'PEN',
        subtotalMinor: 145000,
        adjustmentsMinor: 0,
        totalMinor: 145000,
        depositMinor: 72500,
        items: [estimateItem],
      },
    },
  }));
  await page.route('http://127.0.0.1:8000/api/v1/quotes', async (route) => {
    if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      expect(body).toMatchObject({
        contactName: 'Ana Demo',
        contactEmail: 'ana@example.test',
        items: [{
          productId,
          widthMm: 1800,
          heightMm: 2200,
          depthMm: 550,
          materialId,
          finishId,
        }],
      });
      await route.fulfill({ status: 201, json: { data: quote } });
      return;
    }
    await route.continue();
  });
}

test.describe('Flujo crítico de cotización', () => {
  test('cotiza un mueble, revisa la estimación y usa el modal por teclado', async ({ page }) => {
    await mockQuoteApi(page);
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const pageErrors: string[] = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));

    await page.goto('/cotizador');
    await expect(page.getByRole('heading', { name: 'Cuéntanos sobre tu proyecto.' })).toBeVisible();
    await expect(page.getByText('Clóset Siena', { exact: true }).first()).toBeVisible();
    await expect(page.getByText(/S\/\s*1,450/).first()).toBeVisible();
    await expect(page.getByLabel('Correo')).toHaveAttribute('aria-describedby', 'contact-help');
    await expect(page.getByRole('button', { name: 'Nogal' })).toHaveAttribute('aria-pressed', 'true');

    const accessibility = await new AxeBuilder({ page }).analyze();
    expect(accessibility.violations).toEqual([]);

    await page.getByLabel('Nombre', { exact: true }).fill('Ana Demo');
    await page.getByLabel('Correo', { exact: true }).fill('ana@example.test');
    await page.getByRole('button', { name: 'Enviar cotización' }).first().click();

    await expect(page.getByRole('heading', { name: '¡Tu proyecto está tomando forma!' })).toBeVisible();
    await expect(page.getByText('COT-2026-0099')).toBeVisible();

    const summaryAccessibility = await new AxeBuilder({ page }).analyze();
    expect(summaryAccessibility.violations).toEqual([]);

    await page.getByRole('button', { name: 'Enviar por WhatsApp' }).click();

    const dialog = page.getByRole('dialog', { name: 'Mensaje para WhatsApp' });
    const dialogAccessibility = await new AxeBuilder({ page }).analyze();
    expect(dialogAccessibility.violations).toEqual([]);

    const close = dialog.getByRole('button', { name: 'Cerrar', exact: true }).first();
    const copy = dialog.getByRole('button', { name: 'Copiar mensaje' });
    await expect(close).toBeFocused();
    await close.press('Shift+Tab');
    await expect(copy).toBeFocused();
    await copy.press('Tab');
    await expect(close).toBeFocused();
    await close.press('Escape');
    await expect(dialog).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Enviar por WhatsApp' })).toBeFocused();
    expect(pageErrors).toEqual([]);
  });

  test('mantiene el cotizador dentro del ancho en 360, 768 y 1440 px', async ({ page }) => {
    await mockQuoteApi(page);
    await page.goto('/cotizador');
    await expect(page.getByRole('heading', { name: 'Cuéntanos sobre tu proyecto.' })).toBeVisible();

    for (const width of [360, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      const dimensions = await page.evaluate(() => ({
        viewport: document.documentElement.clientWidth,
        content: document.documentElement.scrollWidth,
      }));
      expect(dimensions.content, `La página desborda a ${width} px`).toBeLessThanOrEqual(dimensions.viewport);
    }
  });
});
