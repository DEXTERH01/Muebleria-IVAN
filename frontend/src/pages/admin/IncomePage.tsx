import { useEffect, useState } from 'react';
import { listOrders, listPayments, type ApiPayment } from '../../api/modules/orders';
import { AdminLayout } from '../../components/layout';
import { moneyMinor } from '../../utils/format';
import './income.css';

const methods = [
  { id: 'bank_transfer', label: 'Transferencia', color: '#397D72' },
  { id: 'cash', label: 'Efectivo', color: '#C58B46' },
  { id: 'card', label: 'Tarjeta', color: '#737AA8' },
  { id: 'other', label: 'Otros', color: '#B46E62' },
];
function todayInLima() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Lima', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
}
function periodStart(date: string, period: string) {
  const value = new Date(`${date}T12:00:00Z`);
  if (period === 'week') value.setUTCDate(value.getUTCDate() - (value.getUTCDay() + 6) % 7);
  if (period === 'month') value.setUTCDate(1);
  return value.toISOString().slice(0, 10);
}
export function IncomePage() {
  const [period, setPeriod] = useState('month');
  const [date, setDate] = useState(todayInLima);
  const [payments, setPayments] = useState<ApiPayment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError(null);
    (async () => {
      const orders = await listOrders();
      const result: ApiPayment[] = [];
      // Bound simultaneous requests while preserving complete payment history.
      for (let index = 0; index < orders.length; index += 5) {
        const batch = await Promise.all(orders.slice(index, index + 5).map(order => listPayments(order.id)));
        result.push(...batch.flat());
      }
      if (active) setPayments(result);
    })().catch(() => { if (active) setError('No pudimos cargar los ingresos. Reintenta para consultar los importes completos.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reload]);
  const start = periodStart(date, period);
  const filtered = payments.filter(payment => payment.status === 'recorded' && payment.paymentDate >= start && payment.paymentDate <= date);
  const total = filtered.reduce((sum, payment) => sum + payment.amountMinor, 0);
  let accumulated = 0;
  const distribution = methods.map(method => {
    const amount = filtered.filter(payment => payment.method === method.id).reduce((sum, payment) => sum + payment.amountMinor, 0);
    const from = accumulated; accumulated += total ? amount / total * 100 : 0;
    return { ...method, amount, segment: `${method.color} ${from}% ${accumulated}%` };
  });
  const daily = new Map<string, number>();
  filtered.forEach(payment => daily.set(payment.paymentDate, (daily.get(payment.paymentDate) ?? 0) + payment.amountMinor));
  const days = [...daily].sort(([left], [right]) => left.localeCompare(right));
  const max = Math.max(1, ...days.map(([, amount]) => amount));
  return <AdminLayout title="Ingresos" subtitle="CONTROL FINANCIERO · DUEÑO">
    <div className="income-page">
      <header className="income-toolbar"><div><h2>Tu negocio, en cifras claras</h2><p>Cobros registrados por fecha de pago. Periodos hasta la fecha seleccionada.</p></div><button className="text-button" onClick={() => setReload(value => value + 1)}>Actualizar</button></header>
      <div className="income-filters"><div role="group" aria-label="Periodo de ingresos">{[['day', 'Diario'], ['week', 'Semanal'], ['month', 'Mensual']].map(([id, label]) => <button key={id} aria-pressed={period === id} onClick={() => setPeriod(id)}>{label}</button>)}</div><label>Fecha de corte<input type="date" value={date} onChange={event => { if (event.target.value) setDate(event.target.value); }} required /></label></div>
      {loading ? <p role="status">Cargando pagos de todos los pedidos…</p> : error ? <p role="alert">{error}</p> : <>
        <section className="income-kpis"><article><small>INGRESOS COBRADOS</small><strong>{moneyMinor(total)}</strong><span>{start} — {date}</span></article><article><small>PAGOS REGISTRADOS</small><strong>{filtered.length}</strong><span>Pagos anulados excluidos</span></article><article><small>COBRO PROMEDIO</small><strong>{moneyMinor(filtered.length ? Math.round(total / filtered.length) : 0)}</strong><span>Por operación del periodo</span></article></section>
        <div className="income-grid"><section className="admin-card"><h2>¿Cómo te pagan?</h2><p>Distribución de ingresos por medio de pago</p><div className="income-distribution"><div className="income-donut" role="img" aria-label={`Ingresos totales: ${moneyMinor(total)}. Desglose en la leyenda.`} style={{ background: total ? `conic-gradient(${distribution.map(item => item.segment).join(',')})` : 'var(--line)' }}><div><small>Total cobrado</small><strong>{moneyMinor(total)}</strong></div></div><ul>{distribution.map(item => <li key={item.id}><i style={{background: item.color}}/><span>{item.label}<small>{total ? (item.amount / total * 100).toFixed(1) : '0'}%</small></span><b>{moneyMinor(item.amount)}</b></li>)}</ul></div></section>
        <section className="admin-card"><h2>Evolución de cobros</h2><p>Importes recibidos por día del periodo</p>{days.length ? <div className="income-trend">{days.map(([day, amount]) => <div key={day}><span>{day.slice(5)}</span><div><i style={{width: `${amount / max * 100}%`}}/></div><b>{moneyMinor(amount)}</b></div>)}</div> : <p className="income-empty">Sin pagos registrados en este periodo.</p>}</section></div>
        <p className="income-note">Los importes incluyen los datos de prueba que existan en el sistema. La utilidad neta requiere registrar costos y gastos; aún no está disponible.</p>
      </>}
    </div>
  </AdminLayout>;
}
