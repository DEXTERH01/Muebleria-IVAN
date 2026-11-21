import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

export type ApiOrder = components['schemas']['OrderOut'];
export type ApiOrderStatus = ApiOrder['status'];
export type ApiPaymentMethod = components['schemas']['PaymentCreate']['method'];
export type ApiPayment = components['schemas']['PaymentOut'];

type OrderListResponse = components['schemas']['OrderListResponse'];
type OrderResponse = components['schemas']['OrderResponse'];
type PaymentListResponse = components['schemas']['PaymentListResponse'];
type PaymentResponse = components['schemas']['PaymentResponse'];

export async function listOrders(): Promise<ApiOrder[]> {
  const response = await apiRequest<OrderListResponse>('/api/v1/orders?page=1&pageSize=100');
  return response.data;
}

export async function setOrderStatus(
  orderId: string,
  newStatus: ApiOrderStatus,
  version: number,
  note?: string,
): Promise<ApiOrder> {
  const response = await apiRequest<OrderResponse>(
    `/api/v1/orders/${encodeURIComponent(orderId)}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ newStatus, version, ...(note ? { note } : {}) }),
    },
  );
  return response.data;
}

export async function listPayments(orderId: string): Promise<ApiPayment[]> {
  const response = await apiRequest<PaymentListResponse>(
    `/api/v1/orders/${encodeURIComponent(orderId)}/payments?page=1&pageSize=100`,
  );
  return response.data;
}

export async function createPayment(
  orderId: string,
  input: components['schemas']['PaymentCreate'],
): Promise<ApiPayment> {
  const response = await apiRequest<PaymentResponse>(
    `/api/v1/orders/${encodeURIComponent(orderId)}/payments`,
    {
      method: 'POST',
      headers: { 'Idempotency-Key': crypto.randomUUID() },
      body: JSON.stringify(input),
    },
  );
  return response.data;
}
