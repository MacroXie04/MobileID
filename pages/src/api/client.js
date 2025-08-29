import { baseURL } from '@/config';

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function apiRequest(endpoint, options = {}) {
  const config = {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  if (config.body && typeof config.body !== 'string') {
    config.body = JSON.stringify(config.body);
  }

  const response = await fetch(`${baseURL}${endpoint}`, config);

  if (!response.ok) {
    let errorData = { message: `Request failed: ${response.statusText}` };
    try {
      errorData = await response.json();
    } catch (e) { /* ignore */ }
    throw new ApiError(errorData.message || errorData.detail || JSON.stringify(errorData), response.status, errorData);
  }

  return response.status === 204 || response.headers.get('Content-Length') === '0' ? null : response.json();
}