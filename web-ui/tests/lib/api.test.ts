/**
 * API Client Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { APIClient } from '@/lib/api';

describe('APIClient', () => {
  let apiClient: APIClient;
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();

    // Create new API client instance
    apiClient = new APIClient('http://localhost:3000');

    // Mock fetch
    mockFetch = vi.fn();
    global.fetch = mockFetch;

    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
  });

  describe('constructor', () => {
    it('should create instance with default base URL', () => {
      const client = new APIClient();
      expect(client).toBeDefined();
    });

    it('should create instance with custom base URL', () => {
      const client = new APIClient('https://api.example.com');
      expect(client).toBeDefined();
    });
  });

  describe('GET requests', () => {
    it('should make successful GET request', async () => {
      const mockData = { id: 1, name: 'Test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockData,
      });

      const result = await apiClient.get('/api/test');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockData);
    });

    it('should include authorization header when token exists', async () => {
      window.localStorage.getItem = vi.fn().mockReturnValue('test-token');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({}),
      });

      await apiClient.get('/api/protected');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
    });
  });

  describe('POST requests', () => {
    it('should make successful POST request with data', async () => {
      const postData = { email: 'test@example.com', password: 'password123' };
      const mockResponse = { token: 'jwt-token', user: { id: 1 } };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse,
      });

      const result = await apiClient.post('/api/auth/login', postData);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/auth/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Error handling', () => {
    it('should handle 401 unauthorized error', async () => {
      const removeItemSpy = vi.spyOn(window.localStorage, 'removeItem');

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ message: 'Unauthorized' }),
      });

      await expect(apiClient.get('/api/protected')).rejects.toThrow();
      expect(removeItemSpy).toHaveBeenCalledWith('token');
    });

    it('should handle 404 not found error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ message: 'Not found' }),
      });

      await expect(apiClient.get('/api/missing')).rejects.toThrow('Resource not found.');
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

      await expect(apiClient.get('/api/test')).rejects.toThrow(
        'Network error. Please check your connection.'
      );
    });

    it('should handle server errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ message: 'Internal server error' }),
      });

      await expect(apiClient.get('/api/test')).rejects.toThrow(
        'Server error. Please try again later.'
      );
    });

    it('should show toast notification when handler is set', async () => {
      const mockToast = vi.fn();
      apiClient.setToastHandler(mockToast);

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ message: 'Bad request' }),
      });

      await expect(apiClient.get('/api/test')).rejects.toThrow();
      expect(mockToast).toHaveBeenCalledWith(
        'Invalid request. Please check your input.',
        'error'
      );
    });
  });

  describe('PUT requests', () => {
    it('should make successful PUT request', async () => {
      const putData = { name: 'Updated' };
      const mockResponse = { id: 1, name: 'Updated' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse,
      });

      const result = await apiClient.put('/api/items/1', putData);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/items/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('PATCH requests', () => {
    it('should make successful PATCH request', async () => {
      const patchData = { status: 'active' };
      const mockResponse = { id: 1, status: 'active' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse,
      });

      const result = await apiClient.patch('/api/items/1', patchData);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/items/1',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(patchData),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('DELETE requests', () => {
    it('should make successful DELETE request', async () => {
      const mockResponse = { success: true };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse,
      });

      const result = await apiClient.delete('/api/items/1');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/items/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });
});