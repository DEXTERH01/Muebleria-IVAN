import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

export type ApiCustomer = components['schemas']['CustomerOut'];
type CustomerListResponse = components['schemas']['CustomerListResponse'];

export interface CustomerPage {
  items: ApiCustomer[];
  total: number;
  page: number;
  pageSize: number;
}

export async function listCustomers(page = 1, pageSize = 100): Promise<CustomerPage> {
  const response = await apiRequest<CustomerListResponse>(
    `/api/v1/customers?page=${page}&pageSize=${pageSize}`,
  );
  return {
    items: response.data,
    total: response.total,
    page: response.page,
    pageSize: response.pageSize,
  };
}
