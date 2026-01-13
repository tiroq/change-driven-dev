/**
 * Test setup utilities and helper functions
 */

export const API_BASE = 'http://localhost:8000/api';

/**
 * Wait for the backend to be ready
 */
export async function waitForBackend(maxAttempts = 30, interval = 1000) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await fetch(`${API_BASE}/projects/`);
      if (response.ok) {
        return true;
      }
    } catch (error) {
      // Backend not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  throw new Error('Backend did not become ready in time');
}

/**
 * Clean up all test data
 */
export async function cleanupTestData() {
  try {
    // Get all projects
    const projectsResponse = await fetch(`${API_BASE}/projects/`);
    const projects = await projectsResponse.json();
    
    // Delete all projects (this should cascade delete related data)
    for (const project of projects) {
      await fetch(`${API_BASE}/projects/${project.id}`, {
        method: 'DELETE',
      });
    }
    
    // Give the backend a moment to settle after cleanup
    await new Promise(resolve => setTimeout(resolve, 500));
  } catch (error) {
    console.error('Cleanup failed:', error);
  }
}

/**
 * Create a test project
 */
export async function createTestProject(name = 'Test Project', description = 'E2E test project') {
  const response = await fetch(`${API_BASE}/projects/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to create project: ${response.status} - ${text}`);
  }
  
  return await response.json();
}

/**
 * Create a test change request
 */
export async function createTestChangeRequest(title = 'Test Change Request', description = 'E2E test CR') {
  const response = await fetch(`${API_BASE}/change-requests/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  });
  return await response.json();
}

/**
 * Get all tasks for a project
 */
export async function getProjectTasks(projectId) {
  const response = await fetch(`${API_BASE}/tasks/?project_id=${projectId}`);
  return await response.json();
}
