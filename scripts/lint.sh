#!/bin/bash
# Linting script

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Running linters...${NC}\n"

# Backend linting
echo -e "${BLUE}=== Backend (ruff) ===${NC}"
cd backend
if ruff check app/; then
    echo -e "${GREEN}✓ Backend lint passed${NC}\n"
else
    echo -e "${RED}✗ Backend lint failed${NC}\n"
    cd ..
    exit 1
fi
cd ..

# Frontend linting
echo -e "${BLUE}=== Frontend (eslint) ===${NC}"
cd frontend
if npm run lint; then
    echo -e "${GREEN}✓ Frontend lint passed${NC}\n"
else
    echo -e "${RED}✗ Frontend lint failed${NC}\n"
    cd ..
    exit 1
fi
cd ..

echo -e "${GREEN}All linting checks passed!${NC}"
