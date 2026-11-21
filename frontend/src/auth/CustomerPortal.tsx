import { useCallback, useEffect, useState } from 'react';

import { getOrder, listOrders, type ApiOrder, type ApiOrderDetail } from '../api/modules/orders';
import { listQuotes, type QuoteData, type QuoteStatus } from '../api/modules/quotes';
import { Button } from '../components/ui';
import { Footer, Navbar, navigate } from '../components/layout';
import { date, moneyMinor } from '../utils/format';

const statusLabel: Record<ApiOrder['status'], string> = {
  confirmed: 'Confirmado',
  materials_pending: 'Materiales pendientes',
  cutting: 'En corte',
  assembly: 'En armado',
  finishing: 'En acabado',
  ready: 'Listo para entrega',
  delivered: 'Entregado',
  installed: 'Instalado',
  cancelled: 'Cancelado',
};

const quoteStatusLabel: Record<QuoteStatus, string> = {
  draft: 'Borrador',
  submitted: 'Enviada',
  reviewing: 'En revisión',
  approved: 'Aprobada',
  rejected: 'Rechazada',
  expired: 'Vencida',
  converted: 'Convertida en pedido',
};

export function CustomerPortal() {
  const [orders, setOrders] = useState<ApiOrder[]>([]);
  const [quotes, setQuotes] = useState<QuoteData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [history, setHistory] = useState<Record<string, ApiOrderDetail['statusHistory']>>({});
  const [historyLoading, setHistoryLoading] = useState<Record<string, boolean>>({});
  const [historyError, setHistoryError] = useState<Record<string, string>>({});

  const loadPortal = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextOrders, quoteList] = await Promise.all([listOrders(), listQuotes()]);
      setOrders(nextOrders);
      setQuotes(quoteList.items);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No pudimos cargar tu información.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPortal();
  }, [loadPortal, retry]);

  const loadHistory = async (orderId: string) => {
    if (orderId in history || historyLoading[orderId]) return;
    setHistoryLoading((current) => ({ ...current, [orderId]: true }));
    setHistoryError((current) => ({ ...current, [orderId]: '' }));
    try {
      const order = await getOrder(orderId);
      setHistory((current) => ({ ...current, [orderId]: order.statusHistory }));
    } catch (reason) {
      setHistoryError((current) => ({
        ...current,
        [orderId]: reason instanceof Error ? reason.message : 'No pudimos cargar el historial.',
      }));
    } finally {
      setHistoryLoading((current) => ({ ...current, [orderId]: false }));
    }
  };

  const toggleHistory = (orderId: string) => {
    const opening = !expanded[orderId];
    setExpanded((current) => ({ ...current, [orderId]: opening }));
    if (opening) void loadHistory(orderId);
  };

  return (
    <>
      <Navbar />
      <main className="customer-portal-page">
        <header className="customer-portal-heading">
          <span className="kicker">MI CUENTA</span>
          <h1>Tus proyectos</h1>
          <p>Consulta tus cotizaciones, el avance de tus pedidos y sus saldos.</p>
        </header>

        {loading && <p role="status" className="portal-notice">Cargando tus pedidos…</p>}
        {error && (
          <section className="portal-notice portal-error" role="alert">
            <b>{error}</b>
            <p>Intenta nuevamente en unos momentos.</p>
            <Button onClick={() => setRetry((value) => value + 1)}>Reintentar</Button>
          </section>
        )}
        {!loading && !error && orders.length === 0 && quotes.length === 0 && (
          <section className="portal-notice portal-empty">
            <h2>Aún no tienes proyectos</h2>
            <p>Las cotizaciones que envíes y sus pedidos aparecerán aquí.</p>
            <Button onClick={() => navigate('/catalogo')}>Explorar catálogo</Button>
          </section>
        )}
        {!loading && !error && quotes.length > 0 && (
          <section className="customer-portal-section" aria-labelledby="customer-quotes-title">
            <div className="customer-section-heading">
              <div>
                <span className="kicker">COTIZACIONES</span>
                <h2 id="customer-quotes-title">Solicitudes enviadas</h2>
              </div>
              <Button variant="secondary" onClick={() => navigate('/cotizador')}>Nueva cotización</Button>
            </div>
            <div className="customer-quote-list">
              {quotes.map((quote) => (
                <article className="customer-quote-card" key={quote.id}>
                  <div>
                    <b>{quote.code}</b>
                    <span className={`customer-quote-status quote-${quote.status}`}>
                      {quoteStatusLabel[quote.status]}
                    </span>
                  </div>
                  <h3>{quote.items.map((item) => item.productName).join(', ')}</h3>
                  <dl>
                    <div><dt>Total referencial</dt><dd>{moneyMinor(quote.totalMinor)}</dd></div>
                    <div><dt>Válida hasta</dt><dd>{date(quote.expiresAt.slice(0, 10))}</dd></div>
                  </dl>
                </article>
              ))}
            </div>
          </section>
        )}
        {!loading && !error && orders.length > 0 && (
          <section className="customer-portal-section" aria-labelledby="customer-orders-title">
            <div className="customer-section-heading">
              <div>
                <span className="kicker">PEDIDOS</span>
                <h2 id="customer-orders-title">Seguimiento del taller</h2>
              </div>
            </div>
            <div className="customer-order-list">
            {orders.map((order) => (
              <article className="customer-order-card" key={order.id}>
                <div className="customer-order-heading">
                  <div>
                    <span className="kicker">PEDIDO</span>
                    <h2>{order.code}</h2>
                  </div>
                  <span className={`customer-order-status status-${order.status}`}>
                    {statusLabel[order.status]}
                  </span>
                </div>
                <dl className="customer-order-details">
                  <div><dt>Creado</dt><dd>{date(order.createdAt.slice(0, 10))}</dd></div>
                  <div><dt>Entrega estimada</dt><dd>{date(order.promisedDate)}</dd></div>
                  <div><dt>Total</dt><dd>{moneyMinor(order.totalMinor)}</dd></div>
                  <div><dt>Pagado</dt><dd>{moneyMinor(order.paidMinor)}</dd></div>
                  <div><dt>Saldo pendiente</dt><dd>{moneyMinor(order.balanceMinor)}</dd></div>
                </dl>
                <button
                  type="button"
                  className="order-history-toggle"
                  aria-expanded={Boolean(expanded[order.id])}
                  onClick={() => toggleHistory(order.id)}
                >
                  {expanded[order.id] ? 'Ocultar historial' : 'Ver historial de etapas'}
                </button>
                {expanded[order.id] && (
                  <div className="order-history-panel">
                    {historyLoading[order.id] && <p role="status">Cargando historial…</p>}
                    {historyError[order.id] && (
                      <p role="alert">
                        {historyError[order.id]}{' '}
                        <button type="button" className="text-button" onClick={() => void loadHistory(order.id)}>Reintentar</button>
                      </p>
                    )}
                    {order.id in history && history[order.id].length === 0 && (
                      <p>Aún no hay cambios de etapa registrados.</p>
                    )}
                    {!!history[order.id]?.length && (
                      <ol className="order-history-list">
                        {history[order.id].map((event, index) => (
                          <li key={`${event.occurredAt}-${index}`}>
                            <span className="order-history-dot" aria-hidden="true" />
                            <div>
                              <b>{statusLabel[event.newStatus]}</b>
                              {event.previousStatus && <span>Desde {statusLabel[event.previousStatus].toLocaleLowerCase('es')}</span>}
                              {event.note && <p>{event.note}</p>}
                              <time dateTime={event.occurredAt}>{date(event.occurredAt.slice(0, 10))}</time>
                            </div>
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                )}
              </article>
            ))}
            </div>
          </section>
        )}
      </main>
      <Footer />
    </>
  );
}
