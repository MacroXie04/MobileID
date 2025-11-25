import api from './axios';

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function apiRequest(endpoint, options = {}) {
  try {
    const config = {
      url: endpoint,
      method: options.method || 'GET',
      headers: options.headers || {},
      data: options.body, // axios uses 'data' for body
      ...options,
    };

    // Remove body from config as we mapped it to data
    delete config.body;

    const response = await api(config);
    return response.data;
  } catch (error) {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const errorData = error.response.data || {};
      const message =
        errorData.message || errorData.detail || JSON.stringify(errorData) || error.message;

      throw new ApiError(message, error.response.status, errorData);
    } else if (error.request) {
      // The request was made but no response was received
      throw new Error('Network Error: No response received');
    } else {
      // Something happened in setting up the request that triggered an Error
      throw error;
    }
  }
}
