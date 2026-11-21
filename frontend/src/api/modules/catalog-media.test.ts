import { beforeEach, describe, expect, it, vi } from 'vitest';

import { attachProductImage } from './catalog';
import { uploadCatalogImage } from './media';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('catalog media API', () => {
  beforeEach(() => vi.unstubAllGlobals());

  it('uploads a signed image, confirms it, and attaches it to a product', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({
        data: {
          cloudName: 'demo-cloud',
          apiKey: 'demo-key',
          timestamp: 123,
          signature: 'signed-request',
          publicId: 'muebleria-ivan/catalog/admin/image-id',
          resourceType: 'image',
          deliveryType: 'upload',
          format: 'webp',
          uploadUrl: 'https://api.cloudinary.test/upload',
        },
      }))
      .mockResolvedValueOnce(jsonResponse({
        public_id: 'muebleria-ivan/catalog/admin/image-id',
        version: 456,
        signature: 'a'.repeat(40),
        format: 'webp',
        resource_type: 'image',
        bytes: 2048,
        width: 1200,
        height: 900,
      }))
      .mockResolvedValueOnce(jsonResponse({
        data: {
          id: 'asset-id',
          externalId: 'muebleria-ivan/catalog/admin/image-id',
          mediaType: 'image/webp',
          access: 'public',
          createdAt: '2026-11-21T12:00:00Z',
        },
      }, 201))
      .mockResolvedValueOnce(jsonResponse({ data: { id: 'product-id', images: [] } }, 201));
    vi.stubGlobal('fetch', fetchMock);
    const file = new File(['image'], 'closet.webp', { type: 'image/webp' });

    const uploaded = await uploadCatalogImage(file);
    await attachProductImage('product-id', {
      assetId: uploaded.asset.id,
      altText: 'Clóset de melamina nogal',
      position: 0,
      width: uploaded.width,
      height: uploaded.height,
    });

    expect(fetchMock.mock.calls[1][0]).toBe('https://api.cloudinary.test/upload');
    expect(fetchMock.mock.calls[1][1].body).toBeInstanceOf(FormData);
    expect(JSON.parse(fetchMock.mock.calls[2][1].body as string)).toEqual(expect.objectContaining({
      purpose: 'catalog_image',
      publicId: 'muebleria-ivan/catalog/admin/image-id',
      version: 456,
    }));
    expect(JSON.parse(fetchMock.mock.calls[3][1].body as string)).toEqual({
      assetId: 'asset-id',
      altText: 'Clóset de melamina nogal',
      position: 0,
      width: 1200,
      height: 900,
    });
  });

  it('rejects unsupported catalog formats before requesting a signature', async () => {
    vi.stubGlobal('fetch', vi.fn());
    const file = new File(['image'], 'closet.gif', { type: 'image/gif' });

    await expect(uploadCatalogImage(file)).rejects.toThrow('JPG, PNG o WebP');
    expect(fetch).not.toHaveBeenCalled();
  });
});
