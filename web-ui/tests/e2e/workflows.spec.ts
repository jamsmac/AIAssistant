/**
 * Workflow Management E2E Tests
 */

import { test, expect } from '@playwright/test';

test.describe('Workflow Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('token', 'test-token');
    });

    await page.route('**/api/workflows', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'workflow-1',
              name: 'Daily Report',
              description: 'Generate daily performance report',
              enabled: true,
              trigger: { type: 'manual' },
              actions: [{ type: 'send_email', config: { to: 'ops@example.com' } }],
              run_count: 30,
              success_count: 28,
              error_count: 2,
            },
            {
              id: 'workflow-2',
              name: 'Data Sync',
              description: 'Sync data between systems',
              enabled: false,
              trigger: { type: 'webhook' },
              actions: [{ type: 'call_webhook', config: { url: 'https://api.example.com' } }],
              run_count: 15,
              success_count: 15,
              error_count: 0,
            },
          ]),
        });
      }
    });
  });

  test('should display workflow list', async ({ page }) => {
    await page.goto('/workflows');

    await expect(page.getByText('Daily Report')).toBeVisible();
    await expect(page.getByText('Data Sync')).toBeVisible();

    await expect(page.getByRole('status', { name: /enabled/i })).toBeVisible();
    await expect(page.getByRole('status', { name: /disabled/i })).toBeVisible();
  });

  test('should create new workflow via builder modal', async ({ page }) => {
    await page.goto('/workflows');

    await page.getByRole('button', { name: /new workflow/i }).click();

    await page.fill('input[placeholder="My automation"]', 'Builder E2E Workflow');
    await page.fill('textarea[placeholder="Describe what this workflow accomplishes"]', 'Created via E2E test');

    const palette = page.getByText('Node Library').locator('..');
    const addPaletteNode = async (label: string, position: { x: number; y: number }) => {
      const handle = palette.getByRole('button', { name: new RegExp(label, 'i') });
      const box = await palette.boundingBox();
      await handle.hover();
      await page.mouse.down();
      await page.mouse.move((box?.x ?? 0) + position.x, (box?.y ?? 0) + position.y, { steps: 5 });
      await page.mouse.up();
    };

    await addPaletteNode('Trigger', { x: 400, y: 220 });
    await addPaletteNode('Action', { x: 400, y: 360 });

    await page.getByText('Trigger Type').locator('..').getByRole('combobox').selectOption('manual');
    await page.getByText('Action Type').locator('..').getByRole('combobox').selectOption('send_email');

    await page.getByLabel(/email to/i).fill('ops@example.com');
    await page.getByLabel(/subject/i).fill('Builder Test');
    await page.getByLabel(/body/i).fill('Generated from Playwright');

    await page.route('**/api/workflows', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ id: 'new-workflow' }) });
      } else {
        await route.continue();
      }
    });

    await page.getByRole('button', { name: /save workflow/i }).click();
    await expect(page.getByText('Workflow created successfully')).toBeVisible();
  });

  test('should execute workflow manually', async ({ page }) => {
    await page.goto('/workflows');

    await page.route('**/api/workflows/*/execute', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'completed' }) });
    });

    await page.getByText('Daily Report').hover();
    await page.getByRole('button', { name: /execute/i }).first().click();

    await expect(page.getByText(/workflow executed successfully/i)).toBeVisible();
  });

  test('should delete workflow after confirmation', async ({ page }) => {
    await page.goto('/workflows');

    await page.route('**/api/workflows/workflow-2', async route => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 204 });
      } else {
        await route.continue();
      }
    });

    await page.getByText('Data Sync').hover();
    await page.getByRole('button', { name: /delete/i }).click();
    await page.getByRole('button', { name: /confirm/i }).click();

    await expect(page.getByText('Data Sync')).not.toBeVisible();
  });
});