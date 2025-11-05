/**
 * MSW Server Setup for Node.js Environment (Tests)
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';
import { afterEach, afterAll } from 'vitest';

// Create the MSW server instance
export const server = setupServer(...handlers);

// Enable request interception
server.listen({
  onUnhandledRequest: 'warn',
});

// Reset handlers after each test
afterEach(() => {
  server.resetHandlers();
});

// Clean up after all tests
afterAll(() => {
  server.close();
});