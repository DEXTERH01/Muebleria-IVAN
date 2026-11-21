import { useEffect, useState } from 'react';

import type { QuoteData } from './api/modules/quotes';
import { AuthGuard, AuthPage } from './auth/AuthPage';
import { AuthProvider } from './auth/AuthProvider';
import { CustomerPortal } from './auth/CustomerPortal';
import { AIAssistant } from './components/AIAssistant';
import { Toast, useToast } from './components/ui';
import { customers } from './data/customers';
import { useOrders } from './hooks/useOrders';
import { AnalyticsPage } from './pages/admin/AnalyticsPage';
import { CatalogAdminPage } from './pages/admin/CatalogAdminPage';
import { QuotesPage } from './pages/admin/QuotesPage';
import { OptimizationsPage } from './pages/admin/OptimizationsPage';
import {
  CustomersPage,
  Dashboard,
  KanbanPage,
  OrderDetail,
  OrdersPage,
  PaymentsPage,
} from './pages/admin/AdminPages';
import { CatalogPage } from './pages/CatalogPage';
import { HomePage } from './pages/HomePage';
import { ProductDetailPage } from './pages/ProductDetailPage';
import { QuotePage } from './pages/QuotePage';
import { QuoteSummaryPage } from './pages/QuoteSummaryPage';

function AppRoutes() {
  const [path, setPath] = useState(window.location.pathname);
  const [quote, setQuote] = useState<QuoteData | null>(null);
  const { orders, loading: ordersLoading, error: ordersError, reload, updateOrder, registerPayment } = useOrders();
  const { toast, show } = useToast();

  useEffect(() => {
    const listener = () => setPath(window.location.pathname);
    window.addEventListener('popstate', listener);
    return () => window.removeEventListener('popstate', listener);
  }, []);

  const detail = path.match(/^\/producto\/([^/]+)$/);
  const adminOrder = path.match(/^\/admin\/pedido\/([^/]+)$/);
  let page;
  if (path === '/') page = <HomePage />;
  else if (path === '/catalogo') page = <CatalogPage />;
  else if (detail) page = <ProductDetailPage id={detail[1]} />;
  else if (path === '/cotizador') {
    page = (
      <QuotePage
        onComplete={setQuote}
        initialType={new URLSearchParams(window.location.search).get('producto') ?? undefined}
      />
    );
  } else if (path === '/cotizacion') page = <QuoteSummaryPage quote={quote} />;
  else if (path === '/iniciar-sesion') page = <AuthPage mode="login" />;
  else if (path === '/crear-cuenta') page = <AuthPage mode="register" />;
  else if (path === '/recuperar-contrasena') page = <AuthPage mode="recovery" />;
  else if (path === '/restablecer-contrasena') page = <AuthPage mode="update-password" />;
  else if (path === '/mi-cuenta') {
    page = <AuthGuard roles={['customer']}><CustomerPortal /></AuthGuard>;
  } else if (path === '/admin') {
    page = <AuthGuard roles={['admin', 'operator']}><Dashboard orders={orders} /></AuthGuard>;
  } else if (path === '/admin/pedidos') {
    page = <AuthGuard roles={['admin', 'operator']}><OrdersPage orders={orders} /></AuthGuard>;
  } else if (path === '/admin/cotizaciones') {
    page = <AuthGuard roles={['admin']}><QuotesPage showToast={show} onOrdersChanged={reload} /></AuthGuard>;
  } else if (path === '/admin/catalogo') {
    page = <AuthGuard roles={['admin']}><CatalogAdminPage showToast={show} /></AuthGuard>;
  }
  else if (path === '/admin/kanban') {
    page = (
      <AuthGuard roles={['admin', 'operator']}><KanbanPage
        orders={orders}
        onMove={(id, status) => {
          void updateOrder(id, { status })
            .then(() => show('Etapa actualizada.'))
            .catch((error: unknown) => show(error instanceof Error ? error.message : 'No se pudo actualizar el pedido.'));
        }}
        showToast={show}
      /></AuthGuard>
    );
  } else if (path === '/admin/pagos') {
    page = <AuthGuard roles={['admin', 'operator']}><PaymentsPage orders={orders} onPayment={registerPayment} showToast={show} /></AuthGuard>;
  } else if (path === '/admin/clientes') {
    page = <AuthGuard roles={['admin', 'operator']}><CustomersPage customers={customers} orders={orders} /></AuthGuard>;
  } else if (path === '/admin/analitica') {
    page = <AuthGuard roles={['admin', 'operator']}><AnalyticsPage orders={orders} /></AuthGuard>;
  } else if (path === '/admin/optimizaciones') {
    page = <AuthGuard roles={['admin', 'operator']}><OptimizationsPage /></AuthGuard>;
  }
  else if (adminOrder) {
    const order = orders.find((item) => item.id === adminOrder[1]);
    if (!order && !ordersLoading) {
      page = <main className="auth-page"><section className="auth-card"><h1>Pedido no disponible</h1><p>No encontramos ese pedido en la API.</p><button className="text-button" onClick={() => void reload()}>Volver a cargar</button></section></main>;
    } else if (order) {
    page = (
      <AuthGuard roles={['admin', 'operator']}><OrderDetail
        order={order}
        customer={customers.find((customer) => customer.id === order.customerId)}
        onMove={(id, status) => {
          void updateOrder(id, { status })
            .then(() => show('Etapa actualizada.'))
            .catch((error: unknown) => show(error instanceof Error ? error.message : 'No se pudo actualizar el pedido.'));
        }}
        onPayment={(id, amount, method) => {
          void registerPayment(id, amount, method)
            .then(() => show('Pago registrado correctamente.'))
            .catch((error: unknown) => show(error instanceof Error ? error.message : 'No se pudo registrar el pago.'));
        }}
      /></AuthGuard>
    );
    }
  } else page = <HomePage />;

  return (
    <>
      {page}
      {ordersLoading && path.startsWith('/admin') && <p className="data-notice" role="status">Cargando pedidos desde la API…</p>}
      {ordersError && path.startsWith('/admin') && <p className="form-error data-notice" role="alert">{ordersError} <button onClick={() => void reload()}>Reintentar</button></p>}
      {!path.startsWith('/admin') && <AIAssistant orders={orders} />}
      <Toast message={toast} />
    </>
  );
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>;
}
