/**
 * Authentication E2E Tests
 */

import { test, expect, Page } from '@playwright/test';

const TEST_USER = {
  email: 'test@example.com',
  password: 'Test123!@#',
  name: 'Test User',
};

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page for unauthenticated users', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*login/);
    await expect(page.locator('h1')).toContainText('AI Assistant');
  });

  test('should complete full authentication flow', async ({ page }) => {
    // Navigate to login
    await page.goto('/login');

    // Fill login form
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);

    // Mock successful login response
    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          token: 'mock-jwt-token',
          user: {
            id: '1',
            email: TEST_USER.email,
            name: TEST_USER.name,
          },
        }),
      });
    });

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/');

    // Token should be stored
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBe('mock-jwt-token');
  });

  test('should handle login errors gracefully', async ({ page }) => {
    await page.goto('/login');

    // Mock error response
    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Invalid credentials',
        }),
      });
    });

    await page.fill('input[type="email"]', 'wrong@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Error message should be displayed
    await expect(page.locator('text=Invalid credentials')).toBeVisible();

    // Should stay on login page
    await expect(page).toHaveURL(/.*login/);
  });

  test('should validate email format', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[type="email"]', 'invalid-email');
    await page.fill('input[type="password"]', 'password123');

    // Check HTML5 validation
    const emailInput = page.locator('input[type="email"]');
    const isValid = await emailInput.evaluate((el: HTMLInputElement) => el.validity.valid);
    expect(isValid).toBe(false);
  });

  test('should navigate between login and register', async ({ page }) => {
    await page.goto('/login');

    // Click on Create Account
    await page.click('text=Create Account');
    await expect(page).toHaveURL(/.*register/);

    // Navigate back to login
    await page.click('text=Sign In');
    await expect(page).toHaveURL(/.*login/);
  });

  test('should handle registration flow', async ({ page }) => {
    await page.goto('/register');

    // Fill registration form
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.fill('input[placeholder*="Confirm"]', TEST_USER.password);

    // Mock successful registration
    await page.route('**/api/auth/register', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          token: 'new-user-token',
          user: {
            id: '2',
            email: TEST_USER.email,
            name: 'New User',
          },
        }),
      });
    });

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/');
  });

  test('should logout successfully', async ({ page }) => {
    // Setup authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('token', 'test-token');
    });

    await page.goto('/');

    // Mock dashboard API response
    await page.route('**/api/dashboard/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_requests: 100,
          active_agents: 5,
          workflows_run: 20,
          success_rate: 95,
        }),
      });
    });

    // Find and click logout button
    await page.click('button[aria-label="Logout"]');

    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);

    // Token should be removed
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeNull();
  });

  test('should persist authentication across page reloads', async ({ page }) => {
    // Set token
    await page.addInitScript(() => {
      localStorage.setItem('token', 'persistent-token');
    });

    await page.goto('/dashboard');

    // Should not redirect to login
    await expect(page).not.toHaveURL(/.*login/);

    // Reload page
    await page.reload();

    // Token should still exist
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBe('persistent-token');
  });
});

test.describe('Password Requirements', () => {
  test('should show password strength indicator', async ({ page }) => {
    await page.goto('/register');

    const passwordInput = page.locator('input[type="password"]').first();

    // Weak password
    await passwordInput.fill('weak');
    await expect(page.locator('text=At least 8 characters')).toBeVisible();

    // Medium password
    await passwordInput.fill('Medium123');
    await expect(page.locator('text=At least 8 characters').locator('..')).toHaveClass(/met/);

    // Strong password
    await passwordInput.fill('Strong123!@#');
    await expect(page.locator('text=One uppercase letter').locator('..')).toHaveClass(/met/);
    await expect(page.locator('text=One number').locator('..')).toHaveClass(/met/);
  });
});

test.describe('Security', () => {
  test('should not expose sensitive data in network requests', async ({ page }) => {
    const requests: string[] = [];

    page.on('request', (request) => {
      requests.push(request.url());
    });

    await page.goto('/login');
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);

    // Password should never appear in URL
    requests.forEach((url) => {
      expect(url).not.toContain(TEST_USER.password);
    });
  });

  test('should handle expired tokens', async ({ page }) => {
    // Set expired token
    await page.addInitScript(() => {
      localStorage.setItem('token', 'expired-token');
    });

    // Mock 401 response for protected route
    await page.route('**/api/dashboard/stats', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Token expired',
        }),
      });
    });

    await page.goto('/dashboard');

    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);

    // Token should be removed
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeNull();
  });
});