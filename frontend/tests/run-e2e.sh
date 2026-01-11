#!/bin/bash
# E2E Test Runner Script
# Ensures backend and frontend are running before executing tests

set -e

echo "🧪 E2E Test Runner"
echo "=================="
echo ""

# Check if backend is running
check_backend() {
    echo "Checking backend..."
    if curl -s http://localhost:8000/api/projects/ > /dev/null 2>&1; then
        echo "✓ Backend is running"
        return 0
    else
        echo "✗ Backend is not running"
        return 1
    fi
}

# Check if frontend is running
check_frontend() {
    echo "Checking frontend..."
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo "✓ Frontend is running"
        return 0
    else
        echo "✗ Frontend is not running"
        return 1
    fi
}

# Start services if not running
START_SERVICES=false

if ! check_backend || ! check_frontend; then
    echo ""
    echo "Services are not running."
    read -p "Start services automatically? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        START_SERVICES=true
        echo ""
        echo "Starting services..."
        cd ..
        task start-bg
        cd frontend
        
        # Wait for services to be ready
        echo "Waiting for services to start..."
        sleep 5
        
        # Verify they're running
        if ! check_backend || ! check_frontend; then
            echo ""
            echo "❌ Failed to start services. Please start them manually:"
            echo "   task start-bg"
            exit 1
        fi
    else
        echo ""
        echo "Please start the services manually:"
        echo "   task start-bg"
        echo ""
        echo "Or run them separately:"
        echo "   task backend-bg"
        echo "   task frontend-bg"
        exit 1
    fi
fi

echo ""
echo "🎬 Running E2E tests..."
echo ""

# Run tests
npm test -- "$@"

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Exit code: $TEST_EXIT_CODE"
    echo ""
    echo "View detailed report:"
    echo "   npm run test:report"
fi

# If we started services, ask if we should stop them
if [ "$START_SERVICES" = true ]; then
    echo ""
    read -p "Stop services? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd ..
        task stop-bg
        cd frontend
    fi
fi

exit $TEST_EXIT_CODE
