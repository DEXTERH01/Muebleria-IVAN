import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

type AssistantChatRequest = components['schemas']['AssistantChatRequest'];
type AssistantChatResponse = components['schemas']['AssistantChatResponse'];
export type AssistantChatData = components['schemas']['AssistantChatData'];

export async function chatWithAssistant(message: string): Promise<AssistantChatData> {
  const body: AssistantChatRequest = { message };
  const response = await apiRequest<AssistantChatResponse>('/api/v1/assistant/chat', {
    method: 'POST',
    body: JSON.stringify(body),
  });
  return response.data;
}
