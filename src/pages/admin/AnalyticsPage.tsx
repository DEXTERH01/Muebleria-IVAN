import { useMemo, useState } from 'react';
import { AdminLayout, navigate } from '../../components/layout';
import { Button, StatusBadge } from '../../components/ui';
import type { Order } from '../../types';
import { categoryDemand, getDemandForecast, getOrderRisk } from '../../utils/analytics';
import { date, money } from '../../utils/format';

export function AnalyticsPage({ orders }: { orders: Order[] }) {
  const [period, setPeriod] = useState<30 | 60 | 90>(60);
  const forecast = useMemo(() => getDemandForecast(period), [period]);
  const demand = useMemo(() => categoryDemand(orders), [orders]);
  const risks = useMemo(() => orders
    .filter((order) => order.status !== 'instalado')
    .map((order) => ({ order, risk: getOrderRisk(order) }))
    .sort((a, b) => b.risk.score - a.risk.score), [orders]);
  const maxValue = Math.max(...forecast.map((point) => point.value));
  const projectedOrders = forecast[forecast.length - 1]?.value ?? 0;
  const averageTicket = Math.round(orders.reduce((sum, order) => sum + order.total, 0) / orders.length);

  return <AdminLayout title="Análisis inteligente" subtitle="IA Y ANÁLISIS PREDICTIVO">
    <section className="ai-disclaimer">
      <span>✦</span>
      <div><b>Laboratorio de IA · Simulación académica</b><p>Las proyecciones se generan con datos simulados y algoritmos demostrativos. No representan predicciones comerciales reales.</p></div>
    </section>

    <div className="analytics-controls">
      <div><h2>Panorama de los próximos meses</h2><p>Indicadores calculados a partir del historial simulado de pedidos.</p></div>
      <div className="period-control" aria-label="Periodo de proyección">{([30, 60, 90] as const).map((value) => <button className={period === value ? 'active' : ''} onClick={() => setPeriod(value)} key={value}>{value} días</button>)}</div>
    </div>

    <section className="ai-metrics">
      <article><span className="metric-icon purple">↗</span><div><small>Demanda estimada</small><strong>{projectedOrders} proyectos</strong><em>+18% frente al periodo anterior</em></div></article>
      <article><span className="metric-icon amber">!</span><div><small>Pedidos con atención</small><strong>{risks.filter((item) => item.risk.level !== 'Bajo').length} pedidos</strong><em>Revisar fechas y anticipos</em></div></article>
      <article><span className="metric-icon green">S/</span><div><small>Ticket promedio</small><strong>{money(averageTicket)}</strong><em>Calculado sobre {orders.length} pedidos</em></div></article>
      <article><span className="metric-icon blue">◎</span><div><small>Confianza simulada</small><strong>84%</strong><em>Modelo demostrativo v1.0</em></div></article>
    </section>

    <section className="analytics-grid">
      <article className="admin-card forecast-card">
        <div className="card-title"><div><h2>Proyección de demanda</h2><p>Regresión lineal simple sobre pedidos mensuales simulados.</p></div><span className="model-chip">Modelo lineal</span></div>
        <div className="forecast-chart" role="img" aria-label="Gráfico de demanda histórica y proyectada">
          {forecast.map((point) => <div className={`forecast-column ${point.projected ? 'projected' : ''}`} key={point.label}>
            <span>{point.value}</span><i style={{ height: `${Math.max(18, point.value / maxValue * 150)}px` }}/><small>{point.label}</small>
          </div>)}
        </div>
        <div className="chart-legend"><span><i className="history"/>Histórico simulado</span><span><i className="projection"/>Proyección IA</span></div>
      </article>

      <article className="admin-card insight-card">
        <div className="ai-insight-label">✦ RECOMENDACIÓN INTELIGENTE</div>
        <h2>Prepárate para una mayor demanda de closets.</h2>
        <p>El patrón de los últimos meses indica que esta categoría podría crecer durante el próximo periodo.</p>
        <ul>
          <li><span>01</span>Revisar stock de melamina en tonos roble.</li>
          <li><span>02</span>Reservar capacidad de corte para noviembre.</li>
          <li><span>03</span>Promocionar el modelo Closet Siena.</li>
        </ul>
        <Button variant="secondary" onClick={() => navigate('/catalogo')}>Revisar catálogo →</Button>
      </article>
    </section>

    <section className="analytics-grid lower">
      <article className="admin-card demand-card">
        <div className="card-title"><div><h2>Demanda por categoría</h2><p>Comparación del volumen actual con el estimado.</p></div></div>
        <div className="demand-list">{demand.map((item) => <div key={item.label}>
          <div><b>{item.label}</b><span>{item.current} actuales · {item.projected} estimados</span></div>
          <div className="demand-track"><i style={{ width: `${Math.min(100, item.current * 18)}%` }}/><i className="predicted" style={{ width: `${Math.min(100, item.projected * 18)}%` }}/></div>
        </div>)}</div>
      </article>

      <article className="admin-card risk-card">
        <div className="card-title"><div><h2>Riesgo de retraso</h2><p>Puntaje heurístico por etapa, fecha y pago.</p></div><button className="text-button" onClick={() => navigate('/admin/pedidos')}>Ver pedidos →</button></div>
        <div className="risk-list">{risks.slice(0, 4).map(({ order, risk }) => <button onClick={() => navigate(`/admin/pedido/${order.id}`)} key={order.id}>
          <div className={`risk-score ${risk.level.toLowerCase()}`}>{risk.score}<small>%</small></div>
          <div><b>{order.id} · {order.customerName}</b><span>{risk.reason}</span><small>Entrega {date(order.deliveryDate)}</small></div>
          <StatusBadge status={order.status}/><i>→</i>
        </button>)}</div>
      </article>
    </section>
  </AdminLayout>;
}
