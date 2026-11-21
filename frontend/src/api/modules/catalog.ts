import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

export type ProductImage = components['schemas']['ProductImageData'];
export type CatalogOption = components['schemas']['CatalogOptionData'];
export type ProductSummary = components['schemas']['ProductSummaryData'];
export type MeasurementLimits = components['schemas']['MeasurementLimits'];
export type ProductDetail = components['schemas']['ProductDetailData'];
type ProductListResponse = components['schemas']['ProductListResponse'];
type ProductResponse = components['schemas']['ProductResponse'];
type ProductImageAttachRequest = components['schemas']['ProductImageAttachRequest'];

export async function listProducts(filters: {
  category?: string;
  search?: string;
} = {}): Promise<ProductListResponse['data']> {
  const params = new URLSearchParams({ page: '1', pageSize: '100' });
  if (filters.category) params.set('category', filters.category);
  if (filters.search && filters.search.trim().length >= 2) {
    params.set('search', filters.search.trim());
  }
  const response = await apiRequest<ProductListResponse>(`/api/v1/products?${params}`);
  return response.data;
}

export async function getProduct(slug: string): Promise<ProductDetail> {
  const response = await apiRequest<ProductResponse>(
    `/api/v1/products/${encodeURIComponent(slug)}`,
  );
  return response.data;
}

export async function attachProductImage(
  productId: string,
  input: ProductImageAttachRequest,
): Promise<ProductDetail> {
  const response = await apiRequest<ProductResponse>(
    `/api/v1/products/${encodeURIComponent(productId)}/images`,
    { method: 'POST', body: JSON.stringify(input) },
  );
  return response.data;
}
