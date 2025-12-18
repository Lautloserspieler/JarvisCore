#!/bin/bash
# Quick test runner for JARVIS Core

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║   JARVIS Core - Test Suite Runner                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend Tests
echo -e "${YELLOW}[1/2] Running Backend Tests (pytest)...${NC}"
cd backend

if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest not found. Installing dev dependencies...${NC}"
    pip install -r requirements-dev.txt
fi

if pytest tests/ -v --cov=. --cov-report=term --cov-report=html; then
    echo -e "${GREEN}✓ Backend tests passed!${NC}"
    BACKEND_PASSED=true
else
    echo -e "${RED}✗ Backend tests failed!${NC}"
    BACKEND_PASSED=false
fi

cd ..

# Frontend Tests
echo ""
echo -e "${YELLOW}[2/2] Running Frontend Tests (vitest)...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo -e "${RED}node_modules not found. Running npm install...${NC}"
    npm install
fi

if npm run test:run; then
    echo -e "${GREEN}✓ Frontend tests passed!${NC}"
    FRONTEND_PASSED=true
else
    echo -e "${RED}✗ Frontend tests failed!${NC}"
    FRONTEND_PASSED=false
fi

cd ..

# Summary
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Test Results Summary                               ║"
echo "╚══════════════════════════════════════════════════════╝"

if [ "$BACKEND_PASSED" = true ]; then
    echo -e "Backend:  ${GREEN}✓ PASSED${NC}"
else
    echo -e "Backend:  ${RED}✗ FAILED${NC}"
fi

if [ "$FRONTEND_PASSED" = true ]; then
    echo -e "Frontend: ${GREEN}✓ PASSED${NC}"
else
    echo -e "Frontend: ${RED}✗ FAILED${NC}"
fi

echo ""
echo "Coverage reports:"
echo "  Backend:  backend/htmlcov/index.html"
echo "  Frontend: frontend/coverage/index.html"
echo ""

if [ "$BACKEND_PASSED" = true ] && [ "$FRONTEND_PASSED" = true ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please fix them before committing.${NC}"
    exit 1
fi
