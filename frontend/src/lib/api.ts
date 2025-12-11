// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5050';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:5050';

export { API_BASE_URL, WS_URL };

// API client helper
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}
