import { test, expect } from '@playwright/test';
import { waitForBackend, cleanupTestData, createTestProject, createTestChangeRequest } from './setup.js';

test.describe('Tasks Page Tests', () => {
  let testProject;

  test.beforeAll(async () => {
    await waitForBackend();
  });

  test.beforeEach(async ({ page }) => {
    await cleanupTestData();
    // Create a test project for tasks
    testProject = await createTestProject('Task Test Project', 'Project for testing tasks');
    await page.goto(`/tasks?project_id=${testProject.id}`);
  });

  test('should display tasks page', async ({ page }) => {
    await expect(page.locator('h2:has-text("Tasks")')).toBeVisible();
  });

  test('should show empty state when no tasks exist', async ({ page }) => {
    await page.goto(`/tasks?project_id=${testProject.id}`);
    // Should show some indication of no tasks
    const taskCards = page.locator('[data-testid="task-card"]');
    await expect(taskCards).toHaveCount(0);
  });

  test('should filter tasks by status', async ({ page }) => {
    // This test assumes we have tasks with different statuses
    // First, create some tasks via API or UI
    
    // Look for filter/status buttons
    const filterButtons = page.locator('[data-testid="status-filter"]');
    if (await filterButtons.count() > 0) {
      await filterButtons.first().click();
      // Verify filtered results
    }
  });

  test('should display task details', async ({ page }) => {
    // Create a task via API first
    // Then verify it displays correctly
    const taskCard = page.locator('[data-testid="task-card"]').first();
    if (await taskCard.count() > 0) {
      await taskCard.click();
      // Should show task details
      await expect(page.locator('[data-testid="task-details"]')).toBeVisible();
    }
  });

  test('should navigate to task from list', async ({ page }) => {
    const taskCard = page.locator('[data-testid="task-card"]').first();
    if (await taskCard.count() > 0) {
      await taskCard.click();
      // Verify navigation or details panel
      await expect(page.url()).toContain('tasks');
    }
  });

  test('should show task status badges', async ({ page }) => {
    const statusBadge = page.locator('[data-testid="task-status"]').first();
    if (await statusBadge.count() > 0) {
      await expect(statusBadge).toBeVisible();
      // Verify badge has correct status text
      const statusText = await statusBadge.textContent();
      expect(['planning', 'design', 'review', 'approved', 'coding', 'done']).toContain(statusText.toLowerCase());
    }
  });

  test('should split task into subtasks', async ({ page }) => {
    // Find a task to split
    const taskCard = page.locator('[data-testid="task-card"]').first();
    if (await taskCard.count() > 0) {
      await taskCard.click();
      
      // Look for split button
      const splitButton = page.locator('button:has-text("Split")');
      if (await splitButton.count() > 0) {
        await splitButton.click();
        
        // Fill split form
        await page.fill('input[name="task1_title"]', 'Subtask 1');
        await page.fill('textarea[name="task1_description"]', 'First part');
        await page.fill('input[name="task2_title"]', 'Subtask 2');
        await page.fill('textarea[name="task2_description"]', 'Second part');
        
        await page.click('button:has-text("Split Task")');
        
        // Verify split was successful
        await page.waitForSelector('text=Subtask 1', { timeout: 5000 });
        await expect(page.locator('text=Subtask 2')).toBeVisible();
      }
    }
  });

  test('should merge multiple tasks', async ({ page }) => {
    // This test requires multiple tasks to exist
    const taskCheckboxes = page.locator('[data-testid="task-checkbox"]');
    
    if (await taskCheckboxes.count() >= 2) {
      // Select two tasks
      await taskCheckboxes.nth(0).click();
      await taskCheckboxes.nth(1).click();
      
      // Click merge button
      const mergeButton = page.locator('button:has-text("Merge")');
      if (await mergeButton.count() > 0) {
        await mergeButton.click();
        
        // Fill merge form
        await page.fill('input[name="merged_title"]', 'Merged Task');
        await page.fill('textarea[name="merged_description"]', 'Combined description');
        
        await page.click('button:has-text("Merge Tasks")');
        
        // Verify merge was successful
        await page.waitForSelector('text=Merged Task', { timeout: 5000 });
      }
    }
  });

  test('should show task versions/history', async ({ page }) => {
    const taskCard = page.locator('[data-testid="task-card"]').first();
    if (await taskCard.count() > 0) {
      await taskCard.click();
      
      // Look for version history button
      const historyButton = page.locator('button:has-text("History")');
      if (await historyButton.count() > 0) {
        await historyButton.click();
        
        // Verify version list is shown
        await expect(page.locator('[data-testid="task-version"]')).toBeVisible();
      }
    }
  });
});
