import { afterEach, describe, expect, it, vi } from 'vitest';

import { setAccessTokenProvider } from '../client/http';
import { MAX_VOUCHER_BYTES, uploadPaymentVoucher } from './media';
import { createPayment } from './orders';

const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

afterEach(() => { vi.unstubAllGlobals(); setAccessTokenProvider(null); });

describe('vouchers privados', () => {
  it.each(['application/pdf', 'image/png'])('carga %s con firma privada, confirma y asocia solo el UUID al pago', async (mime) => {
    const pdf = mime === 'application/pdf';
    const publicId = `muebleria-ivan/vouchers/user/file${pdf ? '.pdf' : ''}`;
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ data: {
        cloudName: 'test', apiKey: 'public-api-key', timestamp: 123, signature: 'upload-signature',
        publicId, resourceType: pdf ? 'raw' : 'image', deliveryType: 'private', format: pdf ? 'pdf' : 'png',
        uploadUrl: 'https://api.cloudinary.test/upload',
      } }))
      .mockResolvedValueOnce(response({
        public_id: publicId, version: 456, signature: 'a'.repeat(40), bytes: 12,
        resource_type: pdf ? 'raw' : 'image', ...(pdf ? {} : { format: 'png' }),
      }))
      .mockResolvedValueOnce(response({ data: { id: 'private-asset-id', access: 'private', url: null } }, 201))
      .mockResolvedValueOnce(response({ data: { id: 'payment-id' } }, 201));
    vi.stubGlobal('fetch', fetchMock);
    setAccessTokenProvider(() => 'jwt-test');
    const asset = await uploadPaymentVoucher(new File(['voucher'], pdf ? 'voucher.pdf' : 'voucher.png', { type: mime }));
    await createPayment('order-id', {
      amountMinor: 39950, currency: 'PEN', method: 'bank_transfer', paymentDate: '2026-11-28',
      voucherAssetId: asset.id,
    }, 'same-operation-key');

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ purpose: 'payment_voucher', format: pdf ? 'pdf' : 'png' });
    const upload = fetchMock.mock.calls[1][1];
    expect(upload.body.get('type')).toBe('private');
    expect(upload.headers).toBeUndefined(); // JWT is only sent to FastAPI.
    expect(JSON.parse(fetchMock.mock.calls[2][1].body)).toMatchObject({
      purpose: 'payment_voucher', publicId, format: pdf ? 'pdf' : 'png', resourceType: pdf ? 'raw' : 'image',
    });
    const payment = fetchMock.mock.calls[3][1];
    expect(payment.headers['Idempotency-Key']).toBe('same-operation-key');
    expect(JSON.parse(payment.body).voucherAssetId).toBe('private-asset-id');
    expect(payment.body).not.toContain('cloudinary');
  });

  it.each(['empty', 'large', 'unsupported'])('rechaza un archivo %s antes de pedir una firma', async (kind) => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const file = new File(kind === 'empty' ? [] : ['voucher'], 'voucher.png', { type: kind === 'unsupported' ? 'image/gif' : 'image/png' });
    if (kind === 'large') Object.defineProperty(file, 'size', { value: MAX_VOUCHER_BYTES + 1 });
    await expect(uploadPaymentVoucher(file)).rejects.toThrow();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('no carga un voucher si la firma indica acceso público', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ data: { deliveryType: 'upload' } }));
    vi.stubGlobal('fetch', fetchMock);
    await expect(uploadPaymentVoucher(new File(['voucher'], 'voucher.png', { type: 'image/png' })))
      .rejects.toThrow('acceso solicitado');
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it('reutiliza la clave de idempotencia suministrada al reintentar', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ data: { id: 'same-payment' } }));
    vi.stubGlobal('fetch', fetchMock);
    const input = { amountMinor: 10001, currency: 'PEN', method: 'cash', paymentDate: '2026-11-28' } as const;
    await createPayment('order-id', input, 'retry-operation-key');
    fetchMock.mockResolvedValueOnce(response({ data: { id: 'same-payment' } }));
    await createPayment('order-id', input, 'retry-operation-key');
    expect(fetchMock.mock.calls[0][1].headers['Idempotency-Key']).toBe('retry-operation-key');
    expect(fetchMock.mock.calls[1][1].headers['Idempotency-Key']).toBe('retry-operation-key');
  });
});
