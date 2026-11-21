const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000')
  .replace(/\/$/, '');
let accessTokenProvider: (() => string | null) | null = null;

export function setAccessTokenProvider(provider: (() => string | null) | null): void {
  accessTokenProvider = provider;
}

interface ApiErrorBody {
  error?: {
    message?: string;
  };
  detail?: string | Array<{ msg?: string }>;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function errorMessage(body: ApiErrorBody, fallback: string): string {
  if (body.error?.message) return body.error.message;
  if (typeof body.detail === 'string') return body.detail;
  if (Array.isArray(body.detail)) {
    const messages = body.detail.flatMap((item) => item.msg ? [item.msg] : []);
    if (messages.length) return messages.join(' ');
  }
  return fallback;
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const accessToken = accessTokenProvider?.();
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let body: ApiErrorBody = {};
    try {
      body = await response.json() as ApiErrorBody;
    } catch {
      // The status remains useful when a proxy returns a non-JSON response.
    }
    throw new ApiError(
      errorMessage(body, 'No pudimos completar la solicitud. Inténtalo nuevamente.'),
      response.status,
    );
  }

  return response.json() as Promise<T>;
}
