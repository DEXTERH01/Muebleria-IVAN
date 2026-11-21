import { useCallback, useEffect, useState } from 'react';

import {
  convertQuote,
  listQuotes,
  updateQuoteStatus,
  type QuoteConvertInput,
  type QuoteData,
  type QuoteStatus,
} from '../../api/modules/quotes';
import { AdminLayout } from '../../components/layout';
import { Button, Modal } from '../../components/ui';
import { date, moneyMinor } from '../../utils/format';

const statusLabel: Record<QuoteStatus, string> = {
  draft: 'Borrador',
  submitted: 'Enviada',
  reviewing: 'En revisión',
  approved: 'Aprobada',
  rejected: 'Rechazada',
  expired: 'Vencida',
  converted: 'Convertida',
};

type ReviewStatus = Extract<QuoteStatus, 'reviewing' | 'approved' | 'rejected' | 'expired'>;

function ConversionModal({
  quote,
  onClose,
  onConvert,
}: {
  quote: QuoteData | null;
  onClose: () => void;
  onConvert: (input: QuoteConvertInput, idempotencyKey: string) => Promise<void>;
}) {
  const [address, setAddress] = useState('');
  const [district, setDistrict] = useState('');
  const [reference, setReference] = useState('');
  const [promisedDate, setPromisedDate] = useState('');
  const [idempotencyKey] = useState(() => crypto.randomUUID());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!quote) return;
    setBusy(true);
    setError(null);
    try {
      await onConvert({
        expectedQuoteVersion: quote.version,
        deliveryAddress: {
          address: address.trim(),
          district: district.trim(),
          reference: reference.trim() || null,
        },
        promisedDate: promisedDate || null,
      }, idempotencyKey);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo convertir la cotización.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={Boolean(quote)} onClose={onClose} title="Convertir cotización en pedido">
      {quote && (
        <form className="quote-convert-form" onSubmit={submit}>
          <p><b>{quote.code}</b> · {quote.contactName}</p>
          <label>
            Dirección de entrega
            <input value={address} onChange={(event) => setAddress(event.target.value)} minLength={5} maxLength={300} required />
          </label>
          <label>
            Distrito
            <input value={district} onChange={(event) => setDistrict(event.target.value)} minLength={2} maxLength={100} required />
          </label>
          <label>
            Referencia
            <input value={reference} onChange={(event) => setReference(event.target.value)} maxLength={300} />
          </label>
          <label>
            Fecha prometida
            <input type="date" value={promisedDate} onChange={(event) => setPromisedDate(event.target.value)} />
          </label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="modal-actions">
            <Button variant="secondary" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={busy}>{busy ? 'Convirtiendo…' : 'Crear pedido'}</Button>
          </div>
        </form>
      )}
    </Modal>
  );
}

export function QuotesPage({
  showToast,
  onOrdersChanged,
}: {
  showToast: (message: string) => void;
  onOrdersChanged: () => Promise<void>;
}) {
  const [quotes, setQuotes] = useState<QuoteData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyQuote, setBusyQuote] = useState<string | null>(null);
  const [selected, setSelected] = useState<QuoteData | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setQuotes((await listQuotes()).items);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No pudimos cargar las cotizaciones.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const changeStatus = async (quote: QuoteData, status: ReviewStatus) => {
    setBusyQuote(quote.id);
    try {
      await updateQuoteStatus(quote.id, status, quote.version);
      await load();
      showToast(`Cotización ${statusLabel[status].toLocaleLowerCase('es')}.`);
    } catch (reason) {
      showToast(reason instanceof Error ? reason.message : 'No se pudo actualizar la cotización.');
    } finally {
      setBusyQuote(null);
    }
  };

  const finishConversion = async (input: QuoteConvertInput, idempotencyKey: string) => {
    if (!selected) return;
    await convertQuote(selected.id, input, idempotencyKey);
    setSelected(null);
    await Promise.all([load(), onOrdersChanged()]);
    showToast('Pedido creado desde la cotización.');
  };

  return (
    <AdminLayout title="Cotizaciones" subtitle="REVISIÓN Y CONVERSIÓN">
      {loading && <p className="portal-notice" role="status">Cargando cotizaciones…</p>}
      {error && (
        <div className="portal-notice portal-error" role="alert">
          <b>{error}</b>
          <Button onClick={() => void load()}>Reintentar</Button>
        </div>
      )}
      {!loading && !error && quotes.length === 0 && (
        <div className="portal-notice portal-empty"><h2>No hay cotizaciones pendientes</h2></div>
      )}
      {!loading && !error && quotes.length > 0 && (
        <div className="admin-quote-list">
          {quotes.map((quote) => (
            <article className="admin-card admin-quote-card" key={quote.id}>
              <div className="admin-quote-heading">
                <div>
                  <span className="kicker">{quote.code}</span>
                  <h2>{quote.contactName}</h2>
                  <p>{quote.contactEmail ?? quote.contactPhone}</p>
                </div>
                <span className={`customer-quote-status quote-${quote.status}`}>{statusLabel[quote.status]}</span>
              </div>
              <dl className="admin-quote-details">
                <div><dt>Proyecto</dt><dd>{quote.items.map((item) => item.productName).join(', ')}</dd></div>
                <div><dt>Total</dt><dd>{moneyMinor(quote.totalMinor)}</dd></div>
                <div><dt>Enviada</dt><dd>{date(quote.createdAt.slice(0, 10))}</dd></div>
                <div><dt>Vencimiento</dt><dd>{date(quote.expiresAt.slice(0, 10))}</dd></div>
              </dl>
              <div className="admin-quote-actions">
                {quote.status === 'submitted' && <Button variant="secondary" disabled={busyQuote === quote.id} onClick={() => void changeStatus(quote, 'reviewing')}>Iniciar revisión</Button>}
                {(quote.status === 'submitted' || quote.status === 'reviewing') && <Button disabled={busyQuote === quote.id} onClick={() => void changeStatus(quote, 'approved')}>Aprobar</Button>}
                {(quote.status === 'submitted' || quote.status === 'reviewing') && <Button variant="danger" disabled={busyQuote === quote.id} onClick={() => void changeStatus(quote, 'rejected')}>Rechazar</Button>}
                {quote.status === 'approved' && <Button onClick={() => setSelected(quote)}>Convertir en pedido</Button>}
                {quote.status === 'approved' && <Button variant="secondary" disabled={busyQuote === quote.id} onClick={() => void changeStatus(quote, 'expired')}>Marcar vencida</Button>}
              </div>
            </article>
          ))}
        </div>
      )}
      <ConversionModal quote={selected} onClose={() => setSelected(null)} onConvert={finishConversion} />
    </AdminLayout>
  );
}
