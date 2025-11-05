/**
 * API Response and Error Types
 */

export interface ApiError extends Error {
  status: number;
  code?: string;
  details?: Record<string, unknown>;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
  organization_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ErrorResponse {
  error: string;
  message?: string;
  details?: Record<string, unknown>;
  code?: string;
}

export type RequestData = Record<string, unknown> | FormData | string;

export interface ApiClientOptions {
  baseURL?: string;
  headers?: HeadersInit;
  interceptors?: {
    request?: (config: RequestInit) => RequestInit;
    response?: (response: Response) => Response;
  };
}