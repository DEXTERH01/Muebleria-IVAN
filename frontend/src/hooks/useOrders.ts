import { useCallback, useEffect, useState } from 'react';

import { useAuth } from '../auth/AuthProvider';
import {
  createPayment as submitPayment,
  listOrders,
  setOrderStatus,
  type ApiOrder,
  type ApiOrderStatus,
  type ApiPaymentMethod,
} from '../api/modules/orders';
import type { Order, OrderStatus, PaymentStatus } from '../types';

const displayStatus: Record<ApiOrderStatus, OrderStatus> = {
  confirmed: 'material-pendiente',
  materials_pending: 'material-pendiente',
  cutting: 'corte',
  assembly: 'armado',
  finishing: 'armado',
  ready: 'listo',
  delivered: 'listo',
  installed: 'instalado',
  cancelled: 'instalado',
};

function toOrder(apiOrder: ApiOrder): Order {
  const total = apiOrder.totalMinor / 100;
  const advancePaid = apiOrder.paidMinor / 100;
  const remainingBalance = apiOrder.balanceMinor / 100;
  const paymentStatus: PaymentStatus = remainingBalance === 0
    ? 'pagado'
    : advancePaid > 0 ? 'anticipo-pagado' : 'pendiente';

  return {
    id: apiOrder.code,
    apiId: apiOrder.id,
    code: apiOrder.code,
    quoteId: apiOrder.quoteId,
    customerId: apiOrder.customerId,
    customerName: 'Cliente',
    productType: 'Proyecto cotizado',
    width: '—',
    height: '—',
    depth: '—',
    material: '—',
    finish: '—',
    accessories: [],
    total,
    advancePaid,
    remainingBalance,
    status: displayStatus[apiOrder.status],
    paymentStatus,
    createdAt: apiOrder.createdAt.slice(0, 10),
    deliveryDate: apiOrder.promisedDate ?? null,
    version: apiOrder.version,
    apiStatus: apiOrder.status,
  };
}

function transitionsTo(target: OrderStatus, current: ApiOrderStatus): ApiOrderStatus[] {
  const next: Partial<Record<ApiOrderStatus, ApiOrderStatus>> = {
    confirmed: 'materials_pending',
    materials_pending: 'cutting',
    cutting: 'assembly',
    assembly: 'finishing',
    finishing: 'ready',
    ready: 'delivered',
    delivered: 'installed',
  };
  const steps: ApiOrderStatus[] = [];
  let state: ApiOrderStatus = current;
  const targetRank: Record<OrderStatus, number> = {
    'material-pendiente': 0,
    corte: 1,
    armado: 2,
    listo: 3,
    instalado: 4,
  };
  while (displayStatus[state] !== target && targetRank[displayStatus[state]] < targetRank[target]) {
    const nextState = next[state];
    if (!nextState) break;
    steps.push(nextState);
    state = nextState;
  }
  if (displayStatus[state] === target) return [];
  if (targetRank[displayStatus[state]] > targetRank[target]) {
    throw new Error('Los pedidos solo pueden avanzar a la siguiente etapa.');
  }
  while (displayStatus[state] !== target) {
    const nextState = next[state];
    if (!nextState) break;
    steps.push(nextState);
    state = nextState;
  }
  if (displayStatus[state] !== target) {
    throw new Error('No hay una transición disponible para esa etapa.');
  }
  return steps;
}

export function useOrders() {
  const auth = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!auth || auth.loading) return;
    if (!auth.session) {
      setOrders([]);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setOrders((await listOrders()).map(toOrder));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No pudimos cargar los pedidos.');
    } finally {
      setLoading(false);
    }
  }, [auth?.loading, auth?.session]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const updateOrder = async (id: string, patch: Partial<Order>) => {
    const order = orders.find((item) => item.id === id);
    if (!order || !patch.status) return;
    const transitions = transitionsTo(patch.status, order.apiStatus as ApiOrderStatus);
    if (transitions.length === 0) return;
    try {
      let current = {
        id: order.apiId,
        version: order.version,
      };
      for (const newStatus of transitions) {
        const updated = await setOrderStatus(current.id, newStatus, current.version);
        current = { id: updated.id, version: updated.version };
      }
      await reload();
    } catch (reason) {
      await reload();
      throw reason;
    }
  };

  const registerPayment = async (
    id: string,
    amount: number,
    method: ApiPaymentMethod = 'bank_transfer',
  ) => {
    try {
      const order = orders.find((item) => item.id === id);
      if (!order) throw new Error('No encontramos el pedido que quieres actualizar.');
      await submitPayment(order.apiId, {
        amountMinor: Math.round(amount * 100),
        currency: 'PEN',
        method,
        paymentDate: new Date().toISOString().slice(0, 10),
      });
      await reload();
    } catch (reason) {
      await reload();
      throw reason;
    }
  };

  return { orders, loading, error, reload, updateOrder, registerPayment };
}
