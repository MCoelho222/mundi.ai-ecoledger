// Copyright Bunting Labs, Inc. 2025

/**
 * Configuration utilities for the frontend application
 */

/**
 * Get the base API URL from environment variables
 * Falls back to window.location.origin if not set
 */
export const getApiBaseUrl = (): string => {
  return import.meta.env.VITE_WEBSITE_DOMAIN || window.location.origin;
};

/**
 * Build API URL with proper base URL handling
 * @param endpoint - The API endpoint (should start with /)
 * @param useLocalhost - Whether to use localhost base URL for development
 */
export const buildApiUrl = (
  endpoint: string,
  useLocalhost: boolean = false
): string => {
  if (useLocalhost && window.location.hostname === "localhost") {
    return `${getApiBaseUrl()}${endpoint}`;
  }
  return endpoint;
};

/**
 * Environment configuration
 */
export const config = {
  apiBaseUrl: getApiBaseUrl(),
  emailVerification: import.meta.env.VITE_EMAIL_VERIFICATION || "enabled",
  authMode: import.meta.env.VITE_AUTH_MODE || "enabled",
  posthogApiKey: import.meta.env.VITE_POSTHOG_API_KEY || "",
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const;
