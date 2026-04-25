import api from './axios';
import { ensureCsrfToken } from './csrf';
import type { AxiosRequestConfig } from 'axios';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export interface ApiRequestOptions extends Omit<AxiosRequestConfig, 'url' | 'data'> {
  body?: unknown;
}

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  try {
    const method = (options.method || 'GET').toUpperCase();
    const needsCsrf = !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method);
    if (needsCsrf) {
      await ensureCsrfToken();
    }

    const {
      headers: optHeaders,
      body,
      method: _m,
      withCredentials: wc,
      timeout,
      params,
      responseType,
      ..._rest
    } = options;

    const config = {
      url: endpoint,
      method,
      headers: optHeaders || {},
      data: body, // axios uses 'data' for body
      withCredentials: typeof wc === 'boolean' ? wc : true,
      ...(timeout !== undefined && { timeout }),
      ...(params !== undefined && { params }),
      ...(responseType !== undefined && { responseType }),
    };

    const response = await api(config);
    return response.data as T;
  } catch (error) {
    const err = error as {
      response?: { data?: { message?: string; detail?: string }; status: number };
      request?: unknown;
      message?: string;
    };

    if (err.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const errorData = err.response.data || {};
      const message =
        errorData.message || errorData.detail || JSON.stringify(errorData) || err.message || '';

      throw new ApiError(message, err.response.status, errorData);
    } else if (err.request) {
      // The request was made but no response was received
      throw new Error('Network Error: No response received');
    } else {
      // Something happened in setting up the request that triggered an Error
      throw error;
    }
  }
}
