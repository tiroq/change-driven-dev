import { test, expect } from '@playwright/test';
import { waitForBackend, cleanupTestData, createTestProject, createTestChangeRequest } from './setup.js';

test.describe('Full Workflow E2E Tests', () => {
  test.beforeAll(async () => {
    // Ensure backend is ready
    await waitForBackend();
  });

  test.beforeEach(async () => {
    // Clean up before each test to ensure clean state
    await cleanupTestData();
  });

  test('Complete workflow: Create Project → Add CR → Generate Tasks → Process Tasks', async ({ page }) => {
    // Step 1: Navigate to Projects page
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Change-Driven Development');

    // Step 2: Create a new project
    await page.click('text=Projects');
    await page.waitForSelector('text=Create New Project', { timeout: 5000 });
    
    await page.click('text=Create New Project');
    await page.fill('input[name="name"]', 'E2E Test Project');
    await page.fill('textarea[name="description"]', 'This is an end-to-end test project');
    await page.click('button:has-text("Create")');
    
    // Wait for project to be created and visible
    await page.waitForSelector('text=E2E Test Project', { timeout: 5000 });
    await expect(page.locator('text=E2E Test Project')).toBeVisible();

    // Step 3: Select the project
    await page.click('text=E2E Test Project');
    await expect(page.locator('text=Selected Project: E2E Test Project')).toBeVisible();

    // Step 4: Navigate to Planner and create a change request
    await page.click('text=Planner');
    await page.waitForSelector('text=Change Requests', { timeout: 5000 });
    
    await page.click('text=Create Change Request');
    await page.fill('input[name="title"]', 'Add user authentication');
    await page.fill('textarea[name="description"]', 'Implement JWT-based authentication with login and registration');
    await page.click('button:has-text("Create")');
    
    // Wait for CR to appear
    await page.waitForSelector('text=Add user authentication', { timeout: 5000 });
    await expect(page.locator('text=Add user authentication')).toBeVisible();

    // Step 5: Generate tasks from the change request
    await page.click('text=Add user authentication');
    await page.click('button:has-text("Generate Tasks")');
    
    // Wait for tasks to be generated
    await page.waitForSelector('text=Tasks generated', { timeout: 10000 });

    // Step 6: Navigate to Tasks page to verify tasks were created
    await page.click('text=Tasks');
    await page.waitForSelector('text=Tasks for E2E Test Project', { timeout: 5000 });
    
    // Should have at least one task
    const taskCards = page.locator('[data-testid="task-card"]');
    await expect(taskCards.first()).toBeVisible();

    // Step 7: Navigate to Architect page and process a task
    await page.click('text=Architect');
    await page.waitForSelector('text=Architect', { timeout: 5000 });
    
    // Select a task in planning status
    const planningTask = page.locator('[data-status="planning"]').first();
    if (await planningTask.count() > 0) {
      await planningTask.click();
      await page.click('button:has-text("Design")');
      await page.waitForSelector('text=Design complete', { timeout: 10000 });
    }

    // Step 8: Navigate to Review/Approval page
    await page.click('text=Review/Approval');
    await page.waitForSelector('text=Review', { timeout: 5000 });
    
    // Should see tasks ready for review
    const reviewTasks = page.locator('[data-status="review"]');
    if (await reviewTasks.count() > 0) {
      await reviewTasks.first().click();
      await page.click('button:has-text("Approve")');
      await page.waitForSelector('text=Approved', { timeout: 5000 });
    }

    // Step 9: Navigate to Coder page
    await page.click('text=Coder');
    await page.waitForSelector('text=Coder', { timeout: 5000 });
    
    // Should see approved tasks ready for coding
    const codingTasks = page.locator('[data-status="approved"]');
    if (await codingTasks.count() > 0) {
      await codingTasks.first().click();
      await page.click('button:has-text("Implement")');
      await page.waitForSelector('text=Implementation complete', { timeout: 10000 });
    }

    // Verify the workflow completed successfully
    await page.click('text=Tasks');
    const completedTasks = page.locator('[data-status="done"]');
    await expect(completedTasks.first()).toBeVisible();
  });

  test('Create and manage multiple projects', async ({ page }) => {
    await page.goto('/');

    // Create first project
    await page.click('text=Create New Project');
    await page.fill('input[name="name"]', 'Project Alpha');
    await page.fill('textarea[name="description"]', 'First test project');
    await page.click('button:has-text("Create")');
    await page.waitForSelector('text=Project Alpha', { timeout: 5000 });

    // Create second project
    await page.click('text=Create New Project');
    await page.fill('input[name="name"]', 'Project Beta');
    await page.fill('textarea[name="description"]', 'Second test project');
    await page.click('button:has-text("Create")');
    await page.waitForSelector('text=Project Beta', { timeout: 5000 });

    // Verify both projects are visible
    await expect(page.locator('text=Project Alpha')).toBeVisible();
    await expect(page.locator('text=Project Beta')).toBeVisible();

    // Switch between projects
    await page.click('text=Project Alpha');
    await expect(page.locator('text=Selected Project: Project Alpha')).toBeVisible();
    
    await page.click('text=Projects');
    await page.click('text=Project Beta');
    await expect(page.locator('text=Selected Project: Project Beta')).toBeVisible();
  });

  test('Create change request and verify details', async ({ page }) => {
    // Create a project first
    await page.goto('/');
    await page.click('text=Create New Project');
    await page.fill('input[name="name"]', 'CR Test Project');
    await page.fill('textarea[name="description"]', 'Project for CR testing');
    await page.click('button:has-text("Create")');
    await page.click('text=CR Test Project');

    // Navigate to Planner
    await page.click('text=Planner');
    
    // Create a change request
    await page.click('text=Create Change Request');
    await page.fill('input[name="title"]', 'Implement dark mode');
    await page.fill('textarea[name="description"]', 'Add dark mode theme toggle to the application');
    await page.click('button:has-text("Create")');

    // Verify CR is created and visible
    await page.waitForSelector('text=Implement dark mode', { timeout: 5000 });
    
    // Click on CR to view details
    await page.click('text=Implement dark mode');
    
    // Verify description is visible
    await expect(page.locator('text=Add dark mode theme toggle to the application')).toBeVisible();
  });

  test('Task status transitions', async ({ page }) => {
    // Setup: Create project and CR with tasks
    await page.goto('/');
    await page.click('text=Create New Project');
    await page.fill('input[name="name"]', 'Status Test Project');
    await page.fill('textarea[name="description"]', 'Project for status testing');
    await page.click('button:has-text("Create")');
    await page.click('text=Status Test Project');

    await page.click('text=Planner');
    await page.click('text=Create Change Request');
    await page.fill('input[name="title"]', 'Test feature');
    await page.fill('textarea[name="description"]', 'Feature for testing status transitions');
    await page.click('button:has-text("Create")');
    
    // Generate tasks
    await page.click('text=Test feature');
    await page.click('button:has-text("Generate Tasks")');
    await page.waitForSelector('text=Tasks generated', { timeout: 10000 });

    // Check initial status
    await page.click('text=Tasks');
    const initialTask = page.locator('[data-testid="task-card"]').first();
    await expect(initialTask).toHaveAttribute('data-status', 'planning');

    // Advance through statuses
    await page.click('text=Architect');
    const task = page.locator('[data-status="planning"]').first();
    if (await task.count() > 0) {
      await task.click();
      await page.click('button:has-text("Design")');
      await page.waitForSelector('text=Design complete', { timeout: 10000 });
    }

    // Verify status changed
    await page.click('text=Tasks');
    const updatedTask = page.locator('[data-testid="task-card"]').first();
    await expect(updatedTask).not.toHaveAttribute('data-status', 'planning');
  });

  test('Navigation and project context persistence', async ({ page }) => {
    // Create a project
    await page.goto('/');
    await page.click('text=Create New Project');
    await page.fill('input[name="name"]', 'Navigation Test');
    await page.fill('textarea[name="description"]', 'Testing navigation');
    await page.click('button:has-text("Create")');
    await page.click('text=Navigation Test');

    // Navigate through all pages
    const pages = ['Tasks', 'Planner', 'Architect', 'Review/Approval', 'Coder'];
    
    for (const pageName of pages) {
      await page.click(`text=${pageName}`);
      // Verify project context is maintained
      await expect(page.locator('text=Selected Project: Navigation Test')).toBeVisible();
    }

    // Reload page and verify project selection persists
    await page.reload();
    await expect(page.locator('text=Selected Project: Navigation Test')).toBeVisible();
  });
});
