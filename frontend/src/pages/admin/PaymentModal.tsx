import { useCallback, useRef, useState, type FormEvent } from 'react';

import { ApiError } from '../../api/client/http';
import { uploadPaymentVoucher, validatePaymentVoucher } from '../../api/modules/media';
import type { ApiPaymentCreate, ApiPaymentMethod } from '../../api/modules/orders';
import { Button, Modal } from '../../components/ui';
import type { Order } from '../../types';
import { moneyMinor } from '../../utils/format';

function today(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

function amountInMinor(value: string): number {
  if (!/^\d+(?:[.,]\d{1,2})?$/.test(value.trim())) {
    throw new Error('Escribe un monto positivo con hasta dos decimales.');
  }
  const [whole, fraction = ''] = value.trim().replace(',', '.').split('.');
  const amount = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
  if (!Number.isSafeInteger(amount) || amount <= 0) throw new Error('El monto debe ser mayor a cero.');
  return amount;
}

export type SavePayment = (input: ApiPaymentCreate, idempotencyKey: string) => Promise<void>;

export function PaymentModal({ open, onClose, order, onSave }: {
  open: boolean; onClose: () => void; order: Order; onSave: SavePayment;
}) {
  const balance = Math.round(order.remainingBalance * 100);
  const depositDue = Math.max(0, (order.depositRequiredMinor ?? Math.ceil(order.total * 50))
    - Math.round(order.advancePaid * 100));
  const [type, setType] = useState(depositDue > 0 ? 'Anticipo' : 'Saldo final');
  const [amount, setAmount] = useState(((depositDue > 0 ? Math.min(depositDue, balance) : balance) / 100).toFixed(2));
  const [method, setMethod] = useState<ApiPaymentMethod>('bank_transfer');
  const [paymentDate, setPaymentDate] = useState(today);
  const [reference, setReference] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [retryOnly, setRetryOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const saving = useRef(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const uploaded = useRef<{ file: File; assetId: string } | null>(null);
  const attempt = useRef<{ body: string; input: ApiPaymentCreate; key: string } | null>(null);
  const limit = type === 'Anticipo' ? Math.min(depositDue, balance) : balance;
  const closeSafely = useCallback(() => { if (!saving.current) onClose(); }, [onClose]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (saving.current || fileError) return;
    saving.current = true;
    setBusy(true);
    setError(null);
    let registering = false;
    try {
      if (retryOnly && attempt.current) {
        registering = true;
        await onSave(attempt.current.input, attempt.current.key);
        onClose();
        return;
      }
      const amountMinor = amountInMinor(amount);
      if (amountMinor > limit) throw new Error(`El monto no puede superar ${moneyMinor(limit)}.`);
      if (!paymentDate) throw new Error('Indica la fecha del pago.');
      if (file && uploaded.current?.file !== file) {
        const asset = await uploadPaymentVoucher(file);
        uploaded.current = { file, assetId: asset.id };
      }
      const input: ApiPaymentCreate = {
        amountMinor, currency: 'PEN', method, paymentDate,
        reference: reference.trim() || null,
        voucherAssetId: file ? uploaded.current?.assetId ?? null : null,
      };
      const body = JSON.stringify(input);
      if (attempt.current?.body !== body) attempt.current = { body, input, key: crypto.randomUUID() };
      registering = true;
      await onSave(input, attempt.current.key);
      onClose();
    } catch (reason) {
      const uncertain = registering && (!(reason instanceof ApiError) || reason.status >= 500 || reason.status === 0);
      setRetryOnly(uncertain);
      setError(uncertain
        ? 'No pudimos confirmar el registro. Reintenta esta misma operación para evitar pagos duplicados.'
        : reason instanceof Error ? reason.message : 'No se pudo registrar el pago.');
    } finally {
      saving.current = false;
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={closeSafely} title="Registrar pago">
      <form className="payment-form" onSubmit={submit}>
        <p className="payment-order"><b>{order.code}</b><span>{order.customerName} · Saldo actual: {moneyMinor(balance)}</span></p>
        <fieldset disabled={busy || retryOnly} className="payment-fields">
          <label>Tipo de pago
            <select value={type} onChange={(event) => {
              setType(event.target.value);
              setAmount(((event.target.value === 'Anticipo' ? Math.min(depositDue, balance) : balance) / 100).toFixed(2));
            }}>
              <option disabled={depositDue === 0}>Anticipo</option><option>Saldo final</option>
            </select>
          </label>
          <label>Monto
            <div className="money-input"><span>S/</span><input inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} required /></div>
          </label>
          <label>Método
            <select value={method} onChange={(event) => setMethod(event.target.value as ApiPaymentMethod)}>
              <option value="bank_transfer">Transferencia, Yape o Plin</option><option value="cash">Efectivo</option><option value="card">Tarjeta</option><option value="other">Otro</option>
            </select>
          </label>
          <label>Fecha del pago<input type="date" value={paymentDate} onChange={(event) => setPaymentDate(event.target.value)} required /></label>
          <label>Referencia de la operación (opcional)<input value={reference} maxLength={200} onChange={(event) => setReference(event.target.value)} /></label>
          <label>Voucher (opcional)
            <input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp,application/pdf" aria-describedby="voucher-help" onChange={(event) => {
              const next = event.target.files?.[0] ?? null;
              uploaded.current = null;
              setFile(null);
              setFileError(null);
              setError(null);
              if (!next) return;
              try { validatePaymentVoucher(next); setFile(next); }
              catch (reason) {
                setFileError(reason instanceof Error ? reason.message : 'El archivo no es válido.');
                event.target.value = '';
              }
            }} />
          </label>
          {(file || fileError) && <Button variant="secondary" onClick={() => {
            setFile(null); setFileError(null); uploaded.current = null;
            if (fileInput.current) fileInput.current.value = '';
          }}>Quitar voucher</Button>}
          <p className="contact-help" id="voucher-help">JPG, PNG, WebP o PDF de hasta 10 MB. El voucher se guarda como archivo privado.</p>
        </fieldset>
        {(error || fileError) && <p className="form-error" role="alert">{error || fileError}</p>}
        {busy && <p role="status">Guardando pago y comprobante…</p>}
        <div className="modal-actions">
          <Button variant="secondary" onClick={closeSafely} disabled={busy}>Cancelar</Button>
          <Button type="submit" disabled={busy || !!fileError || (!retryOnly && balance <= 0)}>{busy ? 'Guardando…' : retryOnly ? 'Reintentar registro' : 'Registrar pago'}</Button>
        </div>
      </form>
    </Modal>
  );
}
