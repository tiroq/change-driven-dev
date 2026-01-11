import { test, expect } from '@playwright/test';

/**
 * Smoke tests - Quick verification that basic functionality works
 * Run with: npx playwright test smoke.spec.js
 */

test.describe('Smoke Tests', () => {
  test('App loads and displays header', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Change-Driven Development');
  });

  test('Navigation menu is present', async ({ page }) => {
    await page.goto('/');
    
    const navLinks = ['Projects', 'Tasks', 'Planner', 'Architect', 'Review', 'Coder'];
    for (const link of navLinks) {
      await expect(page.getByRole('link', { name: link })).toBeVisible();
    }
  });

  test('Backend API is accessible', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/projects/');
    expect(response.ok()).toBeTruthy();
  });

  test('Can navigate to all main pages', async ({ page }) => {
    await page.goto('/');
    
    const pages = [
      { name: 'Projects', url: '/' },
      { name: 'Tasks', url: '/tasks' },
      { name: 'Planner', url: '/planner' },
      { name: 'Architect', url: '/architect' },
    ];
    
    for (const p of pages) {
      await page.click(`text=${p.name}`);
      await page.waitForURL(p.url);
      expect(page.url()).toContain(p.url);
    }
  });

  test('Projects page has create button', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('button:has-text("+ New Project")')).toBeVisible();
  });
});
