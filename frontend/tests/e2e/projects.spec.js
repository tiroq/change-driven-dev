import { test, expect } from '@playwright/test';
import { waitForBackend, cleanupTestData } from './setup.js';

test.describe('Projects Page Tests', () => {
  test.beforeAll(async () => {
    await waitForBackend();
  });

  test.beforeEach(async ({ page }) => {
    await cleanupTestData();
    await page.goto('/');
  });

  test('should display projects page with header', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Change-Driven Development');
    await expect(page.locator('h2:has-text("Projects")')).toBeVisible();
  });

  test('should create a new project', async ({ page }) => {
    await page.click('button:has-text("+ New Project")');
    
    // Wait for form to appear
    await page.waitForSelector('input[name="name"]', { state: 'visible' });
    
    // Fill in project details
    await page.fill('input[name="name"]', 'New Test Project');
    await page.fill('textarea[name="description"]', 'This is a test project description');
    
    // Set up response waiter BEFORE clicking
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/api/projects/') && 
      response.request().method() === 'POST'
    );
    
    // Submit the form
    await page.click('button:has-text("Create Project")');
    
    // Wait for POST to complete
    await responsePromise;
    
    // Wait for project to appear (gives time for reload)
    await page.waitForSelector('text=New Test Project', { timeout: 10000 });
    
    // Verify project is displayed
    await expect(page.locator('text=New Test Project')).toBeVisible();
    await expect(page.locator('text=This is a test project description')).toBeVisible();
  });

  test('should validate project creation form', async ({ page }) => {
    await page.click('button:has-text("+ New Project")');
    
    // Try to submit without filling required fields
    await page.click('button:has-text("Create Project")');
    
    // Should show validation errors or stay on form
    const nameInput = page.locator('input[name="name"]');
    await expect(nameInput).toBeVisible();
  });

  test('should edit an existing project', async ({ page }) => {
    // Create a project first
    await page.click('button:has-text("+ New Project")');
    await page.waitForSelector('input[name="name"]', { state: 'visible' });
    await page.fill('input[name="name"]', 'Project to Edit');
    await page.fill('textarea[name="description"]', 'Original description');
    
    const responsePromise = page.waitForResponse(r => r.url().includes('/api/projects/') && r.request().method() === 'POST');
    await page.click('button:has-text("Create Project")');
    await responsePromise;
    await page.waitForSelector('text=Project to Edit', { timeout: 10000 });
    
    await expect(page.locator('text=Project to Edit')).toBeVisible();
    
    // Edit the project
    await page.click('button:has-text("Edit")');
    await page.fill('input[name="name"]', 'Edited Project Name');
    await page.fill('textarea[name="description"]', 'Updated description');
    await page.click('button:has-text("Save")');
    
    // Verify changes
    await page.waitForSelector('text=Edited Project Name', { timeout: 5000 });
    await expect(page.locator('text=Edited Project Name')).toBeVisible();
    await expect(page.locator('text=Updated description')).toBeVisible();
  });

  test('should delete a project', async ({ page }) => {
    // Create a project first
    await page.click('button:has-text("+ New Project")');
    await page.waitForSelector('input[name="name"]', { state: 'visible' });
    await page.fill('input[name="name"]', 'Project to Delete');
    await page.fill('textarea[name="description"]', 'Will be deleted');
    
    const responsePromise = page.waitForResponse(r => r.url().includes('/api/projects/') && r.request().method() === 'POST');
    await page.click('button:has-text("Create Project")');
    await responsePromise;
    await page.waitForSelector('text=Project to Delete', { timeout: 10000 });
    
    await expect(page.locator('text=Project to Delete')).toBeVisible();
    
    // Delete the project
    await page.click('button:has-text("Delete")');
    
    // Confirm deletion if there's a confirmation dialog
    const confirmButton = page.locator('button:has-text("Confirm")');
    if (await confirmButton.count() > 0) {
      await confirmButton.click();
    }
    
    // Verify project is removed
    await expect(page.locator('text=Project to Delete')).not.toBeVisible();
  });

  test('should select a project', async ({ page }) => {
    // Create a project
    await page.click('button:has-text("+ New Project")');
    await page.waitForSelector('input[name="name"]', { state: 'visible' });
    await page.fill('input[name="name"]', 'Selectable Project');
    await page.fill('textarea[name="description"]', 'Test selection');
    
    const responsePromise = page.waitForResponse(r => r.url().includes('/api/projects/') && r.request().method() === 'POST');
    await page.click('button:has-text("Create Project")');
    await responsePromise;
    await page.waitForSelector('text=Selectable Project', { timeout: 10000 });
    
    await expect(page.locator('text=Selectable Project')).toBeVisible();
    
    // Click to select
    await page.click('text=Selectable Project');
    
    // Verify project is selected
    await expect(page.locator('text=Selected Project: Selectable Project')).toBeVisible();
  });

  test('should display empty state when no projects exist', async ({ page }) => {
    // Should show empty state or create button
    const createButton = page.locator('button:has-text("+ New Project")');
    await expect(createButton).toBeVisible();
  });

  test('should list multiple projects', async ({ page }) => {
    // Create multiple projects
    const projects = [
      { name: 'Project 1', description: 'First project' },
      { name: 'Project 2', description: 'Second project' },
      { name: 'Project 3', description: 'Third project' },
    ];
    
    for (const project of projects) {
      await page.click('button:has-text("+ New Project")');
      await page.waitForSelector('input[name="name"]', { state: 'visible' });
      await page.fill('input[name="name"]', project.name);
      await page.fill('textarea[name="description"]', project.description);
      
      const responsePromise = page.waitForResponse(r => r.url().includes('/api/projects/') && r.request().method() === 'POST');
      await page.click('button:has-text("Create Project")');
      await responsePromise;
      await page.waitForSelector(`text=${project.name}`, { timeout: 10000 });
    }
    
    // Verify all projects are visible
    for (const project of projects) {
      await expect(page.locator(`text=${project.name}`)).toBeVisible();
    }
  });
});
