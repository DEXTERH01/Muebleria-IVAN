import { useEffect, useState } from 'react';

import type { QuoteData } from './api/modules/quotes';
import { AuthGuard, AuthPage, CustomerPortal } from './auth/AuthPage';
import { AuthProvider } from './auth/AuthProvider';
import { AIAssistant } from './components/AIAssistant';
import { Toast, useToast } from './components/ui';
import { customers } from './data/customers';
import { useOrders } from './hooks/useOrders';
import { AnalyticsPage } from './pages/admin/AnalyticsPage';
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
  const { orders, updateOrder, registerPayment } = useOrders();
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
  }
  else if (path === '/admin/kanban') {
    page = (
      <AuthGuard roles={['admin', 'operator']}><KanbanPage
        orders={orders}
        onMove={(id, status) => updateOrder(id, { status })}
        showToast={show}
      /></AuthGuard>
    );
  } else if (path === '/admin/pagos') {
    page = <AuthGuard roles={['admin', 'operator']}><PaymentsPage orders={orders} onPayment={registerPayment} showToast={show} /></AuthGuard>;
  } else if (path === '/admin/clientes') {
    page = <AuthGuard roles={['admin', 'operator']}><CustomersPage customers={customers} orders={orders} /></AuthGuard>;
  } else if (path === '/admin/analitica') {
    page = <AuthGuard roles={['admin', 'operator']}><AnalyticsPage orders={orders} /></AuthGuard>;
  }
  else if (adminOrder) {
    const order = orders.find((item) => item.id === adminOrder[1]) ?? orders[0];
    page = (
      <AuthGuard roles={['admin', 'operator']}><OrderDetail
        order={order}
        customer={customers.find((customer) => customer.id === order.customerId)}
        onMove={(id, status) => {
          updateOrder(id, { status });
          show('Pedido actualizado correctamente.');
        }}
        onPayment={(id, amount) => {
          registerPayment(id, amount);
          show('Pago registrado correctamente.');
        }}
      /></AuthGuard>
    );
  } else page = <HomePage />;

  return (
    <>
      {page}
      {!path.startsWith('/admin') && <AIAssistant orders={orders} />}
      <Toast message={toast} />
    </>
  );
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>;
}
