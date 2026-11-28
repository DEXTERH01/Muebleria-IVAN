import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { createPayment, listOrders, setOrderStatus, type ApiOrder } from '../api/modules/orders';
import { useAuth } from '../auth/AuthProvider';
import { useOrders } from './useOrders';

vi.mock('../api/modules/orders', () => ({
  listOrders: vi.fn(), setOrderStatus: vi.fn(), createPayment: vi.fn(),
}));
vi.mock('../auth/AuthProvider', () => ({ useAuth: vi.fn() }));

const auth = { loading: false, session: { access_token: 'local-test-token' } };
const order = {
  id: 'order-id', code: 'PED-2026-0001', quoteId: 'quote-id', customerId: 'customer-id',
  status: 'confirmed', totalMinor: 100000, paidMinor: 50000, balanceMinor: 50000,
  version: 1, createdAt: '2026-11-28T12:00:00Z', promisedDate: null,
} as ApiOrder;

describe('production transitions through the API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue(auth as ReturnType<typeof useAuth>);
    vi.mocked(listOrders).mockResolvedValue([order]);
    vi.mocked(setOrderStatus).mockImplementation(async (_id, status, version) => ({
      ...order, status, version: version + 1,
    }));
  });

  it.each([
    ['confirmed', 'corte', ['materials_pending', 'cutting']],
    ['assembly', 'listo', ['finishing', 'ready']],
    ['ready', 'instalado', ['delivered', 'installed']],
  ] as const)('advances %s to %s with each canonical stage and current version', async (current, target, stages) => {
    vi.mocked(listOrders).mockResolvedValue([{ ...order, status: current }]);
    const { result } = renderHook(() => useOrders());
    await waitFor(() => expect(result.current.orders).toHaveLength(1));

    await act(async () => result.current.updateOrder(order.code, { status: target }));

    expect(setOrderStatus).toHaveBeenCalledTimes(stages.length);
    stages.forEach((stage, index) => {
      expect(setOrderStatus).toHaveBeenNthCalledWith(index + 1, order.id, stage, index + 1);
    });
    expect(listOrders).toHaveBeenCalledTimes(2);
  });

  it('keeps the current displayed stage without writing and rejects backward moves', async () => {
    vi.mocked(listOrders).mockResolvedValue([{ ...order, status: 'cutting' }]);
    const { result } = renderHook(() => useOrders());
    await waitFor(() => expect(result.current.orders).toHaveLength(1));
    await act(async () => result.current.updateOrder(order.code, { status: 'corte' }));
    await expect(result.current.updateOrder(order.code, { status: 'material-pendiente' }))
      .rejects.toThrow('Los pedidos solo pueden avanzar');
    expect(setOrderStatus).not.toHaveBeenCalled();
  });

  it('sends integer amounts and voucher metadata with the same operation key on retry', async () => {
    const { result } = renderHook(() => useOrders());
    await waitFor(() => expect(result.current.orders).toHaveLength(1));
    const input = {
      amountMinor: 10001, currency: 'PEN', method: 'bank_transfer', paymentDate: '2026-11-28',
      reference: 'REF-123', voucherAssetId: 'private-voucher',
    } as const;
    vi.mocked(createPayment).mockRejectedValueOnce(new Error('Network error')).mockResolvedValueOnce({ id: 'payment-id' } as never);
    await expect(result.current.registerPayment(order.code, input, 'payment-key')).rejects.toThrow('Network error');
    expect(listOrders).toHaveBeenCalledOnce();
    await act(async () => result.current.registerPayment(order.code, input, 'payment-key'));
    expect(createPayment).toHaveBeenNthCalledWith(1, order.id, input, 'payment-key');
    expect(createPayment).toHaveBeenNthCalledWith(2, order.id, input, 'payment-key');
    expect(listOrders).toHaveBeenCalledTimes(2);
  });
});
