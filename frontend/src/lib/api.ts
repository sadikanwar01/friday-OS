export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public data: Record<string, unknown> | string | undefined | null) {
    super((data as Record<string, string>)?.message || (data as Record<string, string>)?.detail || "API Error");
    this.name = "ApiError";
  }
}

async function fetchWrapper<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }
    
    // Log the failed request for the Debug Panel
    if (process.env.NODE_ENV === 'development') {
      import('@/store/useDebugStore').then(({ useDebugStore }) => {
        useDebugStore.getState().addLog({
          endpoint,
          requestBody: options.body as string | undefined,
          response: typeof errorData === 'string' ? errorData : JSON.stringify(errorData),
          status: response.status,
          errorMessage: (errorData as Record<string, unknown>)?.message as string || (errorData as Record<string, unknown>)?.detail as string || "API Error"
        });
      });
    }

    throw new ApiError(response.status, errorData);
  }

  return response.json();
}

export const api = {
  get: <T>(endpoint: string, options?: RequestInit) => 
    fetchWrapper<T>(endpoint, { ...options, method: "GET" }),
    
  post: <T>(endpoint: string, data?: Record<string, unknown> | unknown, options?: RequestInit) => 
    fetchWrapper<T>(endpoint, { 
      ...options, 
      method: "POST",
      body: data ? JSON.stringify(data) : undefined
    }),
};
