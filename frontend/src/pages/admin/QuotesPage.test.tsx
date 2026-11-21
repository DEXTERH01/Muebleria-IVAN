import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { convertQuote, listQuotes, updateQuoteStatus, type QuoteData } from '../../api/modules/quotes';
import { QuotesPage } from './QuotesPage';

vi.mock('../../api/modules/quotes', () => ({
  listQuotes: vi.fn(),
  updateQuoteStatus: vi.fn(),
  convertQuote: vi.fn(),
}));

const mockedListQuotes = vi.mocked(listQuotes);
const mockedUpdateQuoteStatus = vi.mocked(updateQuoteStatus);
const mockedConvertQuote = vi.mocked(convertQuote);

const quote = {
  id: 'quote-id',
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
  version: 3,
  createdAt: '2026-11-21T12:00:00Z',
  updatedAt: '2026-11-21T12:00:00Z',
  items: [{ productName: 'Clóset personalizado' }],
} as QuoteData;

describe('QuotesPage', () => {
  beforeEach(() => {
    mockedListQuotes.mockReset();
    mockedUpdateQuoteStatus.mockReset();
    mockedConvertQuote.mockReset();
  });

  it('converts an approved quote into an order with its delivery address', async () => {
    mockedListQuotes.mockResolvedValue({ items: [quote], total: 1, page: 1, pageSize: 100 });
    mockedConvertQuote.mockResolvedValue({ id: 'order-id', code: 'PED-2026-0001' } as never);
    const showToast = vi.fn();
    const onOrdersChanged = vi.fn().mockResolvedValue(undefined);

    render(<QuotesPage showToast={showToast} onOrdersChanged={onOrdersChanged} />);

    fireEvent.click(await screen.findByRole('button', { name: 'Convertir en pedido' }));
    fireEvent.change(screen.getByLabelText('Dirección de entrega'), { target: { value: 'Av. Lima 123' } });
    fireEvent.change(screen.getByLabelText('Distrito'), { target: { value: 'Miraflores' } });
    fireEvent.change(screen.getByLabelText('Fecha prometida'), { target: { value: '2026-12-15' } });
    fireEvent.click(screen.getByRole('button', { name: 'Crear pedido' }));

    await waitFor(() => expect(mockedConvertQuote).toHaveBeenCalledWith(
      'quote-id',
      {
        expectedQuoteVersion: 3,
        deliveryAddress: {
          address: 'Av. Lima 123',
          district: 'Miraflores',
          reference: null,
        },
        promisedDate: '2026-12-15',
      },
      expect.any(String),
    ));
    expect(onOrdersChanged).toHaveBeenCalledOnce();
    expect(showToast).toHaveBeenCalledWith('Pedido creado desde la cotización.');
  });
});
