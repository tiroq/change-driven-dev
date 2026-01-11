# Testing Guide

## E2E Testing with Playwright

This project includes comprehensive end-to-end tests that verify the complete user workflow.

## Quick Start

### 1. Install Playwright Browsers

First time only:
```bash
task test-e2e-install
```

Or from frontend directory:
```bash
npx playwright install --with-deps
```

### 2. Start the Application

E2E tests require both backend and frontend to be running:
```bash
task start-bg
```

Verify both are running:
```bash
task status-bg
```

Should show:
```
✓ Backend  - Running (PID: xxxx) - http://localhost:8000
✓ Frontend - Running (PID: xxxx) - http://localhost:5173
```

### 3. Run Tests

```bash
task test-e2e
```

## Test Modes

### Headless Mode (Default)
Runs tests without visible browser:
```bash
task test-e2e
```

### UI Mode (Interactive)
Opens Playwright UI for interactive testing:
```bash
task test-e2e-ui
```

### Headed Mode
Runs tests with visible browser:
```bash
task test-e2e-headed
```

### Debug Mode
Step through tests with debugging tools:
```bash
task test-e2e-debug
```

### View Report
After test run, view HTML report:
```bash
task test-e2e-report
```

## Test Structure

### Test Files

Located in `frontend/tests/e2e/`:

- **workflow.spec.js** - Full end-to-end workflow tests
  - Complete project → CR → tasks → implementation cycle
  - Multi-project management
  - Status transitions
  - Navigation and persistence

- **projects.spec.js** - Project management
  - Create/edit/delete projects
  - Project selection
  - Validation
  - Multi-project scenarios

- **tasks.spec.js** - Task operations
  - Task listing and filtering
  - Task details
  - Split/merge operations
  - Version history
  - Status tracking

- **planner.spec.js** - Change request management
  - CR creation and editing
  - Task generation from CRs
  - CR-task linking
  - Status display

### Helper Functions

`setup.js` provides utilities:
- `waitForBackend()` - Wait for API to be ready
- `cleanupTestData()` - Clean database between tests
- `createTestProject()` - Create test project via API
- `createTestChangeRequest()` - Create test CR via API
- `getProjectTasks()` - Get tasks for a project

## Workflow Test Coverage

### Complete User Journey

The main workflow test covers:

1. **Project Creation**
   - Navigate to projects page
   - Create new project
   - Select project

2. **Change Request**
   - Navigate to planner
   - Create change request
   - Add details

3. **Task Generation**
   - Generate tasks from CR
   - Verify tasks created

4. **Architect Phase**
   - View planning tasks
   - Design tasks
   - Verify status change

5. **Review Phase**
   - Review designed tasks
   - Approve tasks

6. **Coding Phase**
   - Implement approved tasks
   - Verify completion

7. **Verification**
   - Check final status
   - Verify workflow completion

## Running Individual Tests

```bash
# From frontend directory
cd frontend

# Run specific test file
npx playwright test workflow.spec.js

# Run specific test by name
npx playwright test -g "Complete workflow"

# Run tests matching pattern
npx playwright test projects
```

## Debugging Failed Tests

### 1. Check Test Output
Tests create detailed output showing each step:
```
✓ Projects page displayed
✓ Create button clicked
✓ Form filled
✗ Project not found after creation
```

### 2. View Screenshots
On failure, screenshots are saved to `test-results/`:
```bash
ls -la frontend/test-results/
```

### 3. View Videos
Videos of failed tests are in `test-results/`:
```bash
# Play with default video player
xdg-open frontend/test-results/*/video.webm
```

### 4. View Trace
Detailed execution trace:
```bash
npx playwright show-trace test-results/<test-name>/trace.zip
```

### 5. Check Logs
View application logs during test:
```bash
task logs-backend
task logs-frontend
```

### 6. Debug Interactively
```bash
task test-e2e-debug
```

This opens the Playwright Inspector where you can:
- Step through test execution
- Pause on errors
- Inspect element selectors
- View console output

## CI/CD Integration

Tests are configured for CI environments:

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          task setup
          task test-e2e-install
      
      - name: Start services
        run: task start-bg
      
      - name: Wait for services
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8000/api/projects/; do sleep 2; done'
      
      - name: Run E2E tests
        run: task test-e2e
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Troubleshooting

### "Backend not ready"
```bash
# Check backend is running
curl http://localhost:8000/api/projects/

# Check backend logs
task logs-backend

# Restart backend
task restart-bg
```

### "Frontend not ready"
```bash
# Check frontend is accessible
curl http://localhost:5173

# Check frontend logs
task logs-frontend

# Restart frontend
task restart-bg
```

### "Timeout waiting for selector"
Increase timeout in `playwright.config.js`:
```javascript
use: {
  timeout: 60000, // Increase from default
}
```

### "Browser not found"
Install Playwright browsers:
```bash
task test-e2e-install
```

### "Permission denied on test files"
Fix permissions:
```bash
chmod +x frontend/tests/run-e2e.sh
```

### Database state issues
Clean database before tests:
```bash
task clean-db
task start-bg
task test-e2e
```

## Best Practices

### 1. Clean State
Tests always start with clean database via `cleanupTestData()`

### 2. Stable Selectors
Use `data-testid` attributes for reliable element selection:
```jsx
<div data-testid="task-card">
```

### 3. Explicit Waits
Always wait for elements:
```javascript
await page.waitForSelector('text=Project Created', { timeout: 5000 });
```

### 4. Independent Tests
Each test should run independently without dependencies

### 5. Meaningful Names
Use descriptive test names:
```javascript
test('should create project and generate tasks from change request', ...)
```

## Performance

- **Full suite**: ~2-3 minutes
- **Individual test**: 10-30 seconds
- **Parallel execution**: Disabled (sequential for database safety)

## Next Steps

1. Add more specific test scenarios
2. Add API-level tests
3. Add performance benchmarks
4. Add accessibility tests
5. Add cross-browser testing
