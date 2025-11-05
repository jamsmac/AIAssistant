/**
 * Workflow Management E2E Tests
 */

import { test, expect } from '@playwright/test';

test.describe('Workflow Management', () => {
  test.beforeEach(async ({ page }) => {
    // Setup authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('token', 'test-token');
    });

    // Mock API responses
    await page.route('**/api/workflows', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'workflow-1',
              name: 'Daily Report',
              description: 'Generate daily performance report',
              status: 'active',
              triggers: [{ type: 'schedule', config: { schedule: '0 9 * * *' } }],
              actions: [{ type: 'api_call', config: {} }],
              run_count: 30,
              success_count: 28,
              error_count: 2,
            },
            {
              id: 'workflow-2',
              name: 'Data Sync',
              description: 'Sync data between systems',
              status: 'inactive',
              triggers: [{ type: 'webhook', config: {} }],
              actions: [{ type: 'database_query', config: {} }],
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

    // Check workflows are displayed
    await expect(page.locator('text=Daily Report')).toBeVisible();
    await expect(page.locator('text=Data Sync')).toBeVisible();

    // Check status badges
    await expect(page.locator('text=active').first()).toBeVisible();
    await expect(page.locator('text=inactive').first()).toBeVisible();
  });

  test('should create new workflow', async ({ page }) => {
    await page.goto('/workflows');

    // Click create button
    await page.click('button:has-text("New Workflow")');

    // Fill workflow form
    await page.fill('input[placeholder*="Workflow name"]', 'Test Workflow');
    await page.fill('textarea[placeholder*="Description"]', 'E2E test workflow');

    // Select trigger type
    await page.click('text=Select trigger');
    await page.click('text=Manual');

    // Add action
    await page.click('button:has-text("Add Action")');
    await page.click('text=Send Email');

    // Fill action details
    await page.fill('input[placeholder*="Email to"]', 'test@example.com');
    await page.fill('input[placeholder*="Subject"]', 'Test Email');

    // Mock create response
    await page.route('**/api/workflows', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-workflow',
            name: 'Test Workflow',
            status: 'active',
          }),
        });
      }
    });

    // Save workflow
    await page.click('button:has-text("Create Workflow")');

    // Should show success message
    await expect(page.locator('text=Workflow created successfully')).toBeVisible();
  });

  test('should execute workflow manually', async ({ page }) => {
    await page.goto('/workflows');

    // Mock execution response
    await page.route('**/api/workflows/*/execute', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'run-1',
          status: 'running',
          workflow_id: 'workflow-1',
        }),
      });
    });

    // Find and execute workflow
    const workflowCard = page.locator('text=Daily Report').locator('..');
    await workflowCard.locator('button[aria-label="Execute"]').click();

    // Should show execution started
    await expect(page.locator('text=Workflow execution started')).toBeVisible();
  });

  test('should edit workflow configuration', async ({ page }) => {
    await page.goto('/workflows');

    // Click edit on first workflow
    const workflowCard = page.locator('text=Daily Report').locator('..');
    await workflowCard.locator('button[aria-label="Edit"]').click();

    // Should open edit modal
    await expect(page.locator('text=Edit Workflow')).toBeVisible();

    // Update name
    await page.fill('input[value="Daily Report"]', 'Updated Daily Report');

    // Mock update response
    await page.route('**/api/workflows/*', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'workflow-1',
            name: 'Updated Daily Report',
          }),
        });
      }
    });

    // Save changes
    await page.click('button:has-text("Save Changes")');

    // Should show success
    await expect(page.locator('text=Workflow updated successfully')).toBeVisible();
  });

  test('should delete workflow with confirmation', async ({ page }) => {
    await page.goto('/workflows');

    // Mock delete response
    await page.route('**/api/workflows/*', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
        });
      }
    });

    // Click delete on workflow
    const workflowCard = page.locator('text=Data Sync').locator('..');
    await workflowCard.locator('button[aria-label="Delete"]').click();

    // Confirm deletion
    await page.click('button:has-text("Confirm Delete")');

    // Workflow should be removed
    await expect(page.locator('text=Data Sync')).not.toBeVisible();
  });

  test('should display workflow execution history', async ({ page }) => {
    // Mock execution history
    await page.route('**/api/workflows/*/executions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'exec-1',
            status: 'completed',
            started_at: new Date().toISOString(),
            completed_at: new Date().toISOString(),
            duration: 1234,
          },
          {
            id: 'exec-2',
            status: 'failed',
            started_at: new Date().toISOString(),
            error: 'Connection timeout',
          },
        ]),
      });
    });

    await page.goto('/workflows');

    // View execution history
    const workflowCard = page.locator('text=Daily Report').locator('..');
    await workflowCard.locator('button:has-text("View History")').click();

    // Should show executions
    await expect(page.locator('text=completed')).toBeVisible();
    await expect(page.locator('text=failed')).toBeVisible();
    await expect(page.locator('text=Connection timeout')).toBeVisible();
  });

  test('should filter workflows by status', async ({ page }) => {
    await page.goto('/workflows');

    // Apply active filter
    await page.click('button:has-text("Filter")');
    await page.click('text=Active only');

    // Only active workflows should be visible
    await expect(page.locator('text=Daily Report')).toBeVisible();
    await expect(page.locator('text=Data Sync')).not.toBeVisible();

    // Clear filter
    await page.click('button:has-text("Clear filters")');

    // All workflows should be visible again
    await expect(page.locator('text=Daily Report')).toBeVisible();
    await expect(page.locator('text=Data Sync')).toBeVisible();
  });

  test('should search workflows', async ({ page }) => {
    await page.goto('/workflows');

    // Search for specific workflow
    await page.fill('input[placeholder*="Search"]', 'Daily');

    // Only matching workflow should be visible
    await expect(page.locator('text=Daily Report')).toBeVisible();
    await expect(page.locator('text=Data Sync')).not.toBeVisible();

    // Clear search
    await page.fill('input[placeholder*="Search"]', '');

    // All workflows visible again
    await expect(page.locator('text=Data Sync')).toBeVisible();
  });
});

test.describe('Workflow Builder', () => {
  test('should build complex workflow with multiple actions', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('token', 'test-token');
    });

    await page.goto('/workflows/new');

    // Add workflow details
    await page.fill('input[name="name"]', 'Complex Workflow');
    await page.fill('textarea[name="description"]', 'Multi-step workflow');

    // Add multiple triggers
    await page.click('button:has-text("Add Trigger")');
    await page.selectOption('select[name="trigger-type"]', 'schedule');
    await page.fill('input[name="cron"]', '0 */6 * * *');

    // Add multiple actions
    // Action 1: API Call
    await page.click('button:has-text("Add Action")');
    await page.selectOption('select[name="action-type-0"]', 'api_call');
    await page.fill('input[name="api-url-0"]', 'https://api.example.com/data');

    // Action 2: Process Data
    await page.click('button:has-text("Add Action")');
    await page.selectOption('select[name="action-type-1"]', 'ai_task');
    await page.fill('textarea[name="ai-prompt-1"]', 'Process the data');

    // Action 3: Send Notification
    await page.click('button:has-text("Add Action")');
    await page.selectOption('select[name="action-type-2"]', 'notification');
    await page.fill('input[name="notification-channel-2"]', '#alerts');

    // Test workflow
    await page.click('button:has-text("Test Workflow")');

    // Mock test response
    await page.route('**/api/workflows/test', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          results: [
            { action: 0, success: true },
            { action: 1, success: true },
            { action: 2, success: true },
          ],
        }),
      });
    });

    // Should show test results
    await expect(page.locator('text=All actions passed')).toBeVisible();

    // Save workflow
    await page.click('button:has-text("Save Workflow")');
  });
});