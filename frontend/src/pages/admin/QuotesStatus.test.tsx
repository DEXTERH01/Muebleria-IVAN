import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { listQuotes, updateQuoteStatus, type QuoteData } from '../../api/modules/quotes';
import { QuotesPage } from './QuotesPage';

vi.mock('../../api/modules/quotes', () => ({
  convertQuote: vi.fn(),
  listQuotes: vi.fn(),
  updateQuoteStatus: vi.fn(),
}));

const mockedListQuotes = vi.mocked(listQuotes);
const mockedUpdateQuoteStatus = vi.mocked(updateQuoteStatus);

const submittedQuote = {
  id: 'quote-id',
  code: 'COT-2026-0002',
  status: 'submitted',
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

describe('QuotesPage status actions', () => {
  beforeEach(() => {
    mockedListQuotes.mockReset();
    mockedUpdateQuoteStatus.mockReset();
  });

  it('approves a submitted quote and reloads its updated state', async () => {
    mockedListQuotes
      .mockResolvedValueOnce({ items: [submittedQuote], total: 1, page: 1, pageSize: 100 })
      .mockResolvedValueOnce({
        items: [{ ...submittedQuote, status: 'approved', version: 4 }],
        total: 1,
        page: 1,
        pageSize: 100,
      });
    mockedUpdateQuoteStatus.mockResolvedValue({ ...submittedQuote, status: 'approved', version: 4 });
    const showToast = vi.fn();

    render(<QuotesPage showToast={showToast} onOrdersChanged={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Aprobar' }));

    await waitFor(() => expect(mockedUpdateQuoteStatus).toHaveBeenCalledWith('quote-id', 'approved', 3));
    expect(await screen.findByRole('button', { name: 'Convertir en pedido' })).toBeInTheDocument();
    expect(showToast).toHaveBeenCalledWith('Cotización aprobada.');
  });
});
