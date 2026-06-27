@echo off
setlocal enabledelayedexpansion

set PROJECT_DIR=%~dp0
set BACKEND_DIR=%PROJECT_DIR%backend
set FRONTEND_DIR=%PROJECT_DIR%frontend
set BACKEND_PORT=8000
set FRONTEND_PORT=5173

echo.
echo ==========================================
echo   ScoreForge - Start Services
echo ==========================================
echo.

:: Check ports
netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING" >nul 2>&1
if !errorlevel!==0 (
    echo [ERROR] Port %BACKEND_PORT% is in use. Run stop.bat first.
    pause
    exit /b 1
)

netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" >nul 2>&1
if !errorlevel!==0 (
    echo [ERROR] Port %FRONTEND_PORT% is in use. Run stop.bat first.
    pause
    exit /b 1
)

:: Start backend
echo [1/2] Starting backend...
cd /d "%BACKEND_DIR%"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
start "ScoreForge-Backend" cmd /c "uvicorn app.main:app --reload --host 0.0.0.0 --port %BACKEND_PORT%"
echo   Backend window opened.

echo   Waiting for backend...
set BACKEND_READY=0
for /l %%i in (1,1,30) do (
    if !BACKEND_READY!==0 (
        curl -s http://localhost:%BACKEND_PORT%/health >nul 2>&1
        if !errorlevel!==0 (
            set BACKEND_READY=1
            echo   [OK] Backend is ready
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)

if !BACKEND_READY!==0 (
    echo   [WARN] Backend startup timeout, check the backend window
)

:: Start frontend
echo [2/2] Starting frontend...
cd /d "%FRONTEND_DIR%"
start "ScoreForge-Frontend" cmd /c "npm run dev:h5"
echo   Frontend window opened.

echo   Waiting for frontend...
set FRONTEND_READY=0
for /l %%i in (1,1,30) do (
    if !FRONTEND_READY!==0 (
        curl -s http://localhost:%FRONTEND_PORT% >nul 2>&1
        if !errorlevel!==0 (
            set FRONTEND_READY=1
            echo   [OK] Frontend is ready
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)

if !FRONTEND_READY!==0 (
    echo   [WARN] Frontend startup timeout, check the frontend window
)

echo.
echo ==========================================
echo   All services started
echo.
echo   Backend API:  http://localhost:%BACKEND_PORT%
echo   API Docs:     http://localhost:%BACKEND_PORT%/docs
echo   Frontend:     http://localhost:%FRONTEND_PORT%
echo.
echo   Close the Backend/Frontend windows to stop
echo ==========================================
echo.

start http://localhost:%FRONTEND_PORT%

pause
