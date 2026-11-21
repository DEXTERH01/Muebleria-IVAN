import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { getOrder, listOrders, type ApiOrder, type ApiOrderDetail } from '../api/modules/orders';
import { listQuotes, type QuoteData } from '../api/modules/quotes';
import { CustomerPortal } from './CustomerPortal';

vi.mock('../api/modules/orders', () => ({ listOrders: vi.fn(), getOrder: vi.fn() }));
vi.mock('../api/modules/quotes', () => ({ listQuotes: vi.fn() }));

const mockedListOrders = vi.mocked(listOrders);
const mockedGetOrder = vi.mocked(getOrder);
const mockedListQuotes = vi.mocked(listQuotes);
const order: ApiOrder = {
  id: 'order-uuid',
  code: 'PED-2026-0001',
  quoteId: 'quote-uuid',
  customerId: 'customer-uuid',
  status: 'cutting',
  currency: 'PEN',
  totalMinor: 125000,
  depositRequiredMinor: 62500,
  paidMinor: 62500,
  balanceMinor: 62500,
  promisedDate: '2026-12-05',
  deliveredAt: null,
  installedAt: null,
  version: 2,
  createdAt: '2026-11-20T12:00:00Z',
  updatedAt: '2026-11-21T12:00:00Z',
};
const orderDetail: ApiOrderDetail = {
  ...order,
  statusHistory: [
    {
      previousStatus: 'confirmed',
      newStatus: 'cutting',
      note: 'Material preparado y corte iniciado.',
      occurredAt: '2026-11-21T12:00:00Z',
    },
  ],
};
const quote = {
  id: 'quote-uuid',
  code: 'COT-2026-0001',
  status: 'approved',
  currency: 'PEN',
  contactName: 'Ana Demo',
  contactEmail: 'ana@example.test',
  contactPhone: null,
  subtotalMinor: 125000,
  adjustmentsMinor: 0,
  totalMinor: 125000,
  depositMinor: 62500,
  expiresAt: '2026-11-28T12:00:00Z',
  version: 2,
  createdAt: '2026-11-21T12:00:00Z',
  updatedAt: '2026-11-21T12:00:00Z',
  items: [{ productName: 'Clóset personalizado' }],
} as QuoteData;

describe('CustomerPortal', () => {
  beforeEach(() => {
    mockedListOrders.mockReset();
    mockedGetOrder.mockReset();
    mockedListQuotes.mockReset();
    mockedListQuotes.mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 100 });
  });

  it('shows the customer’s own quotes', async () => {
    mockedListOrders.mockResolvedValue([]);
    mockedListQuotes.mockResolvedValue({ items: [quote], total: 1, page: 1, pageSize: 100 });

    render(<CustomerPortal />);

    expect(await screen.findByText('COT-2026-0001')).toBeInTheDocument();
    expect(screen.getByText('Aprobada')).toBeInTheDocument();
    expect(screen.getByText('Clóset personalizado')).toBeInTheDocument();
  });

  it('shows the customer’s order progress and balance from the API', async () => {
    mockedListOrders.mockResolvedValue([order]);

    render(<CustomerPortal />);

    expect(await screen.findByText('PED-2026-0001')).toBeInTheDocument();
    expect(screen.getByText('En corte')).toBeInTheDocument();
    expect(screen.getAllByText('S/ 625')).toHaveLength(2);
    expect(mockedListOrders).toHaveBeenCalledOnce();

    mockedGetOrder.mockResolvedValue(orderDetail);
    fireEvent.click(screen.getByRole('button', { name: 'Ver historial de etapas' }));
    expect(await screen.findByText('Material preparado y corte iniciado.')).toBeInTheDocument();
    expect(mockedGetOrder).toHaveBeenCalledWith(order.id);
  });

  it('offers retry after a failed request', async () => {
    mockedListOrders.mockRejectedValueOnce(new Error('Servicio no disponible'));
    mockedListOrders.mockResolvedValueOnce([]);

    render(<CustomerPortal />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible');
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));

    await waitFor(() => expect(screen.getByText('Aún no tienes proyectos')).toBeInTheDocument());
    expect(mockedListOrders).toHaveBeenCalledTimes(2);
  });
});
