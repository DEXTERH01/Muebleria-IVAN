import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

export type ApiOrder = components['schemas']['OrderOut'];
export type ApiOrderDetail = components['schemas']['OrderDetailOut'];
export type ApiOrderStatus = ApiOrder['status'];
export type ApiPaymentMethod = components['schemas']['PaymentCreate']['method'];
export type ApiPayment = components['schemas']['PaymentOut'];
export type ApiPaymentCreate = components['schemas']['PaymentCreate'];
export type PaymentHandler = (orderId: string, input: ApiPaymentCreate, idempotencyKey: string) => Promise<void>;

type OrderListResponse = components['schemas']['OrderListResponse'];
type OrderResponse = components['schemas']['OrderResponse'];
type OrderDetailResponse = components['schemas']['OrderDetailResponse'];
type PaymentListResponse = components['schemas']['PaymentListResponse'];
type PaymentResponse = components['schemas']['PaymentResponse'];

async function listOrderPage(page: number, pageSize: number): Promise<OrderListResponse> {
  return apiRequest<OrderListResponse>(`/api/v1/orders?page=${page}&pageSize=${pageSize}`);
}

export async function listOrders(): Promise<ApiOrder[]> {
  const pageSize = 100;
  const first = await listOrderPage(1, pageSize);
  const pages = Math.ceil(first.total / pageSize);
  if (pages <= 1) return first.data;
  const remaining = await Promise.all(
    Array.from({ length: pages - 1 }, (_, index) => listOrderPage(index + 2, pageSize)),
  );
  return [...first.data, ...remaining.flatMap((page) => page.data)];
}

export async function getOrder(orderId: string): Promise<ApiOrderDetail> {
  const response = await apiRequest<OrderDetailResponse>(
    `/api/v1/orders/${encodeURIComponent(orderId)}`,
  );
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

export async function getPaymentPage(orderId: string, page = 1, pageSize = 20): Promise<PaymentListResponse> {
  return apiRequest<PaymentListResponse>(
    `/api/v1/orders/${encodeURIComponent(orderId)}/payments?page=${page}&pageSize=${pageSize}`,
  );
}

export async function listPayments(orderId: string): Promise<ApiPayment[]> {
  const response = await getPaymentPage(orderId, 1, 100);
  return response.data;
}

export async function createPayment(
  orderId: string,
  input: ApiPaymentCreate,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<ApiPayment> {
  const response = await apiRequest<PaymentResponse>(
    `/api/v1/orders/${encodeURIComponent(orderId)}/payments`,
    {
      method: 'POST',
      headers: { 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify(input),
    },
  );
  return response.data;
}
