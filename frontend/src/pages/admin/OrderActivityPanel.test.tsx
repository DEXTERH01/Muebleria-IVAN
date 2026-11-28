import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { getOrder, getPaymentPage, type ApiOrderDetail, type ApiPayment } from '../../api/modules/orders';
import { OrderActivityPanel, PaymentHistory } from './OrderActivityPanel';

vi.mock('../../api/modules/orders', () => ({ getOrder: vi.fn(), getPaymentPage: vi.fn() }));

const detail = {
  id: 'order-a', status: 'finishing', statusHistory: [
    { previousStatus: null, newStatus: 'confirmed', occurredAt: '2026-11-28T02:00:00Z', note: 'Creado desde COT-2026-42' },
    { previousStatus: 'assembly', newStatus: 'finishing', occurredAt: '2026-11-28T16:00:00Z', note: 'Barniz aplicado' },
  ],
} as ApiOrderDetail;
const payment = {
  id: 'payment-a', orderId: 'order-a', amountMinor: 39950, currency: 'PEN', method: 'bank_transfer',
  reference: 'YAPE-123', paymentDate: '2026-11-28', status: 'recorded',
} as ApiPayment;
const paymentPage = { data: [payment], total: 1, page: 1, pageSize: 10 };

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(getOrder).mockResolvedValue(detail);
  vi.mocked(getPaymentPage).mockResolvedValue(paymentPage);
});
afterEach(cleanup);

describe('historial real del pedido', () => {
  it('muestra etapas canónicas, notas y horas de Perú junto a importes con céntimos', async () => {
    const view = render(<OrderActivityPanel orderId="order-a" />);
    expect(await screen.findByText('Barniz aplicado')).toBeVisible();
    expect(screen.getByText('Etapa anterior: En armado')).toBeVisible();
    expect(screen.getAllByText('En acabado')).toHaveLength(2);
    const time = view.container.querySelector('time');
    expect(time).toHaveAttribute('dateTime', '2026-11-28T02:00:00Z');
    expect(time?.textContent).toContain('27 nov');
    expect(await screen.findByText(/S\/\s*399[.,]5/)).toBeVisible();
    expect(screen.getByText('YAPE-123')).toBeVisible();
    expect(getOrder).toHaveBeenCalledWith('order-a');
  });

  it('permite reintentar el historial sin ocultar los movimientos cargados', async () => {
    vi.mocked(getOrder).mockRejectedValueOnce(new Error('No se pudo consultar el pedido'));
    render(<OrderActivityPanel orderId="order-a" />);
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo consultar el pedido');
    expect(await screen.findByText('YAPE-123')).toBeVisible();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar historial' }));
    expect(await screen.findByText('Barniz aplicado')).toBeVisible();
  });

  it('muestra estados vacíos explícitos', async () => {
    vi.mocked(getOrder).mockResolvedValue({ ...detail, statusHistory: [] });
    vi.mocked(getPaymentPage).mockResolvedValue({ ...paymentPage, data: [], total: 0 });
    render(<OrderActivityPanel orderId="order-a" />);
    expect(await screen.findByText('Aún no hay cambios de etapa registrados.')).toBeVisible();
    expect(await screen.findByText('No hay movimientos de pago registrados.')).toBeVisible();
  });

  it('recarga ambos historiales cuando cambian los pagos o la versión del pedido', async () => {
    const view = render(<OrderActivityPanel orderId="order-a" refreshKey="1:0" />);
    await screen.findByText('Barniz aplicado');
    view.rerender(<OrderActivityPanel orderId="order-a" refreshKey="2:39950" />);
    await waitFor(() => expect(getOrder).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(getPaymentPage).toHaveBeenCalledTimes(2));
  });
});

describe('movimientos paginados', () => {
  it('consulta la siguiente página sin cargar todos los pagos y distingue los revertidos', async () => {
    vi.mocked(getPaymentPage)
      .mockResolvedValueOnce({ ...paymentPage, total: 11 })
      .mockResolvedValueOnce({ ...paymentPage, data: [{ ...payment, id: 'payment-b', status: 'voided', reference: 'REF-REVERTIDA' }], total: 11, page: 2 });
    render(<PaymentHistory orderId="order-a" />);
    await screen.findByText('YAPE-123');
    fireEvent.click(screen.getByRole('button', { name: 'Página siguiente' }));
    expect(await screen.findByText('REF-REVERTIDA')).toBeVisible();
    expect(screen.getByText('Revertido')).toBeVisible();
    expect(screen.queryByText('YAPE-123')).not.toBeInTheDocument();
    expect(getPaymentPage).toHaveBeenNthCalledWith(2, 'order-a', 2, 10);
  });

  it('reintenta un error de pagos sin duplicar los registros visibles', async () => {
    vi.mocked(getPaymentPage).mockRejectedValueOnce(new Error('Servicio de pagos no disponible'));
    render(<PaymentHistory orderId="order-a" />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Servicio de pagos no disponible');
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar pagos' }));
    const list = await screen.findByRole('list', { name: 'Movimientos de pago' });
    expect(within(list).getAllByRole('listitem')).toHaveLength(1);
  });

  it('no muestra una respuesta tardía del pedido anterior y reinicia la paginación', async () => {
    let resolveOld!: (value: typeof paymentPage) => void;
    vi.mocked(getPaymentPage).mockImplementationOnce(() => new Promise((resolve) => { resolveOld = resolve; }));
    const view = render(<PaymentHistory orderId="order-a" />);
    view.rerender(<PaymentHistory orderId="order-b" />);
    await screen.findByText('YAPE-123');
    await act(async () => resolveOld({ ...paymentPage, data: [{ ...payment, reference: 'OLD-ORDER' }] }));
    expect(screen.queryByText('OLD-ORDER')).not.toBeInTheDocument();
    expect(getPaymentPage).toHaveBeenLastCalledWith('order-b', 1, 10);
  });
});
