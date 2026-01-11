# E2E Test Suite

End-to-end tests for the Change-Driven Development web interface.

## Overview

This test suite uses [Playwright](https://playwright.dev/) to test the complete user workflow from creating projects to managing tasks through all phases.

## Test Files

- **workflow.spec.js** - Complete workflow tests covering the full cycle
- **projects.spec.js** - Project management tests (CRUD operations)
- **tasks.spec.js** - Task management and manipulation tests
- **planner.spec.js** - Change request and planning tests
- **setup.js** - Shared utilities and helper functions

## Prerequisites

1. **Backend must be running** on `http://localhost:8000`
2. **Frontend development server** on `http://localhost:5173`

Start both services:
```bash
# From project root
task start-bg

# Or run them separately
task backend-bg
task frontend-bg
```

## Running Tests

### Run all tests
```bash
npm test
```

### Run tests with UI mode (interactive)
```bash
npm run test:ui
```

### Run tests in headed mode (see browser)
```bash
npm run test:headed
```

### Run specific test file
```bash
npx playwright test workflow.spec.js
```

### Run tests in debug mode
```bash
npm run test:debug
```

### View test report
```bash
npm run test:report
```

## Test Coverage

### Full Workflow Test
Tests the complete user journey:
1. Create a new project
2. Add a change request
3. Generate tasks from the change request
4. Process tasks through Architect phase
5. Review and approve tasks
6. Implement tasks in Coder phase
7. Verify completion

### Projects Tests
- Display projects list
- Create new projects
- Edit existing projects
- Delete projects
- Select and switch between projects
- Project context persistence

### Tasks Tests
- Display tasks for a project
- View task details
- Filter tasks by status
- Split tasks into subtasks
- Merge multiple tasks
- View task version history
- Track task status transitions

### Planner Tests
- Create change requests
- Edit/delete change requests
- Generate tasks from change requests
- Link tasks to change requests
- Display change request status

## Writing New Tests

1. Create a new `.spec.js` file in `tests/e2e/`
2. Import helpers from `setup.js`:
```javascript
import { test, expect } from '@playwright/test';
import { waitForBackend, cleanupTestData, createTestProject } from './setup.js';
```

3. Add cleanup in beforeEach:
```javascript
test.beforeEach(async () => {
  await cleanupTestData();
});
```

4. Write your tests using Playwright API

## Selectors Strategy

Tests use a combination of:
- **Data attributes**: `[data-testid="task-card"]` (preferred for stable selection)
- **Text content**: `text=Create Project` (for buttons and labels)
- **Semantic HTML**: Role-based selectors when appropriate

## CI/CD Integration

The tests are configured to run in CI mode with:
- Automatic retries (2 attempts)
- Screenshot on failure
- Video recording on failure
- HTML report generation

Example GitHub Actions workflow:
```yaml
- name: Install dependencies
  run: npm ci
  working-directory: frontend
  
- name: Install Playwright browsers
  run: npx playwright install --with-deps
  working-directory: frontend
  
- name: Run E2E tests
  run: npm test
  working-directory: frontend
```

## Troubleshooting

### Tests timing out
- Increase timeout in `playwright.config.js`
- Check backend is running and accessible
- Verify database is responsive

### Tests failing randomly
- Increase wait times for async operations
- Add explicit waits for elements
- Check for race conditions

### Browser not launching
- Install Playwright browsers: `npx playwright install`
- Check system dependencies

### Backend connection errors
- Verify backend is running: `curl http://localhost:8000/api/projects/`
- Check backend logs: `task logs-backend`
- Restart services: `task restart-bg`

## Best Practices

1. **Clean state**: Always cleanup data before/after tests
2. **Explicit waits**: Use `waitForSelector` instead of arbitrary timeouts
3. **Unique test data**: Use descriptive names to identify test data
4. **Independent tests**: Each test should run independently
5. **Meaningful assertions**: Assert on actual user-visible behavior
6. **Error messages**: Use descriptive expect messages

## Performance

- Tests run sequentially (1 worker) to avoid database conflicts
- Average test run time: ~2-3 minutes for full suite
- Individual test: 10-30 seconds depending on complexity

## Debugging

To debug a failing test:

1. Run in debug mode:
```bash
npx playwright test --debug workflow.spec.js
```

2. Use the Playwright Inspector to step through tests

3. Check screenshots and videos in `test-results/` folder

4. View detailed trace:
```bash
npx playwright show-trace test-results/<test-name>/trace.zip
```
