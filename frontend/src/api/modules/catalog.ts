import { apiRequest } from '../client/http';

export interface ProductImage {
  id: string;
  secureUrl: string;
  altText: string;
  position: number;
  width: number | null;
  height: number | null;
}

export interface CatalogOption {
  id: string;
  code: string;
  name: string;
  description: string;
  priceAdjustmentMinor: number;
  priceAdjustmentPercent: string;
  isDefault: boolean;
}

export interface ProductSummary {
  id: string;
  slug: string;
  name: string;
  description: string;
  category: string;
  basePriceMinor: number;
  minProductionDays: number;
  maxProductionDays: number;
  primaryImage: ProductImage | null;
}

export interface MeasurementLimits {
  minWidthMm: number;
  maxWidthMm: number;
  minHeightMm: number;
  maxHeightMm: number;
  minDepthMm: number;
  maxDepthMm: number;
}

export interface ProductDetail extends ProductSummary {
  active: boolean;
  measurementLimits: MeasurementLimits;
  images: ProductImage[];
  materials: CatalogOption[];
  finishes: CatalogOption[];
  accessories: CatalogOption[];
}

interface ProductListResponse {
  data: {
    items: ProductSummary[];
    page: number;
    pageSize: number;
    total: number;
  };
}

interface ProductResponse {
  data: ProductDetail;
}

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
