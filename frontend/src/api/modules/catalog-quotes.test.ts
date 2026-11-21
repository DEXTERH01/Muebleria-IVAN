import { beforeEach, describe, expect, it, vi } from 'vitest';

import { listProducts } from './catalog';
import { createQuote, estimateQuote } from './quotes';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('catalog and quote API modules', () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it('loads the paginated catalog through the central HTTP client', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      data: { items: [], page: 1, pageSize: 100, total: 0 },
    }));
    vi.stubGlobal('fetch', fetchMock);

    const catalog = await listProducts();

    expect(catalog.total).toBe(0);
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/v1/products?page=1&pageSize=100',
      expect.objectContaining({ headers: expect.objectContaining({ Accept: 'application/json' }) }),
    );
  });

  it('sends measurements in millimeters and integer minor amounts stay in the response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      data: {
        currency: 'PEN',
        subtotalMinor: 100000,
        adjustmentsMinor: 0,
        totalMinor: 100000,
        depositMinor: 50000,
        items: [],
      },
    }));
    vi.stubGlobal('fetch', fetchMock);
    const item = {
      productId: '40000000-0000-4000-8000-000000000001',
      quantity: 1,
      widthMm: 1200,
      heightMm: 1800,
      depthMm: 450,
      accessoryIds: [],
      configuration: {},
    };

    const estimate = await estimateQuote([item]);

    expect(estimate.depositMinor).toBe(50000);
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({ items: [item] });
  });

  it('persists contact data and exposes API errors to the interface', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ data: { id: 'quote-id' } }, 201))
      .mockResolvedValueOnce(jsonResponse({
        error: { message: 'Las medidas no son válidas.' },
      }, 422));
    vi.stubGlobal('fetch', fetchMock);
    const item = {
      productId: '40000000-0000-4000-8000-000000000001',
      quantity: 1,
      widthMm: 1200,
      heightMm: 1800,
      depthMm: 450,
      accessoryIds: [],
      configuration: {},
    };

    await createQuote({ contactName: 'Ana Demo', contactEmail: 'ana@example.test', items: [item] });
    const requestBody = JSON.parse(fetchMock.mock.calls[0][1].body as string);

    expect(requestBody.contactName).toBe('Ana Demo');
    await expect(estimateQuote([item])).rejects.toEqual(
      expect.objectContaining({
        message: 'Las medidas no son válidas.',
        status: 422,
      }),
    );
  });
});
