import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
});

test('Debug button click', async ({ page }) => {
  // Check button exists
  const button = page.locator('button:has-text("+ New Project")');
  await expect(button).toBeVisible();
  console.log('Button found and visible');
  
  // Click it
  await button.click();
  console.log('Button clicked');
  
  // Wait a bit
  await page.waitForTimeout(1000);
  
  // Check if form appeared
  const form = page.locator('h3:has-text("Create New Project")');
  const isVisible = await form.isVisible();
  console.log('Form visible:', isVisible);
  
  // Check for name input
  const nameInput = page.locator('input[name="name"]');
  const nameVisible = await nameInput.isVisible();
  console.log('Name input visible:', nameVisible);
  
  // Try typing
  await page.fill('input[name="name"]', 'Test Project');
  console.log('Filled name field');
  
  // Check value
  const value = await nameInput.inputValue();
  console.log('Name input value:', value);
});
