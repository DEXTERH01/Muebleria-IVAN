import { apiRequest } from '../client/http';

export interface EstimateItemInput {
  productId: string;
  quantity: number;
  widthMm: number;
  heightMm: number;
  depthMm: number;
  materialId?: string;
  finishId?: string;
  accessoryIds: string[];
  configuration: Record<string, unknown>;
}

export interface SelectedOption {
  id: string;
  code: string;
  name: string;
  adjustmentMinor: number;
}

export interface PricingBreakdown {
  referenceBaseMinor: number;
  sizeAdjustedBaseMinor: number;
  materialMinor: number;
  finishMinor: number;
  accessoriesMinor: number;
  rulesMinor: number;
  unitTotalMinor: number;
}

export interface EstimateItem {
  productId: string;
  productName: string;
  quantity: number;
  widthMm: number;
  heightMm: number;
  depthMm: number;
  material: SelectedOption | null;
  finish: SelectedOption | null;
  accessories: SelectedOption[];
  breakdown: PricingBreakdown;
  lineTotalMinor: number;
  minProductionDays: number;
  maxProductionDays: number;
}

export interface QuoteEstimate {
  currency: string;
  subtotalMinor: number;
  adjustmentsMinor: number;
  totalMinor: number;
  depositMinor: number;
  items: EstimateItem[];
}

export interface QuoteItem extends Omit<EstimateItem, 'minProductionDays' | 'maxProductionDays'> {
  id: string;
  productName: string;
  configuration: Record<string, unknown>;
  basePriceMinor: number;
}

export interface QuoteData {
  id: string;
  code: string;
  status: 'draft' | 'submitted' | 'reviewing' | 'approved' | 'rejected' | 'expired' | 'converted';
  currency: string;
  contactName: string;
  contactEmail: string | null;
  contactPhone: string | null;
  subtotalMinor: number;
  adjustmentsMinor: number;
  totalMinor: number;
  depositMinor: number;
  expiresAt: string;
  version: number;
  createdAt: string;
  updatedAt: string;
  items: QuoteItem[];
}

interface EstimateResponse {
  data: QuoteEstimate;
}

interface QuoteResponse {
  data: QuoteData;
}

export async function estimateQuote(items: EstimateItemInput[]): Promise<QuoteEstimate> {
  const response = await apiRequest<EstimateResponse>('/api/v1/quotes/estimate', {
    method: 'POST',
    body: JSON.stringify({ items }),
  });
  return response.data;
}

export async function createQuote(input: {
  contactName: string;
  contactEmail?: string;
  contactPhone?: string;
  items: EstimateItemInput[];
}): Promise<QuoteData> {
  const response = await apiRequest<QuoteResponse>('/api/v1/quotes', {
    method: 'POST',
    body: JSON.stringify(input),
  });
  return response.data;
}
