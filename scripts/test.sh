#!/bin/bash
# Test runner script

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_FAILED=0
FRONTEND_FAILED=0

echo -e "${BLUE}Running Change-Driven Development tests...${NC}\n"

# Backend tests
echo -e "${BLUE}=== Backend Tests ===${NC}"
cd backend
if python -m pytest tests/ -v --tb=short; then
    echo -e "${GREEN}✓ Backend tests passed${NC}\n"
else
    echo -e "${RED}✗ Backend tests failed${NC}\n"
    BACKEND_FAILED=1
fi
cd ..

# Frontend tests
echo -e "${BLUE}=== Frontend Tests ===${NC}"
cd frontend
if npm test -- --run 2>/dev/null || npm test; then
    echo -e "${GREEN}✓ Frontend tests passed${NC}\n"
else
    echo -e "${RED}✗ Frontend tests failed${NC}\n"
    FRONTEND_FAILED=1
fi
cd ..

# Summary
echo -e "${BLUE}=== Test Summary ===${NC}"
if [ $BACKEND_FAILED -eq 0 ] && [ $FRONTEND_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
