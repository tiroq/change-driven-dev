# E2E Test Suite - Quick Reference

## 🎯 Purpose

End-to-end tests for the Change-Driven Development web interface, covering the complete workflow from project creation to task implementation.

## 🚀 Quick Start

```bash
# 1. Ensure services are running
task status-bg

# 2. Run tests
task test-e2e

# 3. View report
task test-e2e-report
```

## 📦 What's Tested

### Complete Workflow
- ✅ Create project
- ✅ Add change request
- ✅ Generate tasks
- ✅ Process through Architect phase
- ✅ Review and approve
- ✅ Code implementation
- ✅ Verify completion

### Projects
- ✅ CRUD operations
- ✅ Selection and switching
- ✅ Validation
- ✅ Multi-project management

### Tasks
- ✅ Display and filtering
- ✅ Split/merge operations
- ✅ Status transitions
- ✅ Version history

### Change Requests
- ✅ Create and edit
- ✅ Generate tasks
- ✅ Link to tasks
- ✅ Status tracking

## 🧪 Test Commands

```bash
# Standard run
task test-e2e

# Interactive UI
task test-e2e-ui

# Visible browser
task test-e2e-headed

# Debug mode
task test-e2e-debug

# Install browsers (first time)
task test-e2e-install
```

## 📁 Test Files

- `workflow.spec.js` - Full workflow (15+ tests)
- `projects.spec.js` - Project management (8+ tests)
- `tasks.spec.js` - Task operations (9+ tests)
- `planner.spec.js` - Change requests (9+ tests)

## ⚙️ Configuration

**playwright.config.js**
- Base URL: http://localhost:5173
- Sequential execution
- Screenshots on failure
- Video recording on failure

## 🐛 Debugging

```bash
# View screenshots
ls frontend/test-results/

# View trace
npx playwright show-trace test-results/<test>/trace.zip

# Check logs
task logs-backend
task logs-frontend
```

## 📊 Coverage

- **42+ test cases**
- **All major user flows**
- **Error handling**
- **State persistence**

## 📚 Documentation

See [docs/TESTING.md](../../docs/TESTING.md) for comprehensive guide.

## ✅ Success Criteria

All tests passing indicates:
- ✅ UI is functional
- ✅ API integration works
- ✅ Workflow completes successfully
- ✅ Data persists correctly
- ✅ Navigation works
- ✅ State management is correct
