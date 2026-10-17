import type { Order, OrderStatus } from '../types';

export interface ForecastPoint {
  label: string;
  value: number;
  projected?: boolean;
}

const historicalDemand = [9, 11, 10, 14, 16, 18];
const historicalLabels = ['May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct'];

function linearProjection(values: number[], futurePeriods: number) {
  const n = values.length;
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

export function getDemandForecast(period: 30 | 60 | 90): ForecastPoint[] {
  const months = period === 30 ? 1 : period === 60 ? 2 : 3;
  const futureLabels = ['Nov', 'Dic', 'Ene'];
  return [
    ...historicalDemand.map((value, index) => ({ label: historicalLabels[index], value })),
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
  const referenceDate = new Date('2026-10-17T12:00:00');
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
