import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

export type EstimateItemInput = components['schemas']['EstimateItemRequest'];
export type SelectedOption = components['schemas']['SelectedOptionData'];
export type PricingBreakdown = components['schemas']['PricingBreakdownData'];
export type EstimateItem = components['schemas']['EstimateItemData'];
export type QuoteEstimate = components['schemas']['QuoteEstimateData'];
export type QuoteItem = components['schemas']['QuoteItemData'];
export type QuoteData = components['schemas']['QuoteData'];
type EstimateResponse = components['schemas']['QuoteEstimateResponse'];
type QuoteResponse = components['schemas']['QuoteResponse'];
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
