import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../api/client/http';
import { uploadPaymentVoucher } from '../../api/modules/media';
import type { Order } from '../../types';
import { PaymentModal } from './AdminPages';

vi.mock('../../api/modules/media', async (importOriginal) => ({
  ...await importOriginal<typeof import('../../api/modules/media')>(),
  uploadPaymentVoucher: vi.fn(),
}));

const order = {
  id: 'PED-2026-0042', apiId: 'order-id', code: 'PED-2026-0042', customerName: 'Cliente de prueba',
  total: 799, advancePaid: 399.5, remainingBalance: 399.5, paymentStatus: 'anticipo-pagado',
} as Order;

describe('registro de pagos', () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(cleanup);

  it('registra el saldo con céntimos, fecha y referencia y cierra después de confirmar', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    const close = vi.fn();
    render(<PaymentModal open order={order} onClose={close} onSave={onSave} />);
    expect(screen.getByRole('dialog', { name: 'Registrar pago' })).toBeVisible();
    expect(screen.getByText(order.code)).toBeVisible();
    expect(screen.getByLabelText('Método')).toHaveValue('bank_transfer');
    expect(screen.getByText(/Saldo actual: S\/\s*399[.,]5/)).toBeVisible();
    fireEvent.change(screen.getByLabelText('Fecha del pago'), { target: { value: '2026-11-28' } });
    fireEvent.change(screen.getByLabelText('Referencia de la operación (opcional)'), { target: { value: '  Yape 123  ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Registrar pago' }));
    await waitFor(() => expect(close).toHaveBeenCalledOnce());
    expect(onSave).toHaveBeenCalledWith({
      amountMinor: 39950, currency: 'PEN', method: 'bank_transfer', paymentDate: '2026-11-28',
      reference: 'Yape 123', voucherAssetId: null,
    }, expect.any(String));
  });

  it.each(['0', '-1', '399.51', '1.001'])('rechaza el monto %s sin registrar el pago', async (value) => {
    const onSave = vi.fn();
    render(<PaymentModal open order={order} onClose={vi.fn()} onSave={onSave} />);
    fireEvent.change(screen.getByLabelText(/^Monto/), { target: { value } });
    fireEvent.click(screen.getByRole('button', { name: 'Registrar pago' }));
    expect(await screen.findByRole('alert')).toBeVisible();
    expect(onSave).not.toHaveBeenCalled();
  });

  it('usa el anticipo definido por la API y acepta coma decimal', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<PaymentModal open order={{ ...order, advancePaid: 0, remainingBalance: 799, depositRequiredMinor: 25001 }} onClose={vi.fn()} onSave={onSave} />);
    expect(screen.getByLabelText(/^Monto/)).toHaveValue('250.01');
    fireEvent.change(screen.getByLabelText(/^Monto/), { target: { value: '250,01' } });
    fireEvent.click(screen.getByRole('button', { name: 'Registrar pago' }));
    await waitFor(() => expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ amountMinor: 25001 }), expect.any(String)));
  });

  it('reintenta con el mismo voucher y clave cuando no se confirma el registro', async () => {
    vi.mocked(uploadPaymentVoucher).mockResolvedValue({ id: 'private-asset', access: 'private' } as never);
    const onSave = vi.fn().mockRejectedValueOnce(new ApiError('Servicio no disponible', 503)).mockResolvedValueOnce(undefined);
    const close = vi.fn();
    const view = render(<PaymentModal open order={order} onClose={close} onSave={onSave} />);
    fireEvent.change(screen.getByLabelText('Voucher (opcional)'), {
      target: { files: [new File(['voucher'], 'recibo.pdf', { type: 'application/pdf' })] },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Registrar pago' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Reintenta esta misma operación');
    expect(close).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/^Monto/)).toBeDisabled();
    // A refresh may reveal that the server already committed the uncertain request.
    view.rerender(<PaymentModal open order={{ ...order, remainingBalance: 0 }} onClose={close} onSave={onSave} />);
    expect(screen.getByRole('button', { name: 'Reintentar registro' })).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar registro' }));
    await waitFor(() => expect(close).toHaveBeenCalledOnce());
    expect(uploadPaymentVoucher).toHaveBeenCalledOnce();
    expect(onSave).toHaveBeenCalledTimes(2);
    expect(onSave.mock.calls[0]).toEqual(onSave.mock.calls[1]);
    expect(onSave.mock.calls[0][0].voucherAssetId).toBe('private-asset');
  });

  it('mantiene el formulario abierto si falla la carga y no registra un pago sin su voucher', async () => {
    vi.mocked(uploadPaymentVoucher).mockRejectedValueOnce(new Error('No se pudo cargar el archivo.'));
    const onSave = vi.fn();
    const close = vi.fn();
    render(<PaymentModal open order={order} onClose={close} onSave={onSave} />);
    fireEvent.change(screen.getByLabelText('Voucher (opcional)'), {
      target: { files: [new File(['voucher'], 'recibo.png', { type: 'image/png' })] },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Registrar pago' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo cargar');
    expect(onSave).not.toHaveBeenCalled();
    expect(close).not.toHaveBeenCalled();
  });

  it('bloquea un archivo inválido hasta reemplazarlo o quitarlo', () => {
    const onSave = vi.fn();
    render(<PaymentModal open order={order} onClose={vi.fn()} onSave={onSave} />);
    fireEvent.change(screen.getByLabelText('Voucher (opcional)'), {
      target: { files: [new File(['gif'], 'recibo.gif', { type: 'image/gif' })] },
    });
    expect(screen.getByRole('alert')).toHaveTextContent('JPG, PNG, WebP o PDF');
    expect(screen.getByRole('button', { name: 'Registrar pago' })).toBeDisabled();
    expect(onSave).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Quitar voucher' }));
    expect(screen.getByRole('button', { name: 'Registrar pago' })).toBeEnabled();
  });

  it('conserva el foco al editar el monto con teclado', () => {
    render(<PaymentModal open order={order} onClose={vi.fn()} onSave={vi.fn()} />);
    const amount = screen.getByLabelText(/^Monto/);
    amount.focus();
    fireEvent.change(amount, { target: { value: '123.45' } });
    expect(amount).toHaveFocus();
  });

  it('impide doble envío y cierre mientras se confirma el pago', async () => {
    let complete!: () => void;
    const onSave = vi.fn(() => new Promise<void>((resolve) => { complete = resolve; }));
    const close = vi.fn();
    render(<PaymentModal open order={order} onClose={close} onSave={onSave} />);
    const submit = screen.getByRole('button', { name: 'Registrar pago' });
    fireEvent.click(submit);
    fireEvent.click(submit);
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onSave).toHaveBeenCalledOnce();
    expect(close).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Guardando…' })).toBeDisabled();
    await act(async () => complete());
    expect(close).toHaveBeenCalledOnce();
  });
});
