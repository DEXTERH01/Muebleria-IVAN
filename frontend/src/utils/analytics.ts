import type { Order, OrderStatus } from '../types';

export interface ForecastPoint {
  label: string;
  value: number;
  projected?: boolean;
}

function linearProjection(values: number[], futurePeriods: number) {
  const n = values.length;
  if (n < 2) return Array.from({ length: futurePeriods }, () => values[0] ?? 0);
  const sumX = values.reduce((sum, _, index) => sum + index, 0);
  const sumY = values.reduce((sum, value) => sum + value, 0);
  const sumXY = values.reduce((sum, value, index) => sum + index * value, 0);
  const sumXX = values.reduce((sum, _, index) => sum + index * index, 0);
  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  return Array.from({ length: futurePeriods }, (_, index) =>
    Math.max(0, Math.round(intercept + slope * (n + index))),
  );
}

export function getDemandForecast(period: 30 | 60 | 90, orders: Order[]): ForecastPoint[] {
  const months = period === 30 ? 1 : period === 60 ? 2 : 3;
  const monthly = new Map<string, number>();
  for (const order of orders) {
    const key = order.createdAt.slice(0, 7);
    monthly.set(key, (monthly.get(key) ?? 0) + 1);
  }
  const periods = [...monthly.keys()].sort().slice(-6);
  const historicalDemand = periods.map((key) => monthly.get(key) ?? 0);
  const label = (key: string) => new Intl.DateTimeFormat('es-PE', { month: 'short' })
    .format(new Date(`${key}-01T12:00:00`))
    .replace('.', '');
  const lastPeriod = periods[periods.length - 1] ?? new Date().toISOString().slice(0, 7);
  const [lastYear, lastMonth] = lastPeriod.split('-').map(Number);
  const futureLabels = Array.from({ length: months }, (_, index) => {
    const date = new Date(lastYear, lastMonth + index, 1);
    return new Intl.DateTimeFormat('es-PE', { month: 'short' }).format(date).replace('.', '');
  });
  return [
    ...historicalDemand.map((value, index) => ({ label: label(periods[index]), value })),
    ...linearProjection(historicalDemand, months).map((value, index) => ({
      label: futureLabels[index],
      value,
      projected: true,
    })),
  ];
}

const statusRisk: Record<OrderStatus, number> = {
  'material-pendiente': 32,
  corte: 22,
  armado: 14,
  listo: 6,
  instalado: 0,
};

export function getOrderRisk(order: Order) {
  const referenceDate = new Date();
  const delivery = new Date(`${order.deliveryDate}T12:00:00`);
  const daysLeft = Math.ceil((delivery.getTime() - referenceDate.getTime()) / 86400000);
  const urgency = daysLeft <= 2 ? 42 : daysLeft <= 5 ? 26 : daysLeft <= 9 ? 12 : 3;
  const paymentRisk = order.paymentStatus === 'pendiente' ? 16 : 0;
  const score = Math.min(96, statusRisk[order.status] + urgency + paymentRisk);
  return {
    score,
    level: score >= 60 ? 'Alto' : score >= 36 ? 'Medio' : 'Bajo',
    reason:
      order.paymentStatus === 'pendiente'
        ? 'Anticipo pendiente y fecha próxima'
        : daysLeft <= 5
          ? 'Pocos días para la fecha de entrega'
          : 'Avance acorde al plazo registrado',
  };
}

export function categoryDemand(orders: Order[]) {
  const categories = ['Closets', 'Cocinas', 'Escritorios', 'Muebles TV'];
  return categories.map((label) => {
    const needle = label === 'Closets' ? 'closet' : label === 'Cocinas' ? 'cocina' : label === 'Escritorios' ? 'escritorio' : 'tv';
    const current = orders.filter((order) => order.productType.toLowerCase().includes(needle)).length;
    const multiplier = label === 'Closets' ? 1.34 : label === 'Cocinas' ? 1.22 : label === 'Escritorios' ? 1.12 : 1.08;
    return { label, current, projected: Math.max(current + 1, Math.round(current * multiplier + 1)) };
  });
}
