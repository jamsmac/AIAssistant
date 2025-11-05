/**
 * Testing utilities for React components
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ToastProvider } from '@/components/ui/Toast';
import { vi } from 'vitest';

// Mock router context
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  refresh: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  prefetch: vi.fn(),
};

// Mock API context
const mockApi = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
};

interface AllProvidersProps {
  children: React.ReactNode;
}

// Wrap components with all necessary providers
export function AllProviders({ children }: AllProvidersProps) {
  return (
    <ToastProvider>
      {children}
    </ToastProvider>
  );
}

// Custom render function that includes providers
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options });

// Re-export everything from Testing Library
export * from '@testing-library/react';
export { customRender as render };
export { mockRouter, mockApi };

// Test data factories
export const createMockUser = (overrides = {}) => ({
  id: '1',
  email: 'test@example.com',
  name: 'Test User',
  role: 'user',
  organization_id: 'org-1',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

export const createMockAgent = (overrides = {}) => ({
  id: 'agent-1',
  organization_id: 'org-1',
  name: 'Test Agent',
  type: 'specialist',
  description: 'A test agent',
  status: 'active',
  capabilities: ['text-generation', 'code-review'],
  config: {
    model: 'gpt-4',
    temperature: 0.7,
  },
  depth_level: 1,
  hierarchy_path: '/root/agent-1',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

export const createMockWorkflow = (overrides = {}) => ({
  id: 'workflow-1',
  name: 'Test Workflow',
  description: 'A test workflow',
  triggers: [{
    type: 'manual',
    config: {},
  }],
  actions: [{
    type: 'api_call',
    config: {
      api_url: 'https://api.example.com/test',
      api_method: 'GET',
    },
  }],
  status: 'active',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  run_count: 0,
  success_count: 0,
  error_count: 0,
  ...overrides,
});

export const createMockDatabase = (overrides = {}) => ({
  id: 'db-1',
  project_id: 'project-1',
  name: 'Test Database',
  type: 'postgresql',
  description: 'A test database',
  tables: [],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

// Mock response helpers
export const createMockApiResponse = <T,>(data: T, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  headers: new Headers({ 'content-type': 'application/json' }),
  json: async () => data,
  text: async () => JSON.stringify(data),
});

export const createMockApiError = (message: string, status = 400) => ({
  ok: false,
  status,
  headers: new Headers({ 'content-type': 'application/json' }),
  json: async () => ({ message, error: message }),
  text: async () => JSON.stringify({ message }),
});

// Wait utility for async operations
export const waitFor = (ms: number) =>
  new Promise(resolve => setTimeout(resolve, ms));

// Mock localStorage helper
export const mockLocalStorage = () => {
  const store: Record<string, string> = {};

  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
    store,
  };
};