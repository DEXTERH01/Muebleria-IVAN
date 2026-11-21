import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

export type EstimateItemInput = components['schemas']['EstimateItemRequest'];
export type SelectedOption = components['schemas']['SelectedOptionData'];
export type PricingBreakdown = components['schemas']['PricingBreakdownData'];
export type EstimateItem = components['schemas']['EstimateItemData'];
export type QuoteEstimate = components['schemas']['QuoteEstimateData'];
export type QuoteItem = components['schemas']['QuoteItemData'];
export type QuoteData = components['schemas']['QuoteData'];
export type QuoteStatus = QuoteData['status'];
export type QuoteListData = components['schemas']['QuoteListData'];
export type QuoteConvertInput = components['schemas']['QuoteConvertRequest'];
type EstimateResponse = components['schemas']['QuoteEstimateResponse'];
type QuoteResponse = components['schemas']['QuoteResponse'];
type QuoteListResponse = components['schemas']['QuoteListResponse'];
type OrderResponse = components['schemas']['OrderResponse'];
type QuoteCreateRequest = components['schemas']['QuoteCreateRequest'];

export async function estimateQuote(items: EstimateItemInput[]): Promise<QuoteEstimate> {
  const response = await apiRequest<EstimateResponse>('/api/v1/quotes/estimate', {
    method: 'POST',
    body: JSON.stringify({ items }),
  });
  return response.data;
}

export async function createQuote(
  input: Omit<QuoteCreateRequest, 'items'> & { items: EstimateItemInput[] },
): Promise<QuoteData> {
  const response = await apiRequest<QuoteResponse>('/api/v1/quotes', {
    method: 'POST',
    body: JSON.stringify(input),
  });
  return response.data;
}

export async function listQuotes(): Promise<QuoteListData> {
  const response = await apiRequest<QuoteListResponse>('/api/v1/quotes?page=1&pageSize=100');
  return response.data;
}

export async function updateQuoteStatus(
  quoteId: string,
  status: Extract<QuoteStatus, 'reviewing' | 'approved' | 'rejected' | 'expired'>,
  expectedVersion: number,
): Promise<QuoteData> {
  const response = await apiRequest<QuoteResponse>(
    `/api/v1/quotes/${encodeURIComponent(quoteId)}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ status, expectedVersion }),
    },
  );
  return response.data;
}

export async function convertQuote(
  quoteId: string,
  input: QuoteConvertInput,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<components['schemas']['OrderOut']> {
  const response = await apiRequest<OrderResponse>(
    `/api/v1/quotes/${encodeURIComponent(quoteId)}/convert`,
    {
      method: 'POST',
      headers: { 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify(input),
    },
  );
  return response.data;
}
