import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { listOrders, type ApiOrder } from '../api/modules/orders';
import { CustomerPortal } from './CustomerPortal';

vi.mock('../api/modules/orders', () => ({ listOrders: vi.fn() }));

const mockedListOrders = vi.mocked(listOrders);
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

describe('CustomerPortal', () => {
  beforeEach(() => mockedListOrders.mockReset());

  it('shows the customer’s order progress and balance from the API', async () => {
    mockedListOrders.mockResolvedValue([order]);

    render(<CustomerPortal />);

    expect(await screen.findByText('PED-2026-0001')).toBeInTheDocument();
    expect(screen.getByText('En corte')).toBeInTheDocument();
    expect(screen.getAllByText('S/ 625')).toHaveLength(2);
    expect(mockedListOrders).toHaveBeenCalledOnce();
  });

  it('offers retry after a failed request', async () => {
    mockedListOrders.mockRejectedValueOnce(new Error('Servicio no disponible'));
    mockedListOrders.mockResolvedValueOnce([]);

    render(<CustomerPortal />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible');
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));

    await waitFor(() => expect(screen.getByText('Aún no tienes pedidos')).toBeInTheDocument());
    expect(mockedListOrders).toHaveBeenCalledTimes(2);
  });
});
