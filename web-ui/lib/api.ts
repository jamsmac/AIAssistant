/**
 * Centralized API Client with automatic error handling and toast notifications
 */

import { API_URL } from './config';

// Types
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}

// Error messages
const ERROR_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your input.',
  401: 'Authentication required. Please log in.',
  403: 'Access denied. You do not have permission.',
  404: 'Resource not found.',
  409: 'Conflict. This resource already exists.',
  422: 'Validation error. Please check your input.',
  429: 'Too many requests. Please slow down.',
  500: 'Server error. Please try again later.',
  502: 'Service unavailable. Please try again.',
  503: 'Service temporarily unavailable.',
};

/**
 * APIClient class with automatic error handling
 */
export class APIClient {
  private baseUrl: string;
  private showToast?: (message: string, type: 'success' | 'error' | 'warning' | 'info') => void;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Set toast notification function (injected from context)
   */
  setToastHandler(handler: (message: string, type: 'success' | 'error' | 'warning' | 'info') => void) {
    this.showToast = handler;
  }

  /**
   * Get authentication token from localStorage
   */
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  }

  /**
   * Build headers for request
   */
  private buildHeaders(includeAuth: boolean = true): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      const token = this.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  /**
   * Handle API errors
   */
  private handleError(status: number, errorData?: any): never {
    const message = errorData?.detail || errorData?.message || ERROR_MESSAGES[status] || 'An error occurred';

    // Show toast notification if handler is available
    if (this.showToast) {
      this.showToast(message, 'error');
    }

    // Handle 401 - redirect to login
    if (status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      setTimeout(() => {
        window.location.href = '/login';
      }, 1000);
    }

    // Throw error for component to catch
    const error: any = new Error(message);
    error.status = status;
    error.data = errorData;
    throw error;
  }

  /**
   * Make HTTP request
   */
  private async request<T>(
    method: string,
    url: string,
    data?: any,
    options: RequestInit = {}
  ): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${url}`, {
        method,
        headers: this.buildHeaders(options.headers !== null),
        body: data ? JSON.stringify(data) : undefined,
        ...options,
      });

      // Handle non-JSON responses
      const contentType = response.headers.get('content-type');
      let responseData;

      if (contentType && contentType.includes('application/json')) {
        responseData = await response.json();
      } else {
        responseData = await response.text();
      }

      // Handle error responses
      if (!response.ok) {
        this.handleError(response.status, responseData);
      }

      return responseData as T;
    } catch (error: any) {
      // Network errors
      if (error.name === 'TypeError' || error.message === 'Failed to fetch') {
        const message = 'Network error. Please check your connection.';
        if (this.showToast) {
          this.showToast(message, 'error');
        }
        throw new Error(message);
      }

      // Re-throw already handled errors
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T>(url: string, options?: RequestInit): Promise<T> {
    return this.request<T>('GET', url, undefined, options);
  }

  /**
   * POST request
   */
  async post<T>(url: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>('POST', url, data, options);
  }

  /**
   * PUT request
   */
  async put<T>(url: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>('PUT', url, data, options);
  }

  /**
   * PATCH request
   */
  async patch<T>(url: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>('PATCH', url, data, options);
  }

  /**
   * DELETE request
   */
  async delete<T>(url: string, options?: RequestInit): Promise<T> {
    return this.request<T>('DELETE', url, undefined, options);
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export default
export default apiClient;
