import { useEffect, useState } from 'react';

import {
  getOrder, getPaymentPage, type ApiOrderDetail, type ApiOrderStatus, type ApiPayment,
} from '../../api/modules/orders';
import { Button, Pagination } from '../../components/ui';
import { date, moneyMinor } from '../../utils/format';

const statusLabels: Record<ApiOrderStatus, string> = {
  confirmed: 'Confirmado', materials_pending: 'Materiales pendientes', cutting: 'En corte',
  assembly: 'En armado', finishing: 'En acabado', ready: 'Listo para entrega',
  delivered: 'Entregado', installed: 'Instalado', cancelled: 'Cancelado',
};

export const orderStageName = (status: string) => statusLabels[status as ApiOrderStatus] ?? 'Estado no disponible';
const methodLabels: Record<ApiPayment['method'], string> = {
  cash: 'Efectivo', bank_transfer: 'Transferencia, Yape o Plin', card: 'Tarjeta', other: 'Otro',
};
const timestamp = (value: string) => new Intl.DateTimeFormat('es-PE', {
  dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Lima',
}).format(new Date(value));

interface ActivityProps { orderId: string; refreshKey?: string }

function StatusHistory({ orderId, refreshKey }: ActivityProps) {
  const [order, setOrder] = useState<ApiOrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getOrder(orderId).then((data) => {
      if (active) setOrder(data);
    }).catch((reason: unknown) => {
      if (active) setError(reason instanceof Error ? reason.message : 'No pudimos cargar el historial.');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [orderId, refreshKey, retry]);

  return (
    <section className="admin-card order-status-history" aria-labelledby="status-history-title">
      <h2 id="status-history-title">Historial del pedido</h2>
      {loading && <p role="status">Cargando historial…</p>}
      {!loading && error && <div role="alert"><p>{error}</p><Button variant="secondary" onClick={() => setRetry((value) => value + 1)}>Reintentar historial</Button></div>}
      {!loading && !error && order && <>
        <p>Etapa actual: <b>{statusLabels[order.status]}</b></p>
        <p className="contact-help">Fechas y horas de Perú.</p>
        {order.statusHistory.length === 0 ? <p>Aún no hay cambios de etapa registrados.</p> : (
          <ol className="order-history-list">
            {order.statusHistory.map((event, index) => (
              <li key={`${event.occurredAt}-${index}`}>
                <span className="order-history-dot" aria-hidden="true" />
                <div>
                  <b>{statusLabels[event.newStatus]}</b>
                  {event.previousStatus && <span>Etapa anterior: {statusLabels[event.previousStatus]}</span>}
                  {event.note && <p>{event.note}</p>}
                  <time dateTime={event.occurredAt}>{timestamp(event.occurredAt)}</time>
                </div>
              </li>
            ))}
          </ol>
        )}
      </>}
    </section>
  );
}

const PAYMENT_PAGE_SIZE = 10;

function PaymentHistoryPage({ orderId, refreshKey }: ActivityProps) {
  const [payments, setPayments] = useState<ApiPayment[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getPaymentPage(orderId, page, PAYMENT_PAGE_SIZE).then((response) => {
      if (active) { setPayments(response.data); setTotal(response.total); }
    }).catch((reason: unknown) => {
      if (active) setError(reason instanceof Error ? reason.message : 'No pudimos cargar los pagos.');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [orderId, page, refreshKey, retry]);

  return (
    <div className="payment-history">
      {loading && <p role="status">Cargando movimientos…</p>}
      {!loading && error && <div role="alert"><p>{error}</p><Button variant="secondary" onClick={() => setRetry((value) => value + 1)}>Reintentar pagos</Button></div>}
      {!loading && !error && <>
        {payments.length === 0 ? <p>No hay movimientos de pago registrados.</p> : (
          <ul className="payment-record-list" aria-label="Movimientos de pago">
            {payments.map((payment) => (
              <li key={payment.id}>
                <div className="payment-record-heading">
                  <b>{moneyMinor(payment.amountMinor)}</b>
                  <span className={`payment-record-status payment-record-${payment.status}`}>{payment.status === 'voided' ? 'Revertido' : 'Registrado'}</span>
                </div>
                <dl>
                  <div><dt>Fecha del pago</dt><dd>{date(payment.paymentDate)}</dd></div>
                  <div><dt>Método</dt><dd>{methodLabels[payment.method]}</dd></div>
                  <div><dt>Referencia</dt><dd>{payment.reference || 'Sin referencia'}</dd></div>
                </dl>
              </li>
            ))}
          </ul>
        )}
        <Pagination page={page} totalPages={Math.max(1, Math.ceil(total / PAYMENT_PAGE_SIZE))} totalItems={total} onPageChange={setPage} label="movimientos" />
      </>}
    </div>
  );
}

export function PaymentHistory(props: ActivityProps) {
  return <PaymentHistoryPage key={props.orderId} {...props} />;
}

export function OrderActivityPanel(props: ActivityProps) {
  return (
    <div className="order-activity-grid">
      <StatusHistory key={props.orderId} {...props} />
      <section className="admin-card" aria-labelledby="payment-history-title">
        <h2 id="payment-history-title">Movimientos de pago</h2>
        <PaymentHistory {...props} />
      </section>
    </div>
  );
}
