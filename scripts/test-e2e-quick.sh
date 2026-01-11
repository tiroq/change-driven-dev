#!/bin/bash
# Quick test runner - checks services and runs E2E tests

set -e

echo "🧪 Quick E2E Test Runner"
echo "======================="
echo ""

# Check if services are running
if curl -s http://localhost:8000/api/projects/ > /dev/null 2>&1 && \
   curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✓ Services are running"
else
    echo "✗ Services not running. Starting..."
    cd "$(dirname "$0")/.."
    task start-bg
    echo "Waiting for services to start..."
    sleep 5
fi

echo ""
echo "Running tests..."
cd "$(dirname "$0")/../frontend"
npm test -- "$@"
