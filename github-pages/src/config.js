// Application configuration

// Base URLs for different environments
export const baseURL = 'https://127.0.0.1:8000'; // Backend API server

// API configuration
export const apiConfig = {
  baseURL: baseURL,  // Use the same base URL
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
};

// HTTPS-specific configuration
export const httpsConfig = {
  // For development with self-signed certificates
  rejectUnauthorized: false, // Allow self-signed certificates in development
  // Additional SSL/TLS options if needed
};

// Other configuration options
export const config = {
  baseURL,
  apiConfig,
  httpsConfig,
  // Add more configuration options here
};

export default config;