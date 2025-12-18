@echo off
REM Quick test runner for JARVIS Core (Windows)

echo ╔══════════════════════════════════════════════════════╗
echo ║   JARVIS Core - Test Suite Runner                   ║
echo ╚══════════════════════════════════════════════════════╝
echo.

SET BACKEND_PASSED=false
SET FRONTEND_PASSED=false

REM Backend Tests
echo [1/2] Running Backend Tests (pytest)...
cd backend

pytest --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo pytest not found. Installing dev dependencies...
    pip install -r requirements-dev.txt
)

pytest tests\ -v --cov=. --cov-report=term --cov-report=html
IF %ERRORLEVEL% EQU 0 (
    echo ✓ Backend tests passed!
    SET BACKEND_PASSED=true
) ELSE (
    echo ✗ Backend tests failed!
)

cd ..

REM Frontend Tests
echo.
echo [2/2] Running Frontend Tests (vitest)...
cd frontend

IF NOT EXIST "node_modules" (
    echo node_modules not found. Running npm install...
    npm install
)

npm run test:run
IF %ERRORLEVEL% EQU 0 (
    echo ✓ Frontend tests passed!
    SET FRONTEND_PASSED=true
) ELSE (
    echo ✗ Frontend tests failed!
)

cd ..

REM Summary
echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║   Test Results Summary                               ║
echo ╚══════════════════════════════════════════════════════╝

IF "%BACKEND_PASSED%"=="true" (
    echo Backend:  ✓ PASSED
) ELSE (
    echo Backend:  ✗ FAILED
)

IF "%FRONTEND_PASSED%"=="true" (
    echo Frontend: ✓ PASSED
) ELSE (
    echo Frontend: ✗ FAILED
)

echo.
echo Coverage reports:
echo   Backend:  backend\htmlcov\index.html
echo   Frontend: frontend\coverage\index.html
echo.

IF "%BACKEND_PASSED%"=="true" IF "%FRONTEND_PASSED%"=="true" (
    echo 🎉 All tests passed!
    exit /b 0
) ELSE (
    echo ❌ Some tests failed. Please fix them before committing.
    exit /b 1
)
