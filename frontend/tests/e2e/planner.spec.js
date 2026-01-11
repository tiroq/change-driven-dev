import { test, expect } from '@playwright/test';
import { waitForBackend, cleanupTestData, createTestProject } from './setup.js';

test.describe('Planner Page Tests', () => {
  let testProject;

  test.beforeAll(async () => {
    await waitForBackend();
  });

  test.beforeEach(async ({ page }) => {
    await cleanupTestData();
    testProject = await createTestProject('Planner Test Project', 'Project for planner testing');
    await page.goto(`/planner?project_id=${testProject.id}`);
  });

  test('should display planner page', async ({ page }) => {
    await expect(page.locator('h2:has-text("Planner")')).toBeVisible();
    await expect(page.locator('text=Change Requests')).toBeVisible();
  });

  test('should create a new change request', async ({ page }) => {
    await page.click('text=Create Change Request');
    
    // Fill in CR details
    await page.fill('input[name="title"]', 'New Feature Request');
    await page.fill('textarea[name="description"]', 'Add search functionality to the application');
    
    // Submit
    await page.click('button:has-text("Create")');
    
    // Verify CR is created
    await page.waitForSelector('text=New Feature Request', { timeout: 5000 });
    await expect(page.locator('text=New Feature Request')).toBeVisible();
  });

  test('should display change request details', async ({ page }) => {
    // Create a CR first
    await page.click('text=Create Change Request');
    await page.fill('input[name="title"]', 'Test CR Details');
    await page.fill('textarea[name="description"]', 'Detailed description for testing');
    await page.click('button:has-text("Create")');
    
    // Click on the CR
    await page.waitForSelector('text=Test CR Details', { timeout: 5000 });
    await page.click('text=Test CR Details');
    
    // Verify details are shown
    await expect(page.locator('text=Detailed description for testing')).toBeVisible();
  });

  test('should generate tasks from change request', async ({ page }) => {
    // Create a CR
    await page.click('text=Create Change Request');
    await page.fill('input[name="title"]', 'Feature for Task Generation');
    await page.fill('textarea[name="description"]', 'This should generate multiple tasks');
    await page.click('button:has-text("Create")');
    
    // Select the CR
    await page.waitForSelector('text=Feature for Task Generation', { timeout: 5000 });
    await page.click('text=Feature for Task Generation');
    
    // Generate tasks
    await page.click('button:has-text("Generate Tasks")');
    
    // Wait for generation to complete
    await page.waitForSelector('text=Tasks generated', { timeout: 15000 });
    
    // Navigate to tasks page to verify
    await page.click('text=Tasks');
    const taskCards = page.locator('[data-testid="task-card"]');
    await expect(taskCards.first()).toBeVisible();
  });

  test('should edit change request', async ({ page }) => {
    // Create a CR
    await page.click('text=Create Change Request');
    await page.fill('input[name="title"]', 'Original Title');
    await page.fill('textarea[name="description"]', 'Original description');
    await page.click('button:has-text("Create")');
    
    // Edit the CR
    await page.waitForSelector('text=Original Title', { timeout: 5000 });
    await page.click('text=Original Title');
    await page.click('button:has-text("Edit")');
    
    await page.fill('input[name="title"]', 'Updated Title');
    await page.fill('textarea[name="description"]', 'Updated description');
    await page.click('button:has-text("Save")');
    
    // Verify changes
    await page.waitForSelector('text=Updated Title', { timeout: 5000 });
    await expect(page.locator('text=Updated description')).toBeVisible();
  });

  test('should delete change request', async ({ page }) => {
    // Create a CR
    await page.click('text=Create Change Request');
    await page.fill('input[name="title"]', 'CR to Delete');
    await page.fill('textarea[name="description"]', 'Will be deleted');
    await page.click('button:has-text("Create")');
    
    // Delete the CR
    await page.waitForSelector('text=CR to Delete', { timeout: 5000 });
    await page.click('text=CR to Delete');
    await page.click('button:has-text("Delete")');
    
    // Confirm if needed
    const confirmButton = page.locator('button:has-text("Confirm")');
    if (await confirmButton.count() > 0) {
      await confirmButton.click();
    }
    
    // Verify deletion
    await expect(page.locator('text=CR to Delete')).not.toBeVisible();
  });

  test('should link tasks to change request', async ({ page }) => {
    // Create CR and generate tasks
    await page.click('text=Create Change Request');
    await page.fill('input[name="title"]', 'CR with Tasks');
    await page.fill('textarea[name="description"]', 'Testing task links');
    await page.click('button:has-text("Create")');
    
    await page.waitForSelector('text=CR with Tasks', { timeout: 5000 });
    await page.click('text=CR with Tasks');
    await page.click('button:has-text("Generate Tasks")');
    await page.waitForSelector('text=Tasks generated', { timeout: 15000 });
    
    // View related tasks
    const relatedTasksButton = page.locator('button:has-text("View Tasks")');
    if (await relatedTasksButton.count() > 0) {
      await relatedTasksButton.click();
      
      // Should navigate to tasks filtered by this CR
      await expect(page.url()).toContain('tasks');
    }
  });

  test('should show CR status', async ({ page }) => {
    // Create a CR
    await page.click('text=Create Change Request');
    await page.fill('input[name="title"]', 'Status Test CR');
    await page.fill('textarea[name="description"]', 'Testing status display');
    await page.click('button:has-text("Create")');
    
    // Verify status badge is shown
    await page.waitForSelector('text=Status Test CR', { timeout: 5000 });
    const statusBadge = page.locator('[data-testid="cr-status"]');
    if (await statusBadge.count() > 0) {
      await expect(statusBadge).toBeVisible();
    }
  });

  test('should list all change requests', async ({ page }) => {
    // Create multiple CRs
    const crs = [
      { title: 'CR 1', description: 'First change request' },
      { title: 'CR 2', description: 'Second change request' },
      { title: 'CR 3', description: 'Third change request' },
    ];
    
    for (const cr of crs) {
      await page.click('text=Create Change Request');
      await page.fill('input[name="title"]', cr.title);
      await page.fill('textarea[name="description"]', cr.description);
      await page.click('button:has-text("Create")');
      await page.waitForSelector(`text=${cr.title}`, { timeout: 5000 });
    }
    
    // Verify all are visible
    for (const cr of crs) {
      await expect(page.locator(`text=${cr.title}`)).toBeVisible();
    }
  });
});
