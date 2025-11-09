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
    await page.context().clearCookies();
    await page.goto('/');
  });

  test('should display login page for unauthenticated users', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*login/);
    await expect(page.locator('h1')).toContainText('AI Assistant');
  });

  test('should complete full authentication flow', async ({ page, context }) => {
    await page.goto('/login');

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);

    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Set-Cookie': 'auth_token=mock-jwt-token; HttpOnly; Secure; SameSite=Lax',
        },
        body: JSON.stringify({
          user: {
            id: '1',
            email: TEST_USER.email,
            name: TEST_USER.name,
          },
        }),
      });
    });

    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/');

    const cookies = await context.cookies();
    const authCookie = cookies.find(cookie => cookie.name === 'auth_token');
    expect(authCookie?.value).toBe('mock-jwt-token');
  });

  test('should handle login errors gracefully', async ({ page }) => {
    await page.goto('/login');

    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Invalid credentials',
        }),
      });
    });

    await page.fill('input[type="email"]', 'wrong@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Invalid credentials')).toBeVisible();
    await expect(page).toHaveURL(/.*login/);
  });

  test('should validate email format', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[type="email"]', 'invalid-email');
    await page.fill('input[type="password"]', 'password123');

    const emailInput = page.locator('input[type="email"]');
    const isValid = await emailInput.evaluate((el: HTMLInputElement) => el.validity.valid);
    expect(isValid).toBe(false);
  });

  test('should navigate between login and register', async ({ page }) => {
    await page.goto('/login');

    await page.click('text=Create Account');
    await expect(page).toHaveURL(/.*register/);

    await page.click('text=Sign In');
    await expect(page).toHaveURL(/.*login/);
  });

  test('should handle registration flow', async ({ page, context }) => {
    await page.goto('/register');

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.fill('input[placeholder*="Confirm"]', TEST_USER.password);

    await page.route('**/api/auth/register', async (route) => {
      await route.fulfill({
        status: 201,
        headers: {
          'Content-Type': 'application/json',
          'Set-Cookie': 'auth_token=new-user-token; HttpOnly; Secure; SameSite=Lax',
        },
        body: JSON.stringify({
          user: {
            id: '2',
            email: TEST_USER.email,
            name: 'New User',
          },
        }),
      });
    });

    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/');

    const cookies = await context.cookies();
    const authCookie = cookies.find(cookie => cookie.name === 'auth_token');
    expect(authCookie?.value).toBe('new-user-token');
  });

  test('should logout successfully', async ({ page, context }) => {
    await context.addCookies([
      {
        name: 'auth_token',
        value: 'test-token',
        url: 'http://localhost:3000',
        path: '/',
        httpOnly: true,
      },
    ]);

    await page.goto('/');

    await page.route('**/api/auth/logout', async (route) => {
      await route.fulfill({
        status: 204,
        headers: {
          'Set-Cookie': 'auth_token=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax',
        },
      });
    });

    await page.click('button[aria-label="Logout"]');

    await expect(page).toHaveURL(/.*login/);

    const cookies = await context.cookies();
    const authCookie = cookies.find(cookie => cookie.name === 'auth_token');
    expect(authCookie).toBeUndefined();
  });

  test('should handle expired tokens by clearing cookie', async ({ page, context }) => {
    await context.addCookies([
      {
        name: 'auth_token',
        value: 'expired-token',
        url: 'http://localhost:3000',
        path: '/',
        httpOnly: true,
      },
    ]);

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

    await expect(page).toHaveURL(/.*login/);

    const cookies = await context.cookies();
    const authCookie = cookies.find(cookie => cookie.name === 'auth_token');
    expect(authCookie).toBeUndefined();
  });
});

test.describe('Password Requirements', () => {
  test('should show password strength indicator', async ({ page }) => {
    await page.goto('/register');

    const passwordInput = page.locator('input[type="password"]').first();

    await passwordInput.fill('weak');
    await expect(page.locator('text=At least 8 characters')).toBeVisible();

    await passwordInput.fill('Medium123');
    await expect(page.locator('text=At least 8 characters').locator('..')).toHaveClass(/met/);

    await passwordInput.fill('Strong123!@#');
    await expect(page.locator('text=One uppercase letter').locator('..')).toHaveClass(/met/);
    await expect(page.locator('text=One number').locator('..')).toHaveClass(/met/);
  });
});

